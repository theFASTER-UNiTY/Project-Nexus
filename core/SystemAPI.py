from __future__ import annotations

class SystemAPI:
    """
    Façade officielle. C'est ça qu'on donnera aux plugins/apps.
    """

    def __init__(self, kernel):
        self._k = kernel

    # Events
    def on(self, event: str, callback, priority: int = 100):
        self._k.bus.subscribe(event, callback, priority=priority)

    def emit(self, event: str, **payload):
        self._k.bus.emit(event, **payload)

    # Services
    def service(self, name: str):
        return self._k.services.get(name)

    # State (simple)
    @property
    def state(self):
        return self._k.state