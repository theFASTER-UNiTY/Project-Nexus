from __future__ import annotations

from PySide6.QtCore import Qt, QSize, Signal, QPoint
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from core.theme.fonts import ElidableLabel


class DesktopIcon(QWidget):
    activated = Signal(str)
    selected = Signal(str)

    dragStarted = Signal(str, QPoint)
    dragMoved = Signal(str, QPoint)
    dragFinished = Signal(str, QPoint)

    def __init__(self, entryId: str, label: str, icon, parent=None):
        super().__init__(parent)

        self.entryId = entryId
        self._selected = False

        self._pressPosLocal: QPoint | None = None
        self._pressPosGlobal: QPoint | None = None
        self._dragging = False
        self._dragThreshold = 8

        self.setObjectName("DesktopIcon")
        self.setFixedSize(100, 100)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.iconLabel = QLabel(self)
        self.iconLabel.setObjectName("DesktopIconImage")
        self.iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.iconLabel.setFixedSize(48, 48)

        self.textLabel = ElidableLabel(label, self)
        self.textLabel.setObjectName("DesktopIconText")
        self.textLabel.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        )
        self.textLabel.setWordWrap(True)

        qicon = icon if isinstance(icon, QIcon) else QIcon(str(icon))
        self.iconLabel.setPixmap(qicon.pixmap(QSize(48, 48)))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        layout.addWidget(self.iconLabel, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.textLabel, 1)

        self._applyStyle()

    def setSelected(self, selected: bool):
        self._selected = selected
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def isSelected(self) -> bool:
        return self._selected

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressPosLocal = event.position().toPoint()
            self._pressPosGlobal = event.globalPosition().toPoint()
            self._dragging = False
            self.selected.emit(self.entryId)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)
            return

        if self._pressPosGlobal is None:
            super().mouseMoveEvent(event)
            return

        currentGlobal = event.globalPosition().toPoint()
        delta = currentGlobal - self._pressPosGlobal

        if not self._dragging and delta.manhattanLength() >= self._dragThreshold:
            self._dragging = True
            self.dragStarted.emit(self.entryId, currentGlobal)

        if self._dragging:
            self.dragMoved.emit(self.entryId, currentGlobal)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._dragging:
                self.dragFinished.emit(
                    self.entryId,
                    event.globalPosition().toPoint()
                )
                self._dragging = False
                self._pressPosLocal = None
                self._pressPosGlobal = None
                event.accept()
                return

            self._pressPosLocal = None
            self._pressPosGlobal = None
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and not self._dragging:
            self.activated.emit(self.entryId)
            event.accept()
            return

        super().mouseDoubleClickEvent(event)

    def _applyStyle(self):
        self.setSelected(self._selected)
