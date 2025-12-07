from buffer.buffer_reader import BufferReader
from buffer.buffer_writer import BufferWriter
from constants import Constants

class NodeMetrics:
    def __init__(self, transport):
        self.transport = transport

    async def handle_get_battery_voltage(self, reader: BufferReader):
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.BatteryVoltage)
        writer.write_uint16_le(3700)  # default example
        await self.send_from_node(writer.to_bytes())

    async def handle_send_telemetry_req(self, reader: BufferReader):
        _r0 = reader.read_uint8()
        _r1 = reader.read_uint8()
        _r2 = reader.read_uint8()
        public_key = reader.read_bytes(32)

        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.TelemetryResponse)
        writer.write_uint8(0)  # reserved
        writer.write_bytes(public_key[:6])
        writer.write_bytes(b"\x01\x67\x00\xC8")  # CayenneLPP temp 20.0C example
        await self.send_from_node(writer.to_bytes())

    async def handle_send_binary_req(self, reader: BufferReader):
        _public_key = reader.read_bytes(32)
        request = reader.read_remaining_bytes()

        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.BinaryResponse)
        writer.write_uint8(0)        # reserved
        writer.write_uint32_le(42)   # tag example
        writer.write_bytes(request)  # echo
        await self.send_from_node(writer.to_bytes())
