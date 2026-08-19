#!/usr/bin/env python3
"""Run the Bluetooth dashboard example for one Joy-Con."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if sys.platform.startswith("linux"):
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from card_widget import run_card
from examples.bluetooth_device.device_card import BluetoothDeviceCard


JOYCON_MAC = "74:84:69:C3:FD:18"


if __name__ == "__main__":
    raise SystemExit(run_card(lambda: BluetoothDeviceCard(JOYCON_MAC, title="Joy-Con"), sys.argv))