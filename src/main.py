import asyncio
from meshcore import MeshCore

async def main():
    core = await MeshCore.create_serial("/dev/ttyUSB0")

    # Subscribe to packet events
    def on_packet(packet):
        print("Received packet:", packet)

    core.on("packet", on_packet)
    core.on("error", lambda e: print("Error:", e))

    # Start MeshCore
    await core.start()

    # Send a flood advert
    await core.commands.send_self_advert(advert_type=1)

    # Query contacts
    contacts = await core.commands.get_contacts()
    print("Contacts:", contacts)

    # Keep running until Ctrl-C
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopping MeshCore...")

    await core.stop()

if __name__ == "__main__":
    asyncio.run(main())
