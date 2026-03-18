from dataclasses import dataclass


@dataclass
class Palette:
    desktopBg: str
    panelBg: str
    panelBgAlt: str
    panelBorder: str

    taskbarBg: str
    taskbarBorder: str

    surface: str
    surfaceAlt: str
    hover: str
    pressed: str

    accent: str
    accentSoft: str
    accentBorder: str

    text: str
    textDim: str
    textMuted: str


darkPalette = Palette(
    desktopBg="#111111",

    panelBg="rgba(18,18,24,0.96)",
    panelBgAlt="rgba(18,18,24,0.80)",
    panelBorder="rgba(255,255,255,0.22)",

    taskbarBg="rgba(20,20,25,0.85)",
    taskbarBorder="rgba(255,255,255,0.10)",

    surface="rgba(255,255,255,0.08)",
    surfaceAlt="rgba(255,255,255,0.05)",
    hover="rgba(255,255,255,0.12)",
    pressed="rgba(255,255,255,0.16)",

    accent="rgba(140,180,255,0.90)",
    accentSoft="rgba(140,180,255,0.16)",
    accentBorder="rgba(140,180,255,0.55)",

    text="white",
    textDim="rgba(255,255,255,0.82)",
    textMuted="rgba(255,255,255,0.65)",
)

lightPalette = Palette(
    desktopBg="#e9edf3",

    panelBg="rgba(250,250,252,0.96)",
    panelBgAlt="rgba(250,250,252,0.80)",
    panelBorder="rgba(0,0,0,0.10)",

    taskbarBg="rgba(245,247,250,0.88)",
    taskbarBorder="rgba(0,0,0,0.08)",

    surface="rgba(0,0,0,0.08)",
    surfaceAlt="rgba(0,0,0,0.05)",
    hover="rgba(0,0,0,0.08)",
    pressed="rgba(0,0,0,0.12)",

    accent="#2f6fff",
    accentSoft="rgba(47,111,255,0.14)",
    accentBorder="rgba(47,111,255,0.38)",

    text="black",
    textDim="rgba(17,24,39,0.78)",
    textMuted="rgba(17,24,39,0.55)",
)

PALETTES = {
    "dark": darkPalette,
    "light": lightPalette
}

ACCENTS = {
    "blue": {
        "accent": "#2196f3",
        "accentSoft": "rgba(110,168,255,0.25)",
        "accentBorder": "rgba(110,168,255,0.50)",
    },
    "violet": {
        "accent": "#8e51ff",
        "accentSoft": "rgba(180,140,255,0.25)",
        "accentBorder": "rgba(180,140,255,0.50)",
    },
    "green": {
        "accent": "#4caf50",
        "accentSoft": "rgba(94,211,138,0.25)",
        "accentBorder": "rgba(94,211,138,0.50)",
    },
}
