from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QFont, QFontMetrics
from PySide6.QtWidgets import QApplication, QLabel


BASE_DIR = Path(__file__).resolve().parents[2]
FONTS_DIR = BASE_DIR / "assets" / "fonts"


class ElidableLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.initText = text
    
    def resizeEvent(self, event):
        metrics = QFontMetrics(self.font())
        self.setText(
            metrics.elidedText(
                self.text(),
                Qt.TextElideMode.ElideRight,
                self.width()
            )
        )
        super().resizeEvent(event)
    
    def setToolTip(self, text: str | None) -> None:
        if text is None: text = self.initText
        super().setToolTip(text)


class FontManager:
    def __init__(self):
        self._loadedFamilies: Dict[str, Optional[str]] = {}
        self.uiFamily: Optional[str] = None
        self.monoFamily: Optional[str] = None

    def loadFont(self, path: str | Path, familyId: int = 0) -> Optional[str]:
        path = Path(path).resolve()
        key = str(path)

        if key in self._loadedFamilies:
            return self._loadedFamilies[key]

        if not path.exists():
            print(f"SmartNexus Fonts: fichier introuvable: {path}")
            self._loadedFamilies[key] = None
            return None

        fontId = QFontDatabase.addApplicationFont(str(path))
        if fontId == -1:
            print(f"SmartNexus Fonts: échec du chargement: {path}")
            self._loadedFamilies[key] = None
            return None

        families = QFontDatabase.applicationFontFamilies(fontId)
        if not families:
            print(f"SmartNexus Fonts: aucune famille détectée: {path}")
            self._loadedFamilies[key] = None
            return None

        family = families[familyId]
        self._loadedFamilies[key] = family
        return family

    def initDefaults(self) -> None:
        self.uiFamily = self.loadFont(FONTS_DIR / "FigtreeVariable.ttf", 2)
        self.monoFamily = self.loadFont(FONTS_DIR / "JetBrainsMono.ttf", 3)

    def applyAppFont(self, app: QApplication, size: int = 10) -> None:
        if self.uiFamily:
            app.setFont(QFont(self.uiFamily, size))

    def uiFont(self, size: int = 10, weight: int = QFont.Weight.Normal) -> QFont:
        f = QFont()
        if self.uiFamily:
            f.setFamily(self.uiFamily)
        f.setPointSize(size)
        f.setWeight(weight) # type: ignore
        return f

    def monoFont(self, size: int = 11, weight: int = QFont.Weight.Normal) -> QFont:
        f = QFont()
        if self.monoFamily:
            f.setFamily(self.monoFamily)
        f.setPointSize(size)
        f.setWeight(weight) # type: ignore
        return f


fonts = FontManager()
