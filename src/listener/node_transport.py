
from events import EventEmitter

class NodeTransport(EventEmitter):
    """
    Minimal transport interface expected by NodeListener.git 
    Subclass this for SX1262, TCP, etc. Must implement send(), receive(), close().
    """

    async def send(self, data: bytes):
        raise NotImplementedError("Transport must implement send()")

    async def receive(self) -> bytes:
        raise NotImplementedError("Transport must implement receive()")

    async def close(self):
        raise NotImplementedError("Transport must implement close()")