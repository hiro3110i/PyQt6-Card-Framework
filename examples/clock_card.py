#!/usr/bin/env python3
"""A minimal card that displays the local time."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if sys.platform.startswith("linux"):
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6 import QtCore, QtWidgets

from card_widget import BaseCardWidget, run_card


class ClockCard(BaseCardWidget):
    def __init__(self) -> None:
        super().__init__("Local time", width=220, height=120)
        self.time_label = QtWidgets.QLabel()
        self.time_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet(
            "QLabel { color: #e5e7eb; font-size: 24px; font-weight: 700; }"
        )
        self.content_layout.addWidget(self.time_label)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self) -> None:
        self.time_label.setText(QtCore.QTime.currentTime().toString("HH:mm:ss"))


if __name__ == "__main__":
    raise SystemExit(run_card(ClockCard, sys.argv))