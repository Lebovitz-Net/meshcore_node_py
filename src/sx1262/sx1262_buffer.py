import spidev
import RPi.GPIO as GPIO
import time

class SX1262Buffer:

    def write_buffer(self, offset: int, data: bytes):
        """Write payload to FIFO buffer."""
        self._wait_busy()
        self.spi.xfer2([0x0E, offset] + list(data))

    def read_buffer(self, offset: int, length: int) -> bytes:
        """Read payload from FIFO buffer."""
        self._wait_busy()
        resp = self.spi.xfer2([0x1E, offset, 0x00] + [0x00]*length)
        return bytes(resp[3:])

    def set_buffer_base(self, tx_base: int, rx_base: int):
        """Configure FIFO base addresses."""
        self._wait_busy()
        self.spi.xfer2([0x8F, tx_base, rx_base])
