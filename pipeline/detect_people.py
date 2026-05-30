from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import torch
from ultralytics import YOLO


@dataclass
class DetectionStats:
    frames_processed: int = 0
    frames_with_people: int = 0
    total_people_detections: int = 0
    avg_fps: float = 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run YOLOv8 person detection on a video.")
    parser.add_argument("--video", required=True, help="Path to input video file.")
    parser.add_argument(
        "--max-width",
        type=int,
        default=1280,
        help="Maximum display width before downscaling.",
    )
    parser.add_argument(
        "--max-seconds",
        type=int,
        default=15,
        help="Optional safety limit for runtime. Set 0 to disable.",
    )
    return parser.parse_args()


def safe_resize(frame, max_width: int):
    height, width = frame.shape[:2]
    if width <= max_width:
        return frame

    scale = max_width / float(width)
    target_size = (int(width * scale), int(height * scale))
    return cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)


def draw_person_detections(frame, result) -> int:
    people_count = 0
    boxes = result.boxes
    if boxes is None:
        return people_count

    for box in boxes:
        cls_idx = int(box.cls[0].item())
        if cls_idx != 0:
            continue

        people_count += 1
        conf = float(box.conf[0].item())
        x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 0), 2)
        cv2.putText(
            frame,
            f"person {conf:.2f}",
            (x1, max(y1 - 8, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 220, 0),
            2,
        )

    return people_count


def run_detection(video_path: Path, max_width: int, max_seconds: int) -> tuple[DetectionStats, str, bool]:
    if not video_path.exists() or not video_path.is_file():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    model = YOLO("yolov8n.pt")
    device = "cpu"
    try:
        device = str(next(model.model.parameters()).device)
    except Exception:
        if torch.cuda.is_available():
            device = "cuda"

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    stats = DetectionStats()
    fps_start = time.perf_counter()
    frame_start = time.perf_counter()
    smoothed_fps = 0.0
    display_enabled = True
    stop_by_limit = False

    start_time = time.perf_counter()

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break

            stats.frames_processed += 1

            infer_result = model.predict(frame, classes=[0], verbose=False)[0]
            people_count = draw_person_detections(frame, infer_result)

            stats.total_people_detections += people_count
            if people_count > 0:
                stats.frames_with_people += 1

            now = time.perf_counter()
            instant_fps = 1.0 / max(now - frame_start, 1e-6)
            smoothed_fps = instant_fps if smoothed_fps == 0 else (0.9 * smoothed_fps + 0.1 * instant_fps)
            frame_start = now

            frame = safe_resize(frame, max_width=max_width)
            cv2.putText(
                frame,
                f"FPS: {smoothed_fps:.1f}",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255),
                2,
            )

            if display_enabled:
                try:
                    cv2.imshow("YOLOv8 Person Detection", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break
                except cv2.error:
                    # Gracefully continue in environments without GUI support.
                    display_enabled = False

            if max_seconds > 0 and (time.perf_counter() - start_time) >= max_seconds:
                stop_by_limit = True
                break

        total_time = max(time.perf_counter() - fps_start, 1e-6)
        stats.avg_fps = stats.frames_processed / total_time
        return stats, device, stop_by_limit
    finally:
        capture.release()
        cv2.destroyAllWindows()


def main() -> int:
    args = parse_args()

    try:
        stats, device, stop_by_limit = run_detection(
            video_path=Path(args.video),
            max_width=args.max_width,
            max_seconds=args.max_seconds,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Device: {device}")
    print(f"Frames processed: {stats.frames_processed}")
    print(f"Frames with people: {stats.frames_with_people}")
    print(f"Total person detections: {stats.total_people_detections}")
    print(f"Average FPS: {stats.avg_fps:.2f}")
    if stop_by_limit:
        print("Stopped by max-seconds limit.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
