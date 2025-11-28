# meshcore_node_py/tcp_node_listener.py
import asyncio
from meshcore_node_py.node_listener import NodeListener

class TCPNodeListener(NodeListener):
    def __init__(self, host="0.0.0.0", port=9000, transport=None):
        super().__init__(transport)
        self.host = host
        self.port = port
        self.server = None
        self.clients = []

    async def start(self):
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        print(f"TCPNodeListener listening on {self.host}:{self.port}")
        await super().start()  # start the radio listener loop too

    async def _handle_client(self, reader, writer):
        self.clients.append((reader, writer))
        print("Client connected")
        while True:
            data = await reader.read(1024)
            if not data:
                break
            # Feed client data into NodeListener
            await self.on_frame_received(data)
        writer.close()
        await writer.wait_closed()
        self.clients.remove((reader, writer))

    async def send_to_clients(self, data: bytes):
        for _, writer in self.clients:
            writer.write(data)
            await writer.drain()
