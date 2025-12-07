from buffer.buffer_reader import BufferReader
from buffer.buffer_writer import BufferWriter
from constants import Constants

class NodeDiagnostics:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def handle_reset_path(self, reader: BufferReader):
        _pubkey = reader.read_bytes(32)
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.Ok)
        await self.send_from_node(writer.to_bytes())

    async def handle_reboot(self, reader: BufferReader):
        _str = reader.read_string()
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.Ok)
        await self.send_from_node(writer.to_bytes())

    async def handle_send_raw_data(self, reader: BufferReader):
        path_len = reader.read_uint8()
        _path = reader.read_bytes(path_len)
        raw = reader.read_remaining_bytes()

        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.LogRxData)
        writer.write_int8(0)    # lastSnr/4
        writer.write_int8(-90)  # lastRssi
        writer.write_bytes(raw)
        await self.send_from_node(writer.to_bytes())

    async def handle_send_login(self, reader: BufferReader):
        _public_key = reader.read_bytes(32)
        _password = reader.read_string()

        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.LoginSuccess)
        writer.write_uint8(0)  # reserved
        writer.write_bytes(b"\x00" * 6)  # pubKeyPrefix placeholder
        await self.send_from_node(writer.to_bytes())

    async def handle_send_status_req(self, reader: BufferReader):
        public_key = reader.read_bytes(32)
        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.StatusResponse)
        writer.write_uint8(0)  # reserved
        writer.write_bytes(public_key[:6])
        writer.write_bytes(b"OK")
        await self.send_from_node(writer.to_bytes())

    async def handle_send_trace_path(self, reader: BufferReader):
        _tag = reader.read_uint32_le()
        _auth = reader.read_uint32_le()
        _flags = reader.read_uint8()
        _path = reader.read_remaining_bytes()
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.Ok)
        await self.send_from_node(writer.to_bytes())
