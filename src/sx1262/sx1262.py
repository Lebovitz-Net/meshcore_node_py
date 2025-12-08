# sx1262.py
import spidev
import RPi.GPIO as GPIO
import time

from .sx1262_buffer import SX1262Buffer
from .sx1262_config import SX1262Config
from .sx1262_mode import SX1262Mode
from .sx1262_status import SX1262Status

CS_PIN   = 21   # Chip select
RST_PIN  = 18   # Reset
BUSY_PIN = 20   # Busy line
DIO1_PIN = 16   # Interrupt (RX/TX done)

class SX1262(SX1262Buffer, SX1262Config, SX1262Mode, SX1262Status):
    def __init__(self, spi_bus=0, spi_dev=0, max_speed=500000):
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(RST_PIN, GPIO.OUT)
        GPIO.setup(BUSY_PIN, GPIO.IN)
        GPIO.setup(DIO1_PIN, GPIO.IN)

        # Setup SPI
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_dev)
        self.spi.max_speed_hz = max_speed

        # Reset chip
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.01)

        # Configure IRQ mapping once at startup
        self.set_dio_irq_params(rx_done=True, tx_done=True, timeout=True, crc_err=True)
        self.clear_irq()

        print("SX1262 initialized and IRQs mapped to DIO1")

    def set_dio_irq_params(self, rx_done=True, tx_done=True, timeout=True, crc_err=True):
        """Map IRQs to DIO1 (RX/TX done, timeout, CRC error)."""
        IRQ_RX_DONE   = 0x0040
        IRQ_TX_DONE   = 0x0001
        IRQ_TIMEOUT   = 0x0080
        IRQ_CRC_ERR   = 0x0020

        irq_mask = 0
        if rx_done: irq_mask |= IRQ_RX_DONE
        if tx_done: irq_mask |= IRQ_TX_DONE
        if timeout: irq_mask |= IRQ_TIMEOUT
        if crc_err: irq_mask |= IRQ_CRC_ERR

        dio1_mask = irq_mask
        dio2_mask = 0x0000
        dio3_mask = 0x0000

        return self._spi_cmd(0x08, [
            (irq_mask >> 8) & 0xFF, irq_mask & 0xFF,
            (dio1_mask >> 8) & 0xFF, dio1_mask & 0xFF,
            (dio2_mask >> 8) & 0xFF, dio2_mask & 0xFF,
            (dio3_mask >> 8) & 0xFF, dio3_mask & 0xFF
        ])

    def clear_irq(self, mask: int = 0xFFFF):
        """Clear IRQ flags (default: all)."""
        return self._spi_cmd(0x02, [(mask >> 8) & 0xFF, mask & 0xFF])

 
    def _wait_busy(self):
        while GPIO.input(BUSY_PIN) == 1:
            time.sleep(0.001)

    def _spi_cmd(self, opcode: int, params: list[int] = None):
        """General SPI command wrapper with BUSY wait."""
        if params is None:
            params = []
        self._wait_busy()
        frame = [opcode] + params
        return self.spi.xfer2(frame)

    def send(self, payload: bytes):
        """Send a packet over LoRa."""
        # WriteBuffer (0x0E) then payload
        self._spi_cmd(0x0E, [0x00] + list(payload))
        # Trigger TX (SetTx opcode 0x83 with timeout)
        self._spi_cmd(0x83, [0x00, 0x00, 0x00])
        print("Packet sent:", payload)

    def read(self) -> bytes:
        """Read a packet if available."""
        if GPIO.input(DIO1_PIN) == 1:  # RX done IRQ
            # ReadBuffer (0x1E)
            resp = self._spi_cmd(0x1E, [0x00, 0x00])  # adjust length as needed
            print("Received raw:", resp)
            return bytes(resp)
        return b""

    def shutdown(self):
        self.close()

    def close(self):
        """Shutdown the radio and release resources."""
        # Put chip into sleep (opcode 0x84)
        self._spi_cmd(0x84, [0x00])
        self.spi.close()
        GPIO.cleanup()
        print("SX1262 shutdown complete.")
