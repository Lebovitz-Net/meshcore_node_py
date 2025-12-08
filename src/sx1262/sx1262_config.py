# SX1262 Driver – Expanded Function Set

# sx1262.py
import spidev
import RPi.GPIO as GPIO
import time

class SX1262Config:
        
        def set_frequency(self, freq_hz: float):
            """Set carrier frequency in Hz."""
            frf = int(freq_hz / (32e6 / (2**25)))
            self._wait_busy()
            self.spi.xfer2([0x86] + list(frf.to_bytes(3, 'big')))

        def set_bandwidth(self, bw_hz: int):
            """Set LoRa bandwidth (discrete values)."""
            # Map Hz to register code per datasheet
            bw_map = {7800:0x00, 10400:0x01, 15600:0x02, 20800:0x03,
                    31250:0x04, 41700:0x05, 62500:0x06, 125000:0x07,
                    250000:0x08, 500000:0x09}
            code = bw_map.get(bw_hz, 0x07)
            self._wait_busy()
            self.spi.xfer2([0x8A, code])

        def set_spreading_factor(self, sf: int):
            """Set LoRa spreading factor (7–12)."""
            self._wait_busy()
            self.spi.xfer2([0x8B, sf])

        def set_coding_rate(self, cr: int):
            """Set LoRa coding rate (4/5 → 4/8)."""
            cr_map = {5:0x01, 6:0x02, 7:0x03, 8:0x04}
            code = cr_map.get(cr, 0x01)
            self._wait_busy()
            self.spi.xfer2([0x8C, code])

        def set_sync_word(self, word: int):
            """Set sync word (0x34 public, 0x12 private)."""
            self._wait_busy()
            self.spi.xfer2([0x8D, word])
