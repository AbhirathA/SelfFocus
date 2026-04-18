from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SessionMode(str, Enum):
    IDLE = "idle"
    STUDYING = "studying"
    ON_BREAK = "on_break"
    CHECKPOINT = "checkpoint"


@dataclass
class BreakSegment:
    start_ts: datetime
    end_ts: datetime | None = None
    durations_chosen_minutes: list[int] = field(default_factory=list)

    def elapsed_seconds(self, now: datetime | None = None) -> int:
        end = self.end_ts or now or datetime.now()
        return max(0, int((end - self.start_ts).total_seconds()))


@dataclass
class AppState:
    session_active: bool = False
    session_start_ts: datetime | None = None
    current_mode: SessionMode = SessionMode.IDLE
    break_start_ts: datetime | None = None
    break_end_deadline_ts: datetime | None = None
    active_break_minutes: int | None = None
    break_count: int = 0
    total_break_seconds: int = 0
    reflections_entered_count: int = 0
    break_segments: list[BreakSegment] = field(default_factory=list)
    overlay_prompt_index: int | None = None

    def reset(self) -> None:
        self.session_active = False
        self.session_start_ts = None
        self.current_mode = SessionMode.IDLE
        self.break_start_ts = None
        self.break_end_deadline_ts = None
        self.active_break_minutes = None
        self.break_count = 0
        self.total_break_seconds = 0
        self.reflections_entered_count = 0
        self.break_segments.clear()
        self.overlay_prompt_index = None

    def elapsed_session_seconds(self, now: datetime | None = None) -> int:
        if not self.session_start_ts:
            return 0
        current = now or datetime.now()
        return max(0, int((current - self.session_start_ts).total_seconds()))

    def current_break_elapsed_seconds(self, now: datetime | None = None) -> int:
        if not self.break_start_ts:
            return 0
        current = now or datetime.now()
        return max(0, int((current - self.break_start_ts).total_seconds()))

    def total_break_seconds_including_active(self, now: datetime | None = None) -> int:
        total = self.total_break_seconds
        if self.current_mode in {SessionMode.ON_BREAK, SessionMode.CHECKPOINT}:
            total += self.current_break_elapsed_seconds(now)
        return total

    def focused_seconds(self, now: datetime | None = None) -> int:
        return max(0, self.elapsed_session_seconds(now) - self.total_break_seconds_including_active(now))
