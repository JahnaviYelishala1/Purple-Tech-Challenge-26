from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CAMERA_ROLES_PATH = PROJECT_ROOT / "config" / "camera_roles.json"


def _normalize_camera_id(camera_id: str) -> str:
    return str(camera_id).strip().upper()


def _normalize_role(role: str) -> str:
    return str(role).strip().upper()


def _load_roles_from_path(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    try:
        raw_mapping = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(raw_mapping, dict):
        return {}

    return {
        _normalize_camera_id(camera_id): _normalize_role(role)
        for camera_id, role in raw_mapping.items()
        if str(camera_id).strip()
    }


@lru_cache(maxsize=1)
def load_camera_roles(path: str | Path | None = None) -> dict[str, str]:
    target_path = Path(path) if path is not None else DEFAULT_CAMERA_ROLES_PATH
    return _load_roles_from_path(target_path)


def get_camera_role(camera_id: str, *, path: str | Path | None = None) -> str:
    roles = load_camera_roles(path)
    return roles.get(_normalize_camera_id(camera_id), "UNKNOWN")


def camera_ids_for_role(role: str, *, path: str | Path | None = None) -> list[str]:
    normalized_role = _normalize_role(role)
    roles = load_camera_roles(path)
    return [camera_id for camera_id, camera_role in roles.items() if camera_role == normalized_role]


def role_label(role: str) -> str:
    return _normalize_role(role).replace("_", " ").title()