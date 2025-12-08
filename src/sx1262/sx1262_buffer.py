# sx1262_buffer.py
class SX1262Buffer:
    def write_buffer(self, offset: int, data: bytes):
        """Write payload to FIFO buffer."""
        # WriteBuffer opcode = 0x0E
        return self._spi_cmd(0x0E, [offset] + list(data))

    def read_buffer(self, offset: int, length: int) -> bytes:
        """Read payload from FIFO buffer."""
        # ReadBuffer opcode = 0x1E
        # Format: [opcode, offset, dummy] + dummy bytes to clock out payload
        resp = self._spi_cmd(0x1E, [offset, 0x00] + [0x00] * length)
        # Response includes opcode echo + offset + dummy, so slice out payload
        return bytes(resp[3:])

    def set_buffer_base(self, tx_base: int, rx_base: int):
        """Configure FIFO base addresses."""
        # SetBufferBaseAddress opcode = 0x8F
        return self._spi_cmd(0x8F, [tx_base, rx_base])
