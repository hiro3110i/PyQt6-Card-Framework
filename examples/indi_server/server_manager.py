"""Service layer for managing the indiserver process using QProcess."""

from __future__ import annotations

import shutil
from typing import Sequence

from PyQt6 import QtCore


class IndiServerManager(QtCore.QObject):
    """Controls background execution of `indiserver`."""

    status_changed = QtCore.pyqtSignal(str)  # "Stopped", "Running", "Starting", "Error", etc.
    log_received = QtCore.pyqtSignal(str)  # Line of stdout/stderr

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._process = QtCore.QProcess(self)
        self._process.setProcessChannelMode(QtCore.QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_ready_read)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_error)
        self._port = 7624
        self._active_drivers: list[str] = []
        self._status = "Stopped"

    @property
    def status(self) -> str:
        return self._status

    @property
    def port(self) -> int:
        return self._port

    @property
    def active_drivers(self) -> list[str]:
        return list(self._active_drivers)

    def is_running(self) -> bool:
        return self._process.state() != QtCore.QProcess.ProcessState.NotRunning

    def start_server(
        self,
        drivers: Sequence[str],
        port: int = 7624,
        extra_args: Sequence[str] | None = None,
    ) -> bool:
        """Start the indiserver with the specified drivers and port."""
        if self.is_running():
            self.stop_server()

        indiserver_bin = shutil.which("indiserver")
        if not indiserver_bin:
            self._set_status("Error: indiserver binary not found")
            self.log_received.emit("Error: 'indiserver' command not found in PATH.")
            return False

        if not drivers:
            self._set_status("Error: No drivers selected")
            self.log_received.emit("Error: Please select at least one driver to start.")
            return False

        self._port = port
        self._active_drivers = list(drivers)

        cmd_args = ["-p", str(port)]
        if extra_args:
            cmd_args.extend(extra_args)
        cmd_args.extend(self._active_drivers)

        self._set_status("Starting...")
        self.log_received.emit(f"Starting: {indiserver_bin} {' '.join(cmd_args)}")

        self._process.start(indiserver_bin, cmd_args)
        if self._process.waitForStarted(3000):
            self._set_status("Running")
            return True
        else:
            self._set_status("Error starting server")
            return False

    def stop_server(self) -> None:
        """Stop the running indiserver process gracefully."""
        if not self.is_running():
            self._set_status("Stopped")
            return

        self._set_status("Stopping...")
        self.log_received.emit("Sending termination signal to indiserver...")
        self._process.terminate()

        # Wait up to 3 seconds for graceful shutdown, then kill if needed
        if not self._process.waitForFinished(3000):
            self.log_received.emit("Server did not stop in time. Force killing...")
            self._process.kill()
            self._process.waitForFinished(1000)

        self._set_status("Stopped")

    def _set_status(self, status: str) -> None:
        self._status = status
        self.status_changed.emit(status)

    def _on_ready_read(self) -> None:
        data = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            if line.strip():
                self.log_received.emit(line)

    def _on_finished(self, exit_code: int, exit_status: QtCore.QProcess.ExitStatus) -> None:
        msg = f"indiserver stopped (exit code: {exit_code})"
        self.log_received.emit(msg)
        self._set_status("Stopped")

    def _on_error(self, error: QtCore.QProcess.ProcessError) -> None:
        if error != QtCore.QProcess.ProcessError.Crashed or self._status != "Stopping...":
            msg = f"Process error: {error.name}"
            self.log_received.emit(msg)
            self._set_status("Error")
