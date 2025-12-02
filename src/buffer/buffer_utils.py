import base64

class BufferUtils:
    @staticmethod
    def bytes_to_hex(data: bytes) -> str:
        """
        Convert bytes/bytearray to hex string.
        """
        return data.hex()

    @staticmethod
    def hex_to_bytes(hex_str: str) -> bytes:
        """
        Convert hex string to bytes.
        """
        return bytes.fromhex(hex_str)

    @staticmethod
    def base64_to_bytes(b64_str: str) -> bytes:
        """
        Convert base64 string to bytes.
        """
        return base64.b64decode(b64_str)

    @staticmethod
    def are_buffers_equal(buf1: bytes, buf2: bytes) -> bool:
        """
        Compare two byte sequences for equality.
        """
        return buf1 == buf2
