from __future__ import annotations

from typing import Dict, List

from PySide6.QtCore import (
    Qt, QRect, Signal, QPropertyAnimation, QParallelAnimationGroup,
    QEasingCurve
)
from PySide6.QtGui import (
    QAction, QColor, QIcon, QPainter, QPixmap
)
from PySide6.QtWidgets import (
    QFrame, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QScrollArea, QGraphicsOpacityEffect, QMenu, QSizePolicy,
    QGridLayout
)

from core.theme.fonts import ElidableLabel


class NexHubCardButton(QPushButton):
    launched = Signal(str)

    def __init__(self, appId: str, title: str, subtitle: str = "", icon=None, parent=None):
        super().__init__(parent)

        self.appId = appId
        self.title = title
        self.subtitle = subtitle or ""
        self._iconSource = icon

        self.setObjectName("NexHubCardButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCheckable(False)
        self.setMinimumSize(80, 80)
        self.setMaximumHeight(88)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        self.iconLabel = QLabel()
        self.iconLabel.setObjectName("NexHubCardIcon")
        self.iconLabel.setFixedSize(40, 40)
        self.iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.titleLabel = ElidableLabel(title)
        self.titleLabel.setObjectName("NexHubCardTitle")
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        """ self.subtitleLabel = QLabel(self.subtitle)
        self.subtitleLabel.setObjectName("NexHubCardSubtitle")
        self.subtitleLabel.setWordWrap(True)
        self.subtitleLabel.setVisible(bool(self.subtitle)) """

        root.addWidget(self.iconLabel, 0, Qt.AlignmentFlag.AlignCenter)
        root.addStretch(1)
        root.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignCenter)
        # root.addWidget(self.subtitleLabel)

        self._setIcon(self._iconSource)
        self.clicked.connect(self._emitLaunch)

    def _emitLaunch(self):
        self.launched.emit(self.appId)

    def matchesQuery(self, query: str) -> bool:
        query = query.strip().lower()
        if not query:
            return True

        haystack = f"{self.appId} {self.title} {self.subtitle}".lower()
        return query in haystack

    def _resolveIconPixmap(self, icon):
        if icon is None:
            return None

        if isinstance(icon, QPixmap):
            return icon

        if isinstance(icon, QIcon):
            return icon.pixmap(42, 42)

        if isinstance(icon, str):
            pm = QPixmap(icon)
            if not pm.isNull():
                return pm

        return None

    def _buildFallbackIcon(self) -> QPixmap:
        size = 42
        canvas = QPixmap(size, size)
        canvas.fill(Qt.GlobalColor.transparent)

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(92, 132, 255, 210))
        painter.drawRoundedRect(0, 0, size, size, 12, 12)

        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(14)
        painter.setFont(font)
        painter.drawText(canvas.rect(), Qt.AlignmentFlag.AlignCenter, (self.title[:1] or "?").upper())
        painter.end()

        return canvas

    def _setIcon(self, icon):
        pixmap = self._resolveIconPixmap(icon)
        if pixmap is None or pixmap.isNull():
            pixmap = self._buildFallbackIcon()

        self.iconLabel.setPixmap(
            pixmap.scaled(
                self.iconLabel.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )


class NexHubAvatar(QLabel):
    def __init__(self, size: int = 64, parent=None):
        super().__init__(parent)

        self._size = size
        self._pixmap = None
        self._fallbackText = "S"

        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("NexHubAvatar")

        self._updateDisplay()

    def setFallbackText(self, text: str):
        self._fallbackText = (text or "?")[:1].upper()
        self._updateDisplay()

    def setAvatarPixmap(self, pixmap: QPixmap | None):
        self._pixmap = pixmap
        self._updateDisplay()

    def _updateDisplay(self):
        if self._pixmap is not None and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled)
            return

        canvas = QPixmap(self._size, self._size)
        canvas.fill(Qt.GlobalColor.transparent)

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(90, 130, 255, 210))
        painter.drawEllipse(0, 0, self._size, self._size)

        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(max(16, self._size // 3))
        painter.setFont(font)
        painter.drawText(canvas.rect(), Qt.AlignmentFlag.AlignCenter, self._fallbackText)

        painter.end()
        self.setPixmap(canvas)


class NexHubPanel(QFrame):
    requestClose = Signal()
    appLaunchRequested = Signal(str)

    sleepRequested = Signal()
    shutdownRequested = Signal()
    restartRequested = Signal()

    lockRequested = Signal()
    logoutRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._animGroup = None
        self._animDuration = 160

        self._appItems: List[NexHubCardButton] = []
        self._visibleItems: List[NexHubCardButton] = []
        self._userName: str = "SYSTEM"
        self._userType: str = "Système"

        self.setObjectName("NexHubPanel")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.hide()

        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)

        self._buildUi()
        self._buildMenus()
        self._applyStyleSheet()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def _buildUi(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        # Header / profil
        self.profileSection = QFrame()
        self.profileSection.setObjectName("NexHubProfileSection")

        profileLayout = QHBoxLayout(self.profileSection)
        profileLayout.setContentsMargins(16, 14, 16, 14)
        profileLayout.setSpacing(12)

        self.avatarWidget = NexHubAvatar(64, self.profileSection)

        self.userInfoHost = QWidget()
        userInfoLayout = QVBoxLayout(self.userInfoHost)
        userInfoLayout.setContentsMargins(0, 0, 0, 0)
        userInfoLayout.setSpacing(2)

        self.userNameLabel = QLabel(self._userName)
        self.userNameLabel.setObjectName("NexHubUserNameLabel")

        self.userStatusRow = QHBoxLayout()
        self.userStatusRow.setContentsMargins(0, 0, 0, 0)
        self.userStatusRow.setSpacing(6)

        self.statusDot = QLabel("●")
        self.statusDot.setObjectName("NexHubStatusDot")

        self.userStatusLabel = QLabel(self._userType)
        self.userStatusLabel.setObjectName("NexHubUserStatusLabel")

        self.userStatusRow.addWidget(self.statusDot)
        self.userStatusRow.addWidget(self.userStatusLabel)
        self.userStatusRow.addStretch(1)

        userInfoLayout.addWidget(self.userNameLabel)
        userInfoLayout.addLayout(self.userStatusRow)

        self.profileMenuButton = QPushButton("⋯")
        self.profileMenuButton.setObjectName("NexHubProfileMenuButton")
        self.profileMenuButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.profileMenuButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.profileMenuButton.setFixedSize(38, 38)

        profileLayout.addWidget(self.avatarWidget, 0, Qt.AlignmentFlag.AlignTop)
        profileLayout.addWidget(self.userInfoHost, 1)
        profileLayout.addWidget(self.profileMenuButton, 0, Qt.AlignmentFlag.AlignVCenter)

        # Recherche
        self.searchEdit = QLineEdit()
        self.searchEdit.setObjectName("NexHubSearchEdit")
        self.searchEdit.setPlaceholderText("Rechercher...")
        self.searchEdit.textChanged.connect(self._applyFilter)

        # Section label
        self.sectionLabel = QLabel("Applications")
        self.sectionLabel.setObjectName("NexHubSectionLabel")

        # Zone apps scrollable
        self.scrollArea = QScrollArea()
        self.scrollArea.setObjectName("NexHubScrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollArea.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.listHost = QWidget()
        self.listHost.setObjectName("NexHubListHost")
        self.listHost.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.gridLayout = QGridLayout(self.listHost)
        self.gridLayout.setContentsMargins(6, 4, 6, 4)
        self.gridLayout.setHorizontalSpacing(8)
        self.gridLayout.setVerticalSpacing(8)

        self.scrollArea.setWidget(self.listHost)

        # Footer
        self.footerHost = QWidget()
        footerLayout = QVBoxLayout(self.footerHost)
        footerLayout.setContentsMargins(0, 4, 0, 0)
        footerLayout.setSpacing(0)

        self.powerButton = QPushButton("⏻")
        self.powerButton.setObjectName("NexHubPowerButton")
        self.powerButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.powerButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.powerButton.setFixedSize(48, 48)

        footerLayout.addWidget(self.powerButton, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignRight)

        root.addWidget(self.profileSection)
        root.addWidget(self.searchEdit)
        root.addWidget(self.sectionLabel)
        root.addWidget(self.scrollArea, 1)
        root.addWidget(self.footerHost)

    def _buildMenus(self):
        # Menu session
        self.profileMenu = QMenu(self)
        self.profileMenu.setObjectName("NexHubMenu")

        lockAction = QAction("Verrouiller", self)
        logoutAction = QAction("Se déconnecter", self)

        lockAction.triggered.connect(self.lockRequested.emit)
        logoutAction.triggered.connect(self.logoutRequested.emit)

        self.profileMenu.addAction(lockAction)
        self.profileMenu.addSeparator()
        self.profileMenu.addAction(logoutAction)

        self.profileMenuButton.clicked.connect(self._showProfileMenu)

        # Menu power
        self.powerMenu = QMenu(self)
        self.powerMenu.setObjectName("NexHubMenu")

        sleepAction = QAction("Veille", self)
        restartAction = QAction("Redémarrer", self)
        shutdownAction = QAction("Arrêter", self)

        sleepAction.triggered.connect(self.sleepRequested.emit)
        restartAction.triggered.connect(self.restartRequested.emit)
        shutdownAction.triggered.connect(self.shutdownRequested.emit)

        self.powerMenu.addAction(sleepAction)
        self.powerMenu.addSeparator()
        self.powerMenu.addAction(restartAction)
        self.powerMenu.addAction(shutdownAction)

        self.powerButton.clicked.connect(self._showPowerMenu)

    def _applyStyleSheet(self):
        self.setStyleSheet("""
        #NexHubPanel {
            background: rgba(18, 26, 42, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
        }

        #NexHubProfileSection {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
        }

        #NexHubUserNameLabel {
            color: white;
            font-size: 24px;
            font-weight: 700;
        }

        #NexHubStatusDot {
            color: #4fd26d;
            font-size: 14px;
        }

        #NexHubUserStatusLabel {
            color: rgba(255, 255, 255, 0.76);
            font-size: 15px;
        }

        #NexHubProfileMenuButton {
            background: rgba(255, 255, 255, 0.08);
            color: white;
            border: none;
            border-radius: 19px;
            font-size: 20px;
            font-weight: 700;
        }

        #NexHubProfileMenuButton:hover {
            background: rgba(255, 255, 255, 0.14);
        }

        #NexHubSearchEdit {
            min-height: 44px;
            padding: 0 14px;
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background: rgba(255, 255, 255, 0.05);
            color: white;
            font-size: 15px;
        }

        #NexHubSearchEdit:focus {
            border: 1px solid rgba(95, 141, 255, 0.95);
        }

        #NexHubSectionLabel {
            color: rgba(255, 255, 255, 0.86);
            font-size: 14px;
            font-weight: 700;
            padding-left: 4px;
        }
        
        #NexHubListHost {
            background: transparent;
            border: none;
        }

        #NexHubCardButton {
            text-align: left;
            background: rgba(255, 255, 255, 0.04);
            border: none;
            border-radius: 8px;
            color: white;
        }

        #NexHubCardButton:hover {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.11);
        }

        #NexHubCardTitle {
            color: white;
        }

        #NexHubCardSubtitle {
            color: rgba(255, 255, 255, 0.62);
            font-size: 12px;
        }

        #NexHubPowerButton {
            background: rgba(255, 255, 255, 0.06);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 24px;
            font-size: 20px;
            font-weight: 700;
        }

        #NexHubPowerButton:hover {
            background: rgba(255, 255, 255, 0.10);
        }

        QMenu#NexHubMenu {
            background: rgba(28, 35, 52, 236);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 8px;
        }

        QMenu#NexHubMenu::item {
            padding: 10px 18px;
            border-radius: 8px;
        }

        QMenu#NexHubMenu::item:selected {
            background: rgba(95, 141, 255, 0.28);
        }

        QScrollArea#NexHubScrollArea {
            background: transparent;
        }
        """)

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------
    def setApps(self, apps: List[Dict[str, str]]):
        self._clearApps()

        for appData in apps:
            appId = appData["id"]
            title = appData["title"]
            subtitle = appData.get("subtitle", "")
            icon = appData.get("icon")

            item = NexHubCardButton(appId, title, subtitle, icon=icon)
            item.launched.connect(self._onAppLaunchRequested)

            self._appItems.append(item)

        self._rebuildGrid()
        self._applyFilter()
        self.searchEdit.clear()

    def setUserProfile(self, userName: str, userStatus: str = "Utilisateur local", avatarPixmap: QPixmap | None = None):
        self._userName = userName
        self._userType = userStatus

        self.userNameLabel.setText(userName)
        self.userStatusLabel.setText(userStatus)

        firstChar = userName[:1].upper() if userName else "?"
        self.avatarWidget.setFallbackText(firstChar)
        self.avatarWidget.setAvatarPixmap(avatarPixmap)

    def toggle(self):
        if self.isVisible():
            self.animateHide()
        else:
            self.animateShow()

    # -------------------------------------------------
    # Menus
    # -------------------------------------------------
    def _showProfileMenu(self):
        globalPos = self.profileMenuButton.mapToGlobal(self.profileMenuButton.rect().bottomRight())
        self.profileMenu.exec(globalPos)

    def _showPowerMenu(self):
        globalPos = self.powerButton.mapToGlobal(self.powerButton.rect().topLeft())
        globalPos.setX(globalPos.x() - 110)
        globalPos.setY(globalPos.y() - 8)
        self.powerMenu.exec(globalPos)

    # -------------------------------------------------
    # Animations
    # -------------------------------------------------
    def animateShow(self):
        self._stopAnimations()

        finalGeom = self.geometry()
        startGeom = QRect(finalGeom.x(), finalGeom.y() + 10, finalGeom.width(), finalGeom.height())

        self.setGeometry(startGeom)
        self._opacity.setOpacity(0.0)
        self.show()
        self.raise_()

        geoAnim = QPropertyAnimation(self, b"geometry")
        geoAnim.setDuration(self._animDuration)
        geoAnim.setStartValue(startGeom)
        geoAnim.setEndValue(finalGeom)
        geoAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        opacityAnim = QPropertyAnimation(self._opacity, b"opacity")
        opacityAnim.setDuration(self._animDuration)
        opacityAnim.setStartValue(0.0)
        opacityAnim.setEndValue(1.0)
        opacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(geoAnim)
        group.addAnimation(opacityAnim)

        def finalize():
            self.searchEdit.setFocus()

        group.finished.connect(finalize)

        self._animGroup = group
        group.start()

    def animateHide(self):
        if not self.isVisible():
            return

        self._stopAnimations()

        startGeom = self.geometry()
        endGeom = QRect(startGeom.x(), startGeom.y() + 10, startGeom.width(), startGeom.height())

        geoAnim = QPropertyAnimation(self, b"geometry")
        geoAnim.setDuration(self._animDuration)
        geoAnim.setStartValue(startGeom)
        geoAnim.setEndValue(endGeom)
        geoAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        opacityAnim = QPropertyAnimation(self._opacity, b"opacity")
        opacityAnim.setDuration(self._animDuration)
        opacityAnim.setStartValue(self._opacity.opacity())
        opacityAnim.setEndValue(0.0)
        opacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(geoAnim)
        group.addAnimation(opacityAnim)

        def finalize():
            self.hide()

        group.finished.connect(finalize)

        self._animGroup = group
        group.start()

    # -------------------------------------------------
    # Internal
    # -------------------------------------------------
    def _stopAnimations(self):
        if self._animGroup is not None:
            try:
                self._animGroup.stop()
            except Exception:
                pass
            self._animGroup = None

    def _clearApps(self):
        while self.gridLayout.count():
            item = self.gridLayout.takeAt(0)
            widget = item.widget()  # type: ignore
            if widget is not None:
                self.gridLayout.removeWidget(widget)
                widget.hide()
                widget.deleteLater()

        self._appItems = []
        self._visibleItems = []

    def _rebuildGrid(self):
        while self.gridLayout.count():
            item = self.gridLayout.takeAt(0)
            widget = item.widget()  # type: ignore
            if widget is not None:
                self.gridLayout.removeWidget(widget)

        visible = self._visibleItems if self._visibleItems else self._appItems

        columns = 5
        for index, widget in enumerate(visible):
            row = index // columns
            col = index % columns
            self.gridLayout.addWidget(widget, row, col)

        for col in range(columns):
            self.gridLayout.setColumnStretch(col, 1)

    def _applyFilter(self):
        query = self.searchEdit.text().strip()
        self._visibleItems = [item for item in self._appItems if item.matchesQuery(query)]

        for item in self._appItems:
            item.setVisible(item in self._visibleItems)

        self._rebuildGrid()

    def _onAppLaunchRequested(self, appId: str):
        self.appLaunchRequested.emit(appId)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.requestClose.emit()
            event.accept()
            return

        super().keyPressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)

        # glow subtil dans le panneau
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(QColor(79, 140, 255, 18))
        painter.drawEllipse(int(self.width() * 0.50), int(self.height() * 0.55), 220, 150)

        painter.setBrush(QColor(255, 180, 120, 12))
        painter.drawEllipse(int(self.width() * 0.10), int(self.height() * 0.70), 160, 120)

        painter.end()
