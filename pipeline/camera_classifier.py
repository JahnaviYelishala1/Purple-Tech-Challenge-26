from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import cv2


KEY_TO_LABEL: dict[str, str] = {
    "e": "ENTRANCE",
    "x": "EXIT",
    "z": "ZONE",
    "b": "BILLING",
    "q": "QUEUE",
    "u": "UNKNOWN",
}

CAMERA_PATTERN = re.compile(r"^(CAM\d+)_(\d+)\.jpe?g$", re.IGNORECASE)


@dataclass
class CameraPreview:
    camera_id: str
    image_path: Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def previews_dir() -> Path:
    return project_root() / "outputs" / "previews"


def mapping_path() -> Path:
    return project_root() / "camera_mapping.json"


def load_mapping(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass

    print(f"Warning: could not parse existing mapping file at {path}. Starting fresh.")
    return {}


def save_mapping(path: Path, mapping: dict[str, str]) -> None:
    path.write_text(json.dumps(mapping, indent=4), encoding="utf-8")


def discover_previews(path: Path) -> list[CameraPreview]:
    if not path.exists() or not path.is_dir():
        print(f"Preview folder not found: {path}")
        return []

    grouped: dict[str, list[tuple[int, Path]]] = {}

    for image_path in sorted(path.glob("*.jpg")) + sorted(path.glob("*.jpeg")):
        match = CAMERA_PATTERN.match(image_path.name)
        if not match:
            continue

        camera_id = match.group(1).upper()
        pct = int(match.group(2))
        grouped.setdefault(camera_id, []).append((pct, image_path))

    previews: list[CameraPreview] = []
    for camera_id in sorted(grouped.keys(), key=lambda cam: int(cam.replace("CAM", ""))):
        candidates = grouped[camera_id]
        preferred = sorted(
            candidates,
            key=lambda item: (
                0 if item[0] == 50 else (1 if item[0] == 10 else (2 if item[0] == 90 else 3)),
                item[0],
            ),
        )
        previews.append(CameraPreview(camera_id=camera_id, image_path=preferred[0][1]))

    return previews


def is_gui_available() -> bool:
    mode_override = os.getenv("CAMERA_CLASSIFIER_MODE", "").strip().lower()
    if mode_override == "cli":
        return False

    try:
        cv2.namedWindow("camera_classifier_probe", cv2.WINDOW_NORMAL)
        cv2.destroyWindow("camera_classifier_probe")
        return True
    except Exception:
        return False


def overlay_text(image, top_text: str, current_label: str | None):
    output = image.copy()
    subtitle = f"Current: {current_label}" if current_label else "Current: UNSET"
    helper = "Keys: e=ENTRANCE x=EXIT z=ZONE b=BILLING q=QUEUE u=UNKNOWN"

    cv2.putText(output, top_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    cv2.putText(output, subtitle, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(output, helper, (20, output.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return output


def classify_with_gui(preview: CameraPreview, current_label: str | None) -> str | None:
    image = cv2.imread(str(preview.image_path))
    if image is None:
        print(f"Skipping unreadable image: {preview.image_path}")
        return None

    window_name = "Camera Classifier"
    display = overlay_text(image, f"{preview.camera_id} - {preview.image_path.name}", current_label)
    cv2.imshow(window_name, display)

    while True:
        key_code = cv2.waitKey(0)
        if key_code == -1:
            continue

        key = chr(key_code & 0xFF).lower()
        if key in KEY_TO_LABEL:
            return KEY_TO_LABEL[key]


def classify_with_cli(preview: CameraPreview, current_label: str | None) -> str | None:
    print("\n---")
    print(f"Camera: {preview.camera_id}")
    print(f"Image: {preview.image_path}")
    print(f"Current classification: {current_label or 'UNSET'}")
    print("Enter one key: e=ENTRANCE, x=EXIT, z=ZONE, b=BILLING, q=QUEUE, u=UNKNOWN")

    while True:
        user_input = input("Classification key: ").strip().lower()
        if user_input in KEY_TO_LABEL:
            return KEY_TO_LABEL[user_input]
        print("Invalid key. Please use: e, x, z, b, q, u")


def run_classifier() -> int:
    previews = discover_previews(previews_dir())
    if not previews:
        print("No preview images found. Nothing to classify.")
        return 0

    out_path = mapping_path()
    mapping = load_mapping(out_path)

    gui_available = is_gui_available()
    print(f"Using {'GUI' if gui_available else 'CLI'} mode for classification.")

    try:
        for preview in previews:
            current_label = mapping.get(preview.camera_id)
            label = (
                classify_with_gui(preview, current_label)
                if gui_available
                else classify_with_cli(preview, current_label)
            )

            if label is None:
                print(f"No classification captured for {preview.camera_id}; keeping previous value.")
                continue

            mapping[preview.camera_id] = label
            save_mapping(out_path, mapping)
            print(f"Saved {preview.camera_id} -> {label}")
    finally:
        if gui_available:
            cv2.destroyAllWindows()

    print("\nFinal camera mapping:")
    print(json.dumps(mapping, indent=4))
    return 0


def main() -> int:
    return run_classifier()


if __name__ == "__main__":
    raise SystemExit(main())
