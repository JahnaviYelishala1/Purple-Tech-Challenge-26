from __future__ import annotations

import argparse
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import cv2
from ultralytics import YOLO

from camera_roles import camera_ids_for_role, get_camera_role
from event_publisher import publish_event
from event_confidence import resolve_event_confidence


@dataclass
class EntryStats:
    frames_processed: int = 0
    entries_detected: int = 0
    events: list[dict[str, str]] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect ENTRY events from person line crossing.")
    parser.add_argument("--video", required=True, help="Path to input video.")
    parser.add_argument(
        "--camera-id",
        default=camera_ids_for_role("ENTRANCE")[0] if camera_ids_for_role("ENTRANCE") else "",
        help="Camera identifier for emitted events.",
    )
    parser.add_argument("--store-id", default="STORE_BLR_001", help="Store identifier for emitted events.")
    parser.add_argument("--max-width", type=int, default=1280, help="Max display width.")
    parser.add_argument(
        "--max-seconds",
        type=int,
        default=20,
        help="Optional runtime limit for non-interactive runs (0 disables).",
    )
    return parser.parse_args()


def safe_resize(frame, max_width: int):
    height, width = frame.shape[:2]
    if width <= max_width:
        return frame

    scale = max_width / float(width)
    target_size = (int(width * scale), int(height * scale))
    return cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_entry_event(
    track_id: int,
    camera_id: str,
    store_id: str,
    *,
    event_type: str = "ENTRY",
    detection_confidence: float | None = None,
    tracker_confidence: float | None = None,
    fallback_confidence: float = 0.5,
) -> dict[str, str | int | float | bool | None]:
    return {
        "event_id": str(uuid.uuid4()),
        "visitor_id": f"track_{track_id}",
        "event_type": event_type,
        "camera_id": camera_id,
        "timestamp": current_timestamp(),
        "store_id": store_id,
        "zone_id": "entrance",
        "dwell_ms": 0,
        "is_staff": False,
        "confidence": resolve_event_confidence(
            detection_confidence=detection_confidence,
            tracker_confidence=tracker_confidence,
            fallback_confidence=fallback_confidence,
        ),
        "metadata": {
            "queue_depth": None,
            "sku_zone": "entrance",
            "session_seq": 0,
        },
    }


def draw_overlays(frame, line_x: int, entry_count: int, fps_value: float) -> None:
    cv2.line(frame, (line_x, 0), (line_x, frame.shape[0]), (0, 200, 255), 2)
    cv2.putText(
        frame,
        f"FPS: {fps_value:.1f}",
        (15, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
    )


def entry_line_x(frame_width: int, camera_role: str) -> int:
    """Return a line position for entry detection based on camera role."""

    if camera_role == "ENTRANCE":
        return max(1, int(frame_width * 0.35))
    return max(1, frame_width // 2)


def is_entry_crossing(previous_side: str | None, current_side: str, camera_role: str) -> bool:
    """Determine whether a tracked person has crossed the entrance line."""

    if previous_side is None or camera_role != "ENTRANCE":
        return False

    return previous_side == "left" and current_side == "right"


def detect_entries(
    video_path: Path,
    camera_id: str,
    store_id: str,
    max_width: int,
    max_seconds: int,
) -> EntryStats:
    if not video_path.exists() or not video_path.is_file():
        raise FileNotFoundError(f"Video not found: {video_path}")

    model = YOLO("yolov8n.pt")

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    camera_role = get_camera_role(camera_id)
    if camera_role != "ENTRANCE":
        print(f"Warning: camera {camera_id} is mapped to {camera_role}; ENTRY events will not be emitted.")

    stats = EntryStats()
    last_side_by_track: dict[int, str] = {}
    triggered_track_ids: set[int] = set()

    frame_start = time.perf_counter()
    smoothed_fps = 0.0
    run_start = time.perf_counter()
    display_enabled = True

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break

            stats.frames_processed += 1
            frame_width = frame.shape[1]
            line_x = entry_line_x(frame_width, camera_role)

            result = model.track(frame, persist=True, classes=[0], verbose=False)[0]
            boxes = result.boxes

            if boxes is not None:
                ids = boxes.id
                for idx, box in enumerate(boxes):
                    x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]
                    conf = float(box.conf[0].item())

                    track_id: int | None = None
                    if ids is not None and len(ids) > idx and ids[idx] is not None:
                        try:
                            track_id = int(ids[idx].item())
                        except Exception:
                            track_id = None

                    center_x = (x1 + x2) / 2.0
                    side = "left" if center_x < line_x else "right"

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (20, 220, 20), 2)
                    label_id = f"ID {track_id}" if track_id is not None else "ID N/A"
                    cv2.putText(
                        frame,
                        f"{label_id} conf {conf:.2f}",
                        (x1, max(20, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (20, 220, 20),
                        2,
                    )

                    if track_id is None:
                        continue

                    previous_side = last_side_by_track.get(track_id)
                    if is_entry_crossing(previous_side, side, camera_role) and track_id not in triggered_track_ids:
                        event = make_entry_event(
                            track_id=track_id,
                            camera_id=camera_id,
                            store_id=store_id,
                            detection_confidence=conf,
                        )
                        triggered_track_ids.add(track_id)
                        stats.entries_detected += 1
                        stats.events.append(event)
                        print(json.dumps(event))
                        if publish_event(event):
                            print("ENTRY EVENT SENT")

                    last_side_by_track[track_id] = side

            now = time.perf_counter()
            instant_fps = 1.0 / max(now - frame_start, 1e-6)
            smoothed_fps = instant_fps if smoothed_fps == 0.0 else (0.9 * smoothed_fps + 0.1 * instant_fps)
            frame_start = now

            draw_overlays(frame=frame, line_x=line_x, entry_count=stats.entries_detected, fps_value=smoothed_fps)
            frame = safe_resize(frame, max_width=max_width)

            if display_enabled:
                try:
                    cv2.imshow("ENTRY Detector", frame)
                    if (cv2.waitKey(1) & 0xFF) == ord("q"):
                        break
                except cv2.error:
                    display_enabled = False

            if max_seconds > 0 and (time.perf_counter() - run_start) >= max_seconds:
                break

        return stats
    finally:
        capture.release()
        cv2.destroyAllWindows()


def main() -> int:
    args = parse_args()

    try:
        stats = detect_entries(
            video_path=Path(args.video),
            camera_id=args.camera_id,
            store_id=args.store_id,
            max_width=args.max_width,
            max_seconds=args.max_seconds,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Frames processed: {stats.frames_processed}")
    print(f"Entries detected: {stats.entries_detected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
