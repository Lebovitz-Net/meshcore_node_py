import time
from buffer.buffer_reader import BufferReader
from buffer.buffer_writer import BufferWriter
from constants import Constants

class NodeInfo:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Responses
    async def send_ok_response(self):
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.Ok)
        await self.send_from_node(writer.to_bytes())

    async def send_err_response(self, err_code=None):
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.Err)
        if err_code is not None:
            writer.write_uint8(err_code)
        await self.send_from_node(writer.to_bytes())

    async def send_self_info_response(self, **kwargs):
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.SelfInfo)
        writer.write_uint8(kwargs.get("type_", 1))
        writer.write_uint8(kwargs.get("tx_power", 10))
        writer.write_uint8(kwargs.get("max_tx_power", 20))
        writer.write_bytes(kwargs.get("public_key", b"\x00" * 32))
        writer.write_int32_le(kwargs.get("adv_lat", 0))
        writer.write_int32_le(kwargs.get("adv_lon", 0))
        writer.write_bytes(b"\x00" * 3)   # reserved
        writer.write_uint8(kwargs.get("manual_add_contacts", 0))
        writer.write_uint32_le(kwargs.get("radio_freq", 915_000_000))
        writer.write_uint32_le(kwargs.get("radio_bw", 125_000))
        writer.write_uint8(kwargs.get("radio_sf", 7))
        writer.write_uint8(kwargs.get("radio_cr", 1))
        writer.write_string(kwargs.get("name", "SX1262Node"))
        await self.send_from_node(writer.to_bytes())

    async def send_battery_voltage_response(self, millivolts=3700):
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.BatteryVoltage)
        writer.write_uint16_le(millivolts)
        await self.send_from_node(writer.to_bytes())

    async def send_device_info_response(self, firmware_ver=1, build_date="2025-11-28", manufacturer_model="SX1262Node"):
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.DeviceInfo)
        writer.write_int8(firmware_ver)
        writer.write_bytes(b"\x00" * 6)  # reserved
        writer.write_cstring(build_date, 12)
        writer.write_string(manufacturer_model)
        await self.send_from_node(writer.to_bytes())

    async def send_curr_time_response(self, epoch_secs):
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.CurrTime)
        writer.write_uint32_le(epoch_secs)
        await self.send_from_node(writer.to_bytes())

    # Handlers
    async def handle_app_start(self, reader: BufferReader):
        _app_ver = reader.read_uint8()
        _reserved = reader.read_bytes(6)
        app_name = reader.read_string()
        await self.send_self_info_response(name=f"{app_name}-SX1262")

    async def handle_device_query(self, reader: BufferReader):
        _app_target_ver = reader.read_uint8()
        await self.send_device_info_response()

    async def handle_get_device_time(self, reader: BufferReader):
        await self.send_curr_time_response(int(time.time()))

    async def handle_set_device_time(self, reader: BufferReader):
        _epoch = reader.read_uint32_le()
        await self.send_ok_response()

    async def handle_send_self_advert(self, reader: BufferReader):
        _advert_type = reader.read_uint8()
        await self.send_ok_response()

    async def handle_set_advert_name(self, reader: BufferReader):
        _name = reader.read_string()
        await self.send_ok_response()

    async def handle_set_radio_params(self, reader: BufferReader):
        freq = reader.read_uint32_le()
        bw   = reader.read_uint32_le()
        sf   = reader.read_uint8()
        cr   = reader.read_uint8()
        # Forward to transport if supported
        await self.set_radio_params(freq, bw, sf, cr)
        await self.send_ok_response()

    async def handle_set_tx_power(self, reader: BufferReader):
        _tx_power = reader.read_uint8()
        await self.send_ok_response()

    async def handle_set_advert_lat_lon(self, reader: BufferReader):
        _lat = reader.read_int32_le()
        _lon = reader.read_int32_le()
        await self.send_ok_response()

    async def handle_set_other_params(self, reader: BufferReader):
        _manual_add_contacts = reader.read_uint8()
        await self.send_ok_response()

    async def handle_get_channel(self, reader: BufferReader):
        channel_idx = reader.read_uint8()
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.ChannelInfo)
        writer.write_uint8(channel_idx)
        writer.write_string(f"Channel{channel_idx}")
        writer.write_bytes(b"\x00" * 16)  # secret placeholder
        await self.send_from_node(writer.to_bytes())

    async def handle_set_channel(self, reader: BufferReader):
        _channel_idx = reader.read_uint8()
        _name = reader.read_cstring(32)
        _secret = reader.read_bytes(16)
        await self.send_ok_response()

    async def handle_sign_start(self, reader: BufferReader):
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.SignStart)
        writer.write_uint8(0)          # reserved
        writer.write_uint32_le(1024)   # maxSignDataLen
        await self.send_from_node(writer.to_bytes())

    async def handle_sign_data(self, reader: BufferReader):
        _data_to_sign = reader.read_remaining_bytes()
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.Signature)
        writer.write_bytes(b"\x00" * 64)
        await self.send_from_node(writer.to_bytes())

    async def handle_sign_finish(self, reader: BufferReader):
        await self.send_ok_response()

    async def handle_export_private_key(self, reader: BufferReader):
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.PrivateKey)
        writer.write_bytes(b"\x00" * 64)
        await self.send_from_node(writer.to_bytes())

    async def handle_import_private_key(self, reader: BufferReader):
        _private_key = reader.read_bytes(64)
        await self.send_ok_response()
