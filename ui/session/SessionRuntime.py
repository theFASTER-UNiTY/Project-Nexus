from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from ui.HostWindow import HostWindow
from ui.Desktop import Desktop
from ui.login.LoginScreen import LoginScreen
from ui.lock.LockScreen import LockScreen


class SessionRuntime(QObject):
    LOGIN_PAGE = "login"
    DESKTOP_PAGE = "desktop"
    LOCK_PAGE = "lock"

    def __init__(self, app: QApplication, kernel):
        super().__init__()

        self.app = app
        self.kernel = kernel

        self.hostWindow = HostWindow(kernel)
        self.loginScreen = None
        self.desktop = None
        self.lockScreen = None

        self._cleanupAfterTransition = []

        self._connectBusSignals()

    # -------------------------------------------------
    # Bus
    # -------------------------------------------------
    def _connectBusSignals(self):
        self.kernel.bus.subscribe("session.logout.requested", self._onLogoutRequested)
        self.kernel.bus.subscribe("session.lock.requested", self._onLockRequested)

    # -------------------------------------------------
    # Start
    # -------------------------------------------------
    def start(self):
        self.hostWindow.show()
        self.hostWindow.raise_()
        self.hostWindow.activateWindow()

        self._bindPowerHost(self.hostWindow)

        profile = None
        try:
            profile = self.kernel.session.startDefaultSession()
        except Exception as exc:
            print(f"Nexus: auto-login failed: {exc}")

        if profile is not None:
            self.showDesktopPage()
        else:
            self.showLoginPage()

    # -------------------------------------------------
    # Transition helper
    # -------------------------------------------------
    def _showPageWithCleanup(self, pageName: str, cleanupPages: list[str] | None = None):
        cleanupPages = cleanupPages or []

        def onFinished(finishedPage: str):
            if finishedPage != pageName:
                return

            """ try:
                self.hostWindow.transitionFinished.disconnect(onFinished)
            except Exception:
                pass """

            for page in cleanupPages:
                if page == self.LOGIN_PAGE:
                    self._destroyLoginPage()
                elif page == self.DESKTOP_PAGE:
                    self._destroyDesktopPage()
                elif page == self.LOCK_PAGE:
                    self._destroyLockPage()

        # self.hostWindow.transitionFinished.connect(onFinished)
        self.hostWindow.showPage(pageName)

    # -------------------------------------------------
    # Login
    # -------------------------------------------------
    def showLoginPage(self):
        if self.loginScreen is None:
            self.loginScreen = LoginScreen(self.kernel)
            self.loginScreen.loginSucceeded.connect(self._onLoginSucceeded)
            self.loginScreen.shutdownRequested.connect(self._onShutdownRequested)
            self.loginScreen.restartRequested.connect(self._onRestartRequested)
            self.loginScreen.sleepRequested.connect(self._onSleepRequested)
            self.hostWindow.setPage(self.LOGIN_PAGE, self.loginScreen)
        else:
            if hasattr(self.loginScreen, "loadUsers"):
                self.loginScreen.loadUsers()
            if hasattr(self.loginScreen, "updateSelectedUserUi"):
                self.loginScreen.updateSelectedUserUi()

        self._showPageWithCleanup(
            self.LOGIN_PAGE,
            cleanupPages=[self.LOCK_PAGE, self.DESKTOP_PAGE]
        )

        if hasattr(self.loginScreen, "passwordEdit"):
            self.loginScreen.passwordEdit.clear()
            self.loginScreen.passwordEdit.setFocus()

    def _onLoginSucceeded(self, username: str):
        self.showDesktopPage()

    # -------------------------------------------------
    # Desktop
    # -------------------------------------------------
    def showDesktopPage(self):
        if self.desktop is None:
            self.desktop = Desktop(self.kernel)
            self.hostWindow.setPage(self.DESKTOP_PAGE, self.desktop)
            self._bindDesktopServices(self.desktop)

        self._showPageWithCleanup(
            self.DESKTOP_PAGE,
            cleanupPages=[self.LOGIN_PAGE, self.LOCK_PAGE]
        )

    def _bindDesktopServices(self, desktop: Desktop):
        win = self.kernel.services.get("windows")
        if win is not None:
            win.bindDesktop(desktop)

        if hasattr(desktop, "taskbar") and hasattr(desktop.taskbar, "_populateNexHubApps"):
            desktop.taskbar._populateNexHubApps()

    # -------------------------------------------------
    # Lock
    # -------------------------------------------------
    def showLockPage(self):
        if self.desktop is None:
            self.showLoginPage()
            return

        if self.lockScreen is None:
            self.lockScreen = LockScreen(self.kernel)
            self.lockScreen.unlockRequested.connect(self._onUnlockRequested)
            self.lockScreen.switchUserRequested.connect(self._onSwitchUserRequested)
            self.hostWindow.setPage(self.LOCK_PAGE, self.lockScreen)

        self.lockScreen.refreshFromSession()
        self.lockScreen.showClockView()

        # IMPORTANT :
        # on ne détruit PAS le desktop ici
        self._showPageWithCleanup(
            self.LOCK_PAGE,
            cleanupPages=[self.LOGIN_PAGE]
        )

    def _onUnlockRequested(self):
        self.showDesktopPage()

    def _onSwitchUserRequested(self):
        try:
            if hasattr(self.kernel, "session") and self.kernel.session.hasActiveSession():
                self.kernel.session.logout()
        except Exception as exc:
            print(f"Nexus: switch user logout failed: {exc}")

        self._destroyLockPage()
        self._destroyDesktopPage()
        self.showLoginPage()

    # -------------------------------------------------
    # Destroy helpers
    # -------------------------------------------------
    def _destroyDesktopPage(self):
        if self.desktop is None:
            return

        try:
            self.desktop.close()
        except Exception:
            pass

        self.hostWindow.removePage(self.DESKTOP_PAGE)
        self.desktop = None

    def _destroyLoginPage(self):
        if self.loginScreen is None:
            return

        try:
            self.loginScreen.close()
        except Exception:
            pass

        self.hostWindow.removePage(self.LOGIN_PAGE)
        self.loginScreen = None

    def _destroyLockPage(self):
        if self.lockScreen is None:
            return

        try:
            self.lockScreen.close()
        except Exception:
            pass

        self.hostWindow.removePage(self.LOCK_PAGE)
        self.lockScreen = None

    # -------------------------------------------------
    # Power
    # -------------------------------------------------
    def _bindPowerHost(self, hostWindow):
        power = self.kernel.services.get("power")
        if power is not None:
            power.bindHostWindow(hostWindow)

    def _onSleepRequested(self):
        self.kernel.bus.emit("system.sleep.requested")
        power = self.kernel.services.get("power")
        if power is not None:
            power.sleep()

    def _onShutdownRequested(self):
        self.kernel.bus.emit("system.shutdown.requested")
        power = self.kernel.services.get("power")
        if power is not None:
            power.quitApplication()

    def _onRestartRequested(self):
        self.kernel.bus.emit("system.restart.requested")
        power = self.kernel.services.get("power")
        if power is not None:
            power.quitApplication()

    # -------------------------------------------------
    # Session events
    # -------------------------------------------------
    def _onLogoutRequested(self, data=None):
        try:
            if hasattr(self.kernel, "session") and self.kernel.session.hasActiveSession():
                self.kernel.session.logout()
        except Exception as exc:
            print(f"Nexus: logout failed: {exc}")

        self._destroyLockPage()
        self._destroyDesktopPage()
        self.showLoginPage()

    def _onLockRequested(self, data=None):
        self.showLockPage()
