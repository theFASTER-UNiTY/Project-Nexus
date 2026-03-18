from core.SystemInfo import SystemInfo
from PySide6.QtWebEngineWidgets import QWebEngineView

class AppExtension:
    systemInfo = SystemInfo()
    appId = "app"
    name = "Application"
    version = "1.0.0"
    description = ""
    icon = None


    def __init__(self, kernel):
        self.kernel = kernel
        self.api = kernel.api
        self.windows = self.kernel.services.get("windows")
        self.webview = QWebEngineView()

    def onLoad(self):
        pass

    def onEnable(self):
        pass

    def onDisable(self):
        pass

    def launch(self):
        raise NotImplementedError