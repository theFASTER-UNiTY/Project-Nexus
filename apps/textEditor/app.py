import os
from PySide6.QtWidgets import QTextEdit
from core.AppExtension import AppExtension

class App(AppExtension):
    appId = "textEditor"
    name = "Text Editor"
    description = "Editeur de texte"
    icon = os.path.join(os.path.dirname(__file__), "icon.png")

    def launch(self):
        editor = QTextEdit()

        windowId = self.windows.openWindow(
            title="Text Editor",
            content=editor,
            icon=self.icon,
            width=800,
            height=450
        )
        editor.textChanged.connect(lambda: self.windows.setTitle(
            windowId,
            f"{editor.toPlainText()[:15]} - {self.name}" if editor.toPlainText() else self.name
        ))