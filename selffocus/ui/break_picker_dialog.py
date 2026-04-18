from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QSlider, QVBoxLayout


class BreakPickerDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Start Break")
        self.setModal(True)
        self.setFixedSize(360, 220)
        self._touched = False

        self.title_label = QLabel("Choose your break duration")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel("Move the slider to pick a duration")
        self.value_label.setAlignment(Qt.AlignCenter)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(2, 15)
        self.slider.setValue(2)
        self.slider.valueChanged.connect(self._on_value_changed)
        self.slider.sliderPressed.connect(self._mark_touched)

        self.start_button = QPushButton("Start Break")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.slider)
        layout.addStretch()
        layout.addWidget(self.start_button)
        layout.addWidget(self.cancel_button)

    def _mark_touched(self) -> None:
        self._touched = True
        self.start_button.setEnabled(True)
        self.value_label.setText(f"{self.slider.value()} minutes")

    def _on_value_changed(self, value: int) -> None:
        if self._touched:
            self.value_label.setText(f"{value} minutes")

    def selected_minutes(self) -> int:
        return int(self.slider.value())
