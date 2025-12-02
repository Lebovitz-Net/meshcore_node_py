import asyncio
from listener.node_listener import NodeListener
from listener.sx1262_transport import SX1262Transport

class SX1262NodeListener(NodeListener):
    def __init__(self, port="/dev/ttyS0", baudrate=9600,
                 contact_store=None, message_store=None):
        self.transport = SX1262Transport(port=port, baudrate=baudrate)
        super().__init__(self.transport, 
                         contact_store=contact_store,
                         message_store=message_store)
        # Transport matches NodeTransport interface
        self._task = None

    async def start(self):
        await self.transport.open()
        print(f"SX1262NodeListener listening on {self.transport.port} @ {self.transport.baudrate}")
        await super().start()
        self._task = asyncio.create_task(self._consume_radio())

    async def stop(self):
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        await self.transport.close()
        await super().stop()

    async def _consume_radio(self):
        while True:
            try:
                data = await self.transport.receive()
                if data:
                    await self.on_frame_received(data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.emit("error", {"error": e})
            await asyncio.sleep(0.05)

    async def send_to_radio(self, data: bytes):
        await self.transport.send(data)
