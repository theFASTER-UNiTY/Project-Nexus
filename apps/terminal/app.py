import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QScrollArea, QSizePolicy
)

from core.AppExtension import AppExtension
from core.theme.fonts import fonts
from ui.NexHub import NexHubPanel


class App(AppExtension):
    sysInfo = AppExtension.systemInfo
    appId = "terminal"
    name = "NexCommander"
    version = f"{sysInfo.version}.{sysInfo.build}-{sysInfo.channel}"
    description = "Console système"
    icon = os.path.join(os.path.dirname(__file__), "icon.png")
    
    def launch(self):
        content = QWidget()

        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        contentScroll = QScrollArea()
        contentScroll.setWidgetResizable(True)
        contentScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        contentScroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # contentScroll.setFrameShape(QFrame.Shape.NoFrame)

        self.content = QWidget()
        self.content.setObjectName("WindowBase")
        self.content.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.contentLayout = QVBoxLayout(self.content)
        self.contentLayout.setContentsMargins(0, 0, 0, 0)
        self.contentLayout.setSpacing(0)

        contentScroll.setWidget(self.content)

        self.contentLabel = QLabel(
            f"{self.sysInfo.name} [version {self.version}]\n"
            f"(c) SmartSoft by #theFASTER™ UN!TY. All rights reserved.\n\n"
            f"/users/SYSTEM/files>_"
        )
        self.contentLabel.setFont(fonts.monoFont(10))
        self.contentLabel.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.contentLayout.addWidget(self.contentLabel)
        self.contentLayout.addStretch(1)

        root.addWidget(contentScroll)

        content.setStyleSheet(f'''
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QWidget#WindowBase {{
                background: white;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
            }}
            QLabel {{
                color: #CCCCCC;
            }}
        ''')
        self.windows.openWindow(
            title=f"NexCommander",
            content=content,
            icon=self.icon,
            width=640,
            height=420
        )