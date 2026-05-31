from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PIPELINE_DIR = Path(__file__).resolve().parent
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

import cv2
from ultralytics import YOLO

from camera_roles import camera_ids_for_role, get_camera_role
from event_publisher import publish_event


@dataclass
class BillingStats:
    frames_processed: int = 0
    billing_events_detected: int = 0
    people_detected: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect BILLING_QUEUE_JOIN events from person tracking.")
    parser.add_argument("--video", required=True, help="Path to input video.")
    parser.add_argument(
        "--camera-id",
        default=camera_ids_for_role("BILLING")[0] if camera_ids_for_role("BILLING") else "",
        help="Camera identifier for emitted events.",
    )
    parser.add_argument("--store-id", default="STORE_BLR_001", help="Store identifier for emitted events.")
    parser.add_argument("--max-width", type=int, default=1280, help="Maximum display width.")
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


def billing_zone(frame_width: int, frame_height: int) -> tuple[int, int, int, int]:
    x1 = int(frame_width * 0.4)
    y1 = int(frame_height * 0.3)
    x2 = int(frame_width * 0.9)
    y2 = int(frame_height * 0.9)
    return x1, y1, x2, y2


def point_in_rectangle(x: float, y: float, rect: tuple[int, int, int, int]) -> bool:
    x1, y1, x2, y2 = rect
    return x1 <= x <= x2 and y1 <= y <= y2


def make_billing_event(track_id: int, camera_id: str, store_id: str) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "visitor_id": f"track_{track_id}",
        "event_type": "BILLING_QUEUE_JOIN",
        "camera_id": camera_id,
        "store_id": store_id,
        "timestamp": current_timestamp(),
        "zone_id": "billing",
        "dwell_ms": 0,
        "is_staff": False,
        "confidence": 0.95,
        "metadata": {
            "queue_depth": 1,
            "sku_zone": "billing",
            "session_seq": 0,
        },
    }


def draw_overlays(
    frame,
    zone: tuple[int, int, int, int],
    billing_count: int,
    fps_value: float,
) -> None:
    x1, y1, x2, y2 = zone
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 165, 0), 2)
    cv2.putText(
        frame,
        f"FPS: {fps_value:.1f}",
        (15, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        frame,
        f"Billing count: {billing_count}",
        (15, 62),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 165, 255),
        2,
    )


def detect_billing_queue(
    video_path: Path,
    camera_id: str,
    store_id: str,
    max_width: int,
    max_seconds: int,
) -> BillingStats:
    if not video_path.exists() or not video_path.is_file():
        raise FileNotFoundError(f"Video not found: {video_path}")

    model = YOLO("yolov8n.pt")
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    camera_role = get_camera_role(camera_id)
    if camera_role != "BILLING":
        print(f"Warning: camera {camera_id} is mapped to {camera_role}; BILLING events will not be emitted.")

    stats = BillingStats()
    last_inside_by_track: dict[int, bool] = {}
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
            zone = billing_zone(frame.shape[1], frame.shape[0])

            result = model.track(frame, persist=True, classes=[0], verbose=False)[0]
            boxes = result.boxes

            if boxes is not None:
                ids = boxes.id
                for idx, box in enumerate(boxes):
                    x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]
                    conf = float(box.conf[0].item())
                    stats.people_detected += 1

                    track_id: int | None = None
                    if ids is not None and len(ids) > idx and ids[idx] is not None:
                        try:
                            track_id = int(ids[idx].item())
                        except Exception:
                            track_id = None

                    center_x = (x1 + x2) / 2.0
                    center_y = (y1 + y2) / 2.0
                    inside = point_in_rectangle(center_x, center_y, zone)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 20), 2)
                    label_id = f"ID {track_id}" if track_id is not None else "ID N/A"
                    cv2.putText(
                        frame,
                        f"{label_id} conf {conf:.2f}",
                        (x1, max(20, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 220, 20),
                        2,
                    )

                    if track_id is None:
                        continue

                    previous_inside = last_inside_by_track.get(track_id, False)
                    if camera_role == "BILLING" and inside and not previous_inside and track_id not in triggered_track_ids:
                        event = make_billing_event(
                            track_id=track_id,
                            camera_id=camera_id,
                            store_id=store_id,
                        )
                        triggered_track_ids.add(track_id)
                        stats.billing_events_detected += 1
                        stats.events.append(event)
                        print(json.dumps(event))
                        if publish_event(event):
                            print("BILLING EVENT SENT")

                    last_inside_by_track[track_id] = inside

            now = time.perf_counter()
            instant_fps = 1.0 / max(now - frame_start, 1e-6)
            smoothed_fps = instant_fps if smoothed_fps == 0.0 else (0.9 * smoothed_fps + 0.1 * instant_fps)
            frame_start = now

            frame = safe_resize(frame, max_width=max_width)
            draw_overlays(frame, zone=zone, billing_count=stats.billing_events_detected, fps_value=smoothed_fps)

            if display_enabled:
                try:
                    cv2.imshow("Billing Detector", frame)
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
        stats = detect_billing_queue(
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
    print(f"People detected: {stats.people_detected}")
    print(f"Billing events detected: {stats.billing_events_detected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
