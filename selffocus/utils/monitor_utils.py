from __future__ import annotations

from PySide6.QtGui import QGuiApplication


def available_screens():
    return QGuiApplication.screens()
