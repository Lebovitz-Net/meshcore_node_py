from buffer.buffer_writer import BufferWriter
from constants import Constants

class NodePush:
    def __init__(self, transport, message_store):
        self.transport = transport
        self.message_store = message_store

    async def push_msg_waiting(self):
        if self.message_store.count() > 0:
            writer = BufferWriter()
            writer.write_uint8(Constants.PushCodes.MsgWaiting)
            await self.send_from_node(writer.to_bytes())

    async def push_advert(self, public_key: bytes):
        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.Advert)
        writer.write_bytes(public_key)
        await self.send_from_node(writer.to_bytes())

    async def push_send_confirmed(self, ack_crc: int = 0):
        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.SendConfirmed)
        writer.write_uint32_le(ack_crc)
        await self.send_from_node(writer.to_bytes())

    async def push_status_response(self, public_key: bytes, status: str = "OK"):
        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.StatusResponse)
        writer.write_uint8(0)  # reserved
        writer.write_bytes(public_key[:6])
        writer.write_string(status)
        await self.send_from_node(writer.to_bytes())

    async def push_telemetry_response(self, public_key: bytes, cayenne_payload: bytes):
        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.TelemetryResponse)
        writer.write_uint8(0)  # reserved
        writer.write_bytes(public_key[:6])
        writer.write_bytes(cayenne_payload)
        await self.send_from_node(writer.to_bytes())

    async def push_binary_response(self, tag: int, payload: bytes):
        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.BinaryResponse)
        writer.write_uint8(0)        # reserved
        writer.write_uint32_le(tag)
        writer.write_bytes(payload)
        await self.send_from_node(writer.to_bytes())
