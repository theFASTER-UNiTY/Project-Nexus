from __future__ import annotations

from PySide6.QtCore import (
    Qt, QEasingCurve, QPropertyAnimation, QParallelAnimationGroup, QRect, QDateTime, QLocale,
    QTimer
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QCalendarWidget, QGraphicsOpacityEffect,
    QGraphicsDropShadowEffect
)


class ClockPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._animGroup = None
        self._animDuration = 140

        # self.setObjectName("ClockPanel")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.hide()

        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        self._blockShadow = QGraphicsDropShadowEffect(self)
        self._blockShadow.setBlurRadius(24)
        self._blockShadow.setOffset(0, 4)
        self._blockShadow.setColor(QColor(0, 0, 0, 90))

        # Bloc 1 : heure + date
        self.timeBlock = QFrame()
        self.timeBlock.setObjectName("ClockPanelTimeBlock")
        # self.timeBlock.setGraphicsEffect(self._blockShadow)

        timeLayout = QVBoxLayout(self.timeBlock)
        timeLayout.setContentsMargins(14, 14, 14, 14)
        timeLayout.setSpacing(2)

        self.timeLabel = QLabel()
        self.timeLabel.setObjectName("ClockPanelTimeLabel")
        self.timeLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.dateLabel = QLabel()
        self.dateLabel.setObjectName("ClockPanelDateLabel")
        self.dateLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        timeLayout.addWidget(self.timeLabel)
        timeLayout.addWidget(self.dateLabel)

        # Bloc 2 : calendrier
        self.calendarBlock = QFrame()
        self.calendarBlock.setObjectName("ClockPanelCalendarBlock")
        # self.calendarBlock.setGraphicsEffect(self._blockShadow)

        calendarLayout = QVBoxLayout(self.calendarBlock)
        calendarLayout.setContentsMargins(12, 12, 12, 12)
        calendarLayout.setSpacing(0)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(False)
        self.calendar.setNavigationBarVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setSelectedDate(QDateTime.currentDateTime().date())

        calendarLayout.addWidget(self.calendar)

        root.addWidget(self.timeBlock)
        root.addWidget(self.calendarBlock, 1)

        self.refreshDateTime()
        self._dateTimeTimer = QTimer(self)
        self._dateTimeTimer.timeout.connect(self.refreshDateTime)
        self._dateTimeTimer.start(100)

    def refreshDateTime(self):
        now = QDateTime.currentDateTime()
        locale = QLocale.system()

        self.timeLabel.setText(now.toString("HH:mm:ss"))
        self.dateLabel.setText(locale.toString(now.date(), QLocale.FormatType.LongFormat))

    def _stopAnimations(self):
        if self._animGroup is not None:
            try:
                self._animGroup.stop()
            except Exception:
                pass
            self._animGroup = None

    def animateShow(self):
        self._stopAnimations()
        self.refreshDateTime()

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
