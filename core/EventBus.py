from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, DefaultDict, List
from collections import defaultdict
import traceback


Listener = Callable[[dict], None]


@dataclass(frozen=True)
class Subscription:
    event: str
    callback: Listener
    priority: int = 100


class EventBus:
    """
    Event bus synchrone simple.

    API :
    - `subscribe(event, callback, priority=100)`
    - `unsubscribe(event, callback)`
    - `emit(event, **payload)`

    Chaque callback reçoit un unique dict payload.
    """

    def __init__(self):
        self._listeners: DefaultDict[str, List[Subscription]] = defaultdict(list)

    def subscribe(self, event: str, callback: Listener, priority: int = 100) -> None:
        sub = Subscription(event=event, callback=callback, priority=priority)
        self._listeners[event].append(sub)
        self._listeners[event].sort(key=lambda s: s.priority)

    def unsubscribe(self, event: str, callback: Listener) -> None:
        listeners = self._listeners.get(event, [])
        self._listeners[event] = [
            sub for sub in listeners if sub.callback != callback
        ]

    def emit(self, event: str, **payload: Any) -> None:
        eventPayload = {"event": event, **payload}

        for sub in list(self._listeners.get(event, [])):
            try:
                sub.callback(eventPayload)
            except Exception:
                traceback.print_exc()