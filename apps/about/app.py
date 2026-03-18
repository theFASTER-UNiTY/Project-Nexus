import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout

from core.AppExtension import AppExtension
from core.classes.widgets import IconWidget


class App(AppExtension):
    sysInfo = AppExtension.systemInfo

    appId = "nexver"
    name = "About Nexus"
    version = sysInfo.version
    description = "A propos de Nexus"
    icon = os.path.join(os.path.dirname(__file__), "icon1.png")

    def launch(self):
        content = QWidget()
        content.setStyleSheet("background: transparent")
        content.setContentsMargins(0, 0, 0, 0)

        root = QVBoxLayout(content)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)
        
        logo = IconWidget(os.path.join(os.path.dirname(__file__), "assets", "logo.png"), 300, 120)
        logo.setMaximumHeight(120)

        nexver = QLabel(f"A propos de Nexus\n\n"
                        f'{self.sysInfo.name} (codename "{self.sysInfo.codename}")'
                        f"\nVersion {self.sysInfo.version}\n"
                        f"Build du système d'exploitation : {self.sysInfo.build}\n"
                        f"Canal de déploiement : {self.sysInfo.channel.capitalize()}\n\n"
                         "(c) SmartSoft by #theFASTER™ UN!TY. All rights reserved."
                 )
        nexver.setWordWrap(True)

        root.addWidget(logo, 0, Qt.AlignmentFlag.AlignCenter)
        root.addWidget(nexver, 0, Qt.AlignmentFlag.AlignCenter)
        # root.addStretch()

        self.windows.openWindow(
            title="About Nexus",
            content=content,
            width=380,
            height=340
        )