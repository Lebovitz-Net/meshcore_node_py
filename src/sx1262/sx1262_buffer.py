# sx1262_buffer.py
class SX1262Buffer:
    OP_READ_BUFFER = 0x1E

    def write_buffer(self, offset: int, data: bytes):
        """Write payload to FIFO buffer."""
        # WriteBuffer opcode = 0x0E
        return self._spi_cmd(0x0E, [offset] + list(data))

    def read_buffer(self, offset, length):
        tx = [0x1E, offset, 0x00] + [0x00] * length
        resp = self.spi.xfer2(tx)
        return resp[3:3+length]



    def set_buffer_base(self, tx_base: int, rx_base: int):
        """Configure FIFO base addresses."""
        # SetBufferBaseAddress opcode = 0x8F
        return self._spi_cmd(0x8F, [tx_base, rx_base])
