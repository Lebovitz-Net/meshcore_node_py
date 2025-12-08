import spidev
import RPi.GPIO as GPIO
import time

class SX1262Status:

    def get_irq_status(self) -> int:
        """Read IRQ flags."""
        self._wait_busy()
        resp = self.spi.xfer2([0x15, 0x00, 0x00])
        return (resp[1] << 8) | resp[2]

    def clear_irq_status(self):
        """Clear IRQ flags."""
        self._wait_busy()
        self.spi.xfer2([0x97, 0xFF, 0xFF])

    def get_rssi(self) -> int:
        """Read RSSI value."""
        self._wait_busy()
        resp = self.spi.xfer2([0x1B, 0x00])
        return resp[1]

    def get_snr(self) -> int:
        """Read SNR value."""
        self._wait_busy()
        resp = self.spi.xfer2([0x1C, 0x00])
        return resp[1]

    def get_device_status(self) -> int:
        """Read device status."""
        self._wait_busy()
        resp = self.spi.xfer2([0xC0, 0x00])
        return resp[1]
