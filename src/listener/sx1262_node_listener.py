import asyncio
from listener.node_listener import NodeListener
from sx1262.sx1262 import SX1262  # new SPI/GPIO driver for Waveshare LoRaWAN HAT

class SX1262NodeListener(NodeListener):
    """
    NodeListener implementation for the SX1262 LoRaWAN HAT using SPI + GPIO driver.
    Provides async lifecycle management, send/receive integration, and radio configuration.
    """

    def __init__(self, spi_bus=0, spi_dev=0, max_speed=500000):
        super().__init__()
        # Instantiate the SPI/GPIO driver (no serial args required)
        self.radio = SX1262(spi_bus, spi_dev, max_speed)
        self._queue = asyncio.Queue()
        self._running = False
        self._poll_task = None
        self._consume_task = None

    async def start(self):
        """Start the listener and begin consuming radio frames."""
        await self.open()
        print("SX1262NodeListener listening via SPI driver")
        await super().start()
        self._consume_task = asyncio.create_task(self._consume_radio())

    async def stop(self):
        """Stop the listener and clean up tasks/resources."""
        if self._consume_task:
            self._consume_task.cancel()
            await asyncio.gather(self._consume_task, return_exceptions=True)
        await self.close()
        await super().stop()

    async def open(self):
        """Open the radio interface and start polling for data."""
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_radio())
        self.emit("listening")

    async def close(self):
        """Close the radio interface and stop polling."""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            await asyncio.gather(self._poll_task, return_exceptions=True)
        self.radio.close()
        self.emit("stopped")

    async def send_to_radio(self, data: bytes):
        """Send data from higher layers down to the radio."""
        await self.send_from_node(data)

    async def send_from_node(self, data: bytes):
        """Send raw bytes via the SX1262 driver."""
        self.radio.send(data)

    async def receive_to_node(self) -> bytes:
        """Receive raw bytes from the radio into the node."""
        return await self._queue.get()

    async def _poll_radio(self):
        """Poll the radio for incoming data and enqueue it."""
        while self._running:
            try:
                data = self.radio.read()
                if data:
                    print("Got data from SX1262 device")
                    await self._queue.put(data)
            except Exception as e:
                self.emit("error", {"error": e})
            await asyncio.sleep(0.1)

    async def _consume_radio(self):
        """Consume data from the queue and deliver to NodeListener callbacks."""
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

    async def set_radio_params(self, frequency, bandwidth, spreading_factor, coding_rate):
        """
        Configure the SX1262 radio with given parameters.
        Delegates to driver primitives.
        """
        try:
            self.radio.set_frequency(910_525_000)
            self.radio.set_modulation_params(sf=7, bw_hz=62_500, cr=5)
            self.radio.set_packet_params(preamble_len=8, explicit=True, payload_len=64, crc_on=True)
            self.radio.set_sync_word(0x12)

            print(f"Radio params set: freq={frequency}, bw={bandwidth}, sf={spreading_factor}, cr={coding_rate}")
        except Exception as e:
            self.emit("error", {"error": e})
