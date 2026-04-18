from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class TrayWindow(QWidget):
    start_break_requested = Signal()
    return_to_study_requested = Signal()
    end_session_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SelfFocus")
        self.setFixedSize(340, 240)

        self.status_label = QLabel("Idle")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.elapsed_label = QLabel("00m 00s")
        self.elapsed_label.setAlignment(Qt.AlignCenter)
        self.break_label = QLabel("")
        self.break_label.setAlignment(Qt.AlignCenter)

        self.start_break_button = QPushButton("Start Break")
        self.start_break_button.clicked.connect(self.start_break_requested.emit)

        self.return_button = QPushButton("Return To Study")
        self.return_button.clicked.connect(self.return_to_study_requested.emit)

        self.end_session_button = QPushButton("End Session")
        self.end_session_button.clicked.connect(self.end_session_requested.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        layout.addWidget(self.status_label)
        layout.addWidget(self.elapsed_label)
        layout.addWidget(self.break_label)
        layout.addStretch()
        layout.addWidget(self.start_break_button)
        layout.addWidget(self.return_button)
        layout.addWidget(self.end_session_button)

    def set_mode(
        self,
        mode_label: str,
        elapsed_text: str,
        break_text: str,
        allow_start_break: bool,
        allow_return: bool,
    ) -> None:
        self.status_label.setText(mode_label)
        self.elapsed_label.setText(elapsed_text)
        self.break_label.setText(break_text)
        self.start_break_button.setVisible(allow_start_break)
        self.return_button.setVisible(allow_return)
