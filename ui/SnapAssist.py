from __future__ import annotations

from typing import List, Tuple

from PySide6.QtCore import (
    Qt, Signal, QEasingCurve, QPropertyAnimation, QParallelAnimationGroup, QRect
)
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QGraphicsOpacityEffect, QHBoxLayout, QSizePolicy
)


class SnapAssistCard(QPushButton):
    def __init__(self, title: str, thumbnail: QPixmap | None = None, parent=None):
        super().__init__(parent)

        self.setObjectName("SnapAssistCard")
        self.setProperty("selected", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._selected = False
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._updateStyle()

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        self.thumbLabel = QLabel()
        self.thumbLabel.setFixedSize(160, 100)
        self.thumbLabel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.thumbLabel.setObjectName("SnapAssistThumb")
        self.thumbLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if thumbnail is not None and not thumbnail.isNull():
            self.thumbLabel.setPixmap(
                thumbnail.scaled(
                    self.thumbLabel.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            self.thumbLabel.setText("Aperçu indisponible")

        self.titleLabel = QLabel(title)
        self.titleLabel.setObjectName("SnapAssistCardTitle")
        self.titleLabel.setWordWrap(True)

        root.addWidget(self.thumbLabel)
        root.addWidget(self.titleLabel, 1)

    def setSelected(self, selected: bool):
        self._selected = selected
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def _updateStyle(self):
        self.setSelected(self._selected)


class SnapAssistPanel(QFrame):
    windowChosen = Signal(str)
    requestClose = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("SnapAssistPanel")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)

        self._cards = []
        self._currentIndex = -1
        
        self._animGroup = None
        self._animDuration = 130

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        self.titleLabel = QLabel("Snap Assist")
        self.titleLabel.setObjectName("SnapAssistTitle")

        self.subtitleLabel = QLabel("Choisissez une fenêtre pour remplir l’espace restant")
        self.subtitleLabel.setObjectName("SnapAssistSubtitle")
        self.subtitleLabel.setWordWrap(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameShape(QFrame.Shape.NoFrame)

        self.container = QWidget()
        self.container.setObjectName("SnapAssistBox")
        self.containerLayout = QVBoxLayout(self.container)
        self.containerLayout.setContentsMargins(0, 0, 0, 0)
        self.containerLayout.setSpacing(10)
        self.containerLayout.addStretch(1)

        self.scrollArea.setWidget(self.container)

        root.addWidget(self.titleLabel)
        root.addWidget(self.subtitleLabel)
        root.addWidget(self.scrollArea, 1)

    def clearChoices(self):
        self._cards = []
        self._currentIndex = -1

        while self.containerLayout.count() > 1:
            item = self.containerLayout.takeAt(0)
            w = item.widget() # type: ignore
            if w is not None:
                w.deleteLater()

    def setChoices(self, windows: List[Tuple[str, str, QPixmap | None]]):
        """
        windows: [(windowId, title, thumbnail), ...]
        """
        self.clearChoices()

        self._cards = []
        self._currentIndex = -1

        for window_id, title, thumbnail in windows:
            card = SnapAssistCard(title, thumbnail)

            def on_click(_, wid=window_id):
                self.windowChosen.emit(wid)

            card.clicked.connect(on_click)
            self.containerLayout.insertWidget(self.containerLayout.count() - 1, card)
            self._cards.append(card)

        if self._cards:
            self._setCurrentIndex(0)
        
        self.setFocus()

    def keyPressEvent(self, e):
        key = e.key()

        if key in (Qt.Key.Key_Down, Qt.Key.Key_Right):
            self._moveSelection(1)
            e.accept()
            return

        if key in (Qt.Key.Key_Up, Qt.Key.Key_Left):
            self._moveSelection(-1)
            e.accept()
            return

        if key == Qt.Key.Key_Tab:
            if e.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._moveSelection(-1)
            else:
                self._moveSelection(1)
            e.accept()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self._activateCurrent()
            e.accept()
            return

        if key == Qt.Key.Key_Escape:
            self.requestClose.emit()
            e.accept()
            return

        super().keyPressEvent(e)

    def _stopAnimations(self):
        if self._animGroup is not None:
            try:
                self._animGroup.stop()
            except Exception:
                pass
            self._animGroup = None
        
        if hasattr(self, "_opacity"):
            self._opacity.setOpacity(1.0)

    def animateShow(self):
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
        opacityAnim.setEndValue(1.0)
        opacityAnim.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(geoAnim)
        group.addAnimation(opacityAnim)

        self._animGroup = group
        group.start()

        self.setFocus()

    def animateHide(self, onFinished=None):
        self._stopAnimations()

        startGeom = self.geometry()
        endGeom = QRect(startGeom.x(), startGeom.y() + 8, startGeom.width(), startGeom.height())

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
            if onFinished is not None:
                onFinished()

        group.finished.connect(finalize)

        self._animGroup = group
        group.start()

    def _setCurrentIndex(self, index: int):
        if not self._cards:
            self._currentIndex = -1
            return

        index = max(0, min(index, len(self._cards) - 1))
        self._currentIndex = index

        for i, card in enumerate(self._cards):
            card.setSelected(i == self._currentIndex)

        current = self._cards[self._currentIndex]
        self.scrollArea.ensureWidgetVisible(current)

        # Le panel garde toujours le focus clavier
        self.setFocus()

    def _moveSelection(self, delta: int):
        if not self._cards:
            return

        if self._currentIndex < 0:
            self._setCurrentIndex(0)
            return

        newIndex = (self._currentIndex + delta) % len(self._cards)
        self._setCurrentIndex(newIndex)

    def _activateCurrent(self):
        if 0 <= self._currentIndex < len(self._cards):
            self._cards[self._currentIndex].click()
