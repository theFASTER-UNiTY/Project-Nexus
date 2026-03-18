from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from core.Service import Service


class PowerService(Service):
    name = "power"

    def __init__(self, kernel):
        super().__init__(kernel)

        self._trayIcon = None
        self._trayMenu = None
        self._hostWindow = None
        self._sleeping = False
        self._hostWasMaximized = False
        self._hostWasFullScreen = False
        self._hostNormalGeometry = None

    def start(self):
        super().start()

    def bindHostWindow(self, hostWindow):
        self._hostWindow = hostWindow

    def isSleeping(self) -> bool:
        return self._sleeping

    def _ensureTray(self):
        if self._trayIcon is not None:
            return

        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        app = QApplication.instance()
        if app is None:
            return

        icon = app.windowIcon() # type: ignore
        if icon.isNull():
            icon = QIcon("assets/icons/icon.png")

        self._trayMenu = QMenu()

        restoreAction = QAction("Restaurer Nexus", self._trayMenu)
        quitAction = QAction("Quitter", self._trayMenu)

        restoreAction.triggered.connect(self.wakeFromSleep)
        quitAction.triggered.connect(self.quitApplication)

        self._trayMenu.addAction(restoreAction)
        self._trayMenu.addSeparator()
        self._trayMenu.addAction(quitAction)

        self._trayIcon = QSystemTrayIcon(icon)
        self._trayIcon.setToolTip("SmartSoft Nexus: Sleep mode")
        self._trayIcon.setContextMenu(self._trayMenu)
        self._trayIcon.activated.connect(self._onTrayActivated)

    def _onTrayActivated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.wakeFromSleep()

    def sleep(self):
        if self._sleeping:
            return

        if self._hostWindow is None:
            return

        self._ensureTray()
        if self._trayIcon is None:
            self._hostWasMaximized = self._hostWindow.isMaximized()
            self._hostWasFullScreen = self._hostWindow.isFullScreen()
            self._hostNormalGeometry = self._hostWindow.geometry()
            self._hostWindow.hide()
            self._sleeping = True
            return

        self._hostWasMaximized = self._hostWindow.isMaximized()
        self._hostWasFullScreen = self._hostWindow.isFullScreen()
        self._hostNormalGeometry = self._hostWindow.geometry()

        self._sleeping = True

        self.kernel.bus.emit("system.sleep.entering")
        self._hostWindow.hide()
        self._trayIcon.show()
        self._trayIcon.showMessage(
            "Sleep mode",
            "Nexus is currently in sleep mode. You can wake it up from your host's system tray.",
            QSystemTrayIcon.MessageIcon.Information,
            2500
        )
        self.kernel.bus.emit("system.sleep.entered")

    def wakeFromSleep(self):
        if not self._sleeping:
            return

        if self._hostWindow is None:
            return

        self.kernel.bus.emit("system.sleep.leaving")

        if self._hostWasFullScreen:
            self._hostWindow.showFullScreen()
        elif self._hostWasMaximized:
            self._hostWindow.showMaximized()
        else:
            if self._hostNormalGeometry is not None:
                self._hostWindow.setGeometry(self._hostNormalGeometry)
            self._hostWindow.show()

        self._hostWindow.raise_()
        self._hostWindow.activateWindow()
        self._hostWindow.update()
        self._hostWindow.repaint()

        if self._trayIcon is not None:
            self._trayIcon.hide()

        self._sleeping = False
        self.kernel.bus.emit("system.sleep.left")

    def quitApplication(self):
        self.kernel.bus.emit("system.shutdown.requested")
        app = QApplication.instance()
        if app is not None:
            app.quit()
