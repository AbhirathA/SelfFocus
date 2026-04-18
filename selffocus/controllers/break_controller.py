from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QTimer, Signal

from selffocus.state import AppState, BreakSegment, SessionMode


class BreakController(QObject):
    checkpoint_due = Signal()
    break_updated = Signal()

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self.break_timer = QTimer(self)
        self.break_timer.setSingleShot(True)
        self.break_timer.timeout.connect(self._handle_timeout)

    def start_break(self, minutes: int) -> None:
        now = datetime.now()
        self.state.break_count += 1
        self.state.break_start_ts = now
        self.state.break_end_deadline_ts = now + timedelta(minutes=minutes)
        self.state.active_break_minutes = minutes
        self.state.current_mode = SessionMode.ON_BREAK
        self.state.break_segments.append(BreakSegment(start_ts=now, durations_chosen_minutes=[minutes]))
        self.break_timer.start(minutes * 60 * 1000)
        self.break_updated.emit()

    def extend_break(self, minutes: int) -> None:
        now = datetime.now()
        self.state.break_end_deadline_ts = now + timedelta(minutes=minutes)
        self.state.active_break_minutes = minutes
        self.state.current_mode = SessionMode.ON_BREAK
        if self.state.break_segments:
            self.state.break_segments[-1].durations_chosen_minutes.append(minutes)
        self.break_timer.start(minutes * 60 * 1000)
        self.break_updated.emit()

    def return_to_study(self) -> None:
        now = datetime.now()
        self.break_timer.stop()
        if self.state.break_segments and self.state.break_segments[-1].end_ts is None:
            self.state.break_segments[-1].end_ts = now
        self.state.total_break_seconds += self.state.current_break_elapsed_seconds(now)
        self.state.break_start_ts = None
        self.state.break_end_deadline_ts = None
        self.state.active_break_minutes = None
        self.state.current_mode = SessionMode.STUDYING
        self.break_updated.emit()

    def _handle_timeout(self) -> None:
        self.state.current_mode = SessionMode.CHECKPOINT
        self.break_updated.emit()
        self.checkpoint_due.emit()
