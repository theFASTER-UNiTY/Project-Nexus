import os
import json
import importlib.util


class ExtensionManager:

    def __init__(self, kernel, extensionsPath = "extensions"):
        self.kernel = kernel
        self.extensionsPath = extensionsPath

    def loadExtensions(self):
        for folder in os.listdir(self.extensionsPath):
            extPath = os.path.join(self.extensionsPath, folder)
            manifestPath = os.path.join(extPath, "manifest.json")

            if not os.path.exists(manifestPath):
                continue

            with open(manifestPath) as f:
                manifest = json.load(f)

            entry = manifest["entry"]
            modulePath = os.path.join(extPath, entry)
            module = self.loadModule(folder, modulePath)
            extensionClass = getattr(module, "Extension")
            instance = extensionClass(self.kernel.api)

            instance.onLoad()
            instance.onEnable()

            if manifest["kind"] == "app":
                self.kernel.app_service.register(
                    manifest["id"],
                    manifest["name"],
                    manifest["version"],
                    instance,
                    manifest
                )

    def loadModule(self, name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec) # type: ignore
        spec.loader.exec_module(module) # type: ignore

        return module