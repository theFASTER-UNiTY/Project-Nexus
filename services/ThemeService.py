from __future__ import annotations

from copy import deepcopy

from core.Service import Service


class ThemeService(Service):
    name = "theme"

    DEFAULT_THEME_STATE = {
        "scheme": "dark",
        "accent": "blue",
        "fontScale": 1.0,
    }

    def __init__(self, kernel):
        self.kernel = kernel
        self.app = None

    def start(self):
        if "theme" not in self.kernel.state or not isinstance(self.kernel.state["theme"], dict):
            self.kernel.state["theme"] = deepcopy(self.DEFAULT_THEME_STATE)
        else:
            for key, value in self.DEFAULT_THEME_STATE.items():
                self.kernel.state["theme"].setdefault(key, value)

    def bindApp(self, app):
        self.app = app

    def state(self) -> dict:
        return self.kernel.state["theme"]

    def getScheme(self) -> str:
        return self.state().get("scheme", "dark")

    def getAccent(self) -> str:
        return self.state().get("accent", "blue")

    def getFontScale(self) -> float:
        try:
            return float(self.state().get("fontScale", 1.0))
        except Exception:
            return 1.0

    def setTheme(self, *, scheme=None, accent=None, fontScale=None, emit=True):
        changed = False
        s = self.state()

        if scheme is not None and s.get("scheme") != scheme:
            s["scheme"] = scheme
            changed = True

        if accent is not None and s.get("accent") != accent:
            s["accent"] = accent
            changed = True

        if fontScale is not None:
            try:
                fontScale = float(fontScale)
            except Exception:
                fontScale = 1.0

            if s.get("fontScale") != fontScale:
                s["fontScale"] = fontScale
                changed = True

        if changed and emit:
            self.applyTheme()

        return changed

    def applyTheme(self):
        if self.app is None:
            print("Set theme failed...")
            return

        from core.theme.theme import theme
        theme.apply(self.app, self.kernel)

        if hasattr(self.kernel, "bus") and self.kernel.bus is not None:
            self.kernel.bus.emit(
                "theme.changed",
                theme=self.state().copy()
            )

    def availableSchemes(self) -> list[str]:
        from core.theme.palette import PALETTES
        return list(PALETTES.keys())

    def availableAccents(self) -> list[str]:
        from core.theme.palette import ACCENTS
        return list(ACCENTS.keys())
