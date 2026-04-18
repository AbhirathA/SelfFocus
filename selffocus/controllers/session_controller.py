from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from selffocus.state import AppState, SessionMode


@dataclass
class SessionSummary:
    total_session_seconds: int
    total_focus_seconds: int
    total_break_seconds: int
    break_count: int
    timeline: list[tuple[str, int]]


class SessionController:
    def __init__(self, state: AppState) -> None:
        self.state = state

    def start_session(self) -> None:
        self.state.reset()
        self.state.session_active = True
        self.state.session_start_ts = datetime.now()
        self.state.current_mode = SessionMode.STUDYING

    def can_end_session(self) -> bool:
        return self.state.current_mode is not SessionMode.CHECKPOINT

    def end_session(self) -> SessionSummary:
        now = datetime.now()
        total_session = self.state.elapsed_session_seconds(now)
        total_break = self.state.total_break_seconds_including_active(now)
        total_focus = max(0, total_session - total_break)
        timeline: list[tuple[str, int]] = []
        cursor = self.state.session_start_ts

        for segment in self.state.break_segments:
            if cursor and segment.start_ts > cursor:
                timeline.append(("focus", int((segment.start_ts - cursor).total_seconds())))
            timeline.append(("break", segment.elapsed_seconds(now)))
            cursor = segment.end_ts or now

        if cursor and self.state.session_start_ts and now > cursor:
            timeline.append(("focus", int((now - cursor).total_seconds())))

        summary = SessionSummary(
            total_session_seconds=total_session,
            total_focus_seconds=total_focus,
            total_break_seconds=total_break,
            break_count=self.state.break_count,
            timeline=timeline,
        )
        self.state.reset()
        return summary
