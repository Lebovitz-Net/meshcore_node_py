# sx1262.py
import spidev
import RPi.GPIO as GPIO
import time

class SX1262Mode:

    def enter_rx_continuous(self):
        """Enter continuous RX mode."""
        self._wait_busy()
        self.spi.xfer2([0x82, 0x00, 0x00, 0x00])

    def enter_rx_window(self, timeout_ms: int):
        """Enter RX mode with timeout."""
        t = int(timeout_ms / 15.625)  # convert ms to register units
        self._wait_busy()
        self.spi.xfer2([0x82] + list(t.to_bytes(3, 'big')))

    def enter_tx(self, payload: bytes, timeout_ms: int = 0):
        """Transmit payload with optional timeout."""
        self.send(payload)
        t = int(timeout_ms / 15.625)
        self._wait_busy()
        self.spi.xfer2([0x83] + list(t.to_bytes(3, 'big')))

    def sleep(self):
        """Put radio into sleep mode."""
        self._wait_busy()
        self.spi.xfer2([0x84, 0x00])

    def standby(self):
        """Put radio into standby mode."""
        self._wait_busy()
        self.spi.xfer2([0x80, 0x00])
