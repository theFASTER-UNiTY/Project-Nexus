from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QWidget

from core.Service import Service


class WindowService(Service):
    name = "windows"

    def __init__(self, kernel):
        super().__init__(kernel)
        self.desktop = None

    def start(self) -> None:
        super().start()
        # écoute éventuelle d'événements système
        # ex: self.kernel.bus.subscribe("app.open_window", ...)

    def bindDesktop(self, desktop) -> None:
        self.desktop = desktop

    def openWindow(self, *, title: str, content: QWidget, icon=None, width=640, height=420):
        if not self.desktop:
            raise RuntimeError("WindowService: Desktop not bound yet.")
        return self.desktop.compositor.createWindow(
            title=title, content=content, icon=icon, width=width, height=height
        )

    def getWindow(self, windowId: str):
        if self.desktop is None:
            return None
        return self.desktop.compositor.getWindow(windowId)

    def setTitle(self, windowId: str, title: str) -> bool:
        wf = self.getWindow(windowId)
        if wf is None:
            return False

        wf.setFrameTitle(title)
        return True

    def setIcon(self, windowId: str, icon) -> bool:
        wf = self.getWindow(windowId)
        if wf is None:
            return False

        wf.setFrameIcon(icon)
        return True

    def update(self, windowId: str, *, title=None, icon=None) -> bool:
        if self.desktop is None:
            return False

        self.desktop.compositor.updateWindow(
            windowId,
            title=title,
            icon=icon
        )
        return True

    def focus(self, windowId: str) -> None:
        if self.desktop:
            self.desktop.compositor.focusWindow(windowId)

    def close(self, windowId: str) -> None:
        if self.desktop:
            self.desktop.compositor.closeWindow(windowId)

    def minimize(self, windowId: str) -> None:
        if self.desktop:
            self.desktop.compositor.minimizeWindow(windowId)

    def restore(self, windowId: str) -> None:
        if self.desktop:
            self.desktop.compositor.restoreWindow(windowId)
