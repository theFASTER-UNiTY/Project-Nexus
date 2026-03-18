import os
from PySide6.QtWidgets import QTextEdit, QWidget, QVBoxLayout
from core.AppExtension import AppExtension


class App(AppExtension):
    appId = "notes"
    name = "NexPad"
    description = "Bloc-notes"
    icon = os.path.join(os.path.dirname(__file__), "icon.png")


    def launch(self):
        content = QWidget()
        content.setContentsMargins(0, 0, 0, 0)

        contentLayout = QVBoxLayout(content)
        contentLayout.setContentsMargins(4, 4, 4, 4)
        contentLayout.setSpacing(0)

        editor = QTextEdit()
        contentLayout.addWidget(editor)

        windowId = self.windows.openWindow(
            title=self.name,
            content=content,
            icon=self.icon,
            width=800,
            height=600
        )

        editor.textChanged.connect(lambda: self.windows.setTitle(
            windowId,
            f"{editor.toPlainText()[:15]} - {self.name}" if editor.toPlainText() else self.name
        ))