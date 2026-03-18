import os
from PySide6.QtWidgets import QLabel
from core.AppExtension import AppExtension


class App(AppExtension):
    sysInfo = AppExtension.systemInfo
    appId = "settings"
    name = "Settings"
    version = f"{sysInfo.version}.{sysInfo.build}-{sysInfo.channel}"
    description = "Configuration système"
    icon = os.path.join(os.path.dirname(__file__), "icon6.png")

    def launch(self):
        content = QLabel("System Settings")

        windows = self.kernel.services.get("windows")
        windows.openWindow(
            title=self.name,
            content=content,
            icon=self.icon,
            width=720,
            height=520
        )