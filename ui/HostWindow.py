from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget


class HostWindow(QMainWindow):
    """
    Fenêtre hôte unique de SmartNexus.

    Elle contient un stack de pages internes :
    - LoginScreen
    - Desktop
    - LockScreen (plus tard)

    Le but est d'éviter d'avoir plusieurs top-level windows.
    """

    def __init__(self, kernel, parent=None):
        super().__init__(parent)

        self.kernel = kernel

        self.setObjectName("HostWindow")
        self.setMinimumSize(1280, 720)
        # self.resize(1366, 768)

        self._pageNames: dict[str, QWidget] = {}

        self._buildUi()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def _buildUi(self):
        central = QWidget(self)
        central.setObjectName("HostWindowCentral")

        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget(central)
        self.stack.setObjectName("HostStack")

        layout.addWidget(self.stack)

        self.setStyleSheet("""
            QMainWindow#HostWindow {
                background: #0e1320;
            }

            QWidget#HostWindowCentral,
            QStackedWidget#HostStack {
                background: transparent;
            }
        """)

    # -------------------------------------------------
    # Pages
    # -------------------------------------------------
    def hasPage(self, name: str) -> bool:
        return name in self._pageNames

    def page(self, name: str):
        return self._pageNames.get(name)

    def setPage(self, name: str, widget: QWidget):
        """
        Ajoute ou remplace une page dans le stack.
        """
        old = self._pageNames.get(name)
        if old is widget:
            return

        if old is not None:
            index = self.stack.indexOf(old)
            if index >= 0:
                self.stack.removeWidget(old)
            old.setParent(None)
            old.deleteLater()

        self._pageNames[name] = widget
        self.stack.addWidget(widget)

    def showPage(self, name: str):
        widget = self._pageNames.get(name)
        if widget is None:
            raise KeyError(f"Unknown page: {name}")

        self.stack.setCurrentWidget(widget)
        widget.show()
        widget.raise_()
        widget.setFocus()

    def removePage(self, name: str):
        widget = self._pageNames.pop(name, None)
        if widget is None:
            return

        index = self.stack.indexOf(widget)
        if index >= 0:
            self.stack.removeWidget(widget)

        widget.setParent(None)
        widget.deleteLater()

    def currentPageName(self) -> str | None:
        current = self.stack.currentWidget()
        if current is None:
            return None

        for name, widget in self._pageNames.items():
            if widget is current:
                return name

        return None
