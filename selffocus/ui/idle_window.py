from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class IdleWindow(QWidget):
    start_session_requested = Signal()
    quit_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SelfFocus")
        self.setFixedSize(320, 220)

        title = QLabel("SelfFocus")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("A quiet checkpoint for intentional breaks.")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignCenter)

        start_button = QPushButton("Start Session")
        start_button.setObjectName("primaryButton")
        start_button.clicked.connect(self.start_session_requested.emit)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.quit_requested.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(start_button)
        layout.addWidget(quit_button)
