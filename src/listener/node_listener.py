import asyncio
import time

from buffer_writer import BufferWriter
from buffer_reader import BufferReader
from constants import Constants
from events import EventEmitter



# section 1

class NodeTransport(EventEmitter):
    """
    Minimal transport interface expected by NodeListener.git 
    Subclass this for SX1262, TCP, etc. Must implement send(), receive(), close().
    """

    async def send(self, data: bytes):
        raise NotImplementedError("Transport must implement send()")

    async def receive(self) -> bytes:
        raise NotImplementedError("Transport must implement receive()")

    async def close(self):
        raise NotImplementedError("Transport must implement close()")


class NodeListener(EventEmitter):
    """
    Server-side listener for MeshCore nodes.
    - Waits for incoming frames from clients.
    - Dispatches commands to handlers.
    - Builds and sends responses/pushes.
    """

    def __init__(self, transport: NodeTransport):
        super().__init__()
        self.transport = transport
        self._running = False
        self._task = None

    # -------------------------
    # Lifecycle
    # -------------------------

    async def start(self):
        """Begin listening for incoming frames."""
        self._running = True
        self._task = asyncio.create_task(self._rx_loop())
        self.emit("listening")

    async def stop(self):
        """Stop listening and close transport."""
        self._running = False
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        await self.transport.close()
        self.emit("stopped")

    async def _rx_loop(self):
        """Background loop to receive frames and dispatch commands."""
        while self._running:
            try:
                frame = await self.transport.receive()
                if frame:
                    await self.on_frame_received(frame)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.emit("error", {"error": e})
            await asyncio.sleep(0.01)

    # -------------------------
    # Frame dispatch
    # -------------------------

    async def on_frame_received(self, frame_bytes: bytes):
        """Parse an incoming command frame and dispatch to the appropriate handler."""
        reader = BufferReader(frame_bytes)
        cmd = reader.read_uint8()

        handlers = {
            Constants.CommandCodes.AppStart: self.handle_app_start,
            Constants.CommandCodes.SendTxtMsg: self.handle_send_txt_msg,
            Constants.CommandCodes.SendChannelTxtMsg: self.handle_send_channel_txt_msg,
            Constants.CommandCodes.GetContacts: self.handle_get_contacts,
            Constants.CommandCodes.GetDeviceTime: self.handle_get_device_time,
            Constants.CommandCodes.SetDeviceTime: self.handle_set_device_time,
            Constants.CommandCodes.SendSelfAdvert: self.handle_send_self_advert,
            Constants.CommandCodes.SetAdvertName: self.handle_set_advert_name,
            Constants.CommandCodes.AddUpdateContact: self.handle_add_update_contact,
            Constants.CommandCodes.SyncNextMessage: self.handle_sync_next_message,
            Constants.CommandCodes.SetRadioParams: self.handle_set_radio_params,
            Constants.CommandCodes.SetTxPower: self.handle_set_tx_power,
            Constants.CommandCodes.ResetPath: self.handle_reset_path,
            Constants.CommandCodes.SetAdvertLatLon: self.handle_set_advert_lat_lon,
            Constants.CommandCodes.RemoveContact: self.handle_remove_contact,
            Constants.CommandCodes.ShareContact: self.handle_share_contact,
            Constants.CommandCodes.ExportContact: self.handle_export_contact,
            Constants.CommandCodes.ImportContact: self.handle_import_contact,
            Constants.CommandCodes.Reboot: self.handle_reboot,
            Constants.CommandCodes.GetBatteryVoltage: self.handle_get_battery_voltage,
            Constants.CommandCodes.DeviceQuery: self.handle_device_query,
            Constants.CommandCodes.ExportPrivateKey: self.handle_export_private_key,
            Constants.CommandCodes.ImportPrivateKey: self.handle_import_private_key,
            Constants.CommandCodes.SendRawData: self.handle_send_raw_data,
            Constants.CommandCodes.SendLogin: self.handle_send_login,
            Constants.CommandCodes.SendStatusReq: self.handle_send_status_req,
            Constants.CommandCodes.SendTelemetryReq: self.handle_send_telemetry_req,
            Constants.CommandCodes.SendBinaryReq: self.handle_send_binary_req,
            Constants.CommandCodes.GetChannel: self.handle_get_channel,
            Constants.CommandCodes.SetChannel: self.handle_set_channel,
            Constants.CommandCodes.SignStart: self.handle_sign_start,
            Constants.CommandCodes.SignData: self.handle_sign_data,
            Constants.CommandCodes.SignFinish: self.handle_sign_finish,
            Constants.CommandCodes.SendTracePath: self.handle_send_trace_path,
            Constants.CommandCodes.SetOtherParams: self.handle_set_other_params,
        }

        handler = handlers.get(cmd)
        if handler:
            await handler(reader)
        else:
            await self.send_err_response(err_code=Constants.ErrorCodes.UnsupportedCmd)

# section 2

    # -------------------------
    # Response builders
    # -------------------------

    async def send_ok_response(self):
        """Send a generic OK response."""
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.Ok)
        await self.transport.send(writer.to_bytes())

    async def send_err_response(self, err_code=None):
        """Send an error response with optional error code."""
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.Err)
        if err_code is not None:
            writer.write_uint8(err_code)
        await self.transport.send(writer.to_bytes())

    async def send_self_info_response(self, **kwargs):
        """Send SelfInfo response with node parameters."""
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
        await self.transport.send(writer.to_bytes())

    async def send_battery_voltage_response(self, millivolts=3700):
        """Send battery voltage response in millivolts."""
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.BatteryVoltage)
        writer.write_uint16_le(millivolts)
        await self.transport.send(writer.to_bytes())

    async def send_device_info_response(self, firmware_ver=1, build_date="2025-11-28", manufacturer_model="SX1262Node"):
        """Send device info response with firmware and model details."""
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.DeviceInfo)
        writer.write_int8(firmware_ver)
        writer.write_bytes(b"\x00" * 6)  # reserved
        writer.write_cstring(build_date, 12)
        writer.write_string(manufacturer_model)
        await self.transport.send(writer.to_bytes())

    async def send_curr_time_response(self, epoch_secs):
        """Send current time response as epoch seconds."""
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.CurrTime)
        writer.write_uint32_le(epoch_secs)
        await self.transport.send(writer.to_bytes())

# section 3

    # -------------------------
    # Command handlers (Part 1)
    # -------------------------

    async def handle_app_start(self, reader: BufferReader):
        """Handle AppStart command: respond with SelfInfo."""
        app_ver = reader.read_uint8()
        _reserved = reader.read_bytes(6)
        app_name = reader.read_string()
        await self.send_self_info_response(name=f"{app_name}-SX1262")

    async def handle_send_txt_msg(self, reader: BufferReader):
        """Handle SendTxtMsg command: echo back as ContactMsgRecv."""
        txt_type = reader.read_uint8()
        attempt = reader.read_uint8()
        sender_timestamp = reader.read_uint32_le()
        pubkey_prefix = reader.read_bytes(6)
        text = reader.read_string()

        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.ContactMsgRecv)
        writer.write_bytes(pubkey_prefix)
        writer.write_uint8(0)  # pathLen
        writer.write_uint8(txt_type)
        writer.write_uint32_le(sender_timestamp)
        writer.write_string(text)
        await self.transport.send(writer.to_bytes())

    async def handle_send_channel_txt_msg(self, reader: BufferReader):
        """Handle SendChannelTxtMsg command: echo back as ChannelMsgRecv."""
        txt_type = reader.read_uint8()
        channel_idx = reader.read_uint8()
        sender_timestamp = reader.read_uint32_le()
        text = reader.read_string()

        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.ChannelMsgRecv)
        writer.write_uint8(channel_idx)
        writer.write_uint8(0)  # pathLen
        writer.write_uint8(txt_type)
        writer.write_uint32_le(sender_timestamp)
        writer.write_string(text)
        await self.transport.send(writer.to_bytes())

    async def handle_get_contacts(self, reader: BufferReader):
        """Handle GetContacts command: respond with EndOfContacts (no contacts)."""
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.EndOfContacts)
        await self.transport.send(writer.to_bytes())

# section 4

    # -------------------------
    # Command handlers (Part 2)
    # -------------------------

    async def handle_get_device_time(self, reader: BufferReader):
        """Handle GetDeviceTime command: respond with current epoch time."""
        await self.send_curr_time_response(int(time.time()))

    async def handle_set_device_time(self, reader: BufferReader):
        """Handle SetDeviceTime command: acknowledge with OK."""
        _epoch = reader.read_uint32_le()
        await self.send_ok_response()

    async def handle_send_self_advert(self, reader: BufferReader):
        """Handle SendSelfAdvert command: acknowledge with OK."""
        _advert_type = reader.read_uint8()
        await self.send_ok_response()

    async def handle_set_advert_name(self, reader: BufferReader):
        """Handle SetAdvertName command: acknowledge with OK."""
        _name = reader.read_string()
        await self.send_ok_response()

    async def handle_add_update_contact(self, reader: BufferReader):
        """Handle AddUpdateContact command: acknowledge with OK."""
        _public_key = reader.read_bytes(32)
        _type = reader.read_uint8()
        _flags = reader.read_uint8()
        _out_path_len = reader.read_uint8()
        _out_path = reader.read_bytes(64)
        _adv_name = reader.read_cstring(32)
        _last_advert = reader.read_uint32_le()
        _adv_lat = reader.read_uint32_le()
        _adv_lon = reader.read_uint32_le()
        await self.send_ok_response()

    async def handle_sync_next_message(self, reader: BufferReader):
        """Handle SyncNextMessage command: respond with EndOfContacts (no messages)."""
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.NoMoreMessages)
        await self.transport.send(writer.to_bytes())

    async def handle_set_radio_params(self, reader: BufferReader):
        """Handle SetRadioParams command: acknowledge with OK."""
        _freq = reader.read_uint32_le()
        _bw = reader.read_uint32_le()
        _sf = reader.read_uint8()
        _cr = reader.read_uint8()
        await self.send_ok_response()

    async def handle_set_tx_power(self, reader: BufferReader):
        """Handle SetTxPower command: acknowledge with OK."""
        _tx_power = reader.read_uint8()
        await self.send_ok_response()

    async def handle_reset_path(self, reader: BufferReader):
        """Handle ResetPath command: acknowledge with OK."""
        _pubkey = reader.read_bytes(32)
        await self.send_ok_response()

    async def handle_set_advert_lat_lon(self, reader: BufferReader):
        """Handle SetAdvertLatLon command: acknowledge with OK."""
        _lat = reader.read_int32_le()
        _lon = reader.read_int32_le()
        await self.send_ok_response()

    async def handle_remove_contact(self, reader: BufferReader):
        """Handle RemoveContact command: acknowledge with OK."""
        _pubkey = reader.read_bytes(32)
        await self.send_ok_response()

    async def handle_share_contact(self, reader: BufferReader):
        """Handle ShareContact command: acknowledge with OK."""
        _pubkey = reader.read_bytes(32)
        await self.send_ok_response()

    async def handle_export_contact(self, reader: BufferReader):
        """Handle ExportContact command: respond with empty ExportContact."""
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.ExportContact)
        writer.write_bytes(b"")
        await self.transport.send(writer.to_bytes())

    async def handle_import_contact(self, reader: BufferReader):
        """Handle ImportContact command: acknowledge with OK."""
        _advert_packet_bytes = reader.read_remaining_bytes()
        await self.send_ok_response()

    async def handle_reboot(self, reader: BufferReader):
        """Handle Reboot command: acknowledge with OK."""
        _str = reader.read_string()
        await self.send_ok_response()

    async def handle_get_battery_voltage(self, reader: BufferReader):
        """Handle GetBatteryVoltage command: respond with battery voltage."""
        await self.send_battery_voltage_response()

    async def handle_device_query(self, reader: BufferReader):
        """Handle DeviceQuery command: respond with DeviceInfo."""
        _app_target_ver = reader.read_uint8()
        await self.send_device_info_response()

    async def handle_export_private_key(self, reader: BufferReader):
        """Handle ExportPrivateKey command: respond with dummy private key."""
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.PrivateKey)
        writer.write_bytes(b"\x00" * 64)
        await self.transport.send(writer.to_bytes())

    async def handle_import_private_key(self, reader: BufferReader):
        """Handle ImportPrivateKey command: acknowledge with OK."""
        _private_key = reader.read_bytes(64)
        await self.send_ok_response()

    async def handle_send_raw_data(self, reader: BufferReader):
        """Handle SendRawData command: echo back raw data as LogRxData push."""
        path_len = reader.read_uint8()
        path = reader.read_bytes(path_len)
        raw = reader.read_remaining_bytes()

        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.LogRxData)
        writer.write_int8(0)   # lastSnr/4
        writer.write_int8(-90) # lastRssi
        writer.write_bytes(raw)
        await self.transport.send(writer.to_bytes())

    async def handle_send_login(self, reader: BufferReader):
        """Handle SendLogin command: respond with LoginSuccess push."""
        _public_key = reader.read_bytes(32)
        _password = reader.read_string()

        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.LoginSuccess)
        writer.write_uint8(0)  # reserved
        writer.write_bytes(b"\x00" * 6)  # pubKeyPrefix
        await self.transport.send(writer.to_bytes())

    async def handle_send_status_req(self, reader: BufferReader):
        """Handle SendStatusReq command: respond with StatusResponse push."""
        public_key = reader.read_bytes(32)

        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.StatusResponse)
        writer.write_uint8(0)  # reserved
        writer.write_bytes(public_key[:6])
        writer.write_bytes(b"OK")
        await self.transport.send(writer.to_bytes())

    async def handle_send_telemetry_req(self, reader: BufferReader):
        """Handle SendTelemetryReq command: respond with TelemetryResponse push."""
        _r0 = reader.read_uint8()
        _r1 = reader.read_uint8()
        _r2 = reader.read_uint8()
        public_key = reader.read_bytes(32)

        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.TelemetryResponse)
        writer.write_uint8(0)  # reserved
        writer.write_bytes(public_key[:6])
        writer.write_bytes(b"\x01\x67\x00\xC8")  # Example CayenneLPP temp 20.0C
        await self.transport.send(writer.to_bytes())

    async def handle_send_binary_req(self, reader: BufferReader):
        """Handle SendBinaryReq command: respond with BinaryResponse push."""
        public_key = reader.read_bytes(32)
        request = reader.read_remaining_bytes()

        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.BinaryResponse)
        writer.write_uint8(0)        # reserved
        writer.write_uint32_le(42)   # tag
        writer.write_bytes(request)  # echo
        await self.transport.send(writer.to_bytes())

    async def handle_get_channel(self, reader: BufferReader):
        """Handle GetChannel command: respond with ChannelInfo."""
        channel_idx = reader.read_uint8()

        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.ChannelInfo)
        writer.write_uint8(channel_idx)
        writer.write_string(f"Channel{channel_idx}")
        writer.write_bytes(b"\x00" * 16)  # secret placeholder
        await self.transport.send(writer.to_bytes())

    async def handle_set_channel(self, reader: BufferReader):
        """Handle SetChannel command: acknowledge with OK."""
        channel_idx = reader.read_uint8()
        name = reader.read_cstring(32)
        secret = reader.read_bytes(16)
        await self.send_ok_response()

    async def handle_sign_start(self, reader: BufferReader):
        """Handle SignStart command: respond with SignStart response."""
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.SignStart)
        writer.write_uint8(0)          # reserved
        writer.write_uint32_le(1024)   # maxSignDataLen
        await self.transport.send(writer.to_bytes())

    async def handle_sign_data(self, reader: BufferReader):
        """Handle SignData command: respond with dummy Signature."""
        _data_to_sign = reader.read_remaining_bytes()

        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.Signature)
        writer.write_bytes(b"\x00" * 64)
        await self.transport.send(writer.to_bytes())

    async def handle_sign_finish(self, reader: BufferReader):
        """Handle SignFinish command: acknowledge with OK."""
        await self.send_ok_response()

    async def handle_send_trace_path(self, reader: BufferReader):
        """Handle SendTracePath command: acknowledge with OK."""
        _tag = reader.read_uint32_le()
        _auth = reader.read_uint32_le()
        _flags = reader.read_uint8()
        path = reader.read_remaining_bytes()
        # For now we just acknowledge; later you could log or process the path
        await self.send_ok_response()

    async def handle_set_other_params(self, reader: BufferReader):
        """Handle SetOtherParams command: acknowledge with OK."""
        _manual_add_contacts = reader.read_uint8()
        await self.send_ok_response()

# section 5

    # -------------------------
    # Push events (server-initiated)
    # -------------------------

    async def push_msg_waiting(self):
        """Push a MsgWaiting event to notify client of pending messages."""
        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.MsgWaiting)
        await self.transport.send(writer.to_bytes())

    async def push_advert(self, public_key: bytes):
        """Push an Advert event with a public key."""
        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.Advert)
        writer.write_bytes(public_key)
        await self.transport.send(writer.to_bytes())

    async def push_send_confirmed(self, ack_crc: int = 0):
        """Push a SendConfirmed event with optional ack CRC."""
        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.SendConfirmed)
        writer.write_uint32_le(ack_crc)
        await self.transport.send(writer.to_bytes())

    async def push_status_response(self, public_key: bytes, status: str = "OK"):
        """Push a StatusResponse event with a public key and status string."""
        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.StatusResponse)
        writer.write_uint8(0)  # reserved
        writer.write_bytes(public_key[:6])
        writer.write_string(status)
        await self.transport.send(writer.to_bytes())

    async def push_telemetry_response(self, public_key: bytes, cayenne_payload: bytes):
        """Push a TelemetryResponse event with CayenneLPP payload."""
        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.TelemetryResponse)
        writer.write_uint8(0)  # reserved
        writer.write_bytes(public_key[:6])
        writer.write_bytes(cayenne_payload)
        await self.transport.send(writer.to_bytes())

    async def push_binary_response(self, tag: int, payload: bytes):
        """Push a BinaryResponse event with tag and payload."""
        writer = BufferWriter()
        writer.write_uint8(Constants.PushCodes.BinaryResponse)
        writer.write_uint8(0)        # reserved
        writer.write_uint32_le(tag)
        writer.write_bytes(payload)
        await self.transport.send(writer.to_bytes())
