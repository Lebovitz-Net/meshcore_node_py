# src/node_manager.py
import asyncio
from listener.tcp_node_listener import TCPNodeListener
from listener.sx1262_node_listener import SX1262NodeListener


class NodeManager:
    def __init__(self,
                 role: str = "router",
                 tcp_port: int = 9000,
                 spi_bus: int = 0,
                 spi_dev: int = 0):
        """
        NodeManager orchestrates listeners based on role:
        - companion: Companion Radio (TCP + SX1262, TCP cannot route)
        - router: Router (TCP + SX1262, mesh side routes packets)
        """
        self.role = role
        self._listeners = []

        if role in ("companion", "router"):
            self.tcp_listener = TCPNodeListener(tcp_port, False)
            self._listeners.append(self.tcp_listener)

        self.sx1262_listener = SX1262NodeListener(spi_bus, spi_dev)
        self._listeners.append(self.sx1262_listener)

    async def start(self):
        """Start all listeners."""
        tasks = [listener.start() for listener in self._listeners]
        await asyncio.gather(*tasks)
        # General radio discovery
        for listener in self._listeners:
            if listener and hasattr(listener, "set_radio_params"):
                print("setting radio params", listener.set_radio_params)
                await listener.set_radio_params(
                    frequency=910_525_000,
                    bandwidth=62_500,
                    spreading_factor=7,
                    coding_rate=5 # 4/5
                )

        print(f"NodeManager started in {self.role} mode")

    async def stop(self):
        """Stop all listeners."""
        tasks = [listener.stop() for listener in self._listeners]
        await asyncio.gather(*tasks)
        print("NodeManager stopped")

    async def broadcast_msg_waiting(self):
        """Push MsgWaiting event across all listeners."""
        tasks = [listener.push_msg_waiting() for listener in self._listeners]
        await asyncio.gather(*tasks)

    async def broadcast_advert(self, public_key: bytes):
        """Push Advert event across all listeners."""
        tasks = [listener.push_advert(public_key) for listener in self._listeners]
        await asyncio.gather(*tasks)
