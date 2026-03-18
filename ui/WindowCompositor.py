from __future__ import annotations
from typing import Dict, Optional

from PySide6.QtCore import Qt, QPoint, QRect, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget

from ui.WindowFrame import WindowFrame
from ui.SnapAssist import SnapAssistPanel
from ui.DesktopIconsArea import DesktopIconsArea, DesktopEntry


class SnapOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setVisible(False)
        self._rect = QRect()

    def showRect(self, rect: QRect):
        self._rect = rect
        self.setVisible(True)
        self.update()

    def hideOverlay(self):
        self.setVisible(False)
        self._rect = QRect()
        self.update()

    def paintEvent(self, event):
        if not self.isVisible() or self._rect.isNull():
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Preview style (simple + clean)
        fill = Qt.GlobalColor.white
        p.setOpacity(0.14)
        p.fillRect(self._rect, fill)

        p.setOpacity(0.45)
        p.drawRect(self._rect.adjusted(0, 0, -1, -1))


class WindowCompositor(QWidget):

    def __init__(self, kernel):
        super().__init__()
        self.kernel = kernel
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("WindowCompositor")

        self._windows: Dict[str, WindowFrame] = {}
        self._activeId: Optional[str] = None

        self._icons = DesktopIconsArea(self)
        self._icons.setGeometry(self.rect())
        self._icons.iconActivated.connect(self._onDesktopEntryActivated)
        self._icons.lower()
        self._icons.addEntry(
            DesktopEntry(
                id="nexver",
                label="About Nexus",
                icon="apps/about/icon1.png",
                entryType="app",
                target="nexver"
            )
        )
        self._icons.addEntry(
            DesktopEntry(
                id="notes",
                label="NexPad",
                icon="apps/notes/icon.png",
                entryType="app",
                target="notes"
            )
        )
        self._icons.addEntry(
            DesktopEntry(
                id="terminal",
                label="NexCommander",
                icon="apps/terminal/icon.png",
                entryType="app",
                target="terminal"
            )
        )

        # Snap system
        self._snapThreshold = 24     # px
        self._snapKind = None        # None | "left" | "right" | "top"
        self._snapWindowId = None

        self._snapOverlay = SnapOverlay(self)
        self._snapOverlay.setGeometry(self.rect())

        self._snapAssist = SnapAssistPanel(self)
        self._snapAssist.hide()
        self._snapAssist.windowChosen.connect(self._onSnapAssistWindowChosen)
        self._snapAssist.requestClose.connect(self._hideSnapAssist)

        self._snapAssistAnchorKind = None   # "left" | "right" | None
        self._snapAssistSourceWindowId = None

        self._snapOverlay.raise_()

        self.setStyleSheet("#WindowCompositor { background: transparent; }")

    @property
    def activeWindowId(self) -> Optional[str]:
        return self._activeId

    def createWindow(self, *, title: str, content: QWidget, icon=None, width=640, height=420) -> str:
        wf = WindowFrame(title=title, content=content, icon=icon)
        wf.setParent(self)
        wf.resize(width, height)

        # position "cascade" sympa
        offset = 24 * (len(self._windows) % 8)
        area = self.workingArea()
        x = min(area.right() - width, area.left() + 80 + offset)
        y = min(area.bottom() - height, area.top() + 60 + offset)
        wf.move(max(area.left(), x), max(area.top(), y))

        wf.requestedFocus.connect(self.focusWindow)
        wf.requestedClose.connect(self.closeWindow)
        wf.requestedMinimize.connect(self.minimizeWindow)
        wf.titlebar.dragStarted.connect(lambda gp, wid=wf.meta.id: self._onWindowDragStarted(wid, gp))
        wf.titlebar.dragMoved.connect(lambda gp, wid=wf.meta.id: self._onWindowDragMoved(wid, gp))
        wf.titlebar.dragEnded.connect(lambda wid=wf.meta.id: self._onWindowDragEnded(wid))

        wf.show()
        wf.raise_()
        self._windows[wf.meta.id] = wf
        self.focusWindow(wf.meta.id)
        self._snapOverlay.raise_()
        if self._snapAssist.isVisible():
            self._snapAssist.raise_()
        wf.animateOpen()

        # Events
        self.kernel.bus.emit("window.created", id=wf.meta.id, title=title, icon=icon)
        return wf.meta.id

    def updateWindow(self, windowId: str, *, title=None, icon=None):
        wf = self._windows.get(windowId)
        if wf is None:
            return

        wf.updateFrame(title=title, icon=icon)

    def focusWindow(self, windowId: str) -> None:
        # print(f"focusWindow({windowId})")
        if windowId not in self._windows:
            return

        # visuel focus off
        if self._activeId and self._activeId in self._windows:
            self._windows[self._activeId].setActive(False)

        wf = self._windows[windowId]
        wf.show()
        wf.raise_()
        wf.setActive(True)
        wf.setFocus()

        self._activeId = windowId
        self.kernel.bus.emit("window.focused", id=windowId, title=wf.meta.title)

    def clearFocus(self) -> None:
        # print("WindowCompositor.clearFocus()")
        if self._activeId and self._activeId in self._windows:
            self._windows[self._activeId].setActive(False)
        self._activeId = None
        self.kernel.bus.emit("window.focus.cleared")
        self._hideSnapAssist()

    def closeWindow(self, windowId: str) -> None:
        wf = self._windows.get(windowId)
        if not wf:
            return
        
        self.focusWindow(windowId)

        def finalize():
            wf.hide()
            wf.deleteLater()

            if windowId in self._windows:
                del self._windows[windowId]

            if self._activeId == windowId:
                self._activeId = None
                if self._windows:
                    last_id = list(self._windows.keys())[-1]
                    self.focusWindow(last_id)

            self.kernel.bus.emit("window.closed", id=windowId)

            if self._snapAssistSourceWindowId == windowId:
                self._hideSnapAssist()

        wf.animateClose(onFinished=finalize)

    def minimizeWindow(self, windowId: str) -> None:
        wf = self._windows.get(windowId)
        if not wf:
            return
        
        self.focusWindow(windowId)

        def finalize():
            wf.hide()
            if self._activeId == windowId:
                self._activeId = None
            self.kernel.bus.emit("window.minimized", id=windowId, title=wf.meta.title)

            if self._snapAssistSourceWindowId == windowId:
                self._hideSnapAssist()

        wf.animateMinimize(onFinished=finalize)

    def restoreWindow(self, windowId: str) -> None:
        wf = self._windows.get(windowId)
        if not wf:
            return
        
        if getattr(wf, "_preMinimizeGeometry", None) is not None:
            wf.setGeometry(wf._preMinimizeGeometry) # type: ignore
            wf._preMinimizeGeometry = None

        wf.show()
        self.focusWindow(windowId)
        wf.animateRestore()
        self.kernel.bus.emit("window.restored", id=windowId, title=wf.meta.title)

    def listWindows(self):
        # utile pour taskbar
        return [(wid, w.meta.title, w.isVisible(), w.meta.icon) for wid, w in self._windows.items()]
    
    def getWindow(self, windowId: str) -> Optional[WindowFrame]:
        return self._windows.get(windowId)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)

        self._icons.setGeometry(self.rect())

        self._snapOverlay.setGeometry(self.rect())
        self._snapOverlay.raise_()

        for wf in self._windows.values():
            if getattr(wf, "isMaximized", None) and wf.isMaximized():
                wf.applyMaximizedGeometry()
            elif getattr(wf, "isSnapped", None) and wf.isSnapped():
                wf.applySnappedGeometry()
        
        if self._snapAssist.isVisible() and self._snapAssistAnchorKind:
            self._snapAssist.setGeometry(self._snapAssistRect(self._snapAssistAnchorKind))
            self._snapAssist.raise_()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            w = self.childAt(e.position().toPoint())

            # Remonter la chaîne de parents pour voir si on a cliqué une fenêtre
            wf = None
            cur = w
            while cur is not None:
                if isinstance(cur, WindowFrame):
                    wf = cur
                    break
                cur = cur.parentWidget()

            if wf is None:
                # clic dans le vide => perte globale de focus
                self.clearFocus()
                self._icons.clearSelection()
            else:
                # clic sur une fenêtre => focus
                self.focusWindow(wf.meta.id)

        super().mousePressEvent(e)

    def workingArea(self) -> QRect:
        taskbarHeight = 48
        return QRect(0, 0, self.width(), max(0, self.height() - taskbarHeight))

    def _snapPreviewRect(self, kind: str) -> QRect:
        area = self.workingArea()
        m = 10

        left = area.left() + m
        top = area.top() + m
        width = max(0, area.width() - 2 * m)
        height = max(0, area.height() - 2 * m)

        halfW = max(0, width // 2)
        halfH = max(0, height // 2)

        if kind == "top":
            return QRect(left, top, width, height)

        if kind == "left":
            return QRect(left, top, halfW, height)

        if kind == "right":
            return QRect(left + width - halfW, top, halfW, height)

        if kind == "top_left":
            return QRect(left, top, halfW, halfH)

        if kind == "top_right":
            return QRect(left + width - halfW, top, halfW, halfH)

        if kind == "bottom_left":
            return QRect(left, top + height - halfH, halfW, halfH)

        if kind == "bottom_right":
            return QRect(left + width - halfW, top + height - halfH, halfW, halfH)

        return QRect()

    def _detectSnapKind(self, globalPos: QPoint) -> str | None:
        p = self.mapFromGlobal(globalPos)
        area = self.workingArea()
        t = self._snapThreshold

        left = p.x() <= area.left() + t
        right = p.x() >= area.right() - t
        top = p.y() <= area.top() + t
        bottom = p.y() >= area.bottom() - t

        if top and left:
            return "top_left"
        if top and right:
            return "top_right"
        if bottom and left:
            return "bottom_left"
        if bottom and right:
            return "bottom_right"

        if top:
            return "top"
        if left:
            return "left"
        if right:
            return "right"

        return None

    def _onWindowDragStarted(self, windowId: str, globalPos: QPoint):
        # Si le Snap Assist est ouvert et qu'on drag une autre fenêtre, on le ferme
        if (
            self._snapAssist.isVisible()
            and self._snapAssistSourceWindowId is not None
            and windowId != self._snapAssistSourceWindowId
        ):
            self._hideSnapAssist()

        self._snapWindowId = windowId
        self._snapKind = None
        self._snapOverlay.hideOverlay()

    def _onWindowDragMoved(self, windowId: str, globalPos: QPoint):
        if self._snapWindowId != windowId:
            return

        kind = self._detectSnapKind(globalPos)
        if kind != self._snapKind:
            self._snapKind = kind
            if kind is None:
                self._snapOverlay.hideOverlay()
            else:
                self._snapOverlay.showRect(self._snapPreviewRect(kind))
                self._snapOverlay.raise_()

    def _onDesktopEntryActivated(self, entryId: str):
        entry = self._icons.entries.get(entryId)
        if entry is None:
            return

        if entry.entryType == "app":
            QTimer.singleShot(0, lambda target=entry.target: self._launchDesktopApp(target))
        
        elif entry.entryType == "folder":
            print(f"Nexus: ouverture du dossier '{entry.target}' non implémentée.")

        elif entry.entryType == "file":
            print(f"Nexus: ouverture du fichier '{entry.target}' non implémentée.")

        else:
            print(f"Nexus: type d'entrée bureau inconnu : {entry.entryType}")

    def _launchDesktopApp(self, appId: str):
        apps = self.kernel.services.get("apps")
        if apps is None:
            print("Nexus: service 'apps' introuvable.")
            return

        try:
            apps.launch(appId)
        except Exception as exc:
            print(f"Nexus: échec du lancement de l'app '{appId}': {exc}")

    def _applySnap(self, windowId: str, kind: str):
        wf = self._windows.get(windowId)
        if not wf:
            return

        wf.saveNormalGeometry()

        def finalize():
            self.focusWindow(windowId)
            self.kernel.bus.emit("window.snapped", id=windowId, kind=kind)

            if kind in ("left", "right", "top_left", "bottom_left", "top_right", "bottom_right"):
                self._showSnapAssist(windowId, kind)
            else:
                self._hideSnapAssist()

        # Cas maximize (snap haut)
        if kind == "top":
            if wf.isSnapped():
                wf.setSnapKind(None)

            if not wf.isMaximized():
                wf._restoreGeom = wf.geometry()

            wf.setSnapKind(None)
            wf._maximized = True
            target = wf.maximizedGeometry()
            wf.animateToGeometry(target, duration=150, onFinished=finalize)
            return

        # Autres snaps
        if wf.isMaximized():
            wf.restore()

        wf._maximized = False
        wf.setSnapKind(kind)

        target = wf.snappedGeometryForKind(kind)
        wf.animateToGeometry(target, duration=150, onFinished=finalize)
    
    def _onWindowDragEnded(self, windowId: str):
        if self._snapWindowId != windowId:
            return

        if self._snapKind is not None:
            self._applySnap(windowId, self._snapKind)

        self._snapOverlay.hideOverlay()
        self._snapKind = None
        self._snapWindowId = None

    def _snapAssistRect(self, anchorKind: str) -> QRect:
        area = self.workingArea()
        m = 10

        innerLeft = area.left() + m
        innerTop = area.top() + m
        innerWidth = max(0, area.width() - 2 * m)
        innerHeight = max(0, area.height() - 2 * m)

        halfW = max(0, innerWidth // 2)
        halfH = max(0, innerHeight // 2)

        if anchorKind == "left":
            return QRect(
                innerLeft + innerWidth - halfW,
                innerTop,
                halfW,
                innerHeight
            )

        if anchorKind == "right":
            return QRect(
                innerLeft,
                innerTop,
                halfW,
                innerHeight
            )

        if anchorKind == "top_left":
            return QRect(
                innerLeft,
                innerTop + innerHeight - halfH,
                halfW,
                halfH
            )

        if anchorKind == "bottom_left":
            return QRect(
                innerLeft,
                innerTop,
                halfW,
                halfH
            )

        if anchorKind == "top_right":
            return QRect(
                innerLeft + innerWidth - halfW,
                innerTop + innerHeight - halfH,
                halfW,
                halfH
            )

        if anchorKind == "bottom_right":
            return QRect(
                innerLeft + innerWidth - halfW,
                innerTop,
                halfW,
                halfH
            )

        return QRect()
    
    def _snapAssistTargetKind(self, anchorKind: str) -> str | None:
        mapping = {
            "left": "right",
            "right": "left",
            "top_left": "bottom_left",
            "bottom_left": "top_left",
            "top_right": "bottom_right",
            "bottom_right": "top_right",
        }
        return mapping.get(anchorKind)

    def _showSnapAssist(self, sourceWindowId: str, anchorKind: str):
        targetKind = self._snapAssistTargetKind(anchorKind)
        if targetKind is None:
            self._hideSnapAssist()
            return

        if self._isSnapZoneOccupied(targetKind, excludeWindowId=sourceWindowId):
            self._hideSnapAssist()
            return

        choices = []
        for wid, wf in self._windows.items():
            if wid == sourceWindowId:
                continue
            if not wf.isVisible():
                continue

            thumb = self._windowThumbnail(wf)
            choices.append((wid, wf.meta.title, thumb))

        if not choices:
            self._hideSnapAssist()
            return

        self._snapAssistSourceWindowId = sourceWindowId
        self._snapAssistAnchorKind = anchorKind

        self._snapAssist.setChoices(choices)
        self._snapAssist.setGeometry(self._snapAssistRect(anchorKind))
        self._snapAssist.raise_()
        self._snapAssist.animateShow()
        self._snapAssist.setFocus()

    def _hideSnapAssist(self):
        self._snapAssistSourceWindowId = None
        self._snapAssistAnchorKind = None
        self._snapAssist.animateHide()

    def _onSnapAssistWindowChosen(self, chosenWindowId: str):
        if not self._snapAssistAnchorKind:
            return

        targetKind = self._snapAssistTargetKind(self._snapAssistAnchorKind)
        if targetKind is None:
            self._hideSnapAssist()
            return

        self._applySnap(chosenWindowId, targetKind)
        self._hideSnapAssist()

    def _isSnapZoneOccupied(self, zoneKind: str, excludeWindowId: str | None = None) -> bool:
        for wid, wf in self._windows.items():
            if excludeWindowId is not None and wid == excludeWindowId:
                continue
            if not wf.isVisible():
                continue

            if hasattr(wf, "isMaximized") and wf.isMaximized():
                return True

            snapKind = wf.snapKind() if hasattr(wf, "snapKind") else None

            if zoneKind == "left" and snapKind in ("right",):
                continue
            if zoneKind == "right" and snapKind in ("left",):
                continue

            if snapKind == zoneKind:
                return True

            # Une moitié entière occupe aussi ses quarts
            if zoneKind in ("top_left", "bottom_left") and snapKind == "left":
                return True
            if zoneKind in ("top_right", "bottom_right") and snapKind == "right":
                return True

            # Un quart occupe aussi sa zone exacte
            if zoneKind == "left" and snapKind in ("top_left", "bottom_left"):
                return True
            if zoneKind == "right" and snapKind in ("top_right", "bottom_right"):
                return True

        return False

    def _windowThumbnail(self, wf) :
        try:
            pix = wf.grab()
            if pix.isNull():
                return None
            return pix
        except Exception:
            return None
