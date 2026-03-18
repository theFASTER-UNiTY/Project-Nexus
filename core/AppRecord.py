class AppRecord:

    def __init__(self, app_id, name, version, instance, manifest):
        self.app_id = app_id
        self.name = name
        self.version = version
        self.instance = instance
        self.manifest = manifest
        self.state = "registered"