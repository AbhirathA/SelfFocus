from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QCloseEvent, QCursor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from selffocus.utils.prompts import PRIVACY_LINE


class CheckpointOverlay(QWidget):
    return_to_study_requested = Signal(str)
    continue_break_requested = Signal(str, int)

    def __init__(self) -> None:
        super().__init__()
        self._slider_touched = False
        self._active_tooltip_key: str | None = None
        self.setWindowTitle("SelfFocus Checkpoint")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        QApplication.instance().installEventFilter(self)

        self.setStyleSheet(
            """
            QWidget { background-color: rgba(20, 24, 28, 238); color: #f5f7fa; }
            QFrame#card {
                background-color: rgba(32, 38, 44, 248);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 20px;
            }
            QLabel#prompt { font-size: 24px; font-weight: 600; }
            QLabel#meta { color: #b7c0c7; }
            QPlainTextEdit {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 14px;
                padding: 10px;
            }
            QPushButton {
                min-height: 42px;
                border-radius: 12px;
                padding: 10px 16px;
                background-color: #e7edf2;
                color: #142028;
                font-weight: 600;
            }
            QPushButton:disabled {
                background-color: #6d7680;
                color: #ced5da;
            }
            """
        )

        container = QVBoxLayout(self)
        container.setContentsMargins(48, 48, 48, 48)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(760)

        self.prompt_label = QLabel("")
        self.prompt_label.setObjectName("prompt")
        self.prompt_label.setWordWrap(True)

        self.meta_label = QLabel("")
        self.meta_label.setObjectName("meta")

        self.privacy_label = QLabel(PRIVACY_LINE)
        self.privacy_label.setWordWrap(True)
        self.privacy_label.setObjectName("meta")

        self.text_input = QPlainTextEdit()
        self.text_input.setPlaceholderText("Type at least 10 characters. I won't read it, but maybe you should.")
        self.text_input.textChanged.connect(self._update_actions)

        self.duration_label = QLabel("Choose a new break duration if you want to continue")
        self.duration_label.setObjectName("meta")

        self.slider_value_label = QLabel("Move the slider to continue the break")
        self.slider_value_label.setObjectName("meta")

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(2, 15)
        self.slider.setValue(2)
        self.slider.sliderPressed.connect(self._mark_slider_touched)
        self.slider.valueChanged.connect(self._on_slider_changed)

        self.return_button = QPushButton("Go Back To Studying")
        self.return_button.setEnabled(False)
        self.return_button.clicked.connect(self._emit_return)

        self.continue_button = QPushButton("Continue Break")
        self.continue_button.setEnabled(False)
        self.continue_button.clicked.connect(self._emit_continue)

        self.action_hint_label = QLabel("")
        self.action_hint_label.setWordWrap(True)
        self.action_hint_label.setObjectName("meta")

        action_row = QHBoxLayout()
        action_row.setSpacing(12)
        action_row.addWidget(self.return_button)
        action_row.addWidget(self.continue_button)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(self.prompt_label)
        layout.addWidget(self.meta_label)
        layout.addWidget(self.privacy_label)
        layout.addWidget(self.text_input)
        layout.addWidget(self.duration_label)
        layout.addWidget(self.slider_value_label)
        layout.addWidget(self.slider)
        layout.addLayout(action_row)
        layout.addWidget(self.action_hint_label)

        container.addStretch()
        container.addWidget(card, alignment=Qt.AlignCenter)
        container.addStretch()

    def configure(self, prompt: str, time_text: str, break_text: str) -> None:
        self.prompt_label.setText(prompt)
        self.meta_label.setText(f"It is {time_text}. You've been on break for {break_text}.")
        self.text_input.clear()
        self._slider_touched = False
        self.slider.setValue(2)
        self.slider_value_label.setText("Move the slider to continue the break")
        self._update_actions()

    def text_value(self) -> str:
        return self.text_input.toPlainText().strip()

    def _mark_slider_touched(self) -> None:
        self._slider_touched = True
        self._update_actions()

    def _on_slider_changed(self, value: int) -> None:
        if self._slider_touched:
            self.slider_value_label.setText(f"Continue break for {value} minutes")
        self._update_actions()

    def _update_actions(self) -> None:
        has_text = len(self.text_value()) >= 10
        self.return_button.setEnabled(has_text)
        self.continue_button.setEnabled(has_text and self._slider_touched)
        if not has_text:
            self.action_hint_label.setText("Type at least 10 characters to unlock both actions.")
        elif not self._slider_touched:
            self.action_hint_label.setText("Now either go back to studying, or move the slider to continue the break.")
        else:
            self.action_hint_label.setText("You can go back to studying or continue the break.")

    def _emit_return(self) -> None:
        self.return_to_study_requested.emit(self.text_value())

    def _emit_continue(self) -> None:
        self.continue_break_requested.emit(self.text_value(), int(self.slider.value()))

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()

    def eventFilter(self, obj, event) -> bool:
        if self.isVisible() and event.type() == QEvent.MouseMove:
            self._update_hover_tooltip()
        elif self._active_tooltip_key and event.type() in {QEvent.Leave, QEvent.WindowDeactivate}:
            self._clear_hover_tooltip()
        return super().eventFilter(obj, event)

    def _update_hover_tooltip(self) -> None:
        global_pos = QCursor.pos()
        tooltip_text = None
        tooltip_key = None

        if self._global_rect_for(self.return_button).contains(global_pos) and not self.return_button.isEnabled():
            tooltip_text = "Type at least 10 characters above to enable this button."
            tooltip_key = "return"
        elif self._global_rect_for(self.continue_button).contains(global_pos) and not self.continue_button.isEnabled():
            if len(self.text_value()) < 10:
                tooltip_text = "Type at least 10 characters above to enable this button."
            else:
                tooltip_text = "Move the slider to choose a new break duration, then this button will unlock."
            tooltip_key = "continue"

        if tooltip_text and tooltip_key != self._active_tooltip_key:
            QToolTip.showText(global_pos, tooltip_text, self)
            self._active_tooltip_key = tooltip_key
        elif not tooltip_text:
            self._clear_hover_tooltip()

    def _clear_hover_tooltip(self) -> None:
        QToolTip.hideText()
        self._active_tooltip_key = None

    def _global_rect_for(self, widget: QWidget) -> QRect:
        top_left = widget.mapToGlobal(QPoint(0, 0))
        return QRect(top_left, widget.size())
