from .buffer_reader import BufferReader
from .advert import Advert

class Packet:
    # Packet::header values
    PH_ROUTE_MASK = 0x03   # 2-bits
    PH_TYPE_SHIFT = 2
    PH_TYPE_MASK = 0x0F    # 4-bits
    PH_VER_SHIFT = 6
    PH_VER_MASK = 0x03     # 2-bits

    ROUTE_TYPE_RESERVED1 = 0x00
    ROUTE_TYPE_FLOOD = 0x01
    ROUTE_TYPE_DIRECT = 0x02
    ROUTE_TYPE_RESERVED2 = 0x03

    PAYLOAD_TYPE_REQ = 0x00
    PAYLOAD_TYPE_RESPONSE = 0x01
    PAYLOAD_TYPE_TXT_MSG = 0x02
    PAYLOAD_TYPE_ACK = 0x03
    PAYLOAD_TYPE_ADVERT = 0x04
    PAYLOAD_TYPE_GRP_TXT = 0x05
    PAYLOAD_TYPE_GRP_DATA = 0x06
    PAYLOAD_TYPE_ANON_REQ = 0x07
    PAYLOAD_TYPE_PATH = 0x08
    PAYLOAD_TYPE_TRACE = 0x09
    PAYLOAD_TYPE_RAW_CUSTOM = 0x0F

    def __init__(self, header: int, path: bytes, payload: bytes):
        self.header = header
        self.path = path
        self.payload = payload

        # parsed info
        self.route_type = self.get_route_type()
        self.route_type_string = self.get_route_type_string()
        self.payload_type = self.get_payload_type()
        self.payload_type_string = self.get_payload_type_string()
        self.payload_version = self.get_payload_ver()
        self.is_marked_do_not_retransmit = self.is_marked_do_not_retransmit()

    @staticmethod
    def from_bytes(data: bytes) -> "Packet":
        buffer_reader = BufferReader(data)
        header = buffer_reader.read_byte()
        path_len = buffer_reader.read_int8()
        path = buffer_reader.read_bytes(path_len)
        payload = buffer_reader.read_remaining_bytes()
        return Packet(header, path, payload)

    def get_route_type(self) -> int:
        return self.header & Packet.PH_ROUTE_MASK

    def get_route_type_string(self) -> str | None:
        rt = self.get_route_type()
        if rt == Packet.ROUTE_TYPE_FLOOD:
            return "FLOOD"
        elif rt == Packet.ROUTE_TYPE_DIRECT:
            return "DIRECT"
        return None

    def is_route_flood(self) -> bool:
        return self.get_route_type() == Packet.ROUTE_TYPE_FLOOD

    def is_route_direct(self) -> bool:
        return self.get_route_type() == Packet.ROUTE_TYPE_DIRECT

    def get_payload_type(self) -> int:
        return (self.header >> Packet.PH_TYPE_SHIFT) & Packet.PH_TYPE_MASK

    def get_payload_type_string(self) -> str | None:
        pt = self.get_payload_type()
        return {
            Packet.PAYLOAD_TYPE_REQ: "REQ",
            Packet.PAYLOAD_TYPE_RESPONSE: "RESPONSE",
            Packet.PAYLOAD_TYPE_TXT_MSG: "TXT_MSG",
            Packet.PAYLOAD_TYPE_ACK: "ACK",
            Packet.PAYLOAD_TYPE_ADVERT: "ADVERT",
            Packet.PAYLOAD_TYPE_GRP_TXT: "GRP_TXT",
            Packet.PAYLOAD_TYPE_GRP_DATA: "GRP_DATA",
            Packet.PAYLOAD_TYPE_ANON_REQ: "ANON_REQ",
            Packet.PAYLOAD_TYPE_PATH: "PATH",
            Packet.PAYLOAD_TYPE_TRACE: "TRACE",
            Packet.PAYLOAD_TYPE_RAW_CUSTOM: "RAW_CUSTOM",
        }.get(pt, None)

    def get_payload_ver(self) -> int:
        return (self.header >> Packet.PH_VER_SHIFT) & Packet.PH_VER_MASK

    def mark_do_not_retransmit(self):
        self.header = 0xFF

    def is_marked_do_not_retransmit(self) -> bool:
        return self.header == 0xFF

    def parse_payload(self):
        pt = self.get_payload_type()
        if pt == Packet.PAYLOAD_TYPE_PATH:
            return self.parse_payload_type_path()
        elif pt == Packet.PAYLOAD_TYPE_REQ:
            return self.parse_payload_type_req()
        elif pt == Packet.PAYLOAD_TYPE_RESPONSE:
            return self.parse_payload_type_response()
        elif pt == Packet.PAYLOAD_TYPE_TXT_MSG:
            return self.parse_payload_type_txt_msg()
        elif pt == Packet.PAYLOAD_TYPE_ACK:
            return self.parse_payload_type_ack()
        elif pt == Packet.PAYLOAD_TYPE_ADVERT:
            return self.parse_payload_type_advert()
        elif pt == Packet.PAYLOAD_TYPE_ANON_REQ:
            return self.parse_payload_type_anon_req()
        return None

    def parse_payload_type_path(self):
        br = BufferReader(self.payload)
        dest = br.read_byte()
        src = br.read_byte()
        return {"src": src, "dest": dest}

    def parse_payload_type_req(self):
        br = BufferReader(self.payload)
        dest = br.read_byte()
        src = br.read_byte()
        encrypted = br.read_remaining_bytes()
        return {"src": src, "dest": dest, "encrypted": encrypted}

    def parse_payload_type_response(self):
        br = BufferReader(self.payload)
        dest = br.read_byte()
        src = br.read_byte()
        return {"src": src, "dest": dest}

    def parse_payload_type_txt_msg(self):
        br = BufferReader(self.payload)
        dest = br.read_byte()
        src = br.read_byte()
        return {"src": src, "dest": dest}

    def parse_payload_type_ack(self):
        return {"ack_code": self.payload}

    def parse_payload_type_advert(self):
        advert = Advert.from_bytes(self.payload)
        return {
            "public_key": advert.public_key,
            "timestamp": advert.timestamp,
            "app_data": advert.parse_app_data(),
        }

    def parse_payload_type_anon_req(self):
        br = BufferReader(self.payload)
        dest = br.read_byte()
        src_public_key = br.read_bytes(32)
        return {"src": src_public_key, "dest": dest}
