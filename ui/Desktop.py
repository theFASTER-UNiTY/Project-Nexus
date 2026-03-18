from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPixmap, QPainter, QIcon
from PySide6.QtWidgets import QWidget

from core.theme.theme import theme
from ui.WindowCompositor import WindowCompositor
from ui.Taskbar import Taskbar


class ClickableWallpaper(QWidget):
    clicked = Signal()

    def __init__(self, parent: Desktop):
        super().__init__(parent)
        self.wallParent = parent
        self._pixmap = QPixmap()

    def setWallpaper(self, path: str):
        self._pixmap = QPixmap(path)
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)

    def paintEvent(self, event):
        if self._pixmap.isNull():
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        scaled = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2

        p.drawPixmap(x, y, scaled)


class Desktop(QWidget):
    def __init__(self, kernel):
        super().__init__()
        self.kernel = kernel

        self._wallPath = ""

        themeState = self.kernel.state.get("theme", {})
        scheme = themeState.get("scheme", "dark") if isinstance(themeState, dict) else "dark"

        if scheme == "dark":
            self._wallPath = "assets/wallpapers/img7.png"
        else:
            self._wallPath = "assets/wallpapers/img5.png"

        self.setMinimumSize(1280, 720)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("Desktop")

        self.wallpaper = ClickableWallpaper(self)
        self.wallpaper.setObjectName("Wallpaper")
        self.wallpaper.setWallpaper(self._wallPath)

        self.compositor = WindowCompositor(kernel)
        self.compositor.setParent(self)

        self.taskbar = Taskbar(kernel, self.compositor)
        self.taskbar.setParent(self)

        self.setStyleSheet(f"""
            #Desktop {{
                background: {theme.palette.desktopBg};
            }}
        """)

        self._updateShellGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._updateShellGeometry()

    def _updateShellGeometry(self):
        fullRect = self.rect()

        self.wallpaper.setGeometry(fullRect)
        self.compositor.setGeometry(fullRect)

        tbHeight = self.taskbar.height()
        self.taskbar.setGeometry(0, self.height() - tbHeight, self.width(), tbHeight)

        self.wallpaper.lower()
        self.compositor.raise_()
        self.taskbar.raise_()
