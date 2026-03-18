import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from core.Kernel import Kernel
from core.SystemInfo import SystemInfo
from core.theme.theme import theme
from services.WindowService import WindowService
from services.AppService import AppService
from services.PasswordService import PasswordService
from services.PowerService import PowerService
from ui.session.SessionRuntime import SessionRuntime


BASE_PATH = Path(__file__).resolve().parent


def launchNexus():
    try:
        app = QApplication(sys.argv)

        sysInfo = SystemInfo()

        app.setApplicationName(sysInfo.name)
        app.setApplicationVersion(f"{sysInfo.version}.{sysInfo.build}-{sysInfo.channel}")
        app.setApplicationDisplayName(
            f"{app.applicationName()} ({sysInfo.codename} - {app.applicationVersion()})"
        )
        app.setWindowIcon(QIcon(str(BASE_PATH / "assets" / "icons" / "icon.png")))

        kernel = Kernel()

        kernel.services.register(WindowService)
        kernel.services.register(AppService)
        kernel.services.register(PasswordService)
        kernel.services.register(PowerService)

        kernel.start()

        # kernel.state["theme"]["scheme"] = "light"
        kernel.state["theme"]["accent"] = "blue"
        theme.apply(app, kernel)

        runtime = SessionRuntime(app, kernel)
        runtime.start()

        return app.exec()

    except Exception as e:
        print(f"Failed to start Nexus: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(launchNexus())
