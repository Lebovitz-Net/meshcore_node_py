from buffer.buffer_reader import BufferReader
from buffer.buffer_writer import BufferWriter
from constants import Constants

class NodeMessages:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def handle_send_txt_msg(self, reader: BufferReader):
        txt_type = reader.read_uint8()
        sender_timestamp = reader.read_uint32_le()
        pubkey_prefix = reader.read_bytes(6)
        text = reader.read_string()

        self.message_store.add({
            "from": pubkey_prefix,
            "text": text,
            "timestamp": sender_timestamp,
            "type": txt_type,
        })

        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.ContactMsgRecv)
        writer.write_bytes(pubkey_prefix)
        writer.write_uint8(0)
        writer.write_uint8(txt_type)
        writer.write_uint32_le(sender_timestamp)
        writer.write_string(text)
        await self.send_from_node(writer.to_bytes())

    async def handle_send_channel_txt_msg(self, reader: BufferReader):
        txt_type = reader.read_uint8()
        channel_idx = reader.read_uint8()
        sender_timestamp = reader.read_uint32_le()
        text = reader.read_string()

        self.message_store.add_message({
            "channel_idx": channel_idx,
            "text": text,
            "timestamp": sender_timestamp,
            "type": txt_type,
        })

        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.ChannelMsgRecv)
        writer.write_uint8(channel_idx)
        writer.write_uint8(0)
        writer.write_uint8(txt_type)
        writer.write_uint32_le(sender_timestamp)
        writer.write_string(text)
        await self.send_from_node(writer.to_bytes())

    async def handle_sync_next_message(self):
        msg = self.message_store.get_next()
        writer = BufferWriter()
        if msg:
            if "channel_idx" in msg:
                writer.write_uint8(Constants.ResponseCodes.ChannelMsgRecv)
                writer.write_uint8(msg["channel_idx"])
                writer.write_uint8(0)
                writer.write_uint8(msg["type"])
                writer.write_uint32_le(msg["timestamp"])
                writer.write_string(msg["text"])
            else:
                writer.write_uint8(Constants.ResponseCodes.ContactMsgRecv)
                writer.write_bytes(msg["pubkey_prefix"])
                writer.write_uint8(0)
                writer.write_uint8(msg["type"])
                writer.write_uint32_le(msg["timestamp"])
                writer.write_string(msg["text"])
        else:
            writer.write_uint8(Constants.ResponseCodes.NoMoreMessages)
        await self.send_from_node(writer.to_bytes())

    async def handle_get_contacts(self):
        for contact in self.contact_store.all_contacts():
            writer = BufferWriter()
            writer.write_uint8(Constants.ResponseCodes.Contact)
            writer.write_bytes(contact["public_key"])
            writer.write_string(contact.get("name", ""))
            await self.send_from_node(writer.to_bytes())

        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.EndOfContacts)
        await self.send_from_node(writer.to_bytes())

    async def handle_add_update_contact(self, reader: BufferReader):
        public_key = reader.read_bytes(32)
        adv_name = reader.read_cstring(32)
        last_advert = reader.read_uint32_le()
        adv_lat = reader.read_uint32_le()
        adv_lon = reader.read_uint32_le()

        self.contact_store.add_contact({
            "public_key": public_key,
            "name": adv_name,
            "last_advert": last_advert,
            "adv_lat": adv_lat,
            "adv_lon": adv_lon,
        })

        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.Ok)
        await self.send_from_node(writer.to_bytes())

    async def handle_remove_contact(self, reader: BufferReader):
        pubkey = reader.read_bytes(32)
        self.contact_store.remove_contact(pubkey)
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.Ok)
        await self.send_from_node(writer.to_bytes())

    async def handle_share_contact(self, reader: BufferReader):
        pubkey = reader.read_bytes(32)
        contact = self.contact_store.get_contact(pubkey)
        writer = BufferWriter()
        if contact:
            writer.write_uint8(Constants.ResponseCodes.ExportContact)
            writer.write_bytes(contact["public_key"])
            writer.write_string(contact.get("name", ""))
        else:
            writer.write_uint8(Constants.ResponseCodes.Err)
            writer.write_uint8(Constants.ErrorCodes.NotFound)
        await self.send_from_node(writer.to_bytes())

    async def handle_export_contact(self, reader: BufferReader):
        pubkey = reader.read_bytes(32)
        contact = self.contact_store.get_contact(pubkey)
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.ExportContact)
        if contact:
            writer.write_bytes(contact["public_key"])
            writer.write_string(contact.get("name", ""))
        await self.send_from_node(writer.to_bytes())

    async def handle_import_contact(self, reader: BufferReader):
        advert_packet_bytes = reader.read_remaining_bytes()
        self.contact_store.add_contact({"public_key": advert_packet_bytes, "name": "Imported"})
        writer = BufferWriter()
        writer.write_uint8(Constants.ResponseCodes.Ok)
        await self.send_from_node(writer.to_bytes())
