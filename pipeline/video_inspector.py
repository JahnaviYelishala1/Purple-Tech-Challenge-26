from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2


PERCENTAGES = (10, 50, 90)


@dataclass
class VideoSummary:
    filename: str
    duration_seconds: float
    fps: float
    frame_count: int
    resolution: str
    status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect MP4 files and extract preview frames at 10%, 50%, and 90%."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to a folder containing .mp4 files.",
    )
    return parser.parse_args()


def normalize_camera_name(video_path: Path) -> str:
    # CAM 1.mp4 -> CAM1, CAM_2.mp4 -> CAM2
    base = video_path.stem.replace(" ", "").replace("_", "")
    return base


def get_output_dir() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "outputs" / "previews"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def frame_index_for_percentage(frame_count: int, pct: int) -> int:
    if frame_count <= 0:
        return 0
    idx = int(frame_count * (pct / 100.0))
    idx = max(idx - 1, 0)
    return min(idx, frame_count - 1)


def inspect_video(video_path: Path, output_dir: Path) -> VideoSummary:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return VideoSummary(
            filename=video_path.name,
            duration_seconds=0.0,
            fps=0.0,
            frame_count=0,
            resolution="N/A",
            status="ERROR: unable to open video",
        )

    try:
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        duration = (frame_count / fps) if fps > 0 else 0.0
        resolution = f"{width}x{height}" if width > 0 and height > 0 else "N/A"

        camera_name = normalize_camera_name(video_path)
        save_errors: list[str] = []

        for pct in PERCENTAGES:
            frame_idx = frame_index_for_percentage(frame_count, pct)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, frame = cap.read()
            if not ok or frame is None:
                save_errors.append(f"{pct}%")
                continue

            output_path = output_dir / f"{camera_name}_{pct}.jpg"
            if not cv2.imwrite(str(output_path), frame):
                save_errors.append(f"{pct}%")

        status = "OK" if not save_errors else f"PARTIAL: failed at {', '.join(save_errors)}"
        return VideoSummary(
            filename=video_path.name,
            duration_seconds=duration,
            fps=fps,
            frame_count=frame_count,
            resolution=resolution,
            status=status,
        )
    except Exception as exc:
        return VideoSummary(
            filename=video_path.name,
            duration_seconds=0.0,
            fps=0.0,
            frame_count=0,
            resolution="N/A",
            status=f"ERROR: {exc}",
        )
    finally:
        cap.release()


def print_video_details(summary: VideoSummary) -> None:
    print(f"\nFile: {summary.filename}")
    print(f"  Duration (s): {summary.duration_seconds:.2f}")
    print(f"  FPS: {summary.fps:.2f}")
    print(f"  Frame Count: {summary.frame_count}")
    print(f"  Resolution: {summary.resolution}")
    print(f"  Status: {summary.status}")


def print_summary_table(summaries: Iterable[VideoSummary]) -> None:
    rows = list(summaries)
    if not rows:
        print("\nNo videos were processed.")
        return

    headers = ("Filename", "Duration(s)", "FPS", "Frames", "Resolution", "Status")
    data = [
        (
            row.filename,
            f"{row.duration_seconds:.2f}",
            f"{row.fps:.2f}",
            str(row.frame_count),
            row.resolution,
            row.status,
        )
        for row in rows
    ]

    widths = [len(h) for h in headers]
    for record in data:
        for i, value in enumerate(record):
            widths[i] = max(widths[i], len(value))

    def fmt(record: tuple[str, ...]) -> str:
        return " | ".join(value.ljust(widths[i]) for i, value in enumerate(record))

    print("\nSummary")
    print(fmt(headers))
    print("-+-".join("-" * width for width in widths))
    for record in data:
        print(fmt(record))


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input)

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input folder does not exist or is not a directory: {input_dir}")
        return 1

    video_paths = sorted(input_dir.glob("*.mp4"))
    if not video_paths:
        print(f"No .mp4 files found in: {input_dir}")
        return 1

    output_dir = get_output_dir()
    print(f"Scanning videos in: {input_dir}")
    print(f"Saving preview frames to: {output_dir}")

    summaries: list[VideoSummary] = []
    for video_path in video_paths:
        summary = inspect_video(video_path, output_dir)
        summaries.append(summary)
        print_video_details(summary)

    print_summary_table(summaries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
