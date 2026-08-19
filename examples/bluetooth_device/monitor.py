"""Event-driven monitoring of one Bluetooth device through bluetoothctl."""

from __future__ import annotations

import re
import subprocess
import threading

from PyQt6 import QtCore


_CHANGE_RE = re.compile(r"^\[(CHG|NEW|DEL)\] Device ([0-9A-Fa-f:]{17})(?:\s+(.*))?$")
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class BluetoothMonitor(QtCore.QObject):
    state_changed = QtCore.pyqtSignal(dict)

    def __init__(self, mac: str) -> None:
        super().__init__()
        self.mac = mac.upper()
        self.info = {"name": "", "address": self.mac, "present": False, "paired": False, "trusted": False, "connected": False}
        self._process: subprocess.Popen[str] | None = None
        self._reader_thread: threading.Thread | None = None
        self._write_lock = threading.Lock()
        self._stopping = False

    def start(self) -> None:
        if self._process is not None:
            return
        self._stopping = False
        self._process = subprocess.Popen(["bluetoothctl"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()
        self.send(f"info {self.mac}")

    def send(self, command: str) -> None:
        process = self._process
        if process is None or process.poll() is not None or process.stdin is None:
            return
        with self._write_lock:
            try:
                process.stdin.write(command + "\n")
                process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass

    def stop(self) -> None:
        self._stopping = True
        process = self._process
        if process is not None and process.poll() is None:
            self.send("quit")
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
        if self._reader_thread is not None:
            self._reader_thread.join(timeout=3)
        self._process = None
        self._reader_thread = None

    def _read_loop(self) -> None:
        process = self._process
        if process is None or process.stdout is None:
            return
        try:
            for raw_line in process.stdout:
                if self._stopping:
                    break
                self._handle_line(raw_line)
        except (ValueError, OSError):
            pass

    def _handle_line(self, raw_line: str) -> None:
        line = _ANSI_RE.sub("", raw_line).strip()
        if not line:
            return
        changed = False
        match = _CHANGE_RE.match(line)
        if match:
            kind, address, remainder = match.groups()
            if address.upper() != self.mac:
                return
            if kind == "DEL":
                changed = self._set("present", False) | self._set("connected", False)
            else:
                changed = self._set("present", True)
                if remainder:
                    if ":" in remainder:
                        key, value = remainder.split(":", 1)
                        changed |= self._apply_key_value(key.strip(), value.strip())
                    else:
                        changed |= self._set("name", remainder)
        elif line.startswith("Device ") and self.mac in line.upper():
            changed = self._set("present", True)
        elif ":" in line:
            key, value = line.split(":", 1)
            changed = self._apply_key_value(key.strip(), value.strip())
        if changed:
            self.state_changed.emit(dict(self.info))

    def _apply_key_value(self, key: str, value: str) -> bool:
        if key in ("Name", "Alias") and value:
            return self._set("name", value)
        if key == "Paired":
            return self._set("paired", value.lower() == "yes")
        if key == "Trusted":
            return self._set("trusted", value.lower() == "yes")
        if key == "Connected":
            return self._set("connected", value.lower() == "yes")
        return False

    def _set(self, key: str, value: object) -> bool:
        if self.info[key] != value:
            self.info[key] = value
            return True
        return False