from __future__ import annotations

import sys
from pathlib import Path

try:
    import winsound
except ImportError:  # pragma: no cover
    winsound = None


def _resource_path(relative_path: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parents[2] / relative_path


ALARM_SOUND_PATH = _resource_path("assets/Alarm01.wav")


def play_checkpoint_sound() -> None:
    if not winsound:
        return
    if ALARM_SOUND_PATH.exists():
        winsound.PlaySound(str(ALARM_SOUND_PATH), winsound.SND_FILENAME | winsound.SND_ASYNC)
        return
    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
