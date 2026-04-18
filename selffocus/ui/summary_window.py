from __future__ import annotations

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QHorizontalStackedBarSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QPainter
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from selffocus.controllers.session_controller import SessionSummary
from selffocus.utils.time_utils import format_duration


class SummaryWindow(QWidget):
    dismissed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SelfFocus Summary")
        self.resize(700, 620)

        self.title_label = QLabel("Session Summary")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.stats_label = QLabel("")
        self.stats_label.setWordWrap(True)
        self.stats_label.setAlignment(Qt.AlignCenter)

        self.comparison_view = QChartView()
        self.comparison_view.setRenderHint(QPainter.Antialiasing)

        self.timeline_view = QChartView()
        self.timeline_view.setRenderHint(QPainter.Antialiasing)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(self.title_label)
        layout.addWidget(self.stats_label)
        layout.addWidget(self.comparison_view, stretch=1)
        layout.addWidget(self.timeline_view, stretch=1)
        layout.addWidget(self.close_button)

    def set_summary(self, summary: SessionSummary) -> None:
        self.stats_label.setText(
            "\n".join(
                [
                    f"Total session time: {format_duration(summary.total_session_seconds)}",
                    f"Focused time: {format_duration(summary.total_focus_seconds)}",
                    f"Breaks taken: {summary.break_count}",
                    f"Total break time: {format_duration(summary.total_break_seconds)}",
                ]
            )
        )
        self.comparison_view.setChart(self._build_comparison_chart(summary))
        self.timeline_view.setChart(self._build_timeline_chart(summary))

    def _build_comparison_chart(self, summary: SessionSummary) -> QChart:
        focus = QBarSet("Focused")
        break_set = QBarSet("Break")
        focus << round(summary.total_focus_seconds / 60, 2)
        break_set << round(summary.total_break_seconds / 60, 2)

        series = QBarSeries()
        series.append(focus)
        series.append(break_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Focus vs Break Time (minutes)")
        chart.setAnimationOptions(QChart.NoAnimation)

        axis_x = QBarCategoryAxis()
        axis_x.append(["Session"])
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("Minutes")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        chart.legend().setVisible(True)
        return chart

    def _build_timeline_chart(self, summary: SessionSummary) -> QChart:
        focus = QBarSet("Focus")
        brk = QBarSet("Break")
        for kind, seconds in summary.timeline:
            minutes = max(0.01, seconds / 60)
            focus << (minutes if kind == "focus" else 0)
            brk << (minutes if kind == "break" else 0)

        series = QHorizontalStackedBarSeries()
        series.append(focus)
        series.append(brk)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Session Rhythm")
        chart.setAnimationOptions(QChart.NoAnimation)

        axis_y = QBarCategoryAxis()
        labels = [f"Segment {index + 1}" for index, _ in enumerate(summary.timeline)] or ["Session"]
        axis_y.append(labels)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        axis_x = QValueAxis()
        axis_x.setTitleText("Minutes")
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        chart.legend().setVisible(True)
        return chart

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)
        self.dismissed.emit()
