from .buffer_reader import BufferReader
from .buffer_writer import BufferWriter

try:
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError
    HAS_NACL = True
except ImportError:
    HAS_NACL = False


class Advert:
    ADV_TYPE_NONE = 0
    ADV_TYPE_CHAT = 1
    ADV_TYPE_REPEATER = 2
    ADV_TYPE_ROOM = 3

    ADV_LATLON_MASK = 0x10
    ADV_BATTERY_MASK = 0x20
    ADV_TEMPERATURE_MASK = 0x40
    ADV_NAME_MASK = 0x80

    def __init__(self, public_key: bytes, timestamp: int, signature: bytes, app_data: bytes):
        self.public_key = public_key
        self.timestamp = timestamp
        self.signature = signature
        self.app_data = app_data
        self.parsed = self.parse_app_data()

    @staticmethod
    def from_bytes(data: bytes) -> "Advert":
        br = BufferReader(data)
        public_key = br.read_bytes(32)
        timestamp = br.read_uint32_le()
        signature = br.read_bytes(64)
        app_data = br.read_remaining_bytes()
        return Advert(public_key, timestamp, signature, app_data)

    def get_flags(self) -> int:
        return self.app_data[0]

    def get_type(self) -> int:
        flags = self.get_flags()
        return flags & 0x0F

    def get_type_string(self) -> str | None:
        type_ = self.get_type()
        if type_ == Advert.ADV_TYPE_NONE:
            return "NONE"
        if type_ == Advert.ADV_TYPE_CHAT:
            return "CHAT"
        if type_ == Advert.ADV_TYPE_REPEATER:
            return "REPEATER"
        if type_ == Advert.ADV_TYPE_ROOM:
            return "ROOM"
        return None

    async def is_verified(self) -> bool:
        """
        Verify the advert signature using Ed25519.
        Requires PyNaCl installed.
        """
        if not HAS_NACL:
            raise RuntimeError("PyNaCl is required for signature verification")

        # build signed data
        bw = BufferWriter()
        bw.write_bytes(self.public_key)
        bw.write_uint32_le(self.timestamp)
        bw.write_bytes(self.app_data)
        signed_data = bw.to_bytes()

        try:
            vk = VerifyKey(self.public_key)
            vk.verify(signed_data, self.signature)
            return True
        except BadSignatureError:
            return False

    def parse_app_data(self) -> dict:
        br = BufferReader(self.app_data)
        flags = br.read_byte()

        lat = None
        lon = None
        if flags & Advert.ADV_LATLON_MASK:
            lat = br.read_int32_le()
            lon = br.read_int32_le()

        name = None
        if flags & Advert.ADV_NAME_MASK:
            name = br.read_string()

        return {
            "type": self.get_type_string(),
            "lat": lat,
            "lon": lon,
            "name": name,
        }
