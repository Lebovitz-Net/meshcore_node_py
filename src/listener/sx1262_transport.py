# src/transport/sx1262_transport.py
import asyncio
from sx1262.sx1262 import SX1262
from listener.serial_transport import SerialTransport

class SX1262Transport(SerialTransport):
    """
    Async transport adapter for SX1262 LoRa HAT.
    Matches NodeTransport interface: open, close, send, receive.
    """

    def __init__(self, port="/dev/ttyS0", baudrate=9600):
        super().__init__()
        self.radio = SX1262(serial_port=port, baudrate=baudrate)
        self._queue = asyncio.Queue()
        self._running = False
        self._task = None

    async def open(self):
        self._running = True
        self._task = asyncio.create_task(self._poll_radio())
        self.emit("listening")

    async def close(self):
        self._running = False
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        self.radio.shutdown()
        self.emit("stopped")

    async def send(self, data: bytes):
        self.radio.send(data)

    async def receive(self) -> bytes:
        return await self._queue.get()

    async def _poll_radio(self):
        while self._running:
            data = self.radio.read()
            if data:
                await self._queue.put(data)
            await asyncio.sleep(0.1)

    def set_radio_params(self, frequency, bandwidth, spreading_factor, coding_rate):
        """
        High-level API: configure the radio with given parameters.
        """
        # Delegate to driver primitives
        frame = (
            self.radio.encode_freq(frequency) +
            self.radio.encode_bw(bandwidth) +
            self.radio.encode_sf(spreading_factor) +
            self.radio.encode_cr(coding_rate)
        )
        self.radio.send(frame)
