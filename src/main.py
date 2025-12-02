# main.py
import asyncio
import argparse
from src.node_manager import NodeManager


async def main():
    parser = argparse.ArgumentParser(description="Start a MeshCore node")
    parser.add_argument(
        "--role",
        choices=["companion", "router"],
        default="router",
        help="Role of the node: companion (Companion Radio: TCP + SX1262, TCP cannot route) "
             "or router (Router: TCP + SX1262, mesh side routes packets)"
    )
    parser.add_argument("--tcp-port", type=int, default=9000,
                        help="TCP port for companion/router")
    parser.add_argument("--sx1262-port", type=str, default="/dev/ttyS0",
                        help="Serial port for SX1262")
    parser.add_argument("--sx1262-baud", type=int, default=9600,
                        help="Baudrate for SX1262")
    args = parser.parse_args()

    manager = NodeManager(
        role=args.role,
        tcp_port=args.tcp_port,
        sx1262_port=args.sx1262_port,
        sx1262_baud=args.sx1262_baud
    )

    try:
        await manager.start()
    except asyncio.CancelledError:
        pass
    finally:
        await manager.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down node...")
