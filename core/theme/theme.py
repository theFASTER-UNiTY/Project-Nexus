from __future__ import annotations

from dataclasses import replace

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from .palette import PALETTES, ACCENTS
from .metrics import defaultMetrics
from .stylesheet import buildStylesheet
from .fonts import fonts


class ThemeManager:
    def __init__(self):
        self.palette = PALETTES["dark"]
        self.metrics = defaultMetrics

    def resolvePalette(self, kernel):
        themeState = kernel.state.get("theme", {})
        scheme = themeState.get("scheme", "dark")
        accentName = themeState.get("accent", "blue")

        base = PALETTES.get(scheme, PALETTES["dark"])
        accent = ACCENTS.get(accentName, ACCENTS["blue"])

        return replace(
            base,
            accent=accent["accent"],
            accentSoft=accent["accentSoft"],
            accentBorder=accent["accentBorder"],
        )

    def apply(self, app: QApplication, kernel):
        self.palette = self.resolvePalette(kernel)

        fonts.initDefaults()

        scale = kernel.state.get("theme", {}).get("fontScale", 1.0)
        try:
            scale = float(scale)
        except Exception:
            scale = 1.0

        baseSize = max(8, round(10 * scale))
        fonts.applyAppFont(app, size=baseSize)

        stylesheet = buildStylesheet(self.palette, self.metrics)
        app.setStyleSheet(stylesheet)


theme = ThemeManager()
