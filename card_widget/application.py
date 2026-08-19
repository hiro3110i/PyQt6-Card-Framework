"""Application lifecycle helpers for desktop cards."""

from __future__ import annotations

import signal
import sys
from collections.abc import Callable, Sequence

from PyQt6 import QtCore, QtWidgets

from .settings import load_window_settings


def run_card(
    card_factory: Callable[[], QtWidgets.QWidget],
    argv: Sequence[str] | None = None,
) -> int:
    """Create, show, and run a card application with Ctrl+C support."""
    arguments = list(argv) if argv is not None else sys.argv
    app = QtWidgets.QApplication(arguments)
    app.setQuitOnLastWindowClosed(True)
    previous_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, lambda *_: app.quit())

    signal_timer = QtCore.QTimer(app)
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start(200)

    card = card_factory()
    apply_settings = getattr(card, "apply_window_settings", None)
    if callable(apply_settings) and arguments:
        apply_settings(load_window_settings(arguments[0]))
    closing_signal = getattr(card, "closing", None)
    if closing_signal is not None:
        closing_signal.connect(app.quit)
    card.show()
    try:
        return app.exec()
    finally:
        signal_timer.stop()
        signal.signal(signal.SIGINT, previous_sigint_handler)