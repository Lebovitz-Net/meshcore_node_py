import asyncio
from collections import defaultdict

class EventEmitter:
    def __init__(self):
        self._event_listeners = defaultdict(list)

    def on(self, event: str, callback):
        """Register a persistent listener for an event."""
        self._event_listeners[event].append(callback)

    def off(self, event: str, callback):
        """Remove a specific listener for an event."""
        if event in self._event_listeners:
            self._event_listeners[event] = [
                cb for cb in self._event_listeners[event] if cb != callback
            ]

    def once(self, event: str, callback):
        """Register a one-time listener for an event."""

        def internal_callback(*args, **kwargs):
            self.off(event, internal_callback)
            loop = asyncio.get_event_loop()
            loop.call_soon(callback, *args, **kwargs)

        self.on(event, internal_callback)

    def emit(self, event: str, *args, **kwargs):
        """Trigger all listeners for an event asynchronously."""
        if event in self._event_listeners:
            loop = asyncio.get_event_loop()
            for listener in list(self._event_listeners[event]):
                loop.call_soon(listener, *args, **kwargs)
