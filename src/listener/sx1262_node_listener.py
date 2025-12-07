import asyncio
from listener.node_listener import NodeListener
from sx1262.sx1262 import SX1262

class SX1262NodeListener(NodeListener):
    def __init__(self, 
                 port="/dev/ttyS0", 
                 baudrate=9600,
                 contact_store=None, 
                 message_store=None):
        # super().__init__(contact_store=contact_store,
        #                  message_store=message_store)
        self.port = port
        self.baudrate = baudrate
        self.radio = SX1262(serial_port=port, baudrate=baudrate)
        self._queue = asyncio.Queue()
        self._running = False
        self._task = None

    async def start(self):
        await self.open()
        print(f"SX1262NodeListener listening on {self.port} @ {self.baudrate}")
        await super().start()
        self._task = asyncio.create_task(self._consume_radio())

    async def stop(self):
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        await self.close()
        await super().stop()

    async def _consume_radio(self):
        while True:
            try:
                data = await self.receive_to_node()
                if data:
                    await self.on_frame_received(data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.emit("error", {"error": e})
            await asyncio.sleep(0.05)

    async def send_to_radio(self, data: bytes):
        await self.send_from_node(data)


    def __init__(self, port="/dev/ttyS0", baudrate=9600):
        super().__init__()


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

    async def send_from_node(self, data: bytes):
        self.radio.send(data)

    async def receive_to_node(self) -> bytes:
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
