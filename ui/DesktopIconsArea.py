from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from PySide6.QtCore import Qt, Signal, QPoint, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QAction
from PySide6.QtWidgets import QWidget, QMenu

from ui.DesktopIcon import DesktopIcon


@dataclass
class DesktopEntry:
    id: str
    label: str
    icon: str
    entryType: str
    target: str
    x: int | None = None
    y: int | None = None


class GhostSlot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def showAt(self, rect: QRect):
        self.setGeometry(rect)
        self.show()
        self.raise_()
        self.update()

    def hideSlot(self):
        self.hide()

    def paintEvent(self, event):
        if not self.isVisible():
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        fill = QColor(255, 255, 255, 28)
        border = QColor(255, 255, 255, 110)

        p.setPen(QPen(border, 1))
        p.setBrush(QBrush(fill))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)


class DesktopIconsArea(QWidget):
    iconActivated = Signal(str)

    MODE_GRID = "grid"
    MODE_FREE = "free"
    MODE_FREE_SNAP = "freeSnap"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("DesktopIconsArea")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        self.entries: Dict[str, DesktopEntry] = {}
        self.icons: Dict[str, DesktopIcon] = {}
        self._orderedIds: List[str] = []

        self._layoutMode = self.MODE_FREE_SNAP

        self._gridMarginLeft = 16
        self._gridMarginTop = 16
        self._gridMarginRight = 16
        self._gridMarginBottom = 16
        self._cellWidth = 96
        self._cellHeight = 108

        self._draggingId: str | None = None
        self._dragOffset = QPoint()
        self._dragTargetIndex: int | None = None

        self._iconAnimations: Dict[str, QPropertyAnimation] = {}

        self._ghostSlot = GhostSlot(self)

    def _workArea(self) -> QRect:
        compositor = self.parentWidget()
        if compositor is not None and hasattr(compositor, "workingArea"):
            try:
                area = compositor.workingArea() # type: ignore
                if isinstance(area, QRect) and area.isValid():
                    return area
            except Exception:
                pass

        return self.rect()

    def addEntry(self, entry: DesktopEntry):
        if entry.x is None or entry.y is None:
            x, y = self._defaultPositionForNewEntry()
            entry.x = x
            entry.y = y

        self.entries[entry.id] = entry
        self._orderedIds.append(entry.id)

        icon = DesktopIcon(
            entryId=entry.id,
            label=entry.label,
            icon=entry.icon,
            parent=self
        )
        icon.selected.connect(self.selectIcon)
        icon.activated.connect(self.iconActivated.emit)
        icon.dragStarted.connect(self._onIconDragStarted)
        icon.dragMoved.connect(self._onIconDragMoved)
        icon.dragFinished.connect(self._onIconDragFinished)
        icon.show()

        self.icons[entry.id] = icon
        self.arrangeIcons(animated=False)

    def removeEntry(self, entryId: str):
        icon = self.icons.pop(entryId, None)
        self.entries.pop(entryId, None)

        if entryId in self._orderedIds:
            self._orderedIds.remove(entryId)

        self._stopAnimation(entryId)

        if self._draggingId == entryId:
            self._draggingId = None
            self._dragOffset = QPoint()
            self._dragTargetIndex = None
            self._ghostSlot.hideSlot()

        if icon is not None:
            icon.hide()
            icon.deleteLater()

        self.arrangeIcons(animated=False)

    def selectIcon(self, entryId: str):
        for wid, icon in self.icons.items():
            icon.setSelected(wid == entryId)

        compositor = self.parentWidget()
        if compositor is not None and hasattr(compositor, "clearFocus"):
            compositor.clearFocus()

    def clearSelection(self):
        for icon in self.icons.values():
            icon.setSelected(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.arrangeIcons(animated=False)
        self._normalizeFreePositionsToWorkArea()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            clicked = self.childAt(event.position().toPoint())

            if clicked is None or clicked == self._ghostSlot:
                self.clearSelection()

                compositor = self.parentWidget()
                if compositor is not None and hasattr(compositor, "clearFocus"):
                    compositor.clearFocus()

                event.accept()
                return

            event.accept()
            return

        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        clicked = self.childAt(event.pos())

        if clicked is not None and clicked != self._ghostSlot:
            super().contextMenuEvent(event)
            return
        
        compositor = self.parentWidget()
        if compositor is not None and hasattr(compositor, "clearFocus"):
            compositor.clearFocus()
        
        menu = QMenu(self)

        alignMenu = menu.addMenu("Alignement des icônes")

        actGrid = QAction("Grille automatique", self)
        actGrid.setCheckable(True)
        actGrid.setChecked(self._layoutMode == self.MODE_GRID)
        actGrid.triggered.connect(lambda: self.setLayoutMode(self.MODE_GRID))

        actFreeSnap = QAction("Grille libre", self)
        actFreeSnap.setCheckable(True)
        actFreeSnap.setChecked(self._layoutMode == self.MODE_FREE_SNAP)
        actFreeSnap.triggered.connect(lambda: self.setLayoutMode(self.MODE_FREE_SNAP))

        actFree = QAction("Sans alignement", self)
        actFree.setCheckable(True)
        actFree.setChecked(self._layoutMode == self.MODE_FREE)
        actFree.triggered.connect(lambda: self.setLayoutMode(self.MODE_FREE))

        alignMenu.addAction(actGrid)
        alignMenu.addAction(actFreeSnap)
        alignMenu.addAction(actFree)

        menu.addSeparator()

        actAutoArrange = QAction("Réorganiser maintenant", self)
        actAutoArrange.setEnabled(self._layoutMode == self.MODE_GRID)
        actAutoArrange.triggered.connect(lambda: self.arrangeIcons(animated=True))
        menu.addAction(actAutoArrange)

        menu.exec(event.globalPos())

    # -------------------------
    # Layout / ordre affiché
    # -------------------------

    def _captureCurrentIconPositions(self):
        for entryId, icon in self.icons.items():
            entry = self.entries.get(entryId)
            if entry is None:
                continue
            entry.x = icon.x()
            entry.y = icon.y()

    def setLayoutMode(self, mode: str):
        if mode not in (self.MODE_GRID, self.MODE_FREE, self.MODE_FREE_SNAP):
            return

        if self._layoutMode == mode:
            return

        self._captureCurrentIconPositions()

        self._layoutMode = mode
        self._draggingId = None
        self._dragOffset = QPoint()
        self._dragTargetIndex = None
        self._ghostSlot.hideSlot()

        for entryId in list(self._iconAnimations.keys()):
            self._stopAnimation(entryId)

        self.arrangeIcons(animated=True)

    def arrangeIcons(self, animated: bool = False):
        if self._layoutMode == self.MODE_GRID:
            order = self._displayOrder()
            rowsPerColumn = self._rowsPerColumn()

            for index, entryId in enumerate(order):
                if entryId == self._draggingId:
                    continue

                icon = self.icons.get(entryId)
                entry = self.entries.get(entryId)
                if icon is None or entry is None:
                    continue

                x, y = self._gridPosForIndex(index, rowsPerColumn)
                entry.x = x
                entry.y = y

                target = QPoint(x, y)
                if animated:
                    self._animateIconTo(entryId, icon, target)
                else:
                    self._stopAnimation(entryId)
                    icon.move(target)

            return

        # MODE_FREE / MODE_FREE_SNAP
        for entryId, icon in self.icons.items():
            if entryId == self._draggingId:
                continue

            entry = self.entries.get(entryId)
            if entry is None:
                continue

            target = QPoint(entry.x, entry.y) # type: ignore
            if animated:
                self._animateIconTo(entryId, icon, target)
            else:
                self._stopAnimation(entryId)
                icon.move(target)

    def _defaultPositionForNewEntry(self) -> tuple[int, int]:
        index = len(self._orderedIds)
        rowsPerColumn = self._rowsPerColumn()
        return self._gridPosForIndex(index, rowsPerColumn)

    def _displayOrder(self) -> List[str]:
        if self._draggingId is None:
            return list(self._orderedIds)

        base = [eid for eid in self._orderedIds if eid != self._draggingId]

        if self._dragTargetIndex is None:
            return base

        insertIndex = max(0, min(self._dragTargetIndex, len(base)))
        base.insert(insertIndex, self._draggingId)
        return base

    def _rowsPerColumn(self) -> int:
        area = self._workArea()
        usableHeight = area.height() - self._gridMarginTop - self._gridMarginBottom
        if usableHeight <= 0:
            return 1
        return max(1, usableHeight // self._cellHeight)

    def _gridPosForIndex(self, index: int, rowsPerColumn: int) -> tuple[int, int]:
        area = self._workArea()

        column = index // rowsPerColumn
        row = index % rowsPerColumn

        x = area.left() + self._gridMarginLeft + column * self._cellWidth
        y = area.top() + self._gridMarginTop + row * self._cellHeight
        return x, y

    def _gridRectForIndex(self, index: int) -> QRect:
        rowsPerColumn = self._rowsPerColumn()
        x, y = self._gridPosForIndex(index, rowsPerColumn)
        return QRect(x, y, 92, 100)  # taille DesktopIcon actuelle

    def _indexFromPoint(self, pos: QPoint) -> int:
        area = self._workArea()
        rowsPerColumn = self._rowsPerColumn()

        relX = pos.x() - (area.left() + self._gridMarginLeft)
        relY = pos.y() - (area.top() + self._gridMarginTop)

        column = max(0, relX // self._cellWidth) if relX >= 0 else 0
        row = max(0, relY // self._cellHeight) if relY >= 0 else 0

        index = column * rowsPerColumn + row
        return max(0, min(index, len(self._orderedIds) - 1))

    def _clampIconPosToWorkArea(self, x: int, y: int, icon: DesktopIcon) -> tuple[int, int]:
        area = self._workArea()

        minX = area.left()
        minY = area.top()
        maxX = max(minX, area.right() - icon.width() + 1)
        maxY = max(minY, area.bottom() - icon.height() + 1)

        x = max(minX, min(x, maxX))
        y = max(minY, min(y, maxY))
        return x, y
    
    def _normalizeFreePositionsToWorkArea(self):
        if self._layoutMode not in (self.MODE_FREE, self.MODE_FREE_SNAP):
            return

        for entryId, icon in self.icons.items():
            entry = self.entries.get(entryId)
            if entry is None:
                continue

            x, y = self._clampIconPosToWorkArea(entry.x, entry.y, icon) # type: ignore
            entry.x = x
            entry.y = y
            if entryId != self._draggingId:
                icon.move(x, y)

    # -------------------------
    # Drag V4.5
    # -------------------------

    def _onIconDragStarted(self, entryId: str, globalPos: QPoint):
        icon = self.icons.get(entryId)
        if icon is None:
            return

        self._draggingId = entryId
        self._stopAnimation(entryId)
        icon.raise_()

        localPos = self.mapFromGlobal(globalPos)
        self._dragOffset = localPos - icon.pos()

        if self._layoutMode == self.MODE_GRID:
            self._dragTargetIndex = self._orderedIds.index(entryId)
            self._updateGhostSlot()
        else:
            self._dragTargetIndex = None
            self._ghostSlot.hideSlot()

        compositor = self.parentWidget()
        if compositor is not None and hasattr(compositor, "clearFocus"):
            compositor.clearFocus()

    def _onIconDragMoved(self, entryId: str, globalPos: QPoint):
        if self._draggingId != entryId:
            return

        icon = self.icons.get(entryId)
        if icon is None:
            return

        localPos = self.mapFromGlobal(globalPos)
        targetPos = localPos - self._dragOffset

        minX = 0
        minY = 0
        maxX = max(minX, self.width() - icon.width())
        maxY = max(minY, self.height() - icon.height())

        x, y = self._clampIconPosToWorkArea(targetPos.x(), targetPos.y(), icon)
        icon.move(x, y)

        if self._layoutMode == self.MODE_GRID:
            targetIndex = self._indexFromPoint(icon.geometry().center())
            if targetIndex != self._dragTargetIndex:
                self._dragTargetIndex = targetIndex
                self.arrangeIcons(animated=True)
            self._updateGhostSlot()

    def _onIconDragFinished(self, entryId: str, globalPos: QPoint):
        if self._draggingId != entryId:
            return

        icon = self.icons.get(entryId)
        entry = self.entries.get(entryId)

        if icon is None or entry is None:
            self._draggingId = None
            self._dragOffset = QPoint()
            self._dragTargetIndex = None
            self._ghostSlot.hideSlot()
            return

        if self._layoutMode == self.MODE_GRID:
            newOrder = [eid for eid in self._orderedIds if eid != entryId]

            insertIndex = self._dragTargetIndex
            if insertIndex is None:
                insertIndex = len(newOrder)

            insertIndex = max(0, min(insertIndex, len(newOrder)))
            newOrder.insert(insertIndex, entryId)
            self._orderedIds = newOrder

            self._draggingId = None
            self._dragOffset = QPoint()
            self._dragTargetIndex = None
            self._ghostSlot.hideSlot()

            self.arrangeIcons(animated=True)
            return

        if self._layoutMode == self.MODE_FREE:
            x, y = self._clampIconPosToWorkArea(icon.x(), icon.y(), icon)
            entry.x = x
            entry.y = y

        elif self._layoutMode == self.MODE_FREE_SNAP:
            snapX, snapY = self._snapPosToGrid(icon.pos())
            entry.x = snapX
            entry.y = snapY

        self._draggingId = None
        self._dragOffset = QPoint()
        self._dragTargetIndex = None
        self._ghostSlot.hideSlot()

        self.arrangeIcons(animated=True)
    
    def _snapPosToGrid(self, pos: QPoint) -> tuple[int, int]:
        area = self._workArea()

        relX = max(0, pos.x() - (area.left() + self._gridMarginLeft))
        relY = max(0, pos.y() - (area.top() + self._gridMarginTop))

        col = round(relX / self._cellWidth)
        row = round(relY / self._cellHeight)

        x = area.left() + self._gridMarginLeft + col * self._cellWidth
        y = area.top() + self._gridMarginTop + row * self._cellHeight

        # clamp dans la zone utile
        maxX = max(area.left(), area.right() - 92 + 1)
        maxY = max(area.top(), area.bottom() - 100 + 1)

        x = max(area.left(), min(x, maxX))
        y = max(area.top(), min(y, maxY))

        return x, y

    def _updateGhostSlot(self):
        if self._draggingId is None or self._dragTargetIndex is None:
            self._ghostSlot.hideSlot()
            return

        rect = self._gridRectForIndex(self._dragTargetIndex)
        self._ghostSlot.showAt(rect)

    # -------------------------
    # Animations robustes
    # -------------------------

    def _animateIconTo(self, entryId: str, icon: DesktopIcon, target: QPoint):
        if icon.pos() == target:
            self._stopAnimation(entryId)
            return

        self._stopAnimation(entryId)

        anim = QPropertyAnimation(icon, b"pos", self)
        anim.setDuration(120)
        anim.setStartValue(icon.pos())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._iconAnimations[entryId] = anim

        def cleanup():
            current = self._iconAnimations.get(entryId)
            if current is anim:
                self._iconAnimations.pop(entryId, None)

        anim.finished.connect(cleanup)
        anim.start()

    def _stopAnimation(self, entryId: str):
        anim = self._iconAnimations.pop(entryId, None)
        if anim is not None:
            anim.stop()
