from dataclasses import dataclass


@dataclass
class Metrics:
    radiusS: int
    radiusM: int
    radiusL: int
    radiusXL: int

    paddingXS: int
    paddingS: int
    paddingM: int
    paddingL: int
    paddingXL: int

    spacingS: int
    spacingM: int
    spacingL: int

    taskbarHeight: int
    titlebarHeight: int
    windowButtonSize: int
    desktopIconWidth: int
    desktopIconHeight: int


defaultMetrics = Metrics(
    radiusS=6,
    radiusM=8,
    radiusL=10,
    radiusXL=12,

    paddingXS=2,
    paddingS=4,
    paddingM=6,
    paddingL=8,
    paddingXL=12,

    spacingS=4,
    spacingM=8,
    spacingL=12,

    taskbarHeight=48,
    titlebarHeight=36,
    windowButtonSize=24,
    desktopIconWidth=92,
    desktopIconHeight=100,
)