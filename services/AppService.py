import os
import importlib.util
import traceback

from core.Service import Service
from core.AppExtension import AppExtension


class AppService(Service):
    name = "apps"

    def __init__(self, kernel):
        super().__init__(kernel)
        self.appsPath = "apps"

        # appId -> {"class": ..., "meta": {...}}
        self._apps = {}

    def start(self):
        super().start()
        self.autoload()

    def registerApp(self, appClass):
        if not isinstance(appClass, type):
            raise TypeError("registerApp() expects a class")

        if not issubclass(appClass, AppExtension):
            raise TypeError(
                f"{appClass.__name__} must inherit from AppExtension"
            )

        appId = getattr(appClass, "appId", None)
        if not appId:
            raise RuntimeError(f"{appClass.__name__} has no appId")

        if appId in self._apps:
            raise RuntimeError(f"Duplicate app id: {appId}")

        meta = {
            "id": appId,
            "title": getattr(appClass, "name", appId),
            "subtitle": getattr(appClass, "description", "") or "",
            "icon": getattr(appClass, "icon", None),
        }

        self._apps[appId] = {
            "class": appClass,
            "meta": meta,
        }

        self.kernel.bus.emit(
            "app.registered",
            appId=appId,
            name=meta["title"]
        )

        print(f"[AppService] Registered app: {appId}")

    def launch(self, appId: str):
        record = self._apps.get(appId)
        if record is None:
            raise RuntimeError(f"App not found: {appId}")

        appClass = record["class"]
        app = appClass(self.kernel)

        self.kernel.bus.emit(
            "app.launching",
            appId=app.appId,
            name=getattr(app, "name", app.appId)
        )

        app.onLoad()
        app.onEnable()
        app.launch()

        self.kernel.bus.emit(
            "app.launched",
            appId=app.appId,
            name=getattr(app, "name", app.appId)
        )

    def listApps(self):
        return [record["meta"] for record in self._apps.values()]

    def getAppMeta(self, appId: str):
        record = self._apps.get(appId)
        if record is None:
            return None
        return record["meta"]

    def autoload(self):
        if not os.path.isdir(self.appsPath):
            print(f"[AppService] Apps folder not found: {self.appsPath}")
            return

        print(f"[AppService] Autoloading apps from: {self.appsPath}")

        for entry in sorted(os.listdir(self.appsPath)):
            folderPath = os.path.join(self.appsPath, entry)

            if not os.path.isdir(folderPath):
                continue

            try:
                self.loadAppFromFolder(folderPath)
            except Exception as exc:
                print(f"[AppService] Failed to load app from '{folderPath}': {exc}")
                traceback.print_exc()

                self.kernel.bus.emit(
                    "app.load_failed",
                    folder=folderPath,
                    error=str(exc)
                )

    def loadAppFromFolder(self, folderPath: str):
        appFile = os.path.join(folderPath, "app.py")

        if not os.path.isfile(appFile):
            print(f"[AppService] Skipping '{folderPath}': no app.py")
            return

        folderName = os.path.basename(folderPath)
        moduleName = f"smartnexus_app_{folderName}"

        spec = importlib.util.spec_from_file_location(moduleName, appFile)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to create module spec for '{appFile}'")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        appClass = getattr(module, "App", None)
        if appClass is None:
            raise RuntimeError(f"No class 'App' found in '{appFile}'")

        if not isinstance(appClass, type):
            raise RuntimeError(f"'App' in '{appFile}' is not a class")

        if not issubclass(appClass, AppExtension):
            raise RuntimeError(
                f"'App' in '{appFile}' must inherit from AppExtension"
            )

        self.registerApp(appClass)
