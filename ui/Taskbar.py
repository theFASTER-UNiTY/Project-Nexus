from __future__ import annotations

from typing import Dict

from PySide6.QtCore import (
    Qt, QTimer, QTime, QDate, QEvent, Signal, QEasingCurve,
    QPropertyAnimation, QParallelAnimationGroup, QPoint, QSize
)
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy,
    QMenu, QFrame, QVBoxLayout, QApplication, QGraphicsOpacityEffect
)

from core.theme.theme import theme
from ui.NexHub import NexHubPanel
from ui.ClockPanel import ClockPanel


class TaskbarWindowButton(QPushButton):
    def __init__(self, windowId: str, title: str, taskbar: "Taskbar", icon=None):
        super().__init__(title)
        self.setProperty("taskbarWindowButton", True)

        self.windowId = windowId
        self.taskbar = taskbar
        self._iconSource = icon

        self._isActive = False
        self._isMinimized = False
        self._isOpen = True

        self._opacityEffect = QGraphicsOpacityEffect(self)
        self._opacityEffect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacityEffect)

        self._animGroup = None

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMinimumWidth(120)
        self.setMaximumWidth(170)
        self.setFixedHeight(34)

        self.setIconSize(QSize(16, 16))
        self._applyIcon(icon)

        self.clicked.connect(self._onClicked)
        self._applyStyle()

    def _onClicked(self):
        self.taskbar.toggleWindow(self.windowId)

    def setState(self, *, active: bool | None = None, minimized: bool | None = None, open_: bool | None = None):
        if active is not None:
            self._isActive = active
        if minimized is not None:
            self._isMinimized = minimized
        if open_ is not None:
            self._isOpen = open_
        self._applyStyle()

    def setFrameTitle(self, title: str):
        self.setText(title)

    def setFrameIcon(self, icon):
        self._iconSource = icon
        self._applyIcon(icon)

    def _applyIcon(self, icon):
        qicon = self._resolveIcon(icon)
        if qicon is None or qicon.isNull():
            self.setIcon(QIcon())
            return
        self.setIcon(qicon)

    def _resolveIcon(self, icon):
        if icon is None:
            return None

        if isinstance(icon, QIcon):
            return icon

        if isinstance(icon, QPixmap):
            return QIcon(icon)

        if isinstance(icon, str):
            pm = QPixmap(icon)
            if not pm.isNull():
                return QIcon(pm)

        return None

    def _applyStyle(self):
        self.setProperty("active", self._isActive)
        self.setProperty("minimized", self._isMinimized)
        self.style().unpolish(self)
        self.style().polish(self)

    def _stopAnimations(self):
        if self._animGroup is not None:
            try:
                self._animGroup.stop()
            except Exception:
                pass
            self._animGroup = None

    def animateShow(self):
        self._stopAnimations()

        self._opacityEffect.setOpacity(0.0)
        self.show()

        opacityAnim = QPropertyAnimation(self._opacityEffect, b"opacity")
        opacityAnim.setDuration(130)
        opacityAnim.setStartValue(0.0)
        opacityAnim.setEndValue(1.0)
        opacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._animGroup = QParallelAnimationGroup(self)
        self._animGroup.addAnimation(opacityAnim)
        self._animGroup.start()

    def animateHide(self, onFinished=None):
        self._stopAnimations()

        opacityAnim = QPropertyAnimation(self._opacityEffect, b"opacity")
        opacityAnim.setDuration(110)
        opacityAnim.setStartValue(self._opacityEffect.opacity())
        opacityAnim.setEndValue(0.0)
        opacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(opacityAnim)

        if onFinished is not None:
            group.finished.connect(onFinished)

        self._animGroup = group
        group.start()

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        actRestore = QAction("Restaurer", self)
        actMinimize = QAction("Minimiser", self)
        actClose = QAction("Fermer", self)

        actRestore.triggered.connect(lambda: self.taskbar.compositor.restoreWindow(self.windowId))
        actMinimize.triggered.connect(lambda: self.taskbar.compositor.minimizeWindow(self.windowId))
        actClose.triggered.connect(lambda: self.taskbar.compositor.closeWindow(self.windowId))

        actRestore.setVisible(self._isMinimized)
        actMinimize.setVisible(not self._isMinimized and self._isOpen)

        menu.addAction(actRestore)
        menu.addAction(actMinimize)
        menu.addSeparator()
        menu.addAction(actClose)

        menu.exec(event.globalPos())


class TaskbarSection(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)


class TaskbarClockWidget(QFrame):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._showSeconds = False
        self._dateFormat = "dd/MM/yyyy"

        self.setObjectName("TaskbarClockWidget")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 2, 8, 2)
        root.setSpacing(0)

        self.timeLabel = QLabel()
        self.timeLabel.setObjectName("TaskbarTimeLabel")
        self.timeLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.dateLabel = QLabel()
        self.dateLabel.setObjectName("TaskbarDateLabel")
        self.dateLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        root.addWidget(self.timeLabel)
        root.addWidget(self.dateLabel)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.updateDisplay)
        self._timer.start(100)

        self.updateDisplay()

    def updateDisplay(self):
        timeFmt = "HH:mm:ss" if self._showSeconds else "HH:mm"
        self.timeLabel.setText(QTime.currentTime().toString(timeFmt))
        self.dateLabel.setText(QDate.currentDate().toString(self._dateFormat))

    def setShowSeconds(self, enabled: bool):
        self._showSeconds = enabled
        self.updateDisplay()

    def setDateFormat(self, fmt: str):
        self._dateFormat = fmt
        self.updateDisplay()

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        showSecondsAction = QAction("Afficher les secondes", self)
        showSecondsAction.setCheckable(True)
        showSecondsAction.setChecked(self._showSeconds)
        showSecondsAction.triggered.connect(self.setShowSeconds)

        dateMenu = menu.addMenu("Format de date")

        dateFormats = [
            ("dd/MM/yyyy", "31/12/2026"),
            ("ddd dd/MM/yyyy", "jeu. 31/12/2026"),
            ("dd MMM yyyy", "31 déc. 2026"),
            ("dddd d MMMM yyyy", "jeudi 31 décembre 2026"),
            ("yyyy-MM-dd", "2026-12-31"),
        ]

        for fmt, label in dateFormats:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(self._dateFormat == fmt)
            action.triggered.connect(lambda checked=False, f=fmt: self.setDateFormat(f))
            dateMenu.addAction(action)

        menu.addAction(showSecondsAction)
        menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class Taskbar(QWidget):
    def __init__(self, kernel, compositor):
        super().__init__()

        self.kernel = kernel
        self.compositor = compositor

        self.taskbarAlignment = "left"   # "left" | "center" | "semiCenter"
        self._buttons = {}
        self._nexHubOpen = False
        self._nexHubFilterInstalled = False
        self._hostWindowForLayout = None
        self._taskbarAlignAnim = None
        self._animDuration = 250
        self._layoutShiftAnims = {}

        self.setFixedHeight(theme.metrics.taskbarHeight)
        self.setObjectName("Taskbar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(False)

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 6)
        root.setSpacing(10)

        # -------------------------
        # Zone centrale
        # -------------------------
        self.centerSection = QWidget()
        self.centerSection.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.centerLayout = QHBoxLayout(self.centerSection)
        self.centerLayout.setContentsMargins(0, 0, 0, 0)
        self.centerLayout.setSpacing(8)

        self.centerBandHost = QWidget()
        self.centerBandLayout = QHBoxLayout(self.centerBandHost)
        self.centerBandLayout.setContentsMargins(0, 0, 0, 0)
        self.centerBandLayout.setSpacing(8)
        self.centerBandHost.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._centerBandAnim = None

        self.startButton = QPushButton("NexHub")
        self.startButton.setObjectName("TaskbarStartButton")
        self.startButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.startButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.startButton.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.startButton.setFixedHeight(34)
        self.startButton.style().unpolish(self.startButton)
        self.startButton.style().polish(self.startButton)
        self.startButton.clicked.connect(self._toggleNexHub)

        self.startButtonHost = QWidget()
        self.startButtonHost.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.startButtonHostLayout = QHBoxLayout(self.startButtonHost)
        self.startButtonHostLayout.setContentsMargins(0, 0, 0, 0)
        self.startButtonHostLayout.setSpacing(0)
        self.startButtonHostLayout.addWidget(self.startButton)

        self.windowsHost = QWidget()
        self.windowsHost.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        self.windowsLayout = QHBoxLayout(self.windowsHost)
        self.windowsLayout.setContentsMargins(0, 0, 0, 0)
        self.windowsLayout.setSpacing(12)

        self.windowsCenterHost = QWidget()
        self.windowsCenterHost.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.windowsCenterLayout = QHBoxLayout(self.windowsCenterHost)
        self.windowsCenterLayout.setContentsMargins(0, 0, 0, 0)
        self.windowsCenterLayout.setSpacing(8)

        self.overflowButton = QPushButton("…")
        self.overflowButton.setObjectName("TaskbarOverflowButton")
        self.overflowButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.overflowButton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.overflowButton.setFixedHeight(34)
        self.overflowButton.setMinimumWidth(38)
        self.overflowButton.hide()

        self.overflowMenu = QMenu(self)
        self.overflowButton.clicked.connect(self._showOverflowMenu)

        # -------------------------
        # Zone droite
        # -------------------------
        self.rightSection = QWidget()
        self.rightSection.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        self.rightLayout = QHBoxLayout(self.rightSection)
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.rightLayout.setSpacing(8)

        self.statusLabel = QLabel("●")
        self.statusLabel.setObjectName("TaskbarStatusLabel")
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.statusLabel.setFixedWidth(22)

        self.clockWidget = TaskbarClockWidget()
        self.clockWidget.setMinimumWidth(110)
        self.clockWidget.clicked.connect(self._toggleClockPanel)

        self.rightLayout.addWidget(self.statusLabel)
        self.rightLayout.addWidget(self.clockWidget)

        # -------------------------
        # Root layout
        # -------------------------
        root.addWidget(self.centerSection, 1)
        root.addWidget(self.rightSection, 0)

        # -------------------------
        # Panels
        # -------------------------
        self.nexHub = NexHubPanel(self)
        self.nexHub.requestClose.connect(self._closeNexHub)
        self.nexHub.appLaunchRequested.connect(self._launchAppFromNexHub)

        self.nexHub.sleepRequested.connect(self._handleSleepRequest)
        self.nexHub.restartRequested.connect(self._handleRestartRequest)
        self.nexHub.shutdownRequested.connect(self._handleShutdownRequest)

        self.nexHub.lockRequested.connect(self._handleLockRequest)
        self.nexHub.logoutRequested.connect(self._handleLogoutRequest)

        # self.nexHub.setApps([
        #     {"id": "welcome", "title": "Welcome", "subtitle": "Ecran de bienvenue"},
        #     {"id": "files", "title": "Files", "subtitle": "Gestionnaire de fichiers"},
        # ])

        currentUser = None
        if hasattr(self.kernel, "session") and self.kernel.session is not None:
            currentUser = self.kernel.session.getCurrentUser()

        self.nexHub.setUserProfile(
            userName=currentUser or "SYSTEM",
            userStatus="Session active" if currentUser else "Système",
            avatarPixmap=None
        )

        self.clockPanel = ClockPanel(self)

        # -------------------------
        # Events bus
        # -------------------------
        self.kernel.bus.subscribe("window.created", self._onWindowCreated)
        self.kernel.bus.subscribe("window.updated", self._onWindowUpdated)
        self.kernel.bus.subscribe("window.closed", self._onWindowClosed)
        self.kernel.bus.subscribe("window.minimized", self._onWindowMinimized)
        self.kernel.bus.subscribe("window.restored", self._onWindowRestored)
        self.kernel.bus.subscribe("window.focused", self._onWindowFocused)
        self.kernel.bus.subscribe("window.focus.cleared", self._onFocusCleared)
        self.kernel.bus.subscribe("app.registered", self._onAppRegistered)

        # -------------------------
        # Filters
        # -------------------------
        QTimer.singleShot(0, self._installNexHubEventFilter)
        QTimer.singleShot(0, self._attachHostWindowFilter)

        # -------------------------
        # Layout initial
        # -------------------------
        self.startButton.setProperty("opened", self.nexHub.isVisible())
        self._rebuildCenterBandContents([])
        self._applyTaskbarAlignment()

    def _onStartClicked(self):
        # Placeholder V1
        self.compositor.clearFocus()

    def _clearLayout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            childLayout = item.layout()

            if childLayout is not None:
                self._clearLayout(childLayout)
            elif widget is not None:
                layout.removeWidget(widget)

    def _captureVisibleButtonPositions(self) -> dict[str, QPoint]:
        positions = {}

        for wid, btn in self._buttons.items():
            if btn.isVisible():
                positions[wid] = btn.mapTo(self, QPoint(0, 0))

        return positions

    def _animateButtonsToNewLayout(self, oldPositions: dict[str, QPoint], duration: int | None = None):
        if duration is None:
            duration = self._animDuration

        # stop anciennes anims
        for wid, anim in list(self._layoutShiftAnims.items()):
            try:
                anim.stop()
            except Exception:
                pass
            self._layoutShiftAnims.pop(wid, None)

        for wid, btn in self._buttons.items():
            if not btn.isVisible():
                continue

            if wid not in oldPositions:
                continue

            oldPos = oldPositions[wid]
            newPos = btn.mapTo(self, QPoint(0, 0))

            if oldPos == newPos:
                continue

            # on remet visuellement le bouton à son ancienne place
            btn.move(btn.pos() + (oldPos - newPos))

            anim = QPropertyAnimation(btn, b"pos", self)
            anim.setDuration(duration)
            anim.setStartValue(btn.pos())
            anim.setEndValue(btn.pos() + (newPos - oldPos))
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            self._layoutShiftAnims[wid] = anim

            def cleanup(wid=wid):
                self._layoutShiftAnims.pop(wid, None)

            anim.finished.connect(cleanup)
            anim.start()

    def _applyTaskbarAlignment(self, animated: bool = False):
        oldPos = self.centerBandHost.pos()

        self._clearLayout(self.centerLayout)

        if self.taskbarAlignment == "left":
            self.centerLayout.addWidget(self.centerBandHost, 0)
            self.centerLayout.addStretch(1)

        elif self.taskbarAlignment == "center":
            self.centerLayout.addStretch(1)
            self.centerLayout.addWidget(self.centerBandHost, 0)
            self.centerLayout.addStretch(1)

        elif self.taskbarAlignment == "semiCenter":
            # NH à gauche, fenêtres centrées, overflow à la suite
            # on gère ça dans le contenu lui-même avec un spacer interne
            self.centerLayout.addWidget(self.centerBandHost, 1)

        self.centerSection.layout().activate() # type: ignore
        self.layout().activate() # type: ignore

        newPos = self.centerBandHost.pos()

        if animated:
            self._animateCenterBand(oldPos, newPos, self._animDuration)

        if self.nexHub.isVisible():
            self._positionNexHub()

        if self.clockPanel.isVisible():
            self._positionClockPanel()

    def _setTaskbarAlignment(self, mode: str):
        if mode not in ("left", "center", "semiCenter"):
            return

        if self.taskbarAlignment == mode:
            return

        self.taskbarAlignment = mode
        self._applyTaskbarAlignment(animated=True)

    def _attachHostWindowFilter(self):
        hostWindow = self.window()
        if hostWindow is None:
            return

        if self._hostWindowForLayout is hostWindow:
            return

        self._hostWindowForLayout = hostWindow
        hostWindow.installEventFilter(self)

    def _rebuildCenterBand(self):
        self._clearLayout(self.centerLayout)

        if self.taskbarAlignment == "left":
            self.centerLayout.addWidget(self.startButtonHost, 0)
            self.centerLayout.addWidget(self.windowsHost, 0)
            self.centerLayout.addWidget(self.overflowButton, 0)
            self.centerLayout.addStretch(1)

        elif self.taskbarAlignment == "center":
            self.centerLayout.addStretch(1)
            self.centerLayout.addWidget(self.startButtonHost, 0)
            self.centerLayout.addWidget(self.windowsHost, 0)
            self.centerLayout.addWidget(self.overflowButton, 0)
            self.centerLayout.addStretch(1)

        elif self.taskbarAlignment == "semiCenter":
            self.centerLayout.addWidget(self.startButtonHost, 0)
            self.centerLayout.addStretch(1)
            self.centerLayout.addWidget(self.windowsHost, 0)
            self.centerLayout.addWidget(self.overflowButton, 0)
            self.centerLayout.addStretch(1)

    def _rebuildCenterBandContents(self, visibleWindowIds: list[str]):
        self._clearLayout(self.centerBandLayout)

        if self.taskbarAlignment == "left":
            self.centerBandLayout.addWidget(self.startButtonHost, 0)

            for windowId in visibleWindowIds:
                btn = self._buttons.get(windowId)
                if btn is not None:
                    self.centerBandLayout.addWidget(btn, 0)

            self.centerBandLayout.addWidget(self.overflowButton, 0)
            self.centerBandLayout.addStretch(1)

        elif self.taskbarAlignment == "center":
            self.centerBandLayout.addWidget(self.startButtonHost, 0)

            for windowId in visibleWindowIds:
                btn = self._buttons.get(windowId)
                if btn is not None:
                    self.centerBandLayout.addWidget(btn, 0)

            self.centerBandLayout.addWidget(self.overflowButton, 0)

        elif self.taskbarAlignment == "semiCenter":
            self.centerBandLayout.addWidget(self.startButtonHost, 0)
            self._rebuildWindowsCenterBand(visibleWindowIds)
            self.centerBandLayout.addWidget(self.windowsCenterHost, 1)

    def _rebuildWindowsCenterBand(self, visibleWindowIds: list[str]):
        self._clearLayout(self.windowsCenterLayout)

        self.windowsCenterLayout.addStretch(1)

        for windowId in visibleWindowIds:
            btn = self._buttons.get(windowId)
            if btn is not None:
                self.windowsCenterLayout.addWidget(btn, 0)

        self.windowsCenterLayout.addWidget(self.overflowButton, 0)
        self.windowsCenterLayout.addStretch(1)

    def _orderedWindowIds(self) -> list[str]:
        return list(self._buttons.keys())
    
    def _measureButtonWidth(self, btn: QPushButton) -> int:
        hint = btn.sizeHint().width()
        return max(btn.minimumWidth(), hint)
    
    def _availableCenterWidth(self) -> int:
        width = self.centerSection.width()
        margins = self.centerLayout.contentsMargins()
        width -= (margins.left() + margins.right())

        spacing = self.centerLayout.spacing()

        if self.taskbarAlignment == "left":
            width -= self.startButtonHost.sizeHint().width()
            width -= spacing

        elif self.taskbarAlignment == "center":
            width -= self.startButtonHost.sizeHint().width()
            width -= spacing

        elif self.taskbarAlignment == "semiCenter":
            width -= self.startButtonHost.sizeHint().width()
            width -= spacing

        return max(0, width)
    
    def _updateOverflow(self, animated: bool = False):
        oldPos = self.centerBandHost.pos()

        orderedIds = self._orderedWindowIds()

        if not orderedIds:
            self._overflowWindowIds = []
            self.overflowButton.hide()
            self._rebuildCenterBandContents([])
            self._refreshStates()
            return

        availableWidth = self._availableCenterWidth()
        spacing = self.centerBandLayout.spacing()
        safetyMargin = 8

        visibleIds = []
        overflowIds = []

        totalWidth = self._measureButtonWidth(self.startButton)
        if self.taskbarAlignment == "semiCenter":
            totalWidth += 24  # petite réserve pour le stretch interne

        overflowButtonWidth = self._measureButtonWidth(self.overflowButton)

        for index, windowId in enumerate(orderedIds):
            btn = self._buttons[windowId]
            btnWidth = self._measureButtonWidth(btn)

            extraSpacing = spacing
            projected = totalWidth + extraSpacing + btnWidth

            if projected <= availableWidth - safetyMargin:
                visibleIds.append(windowId)
                totalWidth = projected
            else:
                overflowIds = orderedIds[index:]
                break

        if overflowIds:
            visibleIds = []
            totalWidth = self._measureButtonWidth(self.startButton)
            if self.taskbarAlignment == "semiCenter":
                totalWidth += 24

            reservedWidth = overflowButtonWidth + spacing

            for index, windowId in enumerate(orderedIds):
                btn = self._buttons[windowId]
                btnWidth = self._measureButtonWidth(btn)

                extraSpacing = spacing
                projected = totalWidth + extraSpacing + btnWidth

                if projected + reservedWidth <= availableWidth - safetyMargin:
                    visibleIds.append(windowId)
                    totalWidth = projected
                else:
                    overflowIds = orderedIds[index:]
                    break

            self.overflowButton.show()
        else:
            self.overflowButton.hide()

        self._overflowWindowIds = overflowIds
        self._rebuildCenterBandContents(visibleIds)
        self._refreshStates()

        self.centerSection.layout().activate() # type: ignore
        self.layout().activate() # type: ignore

        newPos = self.centerBandHost.pos()
        if animated:
            self._animateCenterBand(oldPos, newPos, self._animDuration)

    def _showOverflowMenu(self):
        self.overflowMenu.clear()

        for windowId in getattr(self, "_overflowWindowIds", []):
            btn = self._buttons.get(windowId)
            if btn is None:
                continue

            action = QAction(btn.text(), self)

            def onTriggered(checked=False, wid=windowId):
                windows = {wid2: (title, visible, icon) for wid2, title, visible, icon in self.compositor.listWindows()}
                if wid not in windows:
                    return

                _, visible, _ = windows[wid]
                if not visible:
                    self.compositor.restoreWindow(wid)
                else:
                    self.compositor.focusWindow(wid)

            action.triggered.connect(onTriggered)
            self.overflowMenu.addAction(action)

        if self.overflowMenu.isEmpty():
            return

        globalPos = self.overflowButton.mapToGlobal(self.overflowButton.rect().bottomLeft())
        self.overflowMenu.exec(globalPos)

    def _insertWindowButton(self, windowId: str, title: str, icon=None):
        btn = TaskbarWindowButton(windowId, title, self, icon)
        self._buttons[windowId] = btn
        self._updateOverflow(animated=True)
        btn.animateShow()

    def toggleWindow(self, windowId: str):
        windows = {wid: (title, visible, icon) for wid, title, visible, icon in self.compositor.listWindows()}
        if windowId not in windows:
            return

        _, visible, _ = windows[windowId]

        if not visible:
            self.compositor.restoreWindow(windowId)
            return

        if self.compositor.activeWindowId == windowId:
            self.compositor.minimizeWindow(windowId)
        else:
            self.compositor.focusWindow(windowId)

    def _refreshStates(self):
        active = self.compositor.activeWindowId

        visibleMap = {wid: vis for wid, _, vis, _ in self.compositor.listWindows()}

        for wid, btn in self._buttons.items():
            visible = visibleMap.get(wid, False)
            btn.setState(
                active=(wid == active if active is not None else False),
                minimized=not visible,
                open_=True
            )

    def _onWindowCreated(self, e: dict):
        wid = e["id"]
        title = e.get("title", "Window")
        icon = e.get("icon")
        self._insertWindowButton(wid, title, icon)
        self._refreshStates()

    def _onWindowUpdated(self, e: dict):
        wid = e["id"]
        btn = self._buttons.get(wid)
        if btn is None:
            return

        if "title" in e:
            btn.setFrameTitle(e["title"])

        if "icon" in e:
            btn.setFrameIcon(e["icon"])

        self._refreshStates()

    def _onWindowClosed(self, e: dict):
        wid = e["id"]
        btn = self._buttons.pop(wid, None)

        if btn is None:
            self._updateOverflow(animated=True)
            self._refreshStates()
            return

        def finalize():
            btn.hide()
            btn.deleteLater()
            self._rebuildCenterBandContents([])
            self._updateOverflow(animated=True)
            self._refreshStates()

        btn.animateHide(onFinished=finalize)

    def _onWindowMinimized(self, e: dict):
        self._refreshStates()

    def _onWindowRestored(self, e: dict):
        self._refreshStates()

    def _onWindowFocused(self, e: dict):
        self._refreshStates()

    def _onFocusCleared(self, e: dict):
        self._refreshStates()

    def _onAppRegistered(self, payload=None):
        self._populateNexHubApps()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            w = self.childAt(e.position().toPoint())
            if w is None or not isinstance(w, QPushButton):
                self.compositor.clearFocus()
        super().mousePressEvent(e)

    def _positionNexHub(self):
        hostWindow = self.window()
        if hostWindow is None:
            return

        panelWidth = 550
        panelHeight = 500
        margin = 12

        startButtonTopLeft = self.startButton.mapTo(hostWindow, self.startButton.rect().topLeft())
        startButtonTopRight = self.startButton.mapTo(hostWindow, self.startButton.rect().topRight())

        if self.taskbarAlignment == "center":
            buttonCenterX = (startButtonTopLeft.x() + startButtonTopRight.x()) // 2
            x = buttonCenterX - panelWidth // 2
        else:
            x = startButtonTopLeft.x()

        taskbarTopLeft = self.mapTo(hostWindow, self.rect().topLeft())
        y = taskbarTopLeft.y() - panelHeight - margin

        x = max(margin, min(x, hostWindow.width() - panelWidth - margin))

        self.nexHub.setParent(hostWindow)
        self.nexHub.setGeometry(x, y, panelWidth, panelHeight)
        self.nexHub.raise_()

    def _toggleNexHub(self):
        self.compositor.clearFocus()
        self.nexHub.searchEdit.clear()
        self._positionNexHub()

        if self.nexHub.isVisible():
            self._closeNexHub()
        else:
            self.nexHub.animateShow()
            self._setNexHubButtonState(True)
    
    def _closeNexHub(self):
        self.nexHub.animateHide()
        self._setNexHubButtonState(False)

    def _populateNexHubApps(self):
        appsService = self.kernel.services.get("apps")
        if appsService is None:
            self.nexHub.setApps([])
            return

        items = []
        for appMeta in appsService.listApps():
            items.append({
                "id": appMeta["id"],
                "title": appMeta["title"],
                "subtitle": appMeta.get("subtitle", "") or "",
                "icon": appMeta.get("icon")
            })

        self.nexHub.setApps(items)

    def _launchAppFromNexHub(self, appId: str):
        apps = self.kernel.services.get("apps")
        # TODO: brancher sur ton vrai AppManager plus tard
        """ if appId == "welcome":
            from PySide6.QtWidgets import QLabel
            content = QLabel(f"Hello, {self.nexHub._userName} 👋\n\nWelcome to Nexus by SmartSoft!")
            content.setStyleSheet('''
                color: white;
                padding: 14px;
                background: #112265;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
            ''')
            self.compositor.createWindow(title="Welcome", content=content, width=800, height=450)

        elif appId == "files":
            from PySide6.QtWidgets import QLabel
            content = QLabel("Gestionnaire de fichiers")
            content.setStyleSheet("color: white; padding: 16px;")
            self.compositor.createWindow(title="Files (Nexplore)", content=content, width=700, height=460) """
        
        if apps is None:
            print(f"Nexus: AppService introuvable, impossible de lancer '{appId}'")
            self._closeNexHub()
            return

        try:
            apps.launch(appId)
        except Exception as exc:
            print(f"Nexus: échec du lancement de l'app '{appId}': {exc}")

        self._closeNexHub()

    def _installNexHubEventFilter(self):
        if self._nexHubFilterInstalled:
            return

        app = QApplication.instance()
        if app is None:
            return

        app.installEventFilter(self)
        self._nexHubFilterInstalled = True

    def _isWidgetOrChild(self, widget, target):
        current = target
        while current is not None:
            if current is widget:
                return True
            current = current.parentWidget()
        return False

    def _setNexHubButtonState(self, opened: bool):
        self._nexHubOpen = opened
        self.startButton.setProperty("opened", self._nexHubOpen)
        self.startButton.style().unpolish(self.startButton)
        self.startButton.style().polish(self.startButton)
        self.startButton.update()

    def _handleLockRequest(self):
        self._closeNexHub()
        self.kernel.bus.emit("session.lock.requested")

    def _handleLogoutRequest(self):
        self._closeNexHub()
        self.kernel.bus.emit("session.logout.requested")

    def _handleSleepRequest(self):
        self.kernel.bus.emit("system.sleep.requested")
        self._closeNexHub()
        
        powerService = self.kernel.services.get("power")
        powerService.sleep()

    def _handleShutdownRequest(self):
        self.kernel.bus.emit("system.shutdown.requested")
        self._closeNexHub()
        
        powerService = self.kernel.services.get("power")
        powerService.quitApplication()

    def _handleRestartRequest(self):
        self.kernel.bus.emit("system.restart.requested")
        self._closeNexHub()
        print("Nexus: Restart requested (placeholder)")

    def _positionClockPanel(self):
        hostWindow = self.window()
        if hostWindow is None:
            return

        panelWidth = 320
        panelHeight = 420
        margin = 12

        topRightInWindow = self.mapTo(hostWindow, self.rect().topRight())

        x = topRightInWindow.x() - panelWidth - margin
        y = topRightInWindow.y() - panelHeight - margin

        self.clockPanel.setParent(hostWindow)
        self.clockPanel.setGeometry(x, y, panelWidth, panelHeight)
        self.clockPanel.raise_()

    def _toggleClockPanel(self):
        self.compositor.clearFocus()
        self._positionClockPanel()

        if self.clockPanel.isVisible():
            self.clockPanel.animateHide()
        else:
            self.clockPanel.refreshDateTime()
            self.clockPanel.animateShow()

    def _closeClockPanel(self):
        if self.clockPanel.isVisible():
            self.clockPanel.animateHide()

    def _animateCenterBand(self, oldPos: QPoint, newPos: QPoint, duration: int = 170):
        if oldPos == newPos:
            return

        if self._centerBandAnim is not None:
            try:
                self._centerBandAnim.stop()
            except Exception:
                pass
            self._centerBandAnim = None

        self.centerBandHost.move(oldPos)

        anim = QPropertyAnimation(self.centerBandHost, b"pos", self)
        anim.setDuration(duration)
        anim.setStartValue(oldPos)
        anim.setEndValue(newPos)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()

        self._centerBandAnim = anim

    def eventFilter(self, watched, event):
        # Repositionnement du NexHub / ClockPanel si la fenêtre hôte bouge ou change de taille
        if watched is self._hostWindowForLayout:
            if event.type() in (QEvent.Type.Resize, QEvent.Type.Move):
                self._updateOverflow(True)

                if self.nexHub.isVisible():
                    self._positionNexHub()

                if self.clockPanel.isVisible():
                    self._positionClockPanel()

        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            globalPos = event.globalPosition().toPoint()
            clickedWidget = QApplication.widgetAt(globalPos)

            if self.nexHub.isVisible():
                clickedInsideNexHub = self._isWidgetOrChild(self.nexHub, clickedWidget)
                clickedStartButton = self._isWidgetOrChild(self.startButton, clickedWidget)

                if not clickedInsideNexHub and not clickedStartButton:
                    self._closeNexHub()

            if hasattr(self, "clockPanel") and self.clockPanel.isVisible():
                clickedInsideClockPanel = self._isWidgetOrChild(self.clockPanel, clickedWidget)
                clickedClockWidget = self._isWidgetOrChild(self.clockWidget, clickedWidget)

                if not clickedInsideClockPanel and not clickedClockWidget:
                    self._closeClockPanel()

        return super().eventFilter(watched, event)
    
    def contextMenuEvent(self, event):
        clickedWidget = self.childAt(event.pos())

        if self._isWidgetOrChild(self.rightSection, clickedWidget):
            super().contextMenuEvent(event)
            return

        menu = QMenu(self)

        alignmentMenu = menu.addMenu("Alignement de la barre des tâches")

        actLeft = QAction("Gauche", self)
        actLeft.setCheckable(True)
        actLeft.setChecked(self.taskbarAlignment == "left")
        actLeft.triggered.connect(lambda: self._setTaskbarAlignment("left"))

        actCenter = QAction("Centré", self)
        actCenter.setCheckable(True)
        actCenter.setChecked(self.taskbarAlignment == "center")
        actCenter.triggered.connect(lambda: self._setTaskbarAlignment("center"))

        actSemiCenter = QAction("Semi-centré", self)
        actSemiCenter.setCheckable(True)
        actSemiCenter.setChecked(self.taskbarAlignment == "semiCenter")
        actSemiCenter.triggered.connect(lambda: self._setTaskbarAlignment("semiCenter"))

        alignmentMenu.addAction(actLeft)
        alignmentMenu.addAction(actCenter)

        menu.exec(event.globalPos())
