from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from camera_roles import camera_ids_for_role, load_camera_roles


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = Path(sys.executable)
ENTRY_DETECTOR = PROJECT_ROOT / "pipeline" / "entry_detector.py"
BILLING_DETECTOR = PROJECT_ROOT / "pipeline" / "billing_detector.py"
VIDEO_DIR = PROJECT_ROOT / "CCTV Footage"
API_BASE_URL = "http://localhost:8000"
STORE_ID = "STORE_BLR_001"


@dataclass
class DetectorRunResult:
    name: str
    exit_code: int
    stdout: str
    stderr: str


def run_detector(name: str, script_path: Path, video_path: Path, camera_id: str) -> DetectorRunResult:
    command = [
        str(PYTHON_EXE),
        str(script_path),
        "--video",
        str(video_path),
        "--camera-id",
        camera_id,
        "--store-id",
        STORE_ID,
        "--max-seconds",
        "20",
    ]

    completed = subprocess.run(command, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    return DetectorRunResult(
        name=name,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def find_video_for_camera(camera_id: str) -> Path | None:
    normalized_camera_id = camera_id.upper().replace(" ", "").replace("_", "")
    for video_path in sorted(VIDEO_DIR.glob("*.mp4")):
        normalized_video_name = video_path.stem.upper().replace(" ", "").replace("_", "")
        if normalized_video_name == normalized_camera_id:
            return video_path
    return None


def count_generated_events(output: str, marker: str) -> int:
    return sum(1 for line in output.splitlines() if marker in line)


def fetch_json(path: str) -> tuple[bool, Any, str | None]:
    try:
        response = requests.get(f"{API_BASE_URL}{path}", timeout=5)
        response.raise_for_status()
        return True, response.json(), None
    except requests.RequestException as exc:
        return False, None, str(exc)
    except ValueError as exc:
        return False, None, f"Invalid JSON response: {exc}"


def format_section(title: str) -> None:
    print(title)


def print_summary_line(label: str, value: Any) -> None:
    print(f"{label}")
    if isinstance(value, (dict, list)):
        print(json.dumps(value, indent=2))
    else:
        print(value)
    print()


def main() -> int:
    roles = load_camera_roles()

    entrance_cameras = camera_ids_for_role("ENTRANCE")
    billing_cameras = camera_ids_for_role("BILLING")
    exit_cameras = camera_ids_for_role("EXIT")

    if not entrance_cameras:
        print("No ENTRANCE camera configured in config/camera_roles.json")
        return 1
    if not billing_cameras:
        print("No BILLING camera configured in config/camera_roles.json")
        return 1

    entry_camera = entrance_cameras[0]
    billing_camera = billing_cameras[0]

    entry_video = find_video_for_camera(entry_camera)
    billing_video = find_video_for_camera(billing_camera)
    if entry_video is None:
        print(f"Missing video for camera {entry_camera} in {VIDEO_DIR}")
        return 1
    if billing_video is None:
        print(f"Missing video for camera {billing_camera} in {VIDEO_DIR}")
        return 1

    entry_run = run_detector("entry", ENTRY_DETECTOR, entry_video, entry_camera)
    billing_run = run_detector("billing", BILLING_DETECTOR, billing_video, billing_camera)

    entries_detected = count_generated_events(entry_run.stdout, '"event_type": "ENTRY"')
    billing_events_detected = count_generated_events(billing_run.stdout, '"event_type": "BILLING_QUEUE_JOIN"')

    metrics_ok, metrics_data, metrics_error = fetch_json(f"/stores/{STORE_ID}/metrics")
    funnel_ok, funnel_data, funnel_error = fetch_json(f"/stores/{STORE_ID}/funnel")
    pipeline_ok, pipeline_data, pipeline_error = fetch_json(f"/stores/{STORE_ID}/pipeline-status")
    heatmap_ok, heatmap_data, heatmap_error = fetch_json(f"/stores/{STORE_ID}/heatmap")
    anomalies_ok, anomalies_data, anomalies_error = fetch_json(f"/stores/{STORE_ID}/anomalies")

    print("================================")
    print("STORE INTELLIGENCE DEMO SUMMARY")
    print("================================")
    print()

    print(f"Configured Camera Roles:\n{json.dumps(roles, indent=2)}\n")
    if exit_cameras:
        print(f"Exit cameras configured: {', '.join(exit_cameras)}\n")
    else:
        print("Exit cameras configured: none\n")

    print(f"Entries Detected:\n{entries_detected}\n")
    print(f"Billing Queue Events:\n{billing_events_detected}\n")

    if metrics_ok and isinstance(metrics_data, dict):
        print(f"Conversion Rate:\n{metrics_data.get('conversion_rate')}\n")
    else:
        print(f"Conversion Rate:\nAPI ERROR: {metrics_error}\n")

    if funnel_ok and isinstance(funnel_data, dict):
        print("Funnel Stages:")
        print(json.dumps(funnel_data.get("stages", []), indent=2))
        print()
    else:
        print(f"Funnel Stages:\nAPI ERROR: {funnel_error}\n")

    if pipeline_ok and isinstance(pipeline_data, dict):
        print("CCTV Pipeline Status:")
        print(json.dumps(pipeline_data, indent=2))
        print()
    else:
        print(f"CCTV Pipeline Status:\nAPI ERROR: {pipeline_error}\n")

    if heatmap_ok and isinstance(heatmap_data, dict):
        print("Heatmap Zones:")
        print(json.dumps(heatmap_data.get("zones", []), indent=2))
        print()
    else:
        print(f"Heatmap Zones:\nAPI ERROR: {heatmap_error}\n")

    if anomalies_ok and isinstance(anomalies_data, dict):
        print("Active Anomalies:")
        print(json.dumps(anomalies_data.get("anomalies", []), indent=2))
        print()
    else:
        print(f"Active Anomalies:\nAPI ERROR: {anomalies_error}\n")

    print("Detector Results:")
    print(f"- Entry detector exit code: {entry_run.exit_code}")
    print(f"- Billing detector exit code: {billing_run.exit_code}")

    if entry_run.exit_code != 0:
        print("\nEntry detector stderr:")
        print(entry_run.stderr)
    if billing_run.exit_code != 0:
        print("\nBilling detector stderr:")
        print(billing_run.stderr)

    return 0 if entry_run.exit_code == 0 and billing_run.exit_code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
