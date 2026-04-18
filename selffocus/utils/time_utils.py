from __future__ import annotations

from datetime import datetime


def format_duration(total_seconds: int) -> str:
    total_seconds = max(0, int(total_seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    return f"{minutes:02d}m {seconds:02d}s"


def format_clock(timestamp: datetime | None) -> str:
    if not timestamp:
        return "--:--"
    return timestamp.strftime("%I:%M %p").lstrip("0")
