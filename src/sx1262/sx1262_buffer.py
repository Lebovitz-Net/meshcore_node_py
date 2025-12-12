# sx1262_buffer.py
class SX1262Buffer:
    OP_READ_BUFFER = 0x1E

    def write_buffer(self, offset: int, data: bytes):
        """Write payload to FIFO buffer."""
        # WriteBuffer opcode = 0x0E
        return self._spi_cmd(0x0E, [offset] + list(data))

    def read_buffer(self, offset: int, length: int) -> bytes:
        """Read payload from FIFO buffer."""
        # Build transmit sequence
        tx = [self.OP_READ_BUFFER, offset, 0x00] + [0x00] * length
        # Use the read helper so we get back the response
        resp = self._spi_cmd_read(self.OP_READ_BUFFER, [offset, 0x00] + [0x00] * length, read_len=3+length)
        # Slice out the payload (skip opcode echo, offset, dummy)
        return bytes(resp[3:3+length])

    def set_buffer_base(self, tx_base: int, rx_base: int):
        """Configure FIFO base addresses."""
        # SetBufferBaseAddress opcode = 0x8F
        return self._spi_cmd(0x8F, [tx_base, rx_base])
