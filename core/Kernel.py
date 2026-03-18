from core.EventBus import EventBus
from core.ServiceManager import ServiceManager
from core.SessionManager import SessionManager
from core.SystemAPI import SystemAPI
from core.SystemInfo import SystemInfo
from core.Filesystem import VirtualFileSystem


class Kernel:

    def __init__(self):
        self.system = SystemInfo()
        self.bus = EventBus()
        self.services = ServiceManager(self)
        self.api = SystemAPI(self)
        self.filesystem = VirtualFileSystem()
        self.session = SessionManager(self)

        self.state = {
            "bootMode": "normal",
            "user": None,
            "theme": {
                "scheme": "dark",
                "accent": "blue",
                "fontScale": 1.0,
            },
            "firstBoot": True
        }

    def start(self):
        version = self.system.fullVersion()
        print(version)

        self.bus.emit("system.starting", version=version)
        self.filesystem.ensureBaseTree()
        self.services.startAll()
        self.bus.emit("system.ready", version=version)