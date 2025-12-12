# sx1262.py
import spidev
import RPi.GPIO as GPIO
import time

from .sx1262_buffer import SX1262Buffer
from .sx1262_config import SX1262Config
from .sx1262_mode import SX1262Mode
from .sx1262_status import SX1262Status
from .sx1262_cmds import SX1262Cmds

# Waveshare-style SPI HAT pin mapping (no TXEN/RXEN variant)
RST_PIN  = 18   # Reset
BUSY_PIN = 20   # BUSY (active-high)
DIO1_PIN = 16   # DIO1 (IRQ: RX_DONE, TIMEOUT, CRC_ERR)

class SX1262(SX1262Buffer, SX1262Config, SX1262Mode, SX1262Status, SX1262Cmds):
    def __init__(self, spi_bus=0, spi_dev=None, max_speed=500000, use_tcxo=True):
        # Probe SPI device if not specified
        if spi_dev is None:
            spi_dev = self.probe_spi_device(spi_bus)
            if spi_dev is None:
                raise RuntimeError("No SX1262 found on CE0 or CE1")

        # SPI setup
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_dev)
        self.spi.max_speed_hz = max_speed
        self.spi.mode = 0
        print(f"SX1262 bound to /dev/spidev{spi_bus}.{spi_dev}")

        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RST_PIN, GPIO.OUT)
        GPIO.setup(BUSY_PIN, GPIO.IN)
        GPIO.setup(DIO1_PIN, GPIO.IN)

        # Hardware reset
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.01)

        # Confirm chip responds
        status = self.get_status()
        print("Initial status:", hex(status))

        # Enter standby (RC oscillator)
        self.set_standby()

        # Configure RF switch via DIO2 (no TXEN/RXEN on this board)
        self.set_dio2_rf_switch(True)

        # Configure TCXO via DIO3 if present
        if use_tcxo:
            self.set_dio3_tcxo(voltage=0x02, delay=0x02, trim=0x00)

        # Map IRQs to DIO1 and clear any stale flags
        self.set_dio_irq_params(rx_done=True, timeout=True, crc_err=True)
        self.clear_irq()

        print("SX1262 initialized: standby, RF switch, TCXO (optional), IRQs mapped.")

    # -----------------------------
    # IRQ mapping
    # -----------------------------

    def set_dio_irq_params(self, rx_done=True, tx_done=False, timeout=True, crc_err=True):
        irq_mask = 0
        if rx_done:  irq_mask |= self.IRQ_RX_DONE
        if tx_done:  irq_mask |= self.IRQ_TX_DONE
        if timeout:  irq_mask |= self.IRQ_TIMEOUT
        if crc_err:  irq_mask |= self.IRQ_CRC_ERR

        dio1_mask = irq_mask
        dio2_mask = 0x0000
        dio3_mask = 0x0000

        params = [
            (irq_mask >> 8) & 0xFF, irq_mask & 0xFF,
            (dio1_mask >> 8) & 0xFF, dio1_mask & 0xFF,
            (dio2_mask >> 8) & 0xFF, dio2_mask & 0xFF,
            (dio3_mask >> 8) & 0xFF, dio3_mask & 0xFF
        ]
        self._spi_cmd(self.OP_SET_DIO_IRQ_PARAMS, params)

    # -----------------------------
    # Lifecycle helpers
    # -----------------------------

    def monitor_busy(self, duration=2.0):
        start = time.time()
        while time.time() - start < duration:
            print(f"{time.time()-start:.3f}s BUSY={GPIO.input(BUSY_PIN)}")
            time.sleep(0.01)

    def close(self):
        try:
            self.set_sleep()
        except Exception:
            pass
        try:
            self.spi.close()
        finally:
            GPIO.cleanup()
        print("SX1262 shutdown complete.")

    # -----------------------------
    # High-level receive example
    # -----------------------------
    def listen(self, freq_hz=868_000_000, sf=7, bw_hz=125_000, cr=5,
            preamble_len=12, payload_len=64, sync_word=0x3444, timeout_ms=5000):
        """
        Configure LoRa and listen for packets.
        Polls IRQ status via SPI instead of relying on DIO1.
        """

        # Configure radio
        self.set_packet_type_lora()
        self.set_frequency(freq_hz)
        self.set_modulation_params(sf=sf, bw_hz=bw_hz, cr=cr)
        # self.set_packet_params(preamble_len=preamble_len,
        #                     explicit=True,
        #                     payload_len=payload_len,
        #                     crc_on=True,
        #                     iq_inverted=False)
        # self.set_sync_word(sync_word)
        
        self.set_packet_params(
            preamble_len=8,
            explicit=True,
            payload_len=255,
            crc_on=False,       # disable temporarily
            iq_inverted=False
        )
        self.set_sync_word(0x12)


        # IRQ setup
        self.set_dio_irq_params(rx_done=True, timeout=True, crc_err=True)
        self.clear_irq()

        # Enter RX mode
        self.set_rx(timeout_ms)

        print(f"Listening on {freq_hz/1e6:.3f} MHz, SF{sf}, BW {bw_hz} Hz, CR 4/{cr}, payload {payload_len} bytes")

        try:
            while True:
                # Poll IRQ status directly over SPI
                irq = self.get_irq_status()

                if irq:
                    self.clear_irq()

                    if irq & self.IRQ_RX_DONE:
                        plen, ptr = self.get_rx_buffer_status()
                        length = min(plen, payload_len)
                        data = self.read_buffer(ptr, length)

                        rssi_raw, snr_raw, sig_rssi_raw = self.get_packet_status()
                        rssi = -rssi_raw / 2.0
                        snr = (snr_raw - 256 if snr_raw > 127 else snr_raw) / 4.0
                        sig_rssi = -sig_rssi_raw / 2.0

                        print(f"RX_DONE: len={length}, RSSI={rssi:.1f} dBm, SNR={snr:.2f} dB, signalRSSI={sig_rssi:.1f} dBm")
                        print(f"Payload bytes: {list(data)}")

                        # Re‑arm RX
                        self.set_rx(timeout_ms)

                    elif irq & self.IRQ_TIMEOUT:
                        print("RX timeout; re‑arming RX")
                        self.set_rx(timeout_ms)

                    elif irq & self.IRQ_CRC_ERR:
                        print("CRC error; re‑arming RX")
                        self.set_rx(timeout_ms)

                time.sleep(0.01)  # small polling delay

        except KeyboardInterrupt:
            print("Stopped listening")


    # -----------------------------
    # spi device probing
    # -----------------------------

    def probe_spi_device(self, bus=0):
        """
        Probe both CE0 (/dev/spidev0.0) and CE1 (/dev/spidev0.1).
        Returns the device index (0 or 1) that responds to GetStatus.
        """
        for dev in [0, 1]:
            try:
                spi = spidev.SpiDev()
                spi.open(bus, dev)
                spi.max_speed_hz = 500000
                spi.mode = 0

                resp = spi.xfer2([self.OP_GET_STATUS, 0x00])
                spi.close()

                if any(resp):
                    print(f"SPI device /dev/spidev{bus}.{dev} responded: {resp}")
                    return dev
                else:
                    print(f"SPI device /dev/spidev{bus}.{dev} gave no response")
            except Exception as e:
                print(f"Error probing /dev/spidev{bus}.{dev}: {e}")
        return None
