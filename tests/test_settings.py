"""Tests for per-script window configuration."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import QtCore, QtWidgets

from card_widget import BaseCardWidget, load_window_settings, settings_path


class WindowSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_uses_script_stem_for_settings_filename(self) -> None:
        with tempfile.TemporaryDirectory() as home_directory:
            with patch.dict(os.environ, {"HOME": home_directory}):
                path = settings_path("/cards/status_card.py")
        self.assertEqual(
            path,
            Path(home_directory) / "config" / "pyqt6-cards" / "status_card.json",
        )

    def test_loads_size_and_coordinate_position(self) -> None:
        with tempfile.TemporaryDirectory() as home_directory:
            config_directory = Path(home_directory) / "config" / "pyqt6-cards"
            config_directory.mkdir(parents=True)
            (config_directory / "status_card.json").write_text(
                json.dumps(
                    {
                        "width": 320,
                        "height": 180,
                        "position": {"x": 42, "y": 64},
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"HOME": home_directory}):
                settings = load_window_settings("status_card.py")

        card = BaseCardWidget()
        card.apply_window_settings(settings)
        self.assertEqual((card.width(), card.height()), (320, 180))
        self.assertEqual(card._initial_coordinates, QtCore.QPoint(42, 64))

    def test_uses_a_normal_top_level_window(self) -> None:
        card = BaseCardWidget()

        self.assertEqual(card.windowType(), QtCore.Qt.WindowType.Window)

    def test_invalid_json_uses_empty_settings(self) -> None:
        with tempfile.TemporaryDirectory() as home_directory:
            config_directory = Path(home_directory) / "config" / "pyqt6-cards"
            config_directory.mkdir(parents=True)
            (config_directory / "status_card.json").write_text("{", encoding="utf-8")
            with patch.dict(os.environ, {"HOME": home_directory}):
                self.assertEqual(load_window_settings("status_card.py"), {})