# sx1262.py
import spidev
import RPi.GPIO as GPIO
import time

from .sx1262_buffer import SX1262Buffer
from .sx1262_config import SX1262Config
from .sx1262_mode import SX1262Mode
from .sx1262_status import SX1262Status

# Pin mappings (check Waveshare docs for your variant)
CS_PIN   = 21   # Chip select
RST_PIN  = 18   # Reset
BUSY_PIN = 20   # Busy line
DIO1_PIN = 16   # Interrupt (RX/TX done)

class SX1262 (SX1262Buffer, SX1262Config, SX1262Mode, SX1262Status):

    def __init__(self, spi_bus=0, spi_dev=0, max_speed=500000):
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
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

    def _wait_busy(self):
        while GPIO.input(BUSY_PIN) == 1:
            time.sleep(0.001)

    def send(self, payload: bytes):
        """Send a packet over LoRa."""
        self._wait_busy()
        # Example: write buffer command (0x0E) then payload
        self.spi.xfer2([0x0E, 0x00] + list(payload))
        # Trigger TX (opcode 0x83 with timeout)
        self.spi.xfer2([0x83, 0x00, 0x00, 0x00])
        print("Packet sent:", payload)

    def read(self) -> bytes:
        """Read a packet if available."""
        if GPIO.input(DIO1_PIN) == 1:  # RX done IRQ
            self._wait_busy()
            # Read buffer command (0x1E)
            resp = self.spi.xfer2([0x1E, 0x00, 0x00])  # adjust length
            print("Received raw:", resp)
            return bytes(resp)
        print("no read")
        return b""

    def shutodwn(self):
        self.close()
    
    def close(self):
        """Shutdown the radio and release resources."""
        self._wait_busy()
        # Put chip into sleep (opcode 0x84)
        self.spi.xfer2([0x84, 0x00])
        self.spi.close()
        GPIO.cleanup()
        print("SX1262 shutdown complete.")

    # these are protbably deprecated

    def encode_freq(self, frequency_hz: float) -> bytes:
        # Datasheet-specific encoding
        freq_val = int(frequency_hz / 1e3)
        return freq_val.to_bytes(3, "little")

    def encode_bw(self, bandwidth_hz: float) -> bytes:
        bw_map = {62500: b"\x01", 125000: b"\x02", 250000: b"\x03"}
        return bw_map.get(int(bandwidth_hz), b"\x00")

    def encode_sf(self, sf: int) -> bytes:
        return bytes([sf])

    def encode_cr(self, cr: str) -> bytes:
        cr_map = {"4/5": b"\x01", "4/6": b"\x02", "4/7": b"\x03", "4/8": b"\x04"}
        return cr_map.get(cr, b"\x00")