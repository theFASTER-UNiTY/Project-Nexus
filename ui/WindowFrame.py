from __future__ import annotations
import uuid
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import (
    Qt, QPoint, Signal, QRect, QEasingCurve, QPropertyAnimation, QParallelAnimationGroup,
    QEvent
)
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QGraphicsOpacityEffect
)

from core.theme.theme import theme


@dataclass
class WindowMeta:
    id: str
    title: str
    icon: object = None


class TitleBar(QWidget):
    requestedClose = Signal()
    requestedMinimize = Signal()
    requestedMaximizeToggle = Signal()
    requestedFocus = Signal()

    dragStarted = Signal(QPoint)      # global pos
    dragMoved = Signal(QPoint)        # global pos
    dragEnded = Signal()

    def __init__(self, title: str, icon=None):
        super().__init__()
        self.setObjectName("TitleBar")

        self._dragging = False
        self._dragOffset = QPoint(0, 0)

        # Height "pro" (DPI-friendly)
        self.setMinimumHeight(theme.metrics.titlebarHeight)
        self.setMaximumHeight(theme.metrics.titlebarHeight + 4)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 8, 4)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Icon (optionnelle)
        self.iconLabel = QLabel()
        self.iconLabel.setFixedSize(18, 18)
        self.iconLabel.setObjectName("TitleIcon")

        self._applyIcon(icon)

        # Title
        self.titleLabel = QLabel(title)
        self.titleLabel.setObjectName("WindowTitle")
        self.titleLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        # Spacer “draggable” implicit: label expands
        # Buttons
        self.btnMin = QPushButton("▽") # ("—") ⇱⇲
        self.btnMax = QPushButton("△") # ("□")
        self.btnClose = QPushButton("⨉")

        for b in (self.btnMin, self.btnMax, self.btnClose):
            b.setFixedSize(theme.metrics.windowButtonSize, theme.metrics.windowButtonSize)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.setObjectName("WinBtn")

        self.btnClose.setObjectName("WinBtnClose")

        self.btnMin.clicked.connect(self.requestedMinimize.emit)
        self.btnMax.clicked.connect(self.requestedMaximizeToggle.emit)
        self.btnClose.clicked.connect(self.requestedClose.emit)

        layout.addWidget(self.iconLabel)
        layout.addWidget(self.titleLabel, 1)
        layout.addWidget(self.btnMin)
        layout.addWidget(self.btnMax)
        layout.addWidget(self.btnClose)

    # --- Helpers: empêcher drag depuis les boutons
    def _isOnButtons(self, pos) -> bool:
        w = self.childAt(pos)
        return w in (self.btnMin, self.btnMax, self.btnClose)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.requestedFocus.emit()
            if not self._isOnButtons(e.position().toPoint()):
                self._dragging = True
                self.dragStarted.emit(e.globalPosition().toPoint())
            e.accept()
            return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._dragging:
            self.dragMoved.emit(e.globalPosition().toPoint())
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.dragEnded.emit()
        super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            if not self._isOnButtons(e.position().toPoint()):
                self._dragging = False
                self.dragEnded.emit()
                self.requestedMaximizeToggle.emit()
                e.accept()
                return
        super().mouseDoubleClickEvent(e)

    def setTitle(self, title: str):
        self.titleLabel.setText(title)

    def _applyIcon(self, icon):
        if icon is None:
            self.iconLabel.clear()
            self.iconLabel.hide()
            return

        try:
            if isinstance(icon, QPixmap):
                pm = icon
            else:
                pm = QPixmap(icon)

            if pm.isNull():
                self.iconLabel.clear()
                self.iconLabel.hide()
                return

            self.iconLabel.setPixmap(
                pm.scaled(
                    18, 18,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            self.iconLabel.show()

        except Exception:
            self.iconLabel.clear()
            self.iconLabel.hide()

    def setIcon(self, icon):
        self._applyIcon(icon)


class WindowFrame(QWidget):
    requestedClose = Signal(str)
    requestedMinimize = Signal(str)
    requestedFocus = Signal(str)

    def __init__(self, title: str, content: QWidget, icon=None):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAutoFillBackground(True)
        self.setMouseTracking(True)
        self.setObjectName("WindowFrame")
        self.meta = WindowMeta(id=str(uuid.uuid4()), title=title, icon=icon)

        self._styleNormal = ""
        self._styleSnapped = ""
        self._styleMaximized = ""
        self._dragging = False
        self._dragOffset = QPoint(0, 0)
        self._active = False
        self._maximized = False
        self._restoreGeom = None
        self._maxMargin = 0
        self._restoringFromMaxDrag = False
        self._pendingDragGlobalPos = None
        self.ratioX = 0.5

        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)

        self._animGroup = None
        self._isMinimized = False
        self._animDuration = 250

        # Resize config
        self._resizeMargin = 8     # largeur sensible des bords (px)
        self._minW = 260
        self._minH = 160

        # Resize state
        self._resizing = False
        self._resizeEdge = None     # str: "l","r","t","b","tl","tr","bl","br"
        self._pressGlobal = QPoint(0, 0)
        self._startGeom = QRect()

        self._snapKind = None
        self._normalGeometry = self.geometry()
        self._preMinimizeGeometry = None

        self._buildFrameStyles()

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        self.titlebar = TitleBar(title=title, icon=icon)
        self.titlebar.requestedClose.connect(lambda: self.requestedClose.emit(self.meta.id))
        self.titlebar.requestedMaximizeToggle.connect(self.toggleMaximize)
        self.titlebar.requestedMinimize.connect(lambda: self.requestedMinimize.emit(self.meta.id))
        self.titlebar.requestedFocus.connect(lambda: self.requestedFocus.emit(self.meta.id))
        self.titlebar.dragStarted.connect(self._onDragStarted)
        self.titlebar.dragMoved.connect(self._onDragMoved)
        self.titlebar.dragEnded.connect(self._onDragEnded)
        root.addWidget(self.titlebar)
        root.addWidget(content)

        self._installContentFocusProxy(content)
        self.setStyleSheet(self._styleNormal)
        self._enableMouseTrackingRecursive(self)

    def _onDragStarted(self, globalPos: QPoint):
        self._dragging = True
        self._restoredFromMaxOnDrag = False
        self._restoredFromSnapOnDrag = False

        topLeftGlobal = self.mapToGlobal(QPoint(0, 0))
        self._dragOffset = globalPos - topLeftGlobal

        # Si maximisée OU snappée, calculer le ratio horizontal dans la titlebar
        if self._maximized or self.isSnapped():
            localInTitle = self.titlebar.mapFromGlobal(globalPos)
            self.ratioX = 0.5
            if self.width() > 0:
                self.ratioX = max(0.05, min(0.95, localInTitle.x() / self.width()))

    def _onDragMoved(self, globalPos: QPoint):
        if not self._dragging:
            return

        parent = self.parentWidget()
        if not parent:
            return
        
        # IMPORTANT : pendant la restauration animée depuis maximize,
        # on ne fait pas de drag normal
        if self._restoringFromMaxDrag:
            self._pendingDragGlobalPos = globalPos
            return

        # 1) Si maximisée -> restore une seule fois
        if self._maximized and not self._restoredFromMaxOnDrag:
            if self._restoreGeom is None:
                return

            self._restoringFromMaxDrag = True
            self._pendingDragGlobalPos = globalPos

            targetGeom = self._restoreGeom

            # ratioX a déjà été calculé au drag start
            parentPos = parent.mapFromGlobal(globalPos)

            targetWidth = targetGeom.width()
            targetHeight = targetGeom.height()

            targetX = int(parentPos.x() - self.ratioX * targetWidth)
            targetY = int(parentPos.y() - self.titlebar.height() / 2)

            # Soft clamp
            targetX, targetY = self._clampTopLevelPosToWorkArea(
                targetX, targetY, targetWidth, targetHeight, keep=40
            )

            animatedTarget = QRect(targetX, targetY, targetWidth, targetHeight)

            self._maximized = False
            self._restoredFromMaxOnDrag = True

            def finalize():
                self._restoringFromMaxDrag = False

                # IMPORTANT : recalcul propre de l'offset après l'animation
                finalGlobalTopLeft = self.mapToGlobal(QPoint(0, 0))
                refGlobalPos = self._pendingDragGlobalPos if self._pendingDragGlobalPos is not None else globalPos
                self._dragOffset = refGlobalPos - finalGlobalTopLeft

            self.animateToGeometry(animatedTarget, duration=160, onFinished=finalize)
            self.setStyleSheet(self._styleNormal)
            self.titlebar.btnMax.setText("△")
            self._pendingDragGlobalPos = None
            return

        # 2) Si snappée -> restore une seule fois
        if self.isSnapped() and not self._restoredFromSnapOnDrag:
            self.restoreNormalGeometry()
            self.setSnapKind(None)

            w = self.width()
            p = parent.mapFromGlobal(globalPos)

            newX = int(p.x() - self.ratioX * w)
            newY = int(p.y() - self.titlebar.height() / 2)

            newX, newY = self._clampTopLevelPosToWorkArea(
                newX, newY, self.width(), self.height(), keep=40
            )

            self.move(newX, newY)

            topLeftGlobal = self.mapToGlobal(QPoint(0, 0))
            self._dragOffset = globalPos - topLeftGlobal

            self._restoredFromSnapOnDrag = True
            return

        # 3) Drag normal
        newTopLeftGlobal = globalPos - self._dragOffset
        newPos = parent.mapFromGlobal(newTopLeftGlobal)

        w, h = self.width(), self.height()
        x, y = self._clampTopLevelPosToWorkArea(
            newPos.x(), newPos.y(), w, h, keep=40
        )

        self.move(x, y)

        topLeftGlobal = self.mapToGlobal(QPoint(0, 0))
        self._dragOffset = globalPos - topLeftGlobal

        if not self._maximized and not self.isSnapped():
            self._normalGeometry = self.geometry()

    def _onDragEnded(self):
        self._dragging = False
        self._restoredFromMaxOnDrag = False
        self._restoredFromSnapOnDrag = False
    
    def _buildFrameStyles(self):
        p = theme.palette

        self._styleNormal = f"""
            #WindowFrame {{
                background: rgba(20, 20, 25, 0.9);
                border: 1px solid {p.panelBorder};
                border-radius: 6px;
            }}
        """

        self._styleSnapped = f"""
            #WindowFrame {{
                background: rgba(20, 20, 25, 0.9);
                border: 1px solid {p.panelBorder};
                border-radius: 0;
            }}
        """

        self._styleMaximized = """
            #WindowFrame {
                background: rgba(20, 20, 25, 0.9);
                border: none;
                border-radius: 0;
            }
        """

    def _installContentFocusProxy(self, root: QWidget):
        root.installEventFilter(self)
        for child in root.findChildren(QWidget):
            child.installEventFilter(self)

    def _ensureWindowFocused(self):
        parent = self.parentWidget()
        if parent is not None and hasattr(parent, "focusWindow"):
            try:
                parent.focusWindow(self.meta.id) # type: ignore
                return
            except Exception:
                pass

        self.requestedFocus.emit(self.meta.id)

    def _finalizeVisualState(self):
        self._opacity.setOpacity(1.0 if self._active else 0.7)
        self.setStyleSheet(
            self._styleMaximized if self._maximized else
            self._styleSnapped if self.isSnapped() else
            self._styleNormal
        )

    def setFrameTitle(self, title: str):
        self.meta.title = title
        self.titlebar.setTitle(title)

        parent = self.parentWidget()
        if parent is not None and hasattr(parent, "kernel"):
            parent.kernel.bus.emit( # type: ignore
                "window.updated",
                id=self.meta.id,
                title=self.meta.title,
                icon=self.meta.icon
            )

    def setFrameIcon(self, icon):
        self.meta.icon = icon
        self.titlebar.setIcon(icon)

        parent = self.parentWidget()
        if parent is not None and hasattr(parent, "kernel"):
            parent.kernel.bus.emit( # type: ignore
                "window.updated",
                id=self.meta.id,
                title=self.meta.title,
                icon=self.meta.icon
            )

    def updateFrame(self, *, title=None, icon=None):
        if title is not None:
            self.meta.title = title
            self.titlebar.setTitle(title)

        if icon is not None:
            self.meta.icon = icon
            self.titlebar.setIcon(icon)

        parent = self.parentWidget()
        if parent is not None and hasattr(parent, "kernel"):
            parent.kernel.bus.emit( # type: ignore
                "window.updated",
                id=self.meta.id,
                title=self.meta.title,
                icon=self.meta.icon
            )

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and not self._maximized:
            edge = self._hitTestResizeEdge(e.position().toPoint())
            if edge is not None:
                self._resizing = True
                self._resizeEdge = edge
                self._pressGlobal = e.globalPosition().toPoint()
                self._startGeom = self.geometry()
                self.requestedFocus.emit(self.meta.id)
                e.accept()
                return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._resizing:
            self._applyResizeFromGlobal(e.globalPosition().toPoint())
            e.accept()
            return

        edge = self._hitTestResizeEdge(e.position().toPoint())
        self.setCursor(self._cursorForEdge(edge))
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._resizing:
            self._resizing = False
            self._resizeEdge = None
            print(f'New geometry of "{self.meta.title} ({self.meta.id})": {self.geometry().width()}x{self.geometry().height()}')
            self.unsetCursor()
            e.accept()
            return
        super().mouseReleaseEvent(e)

    def setActive(self, active: bool):
        self._active = active

        # Ne surtout pas stopper les animations structurelles ici
        # (sinon animateOpen / animateRestore sont cassées).
        if self._animGroup is None:
            self._opacity.setOpacity(1.0 if active else 0.7)

        self._opacity.setOpacity(1.0 if active else 0.7)
        self.setStyleSheet(self._styleMaximized if self._maximized else
                           self._styleSnapped if self.isSnapped() else self._styleNormal)
    
    def _isMaximized(self) -> bool:
        return self._maximized
    
    def _parentWorkArea(self) -> QRect:
        parent = self.parentWidget()
        if parent is None:
            return self.geometry()

        if hasattr(parent, "workingArea"):
            try:
                area = parent.workingArea() # type: ignore
                if isinstance(area, QRect) and area.isValid():
                    return area
            except Exception:
                pass

        return parent.rect()

    def _clampTopLevelPosToWorkArea(self, x: int, y: int, w: int, h: int, keep: int = 40) -> tuple[int, int]:
        area = self._parentWorkArea()

        minX = area.left() - w + keep
        maxX = area.right() - keep + 1
        minY = area.top()
        maxY = area.bottom() - keep + 1

        x = max(minX, min(x, maxX))
        y = max(minY, min(y, maxY))
        return x, y

    def applyMaximizedGeometry(self):
        area = self._parentWorkArea()
        m = self._maxMargin

        self.setGeometry(
            area.left() + m,
            area.top() + m,
            max(0, area.width() - 2 * m),
            max(0, area.height() - 2 * m)
        )

    def maximizedGeometry(self) -> QRect:
        area = self._parentWorkArea()
        m = self._maxMargin

        return QRect(
            area.left() + m,
            area.top() + m,
            max(0, area.width() - 2 * m),
            max(0, area.height() - 2 * m)
        )

    def snappedGeometryForKind(self, kind: str) -> QRect:
        area = self._parentWorkArea()
        m = self._maxMargin

        innerLeft = area.left() + m
        innerTop = area.top() + m
        innerWidth = max(0, area.width() - 2 * m)
        innerHeight = max(0, area.height() - 2 * m)

        halfW = max(0, innerWidth // 2)
        halfH = max(0, innerHeight // 2)

        if kind == "left":
            return QRect(innerLeft, innerTop, halfW, innerHeight)

        if kind == "right":
            return QRect(
                innerLeft + innerWidth - halfW,
                innerTop,
                halfW,
                innerHeight
            )

        if kind == "top_left":
            return QRect(innerLeft, innerTop, halfW, halfH)

        if kind == "top_right":
            return QRect(
                innerLeft + innerWidth - halfW,
                innerTop,
                halfW,
                halfH
            )

        if kind == "bottom_left":
            return QRect(
                innerLeft,
                innerTop + innerHeight - halfH,
                halfW,
                halfH
            )

        if kind == "bottom_right":
            return QRect(
                innerLeft + innerWidth - halfW,
                innerTop + innerHeight - halfH,
                halfW,
                halfH
            )

        return self.geometry()
    
    def maximize(self):
        if self._maximized:
            return
        self._restoreGeom = self.geometry()
        
        # IMPORTANT:
        # on ne met à jour normalGeometry que si la fenêtre n'est ni snappée ni déjà maximisée
        if not self.isSnapped():
            self._normalGeometry = self.geometry()

        self._maximized = True
        self._snapKind = None
        self.unsetCursor()
        self.animateToGeometry(self.maximizedGeometry(), self._animDuration)
        self.setStyleSheet(self._styleMaximized)
        self.titlebar.btnMax.setText("◇")
    
    def restore(self):
        if not self._maximized:
            return

        self.setActive(True)

        if self._normalGeometry is not None and not self._normalGeometry.isNull():
            g = self._normalGeometry
            x, y = self._clampTopLevelPosToWorkArea(g.x(), g.y(), g.width(), g.height(), keep=40)
            target = QRect(x, y, g.width(), g.height())
            self.animateToGeometry(target, self._animDuration)

        self._maximized = False
        self.setStyleSheet(self._styleNormal)
        self.titlebar.btnMax.setText("△")

    def toggleMaximize(self):
        self.setActive(True)
        if self._maximized:
            self.restore()
        else:
            self.maximize()

    def isSnapped(self) -> bool:
        return self._snapKind is not None

    def setSnapKind(self, kind: str | None):
        self._snapKind = kind

    def snapKind(self):
        return self._snapKind

    def applySnappedGeometry(self):
        if not self.isSnapped():
            return

        self.setGeometry(self.snappedGeometryForKind(self._snapKind)) # type: ignore

    def saveNormalGeometry(self):
        if not self._maximized and not self.isSnapped():
            self._normalGeometry = self.geometry()

    def restoreNormalGeometry(self):
        if self._normalGeometry is not None and not self._normalGeometry.isNull():
            self.setGeometry(self._normalGeometry)

    def _hitTestResizeEdge(self, pos) -> str | None:
        """Retourne l'edge/corner ciblé par la souris, ou None."""
        if self._maximized:
            return None

        m = self._resizeMargin
        r = self.rect()

        left = pos.x() <= m
        right = pos.x() >= r.width() - m
        top = pos.y() <= m
        bottom = pos.y() >= r.height() - m

        if top and left:
            return "tl"
        if top and right:
            return "tr"
        if bottom and left:
            return "bl"
        if bottom and right:
            return "br"
        if left:
            return "l"
        if right:
            return "r"
        if top:
            return "t"
        if bottom:
            return "b"
        return None

    def _cursorForEdge(self, edge: str | None):
        if edge is None:
            return Qt.CursorShape.ArrowCursor
        return {
            "l": Qt.CursorShape.SizeHorCursor,
            "r": Qt.CursorShape.SizeHorCursor,
            "t": Qt.CursorShape.SizeVerCursor,
            "b": Qt.CursorShape.SizeVerCursor,
            "tl": Qt.CursorShape.SizeFDiagCursor,
            "br": Qt.CursorShape.SizeFDiagCursor,
            "tr": Qt.CursorShape.SizeBDiagCursor,
            "bl": Qt.CursorShape.SizeBDiagCursor,
        }.get(edge, Qt.CursorShape.ArrowCursor)

    def _applyResizeFromGlobal(self, globalPos: QPoint):
        parent = self.parentWidget()
        if not parent:
            return
        
        area = self._parentWorkArea()
        parentLeft = area.left()
        parentTop = area.top()
        parentRight = area.right()
        parentBottom = area.bottom()

        dx = globalPos.x() - self._pressGlobal.x()
        dy = globalPos.y() - self._pressGlobal.y()

        g0 = self._startGeom
        edge = self._resizeEdge

        # On travaille en bords (plus fiable)
        left = g0.left()
        top = g0.top()
        right = g0.right()
        bottom = g0.bottom()

        # Ajustements selon l'edge
        if edge in ("l", "tl", "bl"):
            left = left + dx
        if edge in ("r", "tr", "br"):
            right = right + dx
        if edge in ("t", "tl", "tr"):
            top = top + dy
        if edge in ("b", "bl", "br"):
            bottom = bottom + dy

        # Min size (on corrige le côté manipulé)
        minW = self._minW
        minH = self._minH

        if (right - left + 1) < minW:
            if edge in ("l", "tl", "bl"):
                left = right - (minW - 1)
            else:
                right = left + (minW - 1)

        if (bottom - top + 1) < minH:
            if edge in ("t", "tl", "tr"):
                top = bottom - (minH - 1)
            else:
                bottom = top + (minH - 1)

        # Clamp left/top
        if left < parentLeft:
            # si on tire à gauche, on bloque le left, sans bouger le right
            if edge in ("l", "tl", "bl"):
                left = parentLeft
            else:
                # si on tire à droite, déplacer tout le rect serait bizarre => on bloque via right
                pass

        if top < parentTop:
            if edge in ("t", "tl", "tr"):
                top = parentTop
            else:
                pass

        # Clamp right/bottom
        if right >= parentRight:
            if edge in ("r", "tr", "br"):
                right = parentRight - 1
            else:
                pass

        if bottom >= parentBottom:
            if edge in ("b", "bl", "br"):
                bottom = parentBottom - 1
            else:
                pass

        # Re-check min size après clamp
        if (right - left + 1) < minW:
            # on privilégie le côté manipulé
            if edge in ("l", "tl", "bl"):
                left = max(parentLeft, right - (minW - 1))
            else:
                right = min(parentRight - 1, left + (minW - 1))

        if (bottom - top + 1) < minH:
            if edge in ("t", "tl", "tr"):
                top = max(parentTop, bottom - (minH - 1))
            else:
                bottom = min(parentBottom - 1, top + (minH - 1))

        # Construire le QRect final
        newW = right - left + 1
        newH = bottom - top + 1
        self.setGeometry(left, top, newW, newH)
        if not self._maximized and not self.isSnapped():
            self._normalGeometry = self.geometry()

    def _enableMouseTrackingRecursive(self, w):
        w.setMouseTracking(True)
        w.installEventFilter(self)
        for child in w.findChildren(QWidget):
            child.setMouseTracking(True)
            child.installEventFilter(self)

    def eventFilter(self, obj, event):
        # On veut que le survol sur le contenu mette à jour le curseur
        if self._maximized:
            # Même maximisée, un FocusIn dans le contenu doit réactiver la fenêtre
            if event.type() == event.Type.FocusIn:
                self._ensureWindowFocused()
            return super().eventFilter(obj, event)

        t = event.type()

        # 0) Si un widget enfant reçoit le focus, la fenêtre doit redevenir active
        if t == event.Type.FocusIn:
            self._ensureWindowFocused()
            return False

        # 1) Survol / mouvement => mettre à jour le curseur même si c'est un child
        if t in (event.Type.MouseMove, event.Type.HoverMove):
            try:
                gp = event.globalPosition().toPoint()
            except Exception:
                return super().eventFilter(obj, event)

            lp = self.mapFromGlobal(gp)

            # Si on resize, on ignore le cursor logic (le resize code gère déjà)
            if not self._resizing:
                edge = self._hitTestResizeEdge(lp)
                self.setCursor(self._cursorForEdge(edge))
            return False

        # 2) Press sur un child proche d'un bord => démarrer resize depuis WindowFrame
        if t == event.Type.MouseButtonPress and hasattr(event, "button"):
            if event.button() == Qt.MouseButton.LeftButton and not self._resizing:
                gp = event.globalPosition().toPoint()
                lp = self.mapFromGlobal(gp)
                edge = self._hitTestResizeEdge(lp)

                # Toujours réactiver la fenêtre sur clic dans le contenu
                self._ensureWindowFocused()

                if edge is not None:
                    self._resizing = True
                    self._resizeEdge = edge
                    self._pressGlobal = gp
                    self._startGeom = self.geometry()
                    return True  # on consomme seulement si resize

                return False
        
        event.accept()

        return super().eventFilter(obj, event)

    def _stopAnimations(self):
        if self._animGroup is not None:
            try:
                self._animGroup.stop()
            except Exception:
                pass
            self._animGroup = None

        # Recaler l'opacité sur l'état logique courant
        if hasattr(self, "_opacity"):
            self._opacity.setOpacity(1.0 if self._active else 0.7)

    def _currentInactiveOpacity(self) -> float:
        return 1.0 if getattr(self, "_active", True) else 0.7

    def animateOpen(self):
        self._stopAnimations()

        endGeom = self.geometry()
        startGeom = QRect(endGeom.x(), endGeom.y() + 8, endGeom.width(), endGeom.height())

        self.setGeometry(startGeom)
        self._opacity.setOpacity(0.0)
        self.show()

        geoAnim = QPropertyAnimation(self, b"geometry")
        geoAnim.setDuration(self._animDuration)
        geoAnim.setStartValue(startGeom)
        geoAnim.setEndValue(endGeom)
        geoAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        opacityAnim = QPropertyAnimation(self._opacity, b"opacity")
        opacityAnim.setDuration(self._animDuration)
        opacityAnim.setStartValue(0.0)
        opacityAnim.setEndValue(self._currentInactiveOpacity())
        opacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(geoAnim)
        group.addAnimation(opacityAnim)

        self._animGroup = group
        group.finished.connect(self._onAnimationFinished)
        group.start()

    def animateRestore(self):
        self._stopAnimations()

        endGeom = self.geometry()
        startGeom = QRect(endGeom.x(), endGeom.y() + 8, endGeom.width(), endGeom.height())

        self.setGeometry(startGeom)
        self._opacity.setOpacity(0.0)
        self.show()

        geoAnim = QPropertyAnimation(self, b"geometry")
        geoAnim.setDuration(self._animDuration)
        geoAnim.setStartValue(startGeom)
        geoAnim.setEndValue(endGeom)
        geoAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        opacityAnim = QPropertyAnimation(self._opacity, b"opacity")
        opacityAnim.setDuration(self._animDuration)
        opacityAnim.setStartValue(0.0)
        opacityAnim.setEndValue(self._currentInactiveOpacity())
        opacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(geoAnim)
        group.addAnimation(opacityAnim)

        self._animGroup = group
        group.finished.connect(self._onAnimationFinished)
        group.start()

    def animateMinimize(self, onFinished=None):
        self._stopAnimations()

        self._preMinimizeGeometry = self.geometry()

        startGeom = self.geometry()
        endGeom = QRect(startGeom.x(), startGeom.y() + 10, startGeom.width(), startGeom.height())

        geoAnim = QPropertyAnimation(self, b"geometry")
        geoAnim.setDuration(175)
        geoAnim.setStartValue(startGeom)
        geoAnim.setEndValue(endGeom)
        geoAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        opacityAnim = QPropertyAnimation(self._opacity, b"opacity")
        opacityAnim.setDuration(175)
        opacityAnim.setStartValue(self._opacity.opacity())
        opacityAnim.setEndValue(0.0)
        opacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(geoAnim)
        group.addAnimation(opacityAnim)

        def done():
            self._onAnimationFinished()
            if onFinished is not None:
                onFinished()

        self._animGroup = group
        group.finished.connect(done)
        group.start()

    def animateClose(self, onFinished=None):
        self._stopAnimations()

        startGeom = self.geometry()
        endGeom = QRect(startGeom.x(), startGeom.y() + 12, startGeom.width(), startGeom.height())

        geoAnim = QPropertyAnimation(self, b"geometry")
        geoAnim.setDuration(175)
        geoAnim.setStartValue(startGeom)
        geoAnim.setEndValue(endGeom)
        geoAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        opacityAnim = QPropertyAnimation(self._opacity, b"opacity")
        opacityAnim.setDuration(175)
        opacityAnim.setStartValue(self._opacity.opacity())
        opacityAnim.setEndValue(0.0)
        opacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(geoAnim)
        group.addAnimation(opacityAnim)

        def done():
            self._onAnimationFinished()
            if onFinished is not None:
                onFinished()

        self._animGroup = group
        group.finished.connect(done)
        group.start()

    def animateToGeometry(self, targetGeom: QRect, duration: int = 150, onFinished=None):
        if self.geometry() == targetGeom:
            if onFinished is not None:
                onFinished()
            return
        
        self._stopAnimations()

        startGeom = self.geometry()

        geoAnim = QPropertyAnimation(self, b"geometry")
        geoAnim.setDuration(duration)
        geoAnim.setStartValue(startGeom)
        geoAnim.setEndValue(targetGeom)
        geoAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(geoAnim)

        def done():
            self._onAnimationFinished()
            if onFinished is not None:
                onFinished()

        self._animGroup = group
        group.finished.connect(done)
        group.start()

    def _onAnimationFinished(self):
        self._animGroup = None
        self._finalizeVisualState()

