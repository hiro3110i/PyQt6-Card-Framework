"""Dashboard card for one Bluetooth device."""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from card_widget import BaseCardWidget

from .monitor import BluetoothMonitor


class BluetoothDeviceCard(BaseCardWidget):
    def __init__(
        self,
        mac: str,
        *,
        title: str = "Bluetooth device",
        monitor: BluetoothMonitor | None = None,
    ) -> None:
        super().__init__(title, width=220, height=220)
        self._action_busy = False
        self._pending_connected: bool | None = None
        self._monitor = monitor or BluetoothMonitor(mac)
        self._monitor.state_changed.connect(self._on_status_changed)
        self._build_content()
        self._set_connect_button_state(False)
        self.resync_timer = QtCore.QTimer(self)
        self.resync_timer.timeout.connect(self.refresh_status)
        self.resync_timer.start(30000)
        self.closing.connect(self._shutdown)
        self._monitor.start()

    def _build_content(self) -> None:
        self.status_label = QtWidgets.QLabel("Checking...")
        self.status_label.setStyleSheet(self._status_style("#e5e7eb"))
        self.content_layout.addWidget(self.status_label)
        details = QtWidgets.QGridLayout()
        details.setHorizontalSpacing(8)
        details.setVerticalSpacing(8)
        self.content_layout.addLayout(details)
        self.name_value = self._add_row(details, 0, "Name")
        self.mac_value = self._add_row(details, 1, "MAC")
        self.mac_value.setText(self._monitor.info["address"])
        self.paired_value = self._add_row(details, 2, "Paired")
        self.connected_value = self._add_row(details, 3, "Connected")
        self.connect_button = QtWidgets.QPushButton()
        self.connect_button.setFixedHeight(28)
        self.connect_button.clicked.connect(self.toggle_connection)
        self.content_layout.addWidget(self.connect_button)

    def _add_row(
        self, layout: QtWidgets.QGridLayout, row: int, text: str
    ) -> QtWidgets.QLabel:
        key = QtWidgets.QLabel(text)
        key.setStyleSheet("QLabel { color: #94a3b8; font-size: 11px; }")
        layout.addWidget(key, row, 0)
        value = QtWidgets.QLabel("-")
        value.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        value.setStyleSheet("QLabel { color: #e5e7eb; font-size: 11px; }")
        layout.addWidget(value, row, 1)
        return value

    def refresh_status(self) -> None:
        self._monitor.send(f"info {self._monitor.mac}")

    def toggle_connection(self) -> None:
        self._action_busy = True
        self.connect_button.setEnabled(False)
        info = self._monitor.info
        if info["connected"]:
            self._pending_connected = False
            self.connect_button.setText("Disconnecting...")
            self._monitor.send(f"disconnect {self._monitor.mac}")
        else:
            self._pending_connected = True
            self.connect_button.setText("Connecting...")
            if not info["paired"]:
                self._monitor.send("power on")
                self._monitor.send(f"pair {self._monitor.mac}")
            if not info["trusted"]:
                self._monitor.send(f"trust {self._monitor.mac}")
            self._monitor.send(f"connect {self._monitor.mac}")
        QtCore.QTimer.singleShot(8000, self._on_action_timeout)

    def _on_status_changed(self, info: dict) -> None:
        if not info["present"]:
            self.status_label.setText("Not detected")
            self.status_label.setStyleSheet(self._status_style("#94a3b8"))
        elif info["connected"]:
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet(self._status_style("#4ade80"))
        else:
            self.status_label.setText("Detected")
            self.status_label.setStyleSheet(self._status_style("#fbbf24"))
        self.name_value.setText(info["name"] or "Unknown")
        self.paired_value.setText("Yes" if info["paired"] else "No")
        self.connected_value.setText("Yes" if info["connected"] else "No")
        if self._action_busy and info["connected"] == self._pending_connected:
            self._finish_action(info["connected"])
        elif not self._action_busy:
            self._set_connect_button_state(info["connected"])

    def _on_action_timeout(self) -> None:
        if self._action_busy:
            self._finish_action(self._monitor.info["connected"])

    def _finish_action(self, connected: bool) -> None:
        self._action_busy = False
        self._pending_connected = None
        self.connect_button.setEnabled(True)
        self._set_connect_button_state(connected)

    def _set_connect_button_state(self, connected: bool) -> None:
        if connected:
            self.connect_button.setText("Disconnect")
            color, text = "#c17a7a", "#1f1414"
        else:
            self.connect_button.setText("Connect")
            color, text = "#7ba883", "#14201a"
        self.connect_button.setStyleSheet(
            f"QPushButton {{ background: {color}; color: {text}; border: none; "
            "border-radius: 6px; font-weight: 700; font-size: 11px; } "
            "QPushButton:disabled { background: #4b5563; color: #d1d5db; }"
        )

    def _shutdown(self) -> None:
        self.resync_timer.stop()
        self._monitor.stop()

    @staticmethod
    def _status_style(color: str) -> str:
        return f"QLabel {{ color: {color}; font-size: 13px; font-weight: bold; }}"