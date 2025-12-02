# meshcore/handlers/handler_maps.py
"""
Handler maps for MeshCore protocol commands.
Defines groups of handlers that can be composed into role-specific maps.
"""

from meshcore.constants import Constants

# -------------------------
# Handler Groups
# -------------------------

MESSAGE_HANDLERS = {
    Constants.CommandCodes.SendTxtMsg: "handle_send_txt_msg",
    Constants.CommandCodes.SendChannelTxtMsg: "handle_send_channel_txt_msg",
    Constants.CommandCodes.SyncNextMessage: "handle_sync_next_message",
    Constants.CommandCodes.MsgAck: "handle_msg_ack",
}

CONTACT_HANDLERS = {
    Constants.CommandCodes.GetContacts: "handle_get_contacts",
    Constants.CommandCodes.AddUpdateContact: "handle_add_update_contact",
    Constants.CommandCodes.RemoveContact: "handle_remove_contact",
    Constants.CommandCodes.ShareContact: "handle_share_contact",
    Constants.CommandCodes.ExportContact: "handle_export_contact",
    Constants.CommandCodes.ImportContact: "handle_import_contact",
}

ADVERT_HANDLERS = {
    Constants.CommandCodes.SendSelfAdvert: "handle_self_advert",
    # FloodAdvert is just a variant of SelfAdvert with flood bit set
    Constants.CommandCodes.SetAdvertName: "handle_set_advert_name",
    Constants.CommandCodes.SetAdvertLatLon: "handle_set_advert_lat_lon",
}

DEVICE_HANDLERS = {
    Constants.CommandCodes.DeviceQuery: "handle_device_query",
    Constants.CommandCodes.SelfInfo: "handle_self_info",
    Constants.CommandCodes.SetRadioParams: "handle_set_radio_params",
    Constants.CommandCodes.SetTxPower: "handle_set_tx_power",
    Constants.CommandCodes.GetChannel: "handle_get_channel",
    Constants.CommandCodes.SetChannel: "handle_set_channel",
    Constants.CommandCodes.Reboot: "handle_reboot",
    Constants.CommandCodes.GetBatteryVoltage: "handle_get_battery_voltage",
}

ROUTING_HANDLERS = {
    Constants.CommandCodes.ResetPath: "handle_reset_path",
    Constants.CommandCodes.SendTracePath: "handle_trace_path",
}

SECURITY_HANDLERS = {
    Constants.CommandCodes.ExportPrivateKey: "handle_export_private_key",
    Constants.CommandCodes.ImportPrivateKey: "handle_import_private_key",
    Constants.CommandCodes.SignStart: "handle_sign_start",
    Constants.CommandCodes.SignData: "handle_sign_data",
    Constants.CommandCodes.SignFinish: "handle_sign_finish",
}

SYSTEM_HANDLERS = {
    Constants.CommandCodes.SendLogin: "handle_send_login",
    Constants.CommandCodes.SendStatusReq: "handle_send_status_req",
    Constants.CommandCodes.SendTelemetryReq: "handle_send_telemetry_req",
    Constants.CommandCodes.SendBinaryReq: "handle_send_binary_req",
    Constants.CommandCodes.SendRawData: "handle_send_raw_data",
}

# -------------------------
# Role-specific Maps
# -------------------------

COMMAND_HANDLERS = {
    **MESSAGE_HANDLERS,
    **CONTACT_HANDLERS,
    **ADVERT_HANDLERS,
    **DEVICE_HANDLERS,
    **SECURITY_HANDLERS,
    **SYSTEM_HANDLERS,
}

MESH_HANDLERS = {
    **MESSAGE_HANDLERS,
    **CONTACT_HANDLERS,
    **ADVERT_HANDLERS,
    **ROUTING_HANDLERS,
}

ROUTER_HANDLERS = {
    **COMMAND_HANDLERS,
    **MESH_HANDLERS,
}

# Superset for MeshBridgeServer or testing
ALL_HANDLERS = {
    **COMMAND_HANDLERS,
    **MESH_HANDLERS,
}
