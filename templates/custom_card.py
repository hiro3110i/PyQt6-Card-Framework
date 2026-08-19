#!/usr/bin/env python3
"""Copy this file to start a new card."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if sys.platform.startswith("linux"):
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6 import QtWidgets

from card_widget import BaseCardWidget, run_card


class CustomCard(BaseCardWidget):
    def __init__(self) -> None:
        super().__init__("Custom card", width=220, height=140)
        self.content_layout.addWidget(QtWidgets.QLabel(""))


if __name__ == "__main__":
    raise SystemExit(run_card(CustomCard, sys.argv))