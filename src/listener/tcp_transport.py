# tcp_transport.py
import asyncio
from src.listener.node_listener import NodeTransport

class TCPTransport(NodeTransport):
    def __init__(self, host="0.0.0.0", port=9000):
        super().__init__()
        self.host = host
        self.port = port
        self.server = None
        self.reader = None
        self.writer = None

    async def open(self):
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        print(f"TCPTransport listening on {self.host}:{self.port}")
        async with self.server:
            await self.server.serve_forever()

    async def _handle_client(self, reader, writer):
        self.reader = reader
        self.writer = writer
        print("Client connected")
        while True:
            data = await reader.read(1024)
            if not data:
                break
            # Emit frame event for NodeListener
            await self.emit("frame", data)
        writer.close()
        await writer.wait_closed()

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
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        self.emit("stopped")
