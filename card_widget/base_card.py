"""Base window chrome for desktop card applications."""

from __future__ import annotations

from enum import Enum

from PyQt6 import QtCore, QtGui, QtWidgets


class InitialPosition(Enum):
    """Supported first-show positions for a card window."""

    TOP_RIGHT = "top-right"


class BaseCardWidget(QtWidgets.QWidget):
    """A frameless, draggable desktop card with a content layout."""

    closing = QtCore.pyqtSignal()

    def __init__(
        self,
        title: str = "",
        *,
        width: int = 180,
        height: int = 180,
        initial_position: InitialPosition = InitialPosition.TOP_RIGHT,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._drag_offset: QtCore.QPoint | None = None
        self._initial_position = initial_position
        self._initial_coordinates: QtCore.QPoint | None = None
        self._has_been_shown = False
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(width, height)

        self.card = QtWidgets.QFrame(self)
        self.card.setObjectName("card")
        self.card.setStyleSheet(
            "QFrame#card { background: rgba(17, 24, 39, 0.82); "
            "border: 1px solid rgba(148, 163, 184, 0.22); border-radius: 10px; }"
        )
        card_layout = QtWidgets.QVBoxLayout(self.card)
        card_layout.setContentsMargins(10, 6, 10, 12)
        card_layout.setSpacing(6)

        self.drag_handle = QtWidgets.QWidget(self.card)
        self.drag_handle.setCursor(QtCore.Qt.CursorShape.OpenHandCursor)
        self.drag_handle.installEventFilter(self)
        header_layout = QtWidgets.QHBoxLayout(self.drag_handle)
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QtWidgets.QLabel(title, self.drag_handle)
        self.title_label.setStyleSheet(
            "QLabel { color: #e5e7eb; font-size: 11px; font-weight: 700; }"
        )
        self.title_label.installEventFilter(self)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.close_button = QtWidgets.QPushButton("x", self.drag_handle)
        self.close_button.setAccessibleName("Close card")
        self.close_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.close_button.setFixedSize(14, 14)
        self.close_button.setStyleSheet(
            "QPushButton { background: #ff5f57; color: rgba(0, 0, 0, 0); "
            "border: none; border-radius: 7px; font-size: 9px; font-weight: 700; "
            "padding: 0; } QPushButton:hover { color: #4d0000; }"
        )
        self.close_button.clicked.connect(self.close)
        header_layout.addWidget(self.close_button)
        card_layout.addWidget(self.drag_handle)

        self.content_widget = QtWidgets.QWidget(self.card)
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        card_layout.addWidget(self.content_widget, 1)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        self.card.setGeometry(self.rect())
        super().resizeEvent(event)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        if self._has_been_shown:
            return
        self._has_been_shown = True
        for delay in (0, 50, 200, 500):
            QtCore.QTimer.singleShot(delay, self.move_to_initial_position)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.closing.emit()
        super().closeEvent(event)

    def apply_window_settings(self, settings: dict) -> None:
        """Apply validated size and initial-position settings before showing."""
        width = settings.get("width")
        height = settings.get("height")
        if self._is_positive_int(width) and self._is_positive_int(height):
            self.resize(width, height)

        position = settings.get("position")
        if isinstance(position, str):
            try:
                self._initial_position = InitialPosition(position)
                self._initial_coordinates = None
            except ValueError:
                pass
        elif isinstance(position, dict):
            x = position.get("x")
            y = position.get("y")
            if self._is_int(x) and self._is_int(y):
                self._initial_coordinates = QtCore.QPoint(x, y)

    def move_to_initial_position(self) -> None:
        if self._initial_coordinates is not None:
            self.move(self._initial_coordinates)
            return
        if self._initial_position is not InitialPosition.TOP_RIGHT:
            return
        screen = self.screen() or QtWidgets.QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        self.move(available.right() - self.width() - 10, available.top() + 10)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if watched is not self.drag_handle and watched is not getattr(
            self, "title_label", None
        ):
            return super().eventFilter(watched, event)
        if event.type() == QtCore.QEvent.Type.MouseButtonPress:
            if isinstance(event, QtGui.QMouseEvent):
                self._start_drag(event)
                return event.isAccepted()
        elif event.type() == QtCore.QEvent.Type.MouseMove:
            if isinstance(event, QtGui.QMouseEvent):
                self._move_drag(event)
                return event.isAccepted()
        elif event.type() == QtCore.QEvent.Type.MouseButtonRelease:
            if isinstance(event, QtGui.QMouseEvent):
                self._end_drag(event)
                return event.isAccepted()
        return super().eventFilter(watched, event)

    def _start_drag(self, event: QtGui.QMouseEvent) -> None:
        if event.button() != QtCore.Qt.MouseButton.LeftButton:
            return
        window_handle = self.windowHandle()
        if window_handle is not None and window_handle.startSystemMove():
            event.accept()
            return
        self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        self.drag_handle.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
        event.accept()

    def _move_drag(self, event: QtGui.QMouseEvent) -> None:
        if not event.buttons() & QtCore.Qt.MouseButton.LeftButton or self._drag_offset is None:
            return
        self.move(event.globalPosition().toPoint() - self._drag_offset)
        event.accept()

    def _end_drag(self, event: QtGui.QMouseEvent) -> None:
        self._drag_offset = None
        self.drag_handle.setCursor(QtCore.Qt.CursorShape.OpenHandCursor)
        event.accept()

    @staticmethod
    def _is_int(value: object) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    @classmethod
    def _is_positive_int(cls, value: object) -> bool:
        return cls._is_int(value) and value > 0