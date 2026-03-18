from __future__ import annotations

from PySide6.QtCore import (
    Qt, QTimer, Signal, QDateTime, QPropertyAnimation, QEasingCurve, QPoint,
    QParallelAnimationGroup
)
from PySide6.QtGui import QColor, QLinearGradient, QPainter
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QStackedLayout
)


class LockAvatar(QWidget):
    def __init__(self, size: int = 96, parent=None):
        super().__init__(parent)
        self._size = size
        self._text = "?"
        self.setFixedSize(size, size)

    def setText(self, text: str):
        self._text = (text[:1] if text else "?").upper()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 28))
        painter.drawEllipse(rect)

        inner = rect.adjusted(6, 6, -6, -6)
        painter.setBrush(QColor(79, 140, 255, 210))
        painter.drawEllipse(inner)

        font = painter.font()
        font.setBold(True)
        font.setPointSize(max(18, self._size // 3))
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)


class LockPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("lockPanel")
        self.setFixedWidth(400)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setPen(QColor(255, 255, 255, 28))
        painter.setBrush(QColor(22, 28, 40, 160))
        painter.drawRoundedRect(rect, 18, 18)


class LockScreen(QWidget):
    unlockRequested = Signal()
    switchUserRequested = Signal()

    VIEW_CLOCK = 0
    VIEW_AUTH = 1

    def __init__(self, kernel, parent=None):
        super().__init__(parent)
        self.kernel = kernel
        self.currentUser = None

        self._viewAnim = None
        self._isAnimating = False

        self.setObjectName("LockScreen")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(self._buildStyleSheet())

        self._buildUi()
        self._buildTimer()
        self.refreshFromSession()
        self.showClockView()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def _buildUi(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 24)
        root.setSpacing(0)

        self.stack = QStackedLayout()
        root.addLayout(self.stack)

        # ---------------- CLOCK VIEW ----------------
        self.clockPage = QWidget()
        clockRoot = QVBoxLayout(self.clockPage)
        clockRoot.setContentsMargins(0, 0, 0, 0)
        clockRoot.setSpacing(0)

        clockRoot.addStretch(1)

        centerBox = QVBoxLayout()
        centerBox.setSpacing(8)

        self.bigTimeLabel = QLabel("00:00")
        self.bigTimeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bigTimeLabel.setObjectName("BigTimeLabel")

        self.bigDateLabel = QLabel("Lundi, 01 janvier")
        self.bigDateLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bigDateLabel.setObjectName("BigDateLabel")

        self.hintLabel = QLabel("Cliquez ou appuyez sur une touche pour déverrouiller")
        self.hintLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hintLabel.setObjectName("HintLabel")

        centerBox.addWidget(self.bigTimeLabel)
        centerBox.addWidget(self.bigDateLabel)
        centerBox.addSpacing(12)
        centerBox.addWidget(self.hintLabel)

        clockRoot.addLayout(centerBox)
        clockRoot.addStretch(1)

        # ---------------- AUTH VIEW ----------------
        self.authPage = QWidget()
        authRoot = QVBoxLayout(self.authPage)
        authRoot.setContentsMargins(0, 0, 0, 0)
        authRoot.setSpacing(0)

        authRoot.addStretch(1)

        centerRow = QHBoxLayout()
        centerRow.addStretch(1)

        self.panel = LockPanel(self.authPage)
        panelLayout = QVBoxLayout(self.panel)
        panelLayout.setContentsMargins(34, 28, 34, 24)
        panelLayout.setSpacing(14)

        self.avatar = LockAvatar(104, self.panel)

        avatarRow = QHBoxLayout()
        avatarRow.addStretch(1)
        avatarRow.addWidget(self.avatar)
        avatarRow.addStretch(1)

        self.titleLabel = QLabel("Session verrouillée")
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titleLabel.setObjectName("LockTitleLabel")

        self.userLabel = QLabel("Utilisateur")
        self.userLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.userLabel.setObjectName("LockUserLabel")

        self.passwordEdit = QLineEdit()
        self.passwordEdit.setPlaceholderText("Mot de passe")
        self.passwordEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.passwordEdit.setMinimumHeight(46)
        self.passwordEdit.returnPressed.connect(self._handleUnlock)

        self.errorLabel = QLabel("")
        self.errorLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.errorLabel.setObjectName("LockErrorLabel")

        self.unlockButton = QPushButton("Unlock")
        self.unlockButton.setMinimumHeight(46)
        self.unlockButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.unlockButton.clicked.connect(self._handleUnlock)

        self.switchUserButton = QPushButton("Changer d’utilisateur")
        self.switchUserButton.setObjectName("SecondaryButton")
        self.switchUserButton.setMinimumHeight(42)
        self.switchUserButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.switchUserButton.clicked.connect(self._handleSwitchUser)

        panelLayout.addLayout(avatarRow)
        panelLayout.addSpacing(4)
        panelLayout.addWidget(self.titleLabel)
        panelLayout.addWidget(self.userLabel)
        panelLayout.addSpacing(2)
        panelLayout.addWidget(self.passwordEdit)
        panelLayout.addWidget(self.errorLabel)
        panelLayout.addWidget(self.unlockButton)
        panelLayout.addWidget(self.switchUserButton)

        centerRow.addWidget(self.panel)
        centerRow.addStretch(1)

        authRoot.addLayout(centerRow)
        authRoot.addStretch(1)

        self.stack.addWidget(self.clockPage)
        self.stack.addWidget(self.authPage)

    def _buildTimer(self):
        self.clockTimer = QTimer(self)
        self.clockTimer.timeout.connect(self._updateDateTime)
        self.clockTimer.start(100)
        self._updateDateTime()

    def _buildStyleSheet(self) -> str:
        return """
        QWidget#LockScreen {
            background: transparent;
        }

        QLabel#BigTimeLabel {
            color: white;
            font-size: 72px;
            font-weight: 700;
        }

        QLabel#BigDateLabel {
            color: rgba(255, 255, 255, 0.90);
            font-size: 24px;
            font-weight: 500;
        }

        QLabel#HintLabel {
            color: rgba(255, 255, 255, 0.72);
            font-size: 14px;
        }

        QLineEdit {
            background: rgba(10, 16, 28, 170);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 10px;
            padding: 0 12px;
            font-size: 14px;
        }

        QLineEdit:focus {
            border: 1px solid rgba(79, 140, 255, 0.95);
        }

        QLabel#LockTitleLabel {
            color: rgba(255, 255, 255, 0.88);
            font-size: 15px;
        }

        QLabel#LockUserLabel {
            color: white;
            font-size: 22px;
            font-weight: 700;
        }

        QLabel#LockErrorLabel {
            color: #ffb0b0;
            font-size: 13px;
            min-height: 18px;
        }

        QPushButton {
            border: none;
            border-radius: 10px;
            background: #4f8cff;
            color: white;
            font-size: 14px;
            font-weight: 600;
        }

        QPushButton:hover {
            background: #6ea3ff;
        }

        QPushButton#SecondaryButton {
            background: rgba(255, 255, 255, 0.06);
        }

        QPushButton#SecondaryButton:hover {
            background: rgba(255, 255, 255, 0.12);
        }
        """

    def _animateToView(self, targetIndex: int, duration: int = 180, offset: int = 18):
        if self._isAnimating:
            return

        currentIndex = self.stack.currentIndex()
        if currentIndex == targetIndex:
            return

        currentWidget = self.stack.currentWidget()
        nextWidget = self.stack.widget(targetIndex)

        if currentWidget is None or nextWidget is None:
            self.stack.setCurrentIndex(targetIndex)
            return

        self._isAnimating = True

        currentWidget.move(0, 0)
        nextWidget.move(0, offset)
        nextWidget.show()
        nextWidget.raise_()

        self.stack.setCurrentIndex(targetIndex)

        slideOut = QPropertyAnimation(currentWidget, b"pos", self)
        slideOut.setDuration(duration)
        slideOut.setStartValue(QPoint(0, 0))
        slideOut.setEndValue(QPoint(0, offset))
        slideOut.setEasingCurve(QEasingCurve.Type.OutCubic)

        slideIn = QPropertyAnimation(nextWidget, b"pos", self)
        slideIn.setDuration(duration)
        slideIn.setStartValue(QPoint(0, offset))
        slideIn.setEndValue(QPoint(0, 0))
        slideIn.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(slideOut)
        group.addAnimation(slideIn)

        def finalize():
            currentWidget.move(0, 0)
            nextWidget.move(0, 0)
            self._isAnimating = False

            if targetIndex == self.VIEW_AUTH:
                self.passwordEdit.setFocus()
                self.passwordEdit.selectAll()
            else:
                self.setFocus()

        group.finished.connect(finalize)
        self._viewAnim = group
        group.start()

    # -------------------------------------------------
    # State / refresh
    # -------------------------------------------------
    def refreshFromSession(self):
        user = None
        if hasattr(self.kernel, "session") and self.kernel.session is not None:
            user = self.kernel.session.getCurrentUser()

        hasPassword = False
        if hasattr(self.kernel, "session") and self.kernel.session is not None:
            try:
                hasPassword = self.kernel.session.currentUserHasPassword()
            except Exception:
                hasPassword = False

        self.passwordEdit.setVisible(hasPassword)
        self.unlockButton.setText("Unlock" if hasPassword else "Continuer")

        self.currentUser = user or "SYSTEM"
        self.userLabel.setText(self.currentUser)
        self.avatar.setText(self.currentUser)
        self.passwordEdit.clear()
        self.errorLabel.clear()
        self._updateDateTime()

    def showClockView(self, animated: bool = False):
        self.stack.setCurrentIndex(self.VIEW_CLOCK)
        self.setFocus()

    def showAuthView(self, animated: bool = False):
        self.stack.setCurrentIndex(self.VIEW_AUTH)
        self.passwordEdit.setFocus()
        self.passwordEdit.selectAll()

    def _updateDateTime(self):
        now = QDateTime.currentDateTime()
        self.bigTimeLabel.setText(now.toString("HH:mm"))
        self.bigDateLabel.setText(now.toString("dddd, dd MMMM"))

    # -------------------------------------------------
    # Actions
    # -------------------------------------------------
    def _handleUnlock(self):
        self.errorLabel.clear()

        if not self.currentUser:
            self.errorLabel.setText("Aucune session active.")
            return

        password = self.passwordEdit.text()

        if not hasattr(self.kernel, "session") or self.kernel.session is None:
            self.errorLabel.setText("Session manager indisponible.")
            return

        try:
            ok = self.kernel.session.verifyPassword(self.currentUser, password)
        except Exception as exc:
            self.errorLabel.setText(str(exc))
            return

        if not ok:
            self.errorLabel.setText("Mot de passe incorrect.")
            self.passwordEdit.selectAll()
            self.passwordEdit.setFocus()
            return

        self.unlockRequested.emit()

    def _handleSwitchUser(self):
        self.switchUserRequested.emit()

    # -------------------------------------------------
    # Interaction
    # -------------------------------------------------
    def mousePressEvent(self, event):
        if self.stack.currentIndex() == self.VIEW_CLOCK:
            self.showAuthView(animated=True)
            event.accept()
            return

        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if self.stack.currentIndex() == self.VIEW_CLOCK:
            if event.key() in (
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
                Qt.Key.Key_Space,
                Qt.Key.Key_Tab,
                Qt.Key.Key_Escape,
            ) or event.text():
                self.showAuthView(animated=True)
                event.accept()
                return

        elif self.stack.currentIndex() == self.VIEW_AUTH:
            if event.key() == Qt.Key.Key_Escape:
                self.showClockView(animated=True)
                event.accept()
                return

        super().keyPressEvent(event)

    # -------------------------------------------------
    # Paint
    # -------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(8, 16, 30))
        gradient.setColorAt(0.45, QColor(24, 34, 58))
        gradient.setColorAt(0.75, QColor(18, 28, 44))
        gradient.setColorAt(1.0, QColor(8, 14, 22))
        painter.fillRect(self.rect(), gradient)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 90))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(90, 150, 255, 18))
        painter.drawEllipse(int(self.width() * 0.58), int(self.height() * 0.16), 320, 220)

        painter.setBrush(QColor(255, 170, 120, 12))
        painter.drawEllipse(int(self.width() * 0.10), int(self.height() * 0.72), 260, 180)
