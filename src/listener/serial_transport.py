# serial_transport.py
import asyncio
import serial_asyncio
from listener.node_listener import NodeTransport

class SerialTransport(NodeTransport):
    def __init__(self, port="/dev/ttyS0", baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.reader = None
        self.writer = None

    async def open(self):
        self.reader, self.writer = await serial_asyncio.open_serial_connection(
            url=self.port, baudrate=self.baudrate
        )
        self.emit("listening")

    async def send(self, data: bytes):
        if self.writer:
            self.writer.write(data)
            await self.writer.drain()

    async def receive(self) -> bytes:
        if self.reader:
            return await self.reader.read(1024)
        return b""

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.emit("stopped")
