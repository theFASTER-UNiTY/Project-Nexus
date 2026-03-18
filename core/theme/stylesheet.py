from .palette import Palette
from .metrics import Metrics


def buildStylesheet(p: Palette, m: Metrics) -> str:
    return f"""
    QWidget {{
        color: {p.text};
    }}

    #Taskbar {{
        background: {p.taskbarBg};
        border-top: 1px solid {p.taskbarBorder};
    }}

    QPushButton#TaskbarStartButton {{
        background: transparent;
        border: none;
        color: {p.text};
        border-radius: {m.radiusL}px;
        padding: {m.paddingM}px {m.paddingXL}px;
    }}

    QPushButton#TaskbarStartButton:hover {{
        background: {p.hover};
    }}

    QPushButton#TaskbarStartButton[opened="true"] {{
        background: {p.accent};
        border: none;
        color: {p.text};
        border-radius: {m.radiusL}px;
        padding: {m.paddingM}px {m.paddingXL}px;
        font-weight: 600;
    }}

    QPushButton#TaskbarStartButton[opened="true"]:hover {{
        background: {p.accentSoft};
        border: 1px solid {p.accent};
        color: {p.accent}
    }}

    QPushButton#TaskbarOverflowButton {{
        background: {p.surface};
        border: 1px solid rgba(255,255,255,0.12);
        color: {p.text};
        border-radius: {m.radiusL}px;
        padding: 6px 10px;
        font-weight: 700;
    }}

    QPushButton#TaskbarOverflowButton:hover {{
        background: {p.pressed};
    }}

    QPushButton[taskbarWindowButton="true"] {{
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.12);
        color: {p.text};
        border-radius: 10px;
        padding: 6px 12px;
        text-align: left;
    }}

    QPushButton[taskbarWindowButton="true"]:hover {{
        background: rgba(255,255,255,0.16);
    }}

    QPushButton[taskbarWindowButton="true"][active="true"] {{
        background: rgba(255,255,255,0.22);
        border: 1px solid rgba(255,255,255,0.24);
    }}

    QPushButton[taskbarWindowButton="true"][minimized="true"] {{
        background: rgba(255,255,255,0.06);
        color: {p.textMuted};
    }}

    QLabel#TaskbarStatusLabel {{
        color: {p.textDim};
    }}

    QFrame#TaskbarClockWidget {{
        background: transparent;
        border-radius: {m.radiusM}px;
    }}

    QFrame#TaskbarClockWidget:hover {{
        background: {p.surface};
    }}

    QLabel#TaskbarTimeLabel,
    QLabel#TaskbarDateLabel {{
        color: {p.textDim};
    }}

    #TitleBar {{
        background: rgba(255, 255, 255, 0.06);
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    }}

    QLabel#WindowTitle {{
        color: {p.text};
        font-size: 12px;
    }}

    QPushButton#WinBtn,
    QPushButton#WinBtnClose {{
        padding: 0;
        text-align: center;
        background: transparent;
        border: none;
        color: {p.text};
        border-radius: 12px;
    }}

    QPushButton#WinBtn:hover {{
        background: rgba(255,255,255,0.16);
        border: 1px solid rgba(255,255,255,0.14);
    }}

    QPushButton#WinBtnClose:hover {{
        background: rgba(255,70,70,0.65);
        border: 1px solid rgba(255,90,90,0.85);
    }}

    QFrame#ClockPanel {{
        background: rgba(18,18,24,0.96);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
    }}

    QFrame#ClockPanelTimeBlock,
    QFrame#ClockPanelCalendarBlock {{
        background: rgba(18,18,24,0.80);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        /* backdrop-blur: 20px; */
    }}

    QLabel#ClockPanelTimeLabel {{
        color: {p.text};
        font-size: 28px;
        font-weight: 700;
    }}

    QLabel#ClockPanelDateLabel {{
        color: {p.textDim};
        font-size: 12px;
    }}

    QCalendarWidget {{
        background-color: transparent;
        border-radius: 6px;
    }}

    QCalendarWidget QWidget {{
        alternate-background-color: transparent;
    }}

    #qt_calendar_navigationbar {{
        background-color: transparent;
        border: none;
    }}

    #qt_calendar_prevmonth,
    #qt_calendar_nextmonth {{
        border-radius: 5px;
        background-color: rgba(255, 255, 255, 0.1);
    }}

    #qt_calendar_prevmonth:hover,
    #qt_calendar_nextmonth:hover {{
        border-radius: 5px;
        background-color: rgba(255, 255, 255, 0.15);
    }}

    #qt_calendar_yearedit {{
        margin-left: 5px;
        max-width: 75px;
    }}

    #qt_calendar_yearedit::up-button {{
        subcontrol-position: left;
    }}

    #qt_calendar_yearedit::down-button {{
        subcontrol-position: right;
    }}

    #qt_calendar_calendarview {{
        border-radius: 5px;
        background: transparent;
    }}

    #qt_calendar_calendarview::item:hover {{
        border-radius: 5px;
        background-color: rgba(255, 255, 255, 0.1);
    }}

    #qt_calendar_calendarview::item:selected {{
        border-radius: 5px;
        background-color: rgba(255, 255, 255, 0.15);
    }}

    QCalendarWidget QToolButton {{
        color: {p.text};
        background: transparent;
        border: none;
        padding: 6px;
    }}

    QCalendarWidget QToolButton::menu-indicator {{
        image: none;
    }}

    QCalendarWidget QToolButton:hover {{
        background: rgba(255,255,255,0.10);
        border-radius: 8px;
    }}

    QCalendarWidget QMenu {{
        background: rgba(22,22,28,0.96);
        color: {p.text};
        border: 1px solid rgba(255,255,255,0.10);
    }}

    QCalendarWidget QSpinBox {{
        color: {p.text};
        background: transparent;
        border: none;
    }}

    QCalendarWidget QAbstractItemView:enabled {{
        color: {p.text};
        background: transparent;
        selection-background-color: rgba(140,180,255,0.5);
        selection-color: white;
    }}

    #DesktopIcon {{
        background: transparent;
        border-radius: 10px;
    }}

    #DesktopIcon[selected="true"] {{
        background: rgba(255, 255, 255, 0.16);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }}

    #DesktopIconImage {{
        background: transparent;
    }}

    #DesktopIconText {{
        background: transparent;
        color: {p.text};
        font-size: 12px;
    }}

    QPushButton#NexHubAppItem {{
        text-align: left;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.05);
    }}

    QPushButton#NexHubAppItem:hover {{
        background: rgba(255,255,255,0.11);
        border: 1px solid rgba(255,255,255,0.14);
    }}

    QPushButton#NexHubAppItem[selected="true"] {{
        border: 1px solid rgba(140,180,255,0.55);
        background: rgba(140,180,255,0.16);
    }}

    QPushButton#NexHubAppItem[selected="true"]:hover {{
        background: rgba(140,180,255,0.22);
    }}

    QLabel#NexHubAppItemIcon {{
        background: transparent;
        border-radius: 8px;
    }}

    QLabel#NexHubAppItemTitle {{
        color: {p.text};
        font-size: 13px;
        font-weight: 600;
    }}

    QLabel#NexHubAppItemSubtitle {{
        color: {p.textDim};
        font-size: 11px;
    }}

    QFrame#NexHubPanel {{
        background: {p.panelBg};
        border: 1px solid {p.panelBorder};
        border-radius: 16px;
    }}

    QLabel#NexHubTitle {{
        color: {p.text};
        font-size: 18px;
        font-weight: 700;
    }}

    QPushButton#NexHubCloseButton{{
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.10);
        color: {p.text};
        border-radius: 8px;
    }}

    QPushButton#NexHubCloseButton:hover {{
        background: rgba(255,255,255,0.15);
    }}

    QLineEdit#NexHubSearchEdit {{
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 10px;
        padding: 10px 12px;
        color: {p.text};
        selection-background-color: rgba(120,160,255,0.45);
    }}

    QLabel#NexHubSectionLabel {{
        color: {p.textMuted};
        font-size: 12px;
        font-weight: 600;
    }}

    QWidget#ListHost {{
        background: transparent;
    }}

    QFrame#NexHubProfileSection {{
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
    }}

    QLabel#NexHubUserNameLabel {{
        color: {p.text};
        font-size: 13px;
        font-weight: 600;
    }}

    QLabel#NexHubUserStatusLabel {{
        color: {p.textDim};
        font-size: 11px;
    }}

    QPushButton#NexHubPowerButton {{
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.10);
        color: {p.text};
        border-radius: 10px;
        padding: 8px 12px;
    }}

    QPushButton#NexHubPowerButton:hover {{
        background: rgba(255,255,255,0.14);
    }}

    QPushButton#SnapAssistCard {{
        text-align: left;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.06);
        color: {p.text};
    }}

    QPushButton#SnapAssistCard:hover {{
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
    }}

    QPushButton#SnapAssistCard[selected="true"] {{
        border: 1px solid rgba(140,180,255,0.55);
        background: rgba(140,180,255,0.16);
    }}
    
    QLabel#SnapAssistCardTitle {{
        color: {p.text};
        font-size: 13px;
        font-weight: 500;
    }}
    
    QLabel#SnapAssistThumb {{
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        color: {p.textDim};
    }}

    #SnapAssistPanel {{
        background: rgba(18, 18, 24, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
    }}
    
    QLabel#SnapAssistTitle {{
        color: {p.text};
        font-size: 15px;
        font-weight: 600;
    }}
    
    QLabel#SnapAssistSubtitle {{
        color: {p.textDim};
        font-size: 12px;
    }}
    
    QWidget#SnapAssistBox {{
        background: rgba(18, 18, 24, 0.9);
        border-radius: 10px;
    }}
    
    QPushButton {{
        text-align: center;
        padding: 12px 14px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.10);
        background: rgba(255, 255, 255, 0.06);
        color: {p.text};
    }}
    
    QPushButton:hover {{
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }}

    QScrollArea {{
        background: transparent;
        border: none;
    }}

    QMenu {{
        background: {p.panelBg};
        border: 1px solid {p.panelBorder};
        border-radius: {m.radiusM}px;
        color: {p.text};
        padding: 6px;
    }}

    QMenu::item {{
        padding: 8px 18px;
        border-radius: {m.radiusM}px;
    }}

    QMenu::item:selected {{
        background: {p.hover};
    }}
    """
