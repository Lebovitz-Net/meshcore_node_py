import struct

class BufferReader:
    def __init__(self, data: bytes):
        self.pointer = 0
        # store as bytes for slicing
        self.buffer = data if isinstance(data, (bytes, bytearray)) else bytes(data)

    def get_remaining_bytes_count(self) -> int:
        return len(self.buffer) - self.pointer

    def read_byte(self) -> int:
        return self.read_bytes(1)[0]

    def read_bytes(self, count: int) -> bytes:
        data = self.buffer[self.pointer:self.pointer + count]
        self.pointer += count
        return data

    def read_remaining_bytes(self) -> bytes:
        return self.read_bytes(self.get_remaining_bytes_count())

    def read_string(self) -> str:
        return self.read_remaining_bytes().decode("utf-8", errors="ignore")

    def read_cstring(self, max_length: int) -> str:
        bytes_ = self.read_bytes(max_length)
        # stop at first null terminator
        terminator_index = bytes_.find(b"\x00")
        if terminator_index != -1:
            bytes_ = bytes_[:terminator_index]
        return bytes_.decode("utf-8", errors="ignore")

    def read_int8(self) -> int:
        return struct.unpack("b", self.read_bytes(1))[0]

    def read_uint8(self) -> int:
        return struct.unpack("B", self.read_bytes(1))[0]

    def read_uint16_le(self) -> int:
        return struct.unpack("<H", self.read_bytes(2))[0]

    def read_uint16_be(self) -> int:
        return struct.unpack(">H", self.read_bytes(2))[0]

    def read_uint32_le(self) -> int:
        return struct.unpack("<I", self.read_bytes(4))[0]

    def read_uint32_be(self) -> int:
        return struct.unpack(">I", self.read_bytes(4))[0]

    def read_int16_le(self) -> int:
        return struct.unpack("<h", self.read_bytes(2))[0]

    def read_int16_be(self) -> int:
        return struct.unpack(">h", self.read_bytes(2))[0]

    def read_int32_le(self) -> int:
        return struct.unpack("<i", self.read_bytes(4))[0]

    def read_int24_be(self) -> int:
        # read 3 bytes big endian
        b1, b2, b3 = self.read_bytes(3)
        value = (b1 << 16) | (b2 << 8) | b3
        # convert to signed 24-bit
        if value & 0x800000:
            value -= 0x1000000
        return value
