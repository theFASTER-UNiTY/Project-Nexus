import os
from PyQt6.QtCore import QUrl 
from PyQt6.QtWidgets import QLineEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from core.AppExtension import AppExtension

class App(AppExtension):
    appId = "webbrowser"
    name = "NexSurf"
    description = "Navigateur web"
    icon = os.path.join(os.path.dirname(__file__), "icon.png")

    # constructor
    def launch(self):
        self.windowId = ""

        def updateTitle():
            title = self.webview.page().title() # type: ignore
            self.windows.setTitle(self.windowId, f"{title} | NexSurf")
        
        content = QWidget()
        content.setContentsMargins(0, 0, 0, 0)

        contentLayout = QVBoxLayout(content)
        contentLayout.setContentsMargins(0, 0, 0, 0)
        contentLayout.setSpacing(0)

        # creating a tool bar for navigation
        toolbarLayout = QHBoxLayout()
        toolbarLayout.setContentsMargins(0, 0, 0, 0)
        toolbarLayout.setSpacing(4)

        # creating a QWebEngineView
        # from PyQt6.QtWebEngineWidgets import QWebEngineView 
        self.webview.setUrl("http://www.google.com//")
        self.webview.urlChanged.connect(self.updateUrlBar)
        self.webview.loadFinished.connect(updateTitle)

        # adding actions to the tool bar
        self.backBtn = QPushButton("Back")
        self.backBtn.setToolTip("Back to previous page")
        self.backBtn.clicked.connect(self.webview.back)

        self.nextBtn = QPushButton("Forward")
        self.nextBtn.setToolTip("Forward to next page")
        self.nextBtn.clicked.connect(self.webview.forward)

        self.reloadBtn = QPushButton("Reload")
        self.reloadBtn.setToolTip("Reload page")
        self.reloadBtn.clicked.connect(self.webview.reload)

        self.homeBtn = QPushButton("Home")
        self.homeBtn.setToolTip("Back to homepage")
        self.homeBtn.clicked.connect(self.navigateHome)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigateToUrl)

        self.stopBtn = QPushButton("Stop")
        self.stopBtn.setToolTip("Stop loading current page")
        self.stopBtn.clicked.connect(self.webview.stop)

        """ toolbarLayout.addWidget(self.backBtn)
        toolbarLayout.addWidget(self.nextBtn)
        toolbarLayout.addWidget(self.reloadBtn)
        toolbarLayout.addWidget(self.homeBtn)
        toolbarLayout.addWidget(self.urlbar)
        toolbarLayout.addWidget(self.stopBtn) """

        self.webview.setStyleSheet("""
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
        """)

        contentLayout.addLayout(toolbarLayout)
        # contentLayout.addWidget(self.toolbar)
        # contentLayout.addWidget(self.webview) if self.webview else None

        self.windowId = self.windows.openWindow(
            title=self.name,
            content=self.webview,
            icon=self.icon,
            width=800,
            height=600
        )

    # method for updating the title of the window
    def updateTitle(self):
        title = self.webview.page().title() # type: ignore
        self.windows.setTitle(self.windowId, f"{title} - NexSurf")

    # method called by the home action
    def navigateHome(self):
        self.webview.setUrl("http://www.google.com/")

    # method called by the line edit when return key is pressed
    def navigateToUrl(self):
        q = QUrl(self.urlbar.text())

        # if url is scheme is blank
        if q.scheme() == "":
            # set url scheme to html
            q.setScheme("http")

        # set the url to the browser
        self.webview.setUrl(str(q))

    # method for updating url
    def updateUrlBar(self, q):

        self.urlbar.setText(q.toString())
        # setting cursor position of the url bar
        self.urlbar.setCursorPosition(0)