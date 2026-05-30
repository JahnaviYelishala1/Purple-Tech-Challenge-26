from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2
from ultralytics import YOLO


@dataclass
class TrackRecord:
    track_id: int | None
    confidence: float
    bbox: tuple[int, int, int, int]
    center: tuple[float, float]


@dataclass
class TrackStats:
    frames_processed: int = 0
    detections_total: int = 0
    detections_with_id: int = 0
    frames_with_ids: int = 0
    avg_fps: float = 0.0
    id_switch_events: int = 0
    track_lifespans: dict[int, int] = field(default_factory=dict)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Track people using YOLOv8 on a video.")
    parser.add_argument("--video", required=True, help="Path to the input video file.")
    parser.add_argument(
        "--max-width",
        type=int,
        default=1280,
        help="Maximum display width before downscaling.",
    )
    parser.add_argument(
        "--max-seconds",
        type=int,
        default=0,
        help="Optional runtime cap for automated checks (0 means no limit).",
    )
    return parser.parse_args()


def safe_resize(frame, max_width: int):
    height, width = frame.shape[:2]
    if width <= max_width:
        return frame

    scale = max_width / float(width)
    target = (int(width * scale), int(height * scale))
    return cv2.resize(frame, target, interpolation=cv2.INTER_AREA)


def extract_track_records(result) -> list[TrackRecord]:
    records: list[TrackRecord] = []
    boxes = result.boxes
    if boxes is None:
        return records

    ids = boxes.id
    for idx, box in enumerate(boxes):
        confidence = float(box.conf[0].item())
        x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]
        center = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

        track_id: int | None = None
        if ids is not None and len(ids) > idx and ids[idx] is not None:
            try:
                track_id = int(ids[idx].item())
            except Exception:
                track_id = None

        records.append(
            TrackRecord(
                track_id=track_id,
                confidence=confidence,
                bbox=(x1, y1, x2, y2),
                center=center,
            )
        )

    return records


def estimate_id_switches(prev_records: list[TrackRecord], curr_records: list[TrackRecord]) -> int:
    """Estimate potential ID switches by nearest-neighbor center matching.

    If a current detection is close to a previous detection but has a different
    non-null track ID, count it as a likely switch.
    """

    if not prev_records or not curr_records:
        return 0

    switches = 0
    max_distance = 80.0

    for curr in curr_records:
        if curr.track_id is None:
            continue

        best_prev: TrackRecord | None = None
        best_dist = float("inf")

        for prev in prev_records:
            if prev.track_id is None:
                continue

            dx = curr.center[0] - prev.center[0]
            dy = curr.center[1] - prev.center[1]
            dist = math.hypot(dx, dy)
            if dist < best_dist:
                best_dist = dist
                best_prev = prev

        if best_prev is None or best_dist > max_distance:
            continue

        if best_prev.track_id != curr.track_id:
            switches += 1

    return switches


def draw_tracks(frame, records: list[TrackRecord], fps_text: str) -> int:
    active_tracked = 0

    for record in records:
        x1, y1, x2, y2 = record.bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), (20, 220, 20), 2)

        label_id = f"ID {record.track_id}" if record.track_id is not None else "ID N/A"
        label = f"{label_id} conf {record.confidence:.2f}"

        if record.track_id is not None:
            active_tracked += 1

        cv2.putText(
            frame,
            label,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (20, 220, 20),
            2,
        )

    cv2.putText(
        frame,
        fps_text,
        (15, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        frame,
        f"Active tracked people: {active_tracked}",
        (15, 62),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )

    return active_tracked


def run_tracking(video_path: Path, max_width: int, max_seconds: int) -> TrackStats:
    if not video_path.exists() or not video_path.is_file():
        raise FileNotFoundError(f"Video not found: {video_path}")

    model = YOLO("yolov8n.pt")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {video_path}")

    stats = TrackStats()
    wall_start = time.perf_counter()
    frame_start = time.perf_counter()
    run_start = time.perf_counter()
    smoothed_fps = 0.0
    prev_records: list[TrackRecord] = []
    display_enabled = True

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            stats.frames_processed += 1

            result = model.track(frame, persist=True, classes=[0], verbose=False)[0]
            records = extract_track_records(result)

            stats.detections_total += len(records)
            ids_this_frame = [r.track_id for r in records if r.track_id is not None]
            stats.detections_with_id += len(ids_this_frame)
            if ids_this_frame:
                stats.frames_with_ids += 1

            for track_id in ids_this_frame:
                stats.track_lifespans[track_id] = stats.track_lifespans.get(track_id, 0) + 1

            stats.id_switch_events += estimate_id_switches(prev_records, records)
            prev_records = records

            now = time.perf_counter()
            instant_fps = 1.0 / max(now - frame_start, 1e-6)
            smoothed_fps = instant_fps if smoothed_fps == 0.0 else (0.9 * smoothed_fps + 0.1 * instant_fps)
            frame_start = now

            frame = safe_resize(frame, max_width=max_width)
            draw_tracks(frame, records, fps_text=f"FPS: {smoothed_fps:.1f}")

            if display_enabled:
                try:
                    cv2.imshow("YOLOv8 Person Tracking", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break
                except cv2.error:
                    display_enabled = False

            if max_seconds > 0 and (time.perf_counter() - run_start) >= max_seconds:
                break

        elapsed = max(time.perf_counter() - wall_start, 1e-6)
        stats.avg_fps = stats.frames_processed / elapsed
        return stats
    finally:
        cap.release()
        cv2.destroyAllWindows()


def main() -> int:
    args = parse_args()

    try:
        stats = run_tracking(
            video_path=Path(args.video),
            max_width=args.max_width,
            max_seconds=args.max_seconds,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Frames processed: {stats.frames_processed}")
    print(f"Detections total: {stats.detections_total}")
    print(f"Detections with IDs: {stats.detections_with_id}")
    print(f"Frames with IDs: {stats.frames_with_ids}")
    print(f"Estimated ID switches: {stats.id_switch_events}")
    print(f"Average FPS: {stats.avg_fps:.2f}")

    if stats.track_lifespans:
        max_lifespan = max(stats.track_lifespans.values())
        print(f"Longest track lifespan (frames): {max_lifespan}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
