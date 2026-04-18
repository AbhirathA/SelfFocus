from __future__ import annotations

import sys
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from selffocus.controllers.break_controller import BreakController
from selffocus.controllers.overlay_controller import OverlayController
from selffocus.controllers.session_controller import SessionController
from selffocus.state import AppState, SessionMode
from selffocus.ui.break_picker_dialog import BreakPickerDialog
from selffocus.ui.checkpoint_overlay import CheckpointOverlay
from selffocus.ui.idle_window import IdleWindow
from selffocus.ui.summary_window import SummaryWindow
from selffocus.ui.tray_window import TrayWindow
from selffocus.utils.monitor_utils import available_screens
from selffocus.utils.sound import play_checkpoint_sound
from selffocus.utils.time_utils import format_clock, format_duration


class SelfFocusApplication:
    def __init__(self) -> None:
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)
        self.qt_app.setApplicationName("SelfFocus")
        self.app_icon = self._create_app_icon()
        self.qt_app.setWindowIcon(self.app_icon)

        self.state = AppState()
        self.session_controller = SessionController(self.state)
        self.break_controller = BreakController(self.state)
        self.overlay_controller = OverlayController(self.state)

        self.idle_window = IdleWindow()
        self.tray_window = TrayWindow()
        self.summary_window = SummaryWindow()
        self.break_dialog = BreakPickerDialog()
        self.overlay_windows: list[CheckpointOverlay] = []

        self.ui_timer = QTimer()
        self.ui_timer.setInterval(1000)
        self.ui_timer.timeout.connect(self.refresh_ui)
        self.ui_timer.start()

        self.break_controller.checkpoint_due.connect(self.show_checkpoint)

        self._build_tray()
        self._wire_signals()
        self.apply_styles()
        self.show_idle()

    def _build_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self._create_app_icon(), self.qt_app)
        menu = QMenu()
        self.open_action = QAction("Open SelfFocus", self.qt_app)
        self.quit_action = QAction("Quit", self.qt_app)
        self.open_action.triggered.connect(self.on_tray_activated)
        self.quit_action.triggered.connect(self.request_quit)
        menu.addAction(self.open_action)
        menu.addSeparator()
        menu.addAction(self.quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_icon_clicked)
        self.tray_icon.show()

        self.idle_window.setWindowIcon(self.app_icon)
        self.tray_window.setWindowIcon(self.app_icon)
        self.summary_window.setWindowIcon(self.app_icon)
        self.break_dialog.setWindowIcon(self.app_icon)

    def _create_app_icon(self) -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("#00000000"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#1f2a30"))
        painter.setPen(QColor("#1f2a30"))
        painter.drawEllipse(4, 4, 56, 56)
        painter.setPen(QColor("#f5f7f8"))
        font = QFont("Segoe UI", 24)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "S")
        painter.end()
        return QIcon(pixmap)

    def _wire_signals(self) -> None:
        self.idle_window.start_session_requested.connect(self.start_session)
        self.idle_window.quit_requested.connect(self.request_quit)
        self.tray_window.start_break_requested.connect(self.show_break_picker)
        self.tray_window.return_to_study_requested.connect(self.return_to_study)
        self.tray_window.end_session_requested.connect(self.end_session)
        self.summary_window.dismissed.connect(self.handle_summary_closed)

    def apply_styles(self) -> None:
        self.qt_app.setStyleSheet(
            """
            QWidget {
                background: #f5f7f8;
                color: #1f2a30;
                font-family: "Segoe UI";
                font-size: 14px;
            }
            QLabel#title {
                font-size: 28px;
                font-weight: 600;
            }
            QPushButton {
                min-height: 34px;
                border-radius: 10px;
                border: 1px solid #d8dee2;
                background: #ffffff;
                padding: 6px 12px;
            }
            QPushButton#primaryButton {
                background: #1f2a30;
                color: white;
                border: none;
            }
            """
        )

    def show_idle(self) -> None:
        self.tray_window.hide()
        self.summary_window.hide()
        self.idle_window.show()
        self.idle_window.raise_()
        self.idle_window.activateWindow()

    def show_tray_window(self) -> None:
        if self.state.current_mode is SessionMode.IDLE:
            self.show_idle()
            return
        self.idle_window.hide()
        self.summary_window.hide()
        self.tray_window.show()
        self.tray_window.raise_()
        self.tray_window.activateWindow()
        self.refresh_ui()

    def on_tray_icon_clicked(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self.on_tray_activated()

    def on_tray_activated(self) -> None:
        if self.summary_window.isVisible():
            self.summary_window.hide()
            return
        if self.state.current_mode is SessionMode.IDLE:
            if self.idle_window.isVisible():
                self.idle_window.hide()
            else:
                self.show_idle()
            return
        if self.tray_window.isVisible():
            self.tray_window.hide()
        else:
            self.show_tray_window()

    def start_session(self) -> None:
        self.session_controller.start_session()
        self.idle_window.hide()
        self.show_tray_window()

    def show_break_picker(self) -> None:
        if self.state.current_mode is not SessionMode.STUDYING:
            return
        if self.break_dialog.exec() == BreakPickerDialog.Accepted:
            self.break_controller.start_break(self.break_dialog.selected_minutes())
            self.refresh_ui()

    def show_checkpoint(self) -> None:
        self.hide_overlay()
        play_checkpoint_sound()
        prompt = self.overlay_controller.choose_prompt()
        now = datetime.now()
        time_text = format_clock(now)
        break_text = format_duration(self.state.current_break_elapsed_seconds(now))
        screens = available_screens()
        targets = screens if screens else [self.qt_app.primaryScreen()]
        for screen in targets:
            overlay = CheckpointOverlay()
            overlay.setWindowIcon(self.app_icon)
            overlay.configure(prompt, time_text, break_text)
            overlay.return_to_study_requested.connect(self.handle_overlay_return)
            overlay.continue_break_requested.connect(self.handle_overlay_continue)
            overlay.setGeometry(screen.geometry())
            overlay.showFullScreen()
            overlay.raise_()
            overlay.activateWindow()
            self.overlay_windows.append(overlay)
        self.refresh_ui()

    def hide_overlay(self) -> None:
        for overlay in self.overlay_windows:
            overlay.hide()
            overlay.deleteLater()
        self.overlay_windows.clear()

    def handle_overlay_return(self, _text: str) -> None:
        self.state.reflections_entered_count += 1
        self.hide_overlay()
        self.return_to_study()

    def handle_overlay_continue(self, _text: str, minutes: int) -> None:
        self.state.reflections_entered_count += 1
        self.hide_overlay()
        self.break_controller.extend_break(minutes)
        self.refresh_ui()

    def return_to_study(self) -> None:
        if self.state.current_mode not in {SessionMode.ON_BREAK, SessionMode.CHECKPOINT}:
            return
        self.hide_overlay()
        self.break_controller.return_to_study()
        self.refresh_ui()

    def end_session(self) -> None:
        if not self.session_controller.can_end_session():
            QMessageBox.information(None, "Resolve Break Checkpoint", "Choose an action on the checkpoint screen before ending the session.")
            return
        response = QMessageBox.question(
            None,
            "End Session",
            "End session and discard current stats after the summary closes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if response != QMessageBox.Yes:
            return
        summary = self.session_controller.end_session()
        self.hide_overlay()
        self.tray_window.hide()
        self.idle_window.hide()
        self.summary_window.set_summary(summary)
        self.summary_window.show()
        self.summary_window.raise_()
        self.summary_window.activateWindow()

    def request_quit(self) -> None:
        if self.state.current_mode is SessionMode.CHECKPOINT:
            QMessageBox.information(None, "Resolve Break Checkpoint", "Choose an action on the checkpoint screen before closing SelfFocus.")
            return
        if self.state.session_active:
            response = QMessageBox.question(
                None,
                "Quit SelfFocus",
                "Closing SelfFocus will end the current session and discard session data. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if response != QMessageBox.Yes:
                return
        self.hide_overlay()
        self.qt_app.quit()

    def handle_summary_closed(self) -> None:
        if self.state.current_mode is SessionMode.IDLE:
            self.show_idle()

    def refresh_ui(self) -> None:
        if self.state.current_mode is SessionMode.IDLE:
            return
        elapsed = format_duration(self.state.elapsed_session_seconds())
        if self.state.current_mode is SessionMode.STUDYING:
            self.tray_window.set_mode("Studying", elapsed, "No active break", True, False)
        elif self.state.current_mode is SessionMode.ON_BREAK:
            remaining = 0
            if self.state.break_end_deadline_ts:
                remaining = int((self.state.break_end_deadline_ts - datetime.now()).total_seconds())
            self.tray_window.set_mode("On Break", elapsed, f"Break ends in {format_duration(remaining)}", False, True)
        else:
            self.tray_window.set_mode("Break Checkpoint", elapsed, "Resolve the checkpoint overlay", False, False)

    def run(self) -> int:
        return self.qt_app.exec()
