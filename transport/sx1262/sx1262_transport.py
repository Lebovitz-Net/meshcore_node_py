# src/transport/sx1262_transport.py
import asyncio
from sx1262.sx1262 import SX1262

class SX1262Transport:
    """
    Async transport adapter for SX1262 LoRa HAT.
    Wraps the low-level driver and exposes send/receive for NodeListener.
    """

    def __init__(self, serial_port="/dev/ttyS0", baudrate=9600):
        self.radio = SX1262(serial_port=serial_port, baudrate=baudrate)
        self._queue = asyncio.Queue()
        self._running = False
        self._task = None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._poll_radio())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        self.radio.shutdown()

    async def send(self, packet: bytes):
        self.radio.send(packet)

    async def receive(self) -> bytes:
        return await self._queue.get()

    async def _poll_radio(self):
        while self._running:
            data = self.radio.read()
            if data:
                await self._queue.put(data)
            await asyncio.sleep(0.1)
