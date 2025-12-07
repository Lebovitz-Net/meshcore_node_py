import asyncio
from src.events import EventEmitter
from .node_messages import NodeMessages
from .node_diagnostics import NodeDiagnostics
from .node_metrics import NodeMetrics
from .node_info import NodeInfo
from .node_push import NodePush
from src.buffer.buffer_reader import BufferReader
from src.constants import Constants

class NodeListener(EventEmitter,
                   NodeMessages,
                   NodeDiagnostics,
                   NodeMetrics,
                   NodeInfo,
                   NodePush):
    def __init__(self, contact_store, message_store):
        EventEmitter.__init__(self)
        NodeMessages.__init__(self, contact_store, message_store)
        NodeDiagnostics.__init__(self)
        NodeMetrics.__init__(self)
        NodeInfo.__init__(self)
        NodePush.__init__(self, message_store)

    async def on_frame_received(self, frame_bytes: bytes):
        reader = BufferReader(frame_bytes)
        cmd = reader.read_uint8()
        handlers = {
            # Messages
            Constants.CommandCodes.SendTxtMsg: self.handle_send_txt_msg,
            Constants.CommandCodes.SendChannelTxtMsg: self.handle_send_channel_txt_msg,
            Constants.CommandCodes.SyncNextMessage: self.handle_sync_next_message,
            Constants.CommandCodes.GetContacts: self.handle_get_contacts,
            Constants.CommandCodes.AddUpdateContact: self.handle_add_update_contact,
            Constants.CommandCodes.RemoveContact: self.handle_remove_contact,
            Constants.CommandCodes.ShareContact: self.handle_share_contact,
            Constants.CommandCodes.ExportContact: self.handle_export_contact,
            Constants.CommandCodes.ImportContact: self.handle_import_contact,
            # Diagnostics
            Constants.CommandCodes.ResetPath: self.handle_reset_path,
            Constants.CommandCodes.Reboot: self.handle_reboot,
            Constants.CommandCodes.SendRawData: self.handle_send_raw_data,
            Constants.CommandCodes.SendLogin: self.handle_send_login,
            Constants.CommandCodes.SendStatusReq: self.handle_send_status_req,
            Constants.CommandCodes.SendTracePath: self.handle_send_trace_path,
            # Metrics
            Constants.CommandCodes.GetBatteryVoltage: self.handle_get_battery_voltage,
            Constants.CommandCodes.SendTelemetryReq: self.handle_send_telemetry_req,
            Constants.CommandCodes.SendBinaryReq: self.handle_send_binary_req,
            # Node Info
            Constants.CommandCodes.AppStart: self.handle_app_start,
            Constants.CommandCodes.DeviceQuery: self.handle_device_query,
            Constants.CommandCodes.GetDeviceTime: self.handle_get_device_time,
            Constants.CommandCodes.SetDeviceTime: self.handle_set_device_time,
            Constants.CommandCodes.SendSelfAdvert: self.handle_send_self_advert,
            Constants.CommandCodes.SetAdvertName: self.handle_set_advert_name,
            Constants.CommandCodes.SetRadioParams: self.handle_set_radio_params,
            Constants.CommandCodes.SetTxPower: self.handle_set_tx_power,
            Constants.CommandCodes.SetAdvertLatLon: self.handle_set_advert_lat_lon,
            Constants.CommandCodes.SetOtherParams: self.handle_set_other_params,
            Constants.CommandCodes.GetChannel: self.handle_get_channel,
            Constants.CommandCodes.SetChannel: self.handle_set_channel,
            Constants.CommandCodes.SignStart: self.handle_sign_start,
            Constants.CommandCodes.SignData: self.handle_sign_data,
            Constants.CommandCodes.SignFinish: self.handle_sign_finish,
            Constants.CommandCodes.ExportPrivateKey: self.handle_export_private_key,
            Constants.CommandCodes.ImportPrivateKey: self.handle_import_private_key,
        }
        handler = handlers.get(cmd)
        if handler:
            await handler(reader)
        else:
            await self.send_err_response(err_code=Constants.ErrorCodes.UnsupportedCmd)

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._rx_loop())
        self.emit("listening")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        await self.close()
        self.emit("stopped")

    async def _rx_loop(self):
        while self._running:
            try:
                frame = await self.receive_to_node()
                if frame:
                    await self.on_frame_received(frame)
            except asyncio.CancelledError:
                break
            except Exception as e:
                 self.emit("error", {"error": e})
            await asyncio.sleep(0.01)

    async def on_frame_received(self, frame_bytes: bytes):
        reader = BufferReader(frame_bytes)
        cmd = reader.read_uint8()
        # This method should be overridden or wired to a dispatcher
        # e.g., call an injected dispatcher: self._dispatch(cmd, reader)
        self.emit("debug", {"cmd": cmd})

    async def send_from_node(self, data: bytes):
        raise NotImplementedError("Transport must implement send()")
    
    async def send_err_response(self, data: bytes):
        raise NotImplementedError("Transport must implement send()")


    async def receive_to_node(self) -> bytes:
        raise NotImplementedError("Transport must implement receive()")

    async def close(self):
        raise NotImplementedError("Transport must implement close()")
