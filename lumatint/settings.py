"""Store settings in the current user's AppData directory."""

import json
import os
from dataclasses import asdict
from pathlib import Path

from .profiles import ColorProfile


def settings_path() -> Path:
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / ".local" / "share")
    return Path(base) / "LumaTint" / "settings.json"


def load_settings(path: Path | None = None) -> dict:
    result = {"enabled": False, "profile": ColorProfile(), "preset": "Neutral"}
    path = path or settings_path()
    if not path.is_file():
        return result
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return result
        result["enabled"] = bool(data.get("enabled", False))
        result["profile"] = ColorProfile.from_dict(data.get("profile", {}))
        name = data.get("preset", "Custom")
        result["preset"] = name if isinstance(name, str) else "Custom"
    except (OSError, ValueError, TypeError):
        pass
    return result


def save_settings(enabled: bool, profile: ColorProfile, preset: str, path: Path | None = None) -> None:
    path = path or settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name("settings.tmp")
    data = {"enabled": bool(enabled), "profile": asdict(profile), "preset": preset}
    temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(temporary, path)
