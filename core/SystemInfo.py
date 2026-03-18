import json
from pathlib import Path


class SystemInfo:

    def __init__(self):

        path = Path("system/version.json")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.name = data["name"]
        self.codename = data["codename"]
        self.version = data["version"]
        self.build = data["build"]
        self.channel = data["channel"]

    def fullVersion(self):
        return f"{self.name} {self.version} {self.codename} (build {self.build}-{self.channel})"