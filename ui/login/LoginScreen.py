from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QFont, QPainter, QColor, QLinearGradient, QAction
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox,
    QToolButton, QMenu, QMessageBox, QSizePolicy,
)


class AvatarWidget(QWidget):
    def __init__(self, size: int = 96, parent=None):
        super().__init__(parent)
        self._size = size
        self._text = "?"
        self.setFixedSize(size, size)

    def setText(self, text: str) -> None:
        self._text = (text[:1] if text else "?").upper()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(2, 2, -2, -2)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 28))
        painter.drawEllipse(rect)

        innerRect = rect.adjusted(6, 6, -6, -6)
        painter.setBrush(QColor(79, 140, 255, 210))
        painter.drawEllipse(innerRect)

        font = painter.font()
        font.setPointSize(max(18, self._size // 3))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)


class GlassPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LoginPanel")
        self.setFixedWidth(420)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)

        painter.setPen(QColor(255, 255, 255, 28))
        painter.setBrush(QColor(22, 28, 40, 150))
        painter.drawRoundedRect(rect, 18, 18)


class BottomBar(QFrame):
    shutdownRequested = Signal()
    restartRequested = Signal()
    sleepRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BottomBar")
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 8, 18, 8)
        layout.setSpacing(12)

        self.leftRow = QHBoxLayout()
        self.leftRow.setSpacing(10)

        self.networkButton = self._makeIconButton("📶", "Réseau")
        self.accessibilityButton = self._makeIconButton("♿", "Accessibilité")
        self.powerButton = QToolButton()
        self.powerButton.setText("⏻")
        self.powerButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.powerButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.powerButton.setStyleSheet("""
            QToolButton {
                color: white;
                background: transparent;
                border: none;
                font-size: 22px;
                padding: 6px 10px;
            }
            QToolButton:hover {
                background: rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)

        powerMenu = QMenu(self)
        actionSleep = QAction("Veille", self)
        actionRestart = QAction("Redémarrer", self)
        actionShutdown = QAction("Éteindre", self)

        actionSleep.triggered.connect(self.sleepRequested.emit)
        actionRestart.triggered.connect(self.restartRequested.emit)
        actionShutdown.triggered.connect(self.shutdownRequested.emit)

        powerMenu.addAction(actionSleep)
        powerMenu.addSeparator()
        powerMenu.addAction(actionShutdown)
        powerMenu.addAction(actionRestart)

        self.powerButton.setMenu(powerMenu)

        self.leftRow.addWidget(self.networkButton)
        self.leftRow.addWidget(self.accessibilityButton)
        self.leftRow.addWidget(self.powerButton)

        self.timeLabel = QLabel("00:00")
        self.timeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timeLabel.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: 600;
            }
        """)

        self.dateLabel = QLabel("Lundi, 01 janvier")
        self.dateLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.dateLabel.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.92);
                font-size: 14px;
            }
        """)

        layout.addLayout(self.leftRow)
        layout.addStretch(1)
        layout.addWidget(self.timeLabel)
        layout.addStretch(1)
        layout.addWidget(self.dateLabel)

        timer = QTimer(self)
        timer.timeout.connect(self.updateDateTime)
        timer.start(100)
        self.updateDateTime()

    def _makeIconButton(self, text: str, tooltip: str) -> QPushButton:
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip(tooltip)
        button.setFixedSize(40, 40)
        button.setStyleSheet("""
            QPushButton {
                color: white;
                background: transparent;
                border: none;
                font-size: 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
            }
        """)
        return button

    def updateDateTime(self) -> None:
        from PySide6.QtCore import QDateTime

        now = QDateTime.currentDateTime()
        self.timeLabel.setText(now.toString("HH:mm"))
        self.dateLabel.setText(now.toString("dddd, dd MMMM"))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 72))


class LoginScreen(QWidget):
    loginSucceeded = Signal(str)
    shutdownRequested = Signal()
    restartRequested = Signal()
    sleepRequested = Signal()

    def __init__(self, kernel, parent=None):
        super().__init__(parent)
        self.kernel = kernel
        self.selectedUser = None
        self.hasUsers = False

        self.setObjectName("LoginScreen")
        # self.setWindowTitle("Connexion")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet(self.buildStyleSheet())

        self.buildUi()
        self.loadUsers()
        self.updateSelectedUserUi()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def buildUi(self) -> None:
        rootLayout = QVBoxLayout(self)
        rootLayout.setContentsMargins(30, 30, 30, 20)
        rootLayout.setSpacing(0)

        rootLayout.addStretch(1)

        centerRow = QHBoxLayout()
        centerRow.addStretch(1)

        self.panel = GlassPanel(self)

        panelLayout = QVBoxLayout(self.panel)
        panelLayout.setContentsMargins(34, 28, 34, 24)
        panelLayout.setSpacing(14)

        self.avatar = AvatarWidget(104, self.panel)

        self.welcomeLabel = QLabel("Welcome back")
        self.welcomeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcomeLabel.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.88);
                font-size: 15px;
            }
        """)

        self.usernameLabel = QLabel("Utilisateur")
        self.usernameLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.usernameLabel.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 22px;
                font-weight: 700;
            }
        """)

        self.usernameEdit = QLineEdit()
        self.usernameEdit.setPlaceholderText("Nom d'utilisateur")
        self.usernameEdit.setVisible(False)
        self.usernameEdit.setMinimumHeight(44)

        self.passwordEdit = QLineEdit()
        self.passwordEdit.setPlaceholderText("Mot de passe")
        self.passwordEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.passwordEdit.setMinimumHeight(46)
        self.passwordEdit.returnPressed.connect(self.handleLogin)

        self.errorLabel = QLabel("")
        self.errorLabel.setWordWrap(True)
        self.errorLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.errorLabel.setStyleSheet("""
            QLabel {
                color: #ffb0b0;
                font-size: 13px;
                min-height: 18px;
            }
        """)

        self.loginButton = QPushButton("Login")
        self.loginButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.loginButton.setMinimumHeight(46)
        self.loginButton.clicked.connect(self.handleLogin)

        self.userSwitcher = QComboBox()
        self.userSwitcher.setMinimumHeight(40)
        self.userSwitcher.currentIndexChanged.connect(self.onUserChanged)

        avatarRow = QHBoxLayout()
        avatarRow.addStretch(1)
        avatarRow.addWidget(self.avatar)
        avatarRow.addStretch(1)

        panelLayout.addLayout(avatarRow)
        panelLayout.addSpacing(4)
        panelLayout.addWidget(self.welcomeLabel)
        panelLayout.addWidget(self.usernameLabel)
        panelLayout.addWidget(self.usernameEdit)
        panelLayout.addSpacing(2)
        panelLayout.addWidget(self.passwordEdit)
        panelLayout.addWidget(self.errorLabel)
        panelLayout.addWidget(self.loginButton)
        panelLayout.addSpacing(4)
        panelLayout.addWidget(self.userSwitcher)

        centerRow.addWidget(self.panel)
        centerRow.addStretch(1)

        rootLayout.addLayout(centerRow)
        rootLayout.addStretch(1)

        self.bottomBar = BottomBar(self)
        self.bottomBar.shutdownRequested.connect(self.shutdownRequested.emit)
        self.bottomBar.restartRequested.connect(self.restartRequested.emit)
        self.bottomBar.sleepRequested.connect(self.sleepRequested.emit)
        rootLayout.addWidget(self.bottomBar)

    def buildStyleSheet(self) -> str:
        return """
        QWidget#LoginScreen {
            background: transparent;
        }

        QLineEdit, QComboBox {
            background: rgba(10, 16, 28, 170);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 10px;
            padding: 0 12px;
            font-size: 14px;
        }

        QLineEdit:focus, QComboBox:focus {
            border: 1px solid rgba(79, 140, 255, 0.95);
        }

        QPushButton {
            border: none;
            border-radius: 10px;
        }

        QPushButton:disabled {
            background: rgba(79, 140, 255, 0.35);
            color: rgba(255, 255, 255, 0.7);
        }

        QPushButton:hover {
            background: #6ea3ff;
        }

        QPushButton#secondaryButton {
            background: rgba(255, 255, 255, 0.06);
            color: white;
        }

        QPushButton#secondaryButton:hover {
            background: rgba(255, 255, 255, 0.12);
        }

        QComboBox::drop-down {
            border: none;
            width: 28px;
        }

        QComboBox QAbstractItemView {
            background: rgb(28, 34, 48);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.10);
            selection-background-color: rgba(79, 140, 255, 0.45);
            outline: none;
        }
        """

    # -------------------------------------------------
    # Données utilisateurs
    # -------------------------------------------------
    def loadUsers(self) -> None:
        self.userSwitcher.blockSignals(True)
        self.userSwitcher.clear()

        users = self.getAvailableUsers()
        self.hasUsers = len(users) > 0

        if self.hasUsers:
            for username in users:
                self.userSwitcher.addItem(username)

            self.selectedUser = users[0]
            self.usernameEdit.setVisible(False)
            self.usernameLabel.setVisible(True)
            self.userSwitcher.setVisible(True)
            self.userSwitcher.setEnabled(len(users) > 1)
        else:
            self.selectedUser = None
            self.usernameEdit.setVisible(True)
            self.usernameLabel.setVisible(False)
            self.userSwitcher.setVisible(False)

        self.userSwitcher.blockSignals(False)

    def getAvailableUsers(self) -> list[str]:
        usersRoot = "/users"

        if not hasattr(self.kernel, "filesystem"):
            return []

        fs = self.kernel.filesystem

        if not fs.exists(usersRoot):
            return []

        if not fs.isDir(usersRoot):
            return []

        result = []
        for entry in fs.listDir(usersRoot):
            try:
                path = f"/users/{entry}"
                if fs.isDir(path):
                    result.append(entry)
            except Exception:
                continue

        return sorted(result, key=lambda x: x.lower())

    def onUserChanged(self, index: int) -> None:
        if index < 0:
            return

        self.selectedUser = self.userSwitcher.currentText().strip()
        self.updateSelectedUserUi()
        self.passwordEdit.clear()
        self.errorLabel.clear()
        self.passwordEdit.setFocus()

    def updateSelectedUserUi(self) -> None:
        if self.hasUsers:
            username = self.selectedUser or self.userSwitcher.currentText().strip() or "User"
            self.usernameLabel.setText(username)
            self.avatar.setText(username)
        else:
            username = self.usernameEdit.text().strip() or "?"
            self.avatar.setText(username)

    # -------------------------------------------------
    # Actions
    # -------------------------------------------------
    def handleLogin(self) -> None:
        self.errorLabel.clear()
        self.loginButton.setEnabled(False)

        try:
            if self.hasUsers:
                username = (self.selectedUser or "").strip()
            else:
                username = self.usernameEdit.text().strip()

            password = self.passwordEdit.text()

            if not username:
                raise ValueError("Veuillez renseigner un nom d'utilisateur.")

            # vérification mot de passe
            if self.hasUsers and not self.kernel.session.verifyPassword(username, password):
                raise ValueError("Mot de passe incorrect.")

            if not self.hasUsers: self.kernel.session.setUserPassword(username, password)
            self.kernel.session.login(username)
            self.loginSucceeded.emit(username)

        except Exception as exc:
            self.errorLabel.setText(str(exc))
            self.passwordEdit.selectAll()
            self.passwordEdit.setFocus()

        finally:
            self.loginButton.setEnabled(True)

    # -------------------------------------------------
    # Rendu fond
    # -------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(10, 24, 48))
        gradient.setColorAt(0.45, QColor(58, 68, 102))
        gradient.setColorAt(0.75, QColor(36, 48, 80))
        gradient.setColorAt(1.0, QColor(10, 16, 28))
        painter.fillRect(self.rect(), gradient)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 55))

        # halos lumineux subtils pour rappeler le mockup
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 160, 120, 30))
        painter.drawEllipse(int(self.width() * 0.08), int(self.height() * 0.68), 260, 180)

        painter.setBrush(QColor(90, 150, 255, 26))
        painter.drawEllipse(int(self.width() * 0.62), int(self.height() * 0.14), 320, 220)

        painter.setBrush(QColor(255, 200, 120, 18))
        painter.drawEllipse(int(self.width() * 0.74), int(self.height() * 0.62), 260, 180)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateSelectedUserUi()
