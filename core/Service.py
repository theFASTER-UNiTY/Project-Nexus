from __future__ import annotations

class Service:
    name: str = "service"

    def __init__(self, kernel):
        self.kernel = kernel
        self.running = False

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False