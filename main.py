# main.py
import asyncio
import argparse
from node_manager import NodeManager


async def main():
    # parser for command lines
    parser = argparse.ArgumentParser(description="Start a MeshCore node")

    parser.add_argument(
        "--role",
        choices=["companion", "router"],
        default="router",
        help=(
            "Role of the node: "
            "companion (Companion Radio: TCP + SX1262, TCP cannot route) "
            "or router (Router: TCP + SX1262, mesh side routes packets)"
        ),
    )

    parser.add_argument(
        "--tcp-port",
        type=int,
        default=9000,
        help="TCP port for companion/router",
    )

    args = parser.parse_args()

    # NodeManager now only needs role and tcp_port;
    # SX1262 SPI driver is configured inside the listener/driver itself.
    manager = NodeManager(
        role=args.role,
        tcp_port=args.tcp_port,
    )

    try:
        await manager.start()
        # Keep running until cancelled (Ctrl+C)
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        await manager.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down node...")
