import struct

class BufferWriter:
    def __init__(self):
        self.buffer = bytearray()

    def to_bytes(self) -> bytes:
        """Return the accumulated buffer as immutable bytes."""
        return bytes(self.buffer)

    def write_bytes(self, data: bytes | bytearray):
        """Append raw bytes to the buffer."""
        self.buffer.extend(data)

    def write_byte(self, value: int):
        """Append a single byte."""
        self.buffer.append(value & 0xFF)

    def write_uint16_le(self, value: int):
        """Append a 16‑bit unsigned integer (little‑endian)."""
        self.buffer.extend(struct.pack("<H", value))

    def write_uint32_le(self, value: int):
        """Append a 32‑bit unsigned integer (little‑endian)."""
        self.buffer.extend(struct.pack("<I", value))

    def write_int32_le(self, value: int):
        """Append a 32‑bit signed integer (little‑endian)."""
        self.buffer.extend(struct.pack("<i", value))

    def write_string(self, text: str):
        """Append a UTF‑8 encoded string (no terminator)."""
        self.buffer.extend(text.encode("utf-8"))

    def write_cstring(self, text: str, max_length: int):
        """
        Append a fixed‑length C‑string (null‑terminated).
        - Encodes to UTF‑8.
        - Truncates if longer than max_length-1.
        - Pads with zeros up to max_length.
        """
        encoded = text.encode("utf-8")
        # truncate if necessary
        encoded = encoded[: max_length - 1]
        # pad with zeros
        padded = encoded + b"\x00" * (max_length - len(encoded))
        self.buffer.extend(padded)
