class ExtensionAPI:

    def __init__(self, kernel):
        self.kernel = kernel

    @property
    def windows(self):
        return self.kernel.windowService

    @property
    def events(self):
        return self.kernel.eventService

    @property
    def apps(self):
        return self.kernel.appService