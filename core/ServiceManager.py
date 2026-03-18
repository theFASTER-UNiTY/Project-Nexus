from __future__ import annotations
from typing import Dict, Type

from core.Service import Service


class ServiceManager:

    def __init__(self, kernel):
        self.kernel = kernel
        self._services: Dict[str, Service] = {}

    def register(self, serviceCls: Type[Service]) -> Service:
        service = serviceCls(self.kernel)
        if service.name in self._services:
            raise RuntimeError(f"Service already registered: {service.name}")
        self._services[service.name] = service
        return service

    def get(self, name: str) -> Service:
        if name not in self._services:
            raise KeyError(f"Unknown service: {name}")
        return self._services[name]

    def startAll(self) -> None:
        for svc in self._services.values():
            svc.start()

    def stopAll(self) -> None:
        for svc in reversed(list(self._services.values())):
            svc.stop()