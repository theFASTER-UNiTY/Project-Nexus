class AppRegistry:
    def __init__(self):
        self._apps = {}

    def register(self, app):
        self._apps[app.appId] = app

    def get(self, appId):
        return self._apps.get(appId)

    def all(self):
        return list(self._apps.values())