# sx1262.py
import spidev
import RPi.GPIO as GPIO
import time

from .sx1262_buffer import SX1262Buffer
from .sx1262_config import SX1262Config
from .sx1262_mode import SX1262Mode
from .sx1262_status import SX1262Status

# Waveshare SPI HAT pin mapping
RST_PIN  = 18   # Reset
BUSY_PIN = 20   # BUSY (active-high)
DIO1_PIN = 16   # DIO1 (IRQ: RX_DONE, TIMEOUT, CRC_ERR)
TXEN_PIN = 6    # TX enable (Waveshare uses only TXEN)
RXEN_PIN = -1   # Not wired on Waveshare HAT

# IRQ masks (SX1262)
IRQ_TX_DONE   = 0x0001
IRQ_RX_DONE   = 0x0040
IRQ_TIMEOUT   = 0x0080
IRQ_CRC_ERR   = 0x0020
IRQ_ALL       = 0xFFFF

# Common opcodes (subset)
OP_SET_STANDBY         = 0x80
OP_SET_RX              = 0x82
OP_SET_TX              = 0x83
OP_SET_SLEEP           = 0x84
OP_SET_PACKET_TYPE     = 0x8A
OP_SET_RF_FREQUENCY    = 0x86
OP_SET_DIO_IRQ_PARAMS  = 0x08
OP_CLEAR_IRQ_STATUS    = 0x02
OP_GET_IRQ_STATUS      = 0x12
OP_READ_BUFFER         = 0x1E
OP_WRITE_BUFFER        = 0x0E
OP_GET_RX_BUFFER_STATUS= 0x13
OP_GET_PACKET_STATUS   = 0x14
OP_SET_DIO2_RF_SWITCH  = 0x97
OP_SET_DIO3_TCXO       = 0x9D
OP_GET_STATUS          = 0xC0

class SX1262(SX1262Buffer, SX1262Config, SX1262Mode, SX1262Status):
    def __init__(self, spi_bus=0, spi_dev=None, max_speed=500000):
        # If no device specified, probe automatically
        if spi_dev is None:
            spi_dev = self.probe_spi_device(spi_bus)
            if spi_dev is None:
                raise RuntimeError("No SX1262 found on CE0 or CE1")

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
        GPIO.setup(TXEN_PIN, GPIO.OUT)
        if RXEN_PIN != -1:
            GPIO.setup(RXEN_PIN, GPIO.OUT)

        # SPI setup
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_dev)           # /dev/spidev0.0 by default
        self.spi.max_speed_hz = max_speed
        self.spi.mode = 0

        # Reset chip
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.01)

        # Enter standby (RC oscillator)
        self._spi_cmd(OP_SET_STANDBY, [0x00])

        # Configure RF switch (DIO2) and TCXO (DIO3: 1.8V, 2ms)
        self._spi_cmd(OP_SET_DIO2_RF_SWITCH, [0x00, 0x01, 0x00, 0x00])
        self._spi_cmd(OP_SET_DIO3_TCXO, [0x01, 0x02, 0x00])

        # Map IRQs to DIO1
        self.set_dio_irq_params(rx_done=True, timeout=True, crc_err=True)
        self.clear_irq()

        # Default TX/RX pins state (receive)
        GPIO.output(TXEN_PIN, GPIO.LOW)
        if RXEN_PIN != -1:
            GPIO.output(RXEN_PIN, GPIO.HIGH)

        print("SX1262 initialized: standby, TCXO, RF switch, IRQs mapped.")

    # -----------------------------
    # Low-level SPI helpers
    # -----------------------------

    def _wait_busy(self):
        # BUSY is active-high; wait while high
        while GPIO.input(BUSY_PIN) == 1:
            time.sleep(0.001)

    def _spi_cmd(self, opcode: int, params: list[int] = None):
        """Write-only SPI command with BUSY wait."""
        if params is None:
            params = []
        self._wait_busy()
        frame = [opcode] + params
        return self.spi.xfer2(frame)

    def _spi_cmd_read(self, opcode: int, params: list[int], read_len: int) -> list[int]:
        """Read SPI command: send opcode+params, clock out read_len bytes."""
        self._wait_busy()
        frame = [opcode] + (params or []) + ([0x00] * read_len)
        resp = self.spi.xfer2(frame)
        # Return only the trailing read_len bytes
        return resp[-read_len:]

    # -----------------------------
    # IRQ handling
    # -----------------------------

    def set_dio_irq_params(self, rx_done=True, tx_done=False, timeout=True, crc_err=True):
        irq_mask = 0
        if rx_done:  irq_mask |= IRQ_RX_DONE
        if tx_done:  irq_mask |= IRQ_TX_DONE
        if timeout:  irq_mask |= IRQ_TIMEOUT
        if crc_err:  irq_mask |= IRQ_CRC_ERR

        dio1_mask = irq_mask
        dio2_mask = 0x0000
        dio3_mask = 0x0000

        params = [
            (irq_mask >> 8) & 0xFF, irq_mask & 0xFF,
            (dio1_mask >> 8) & 0xFF, dio1_mask & 0xFF,
            (dio2_mask >> 8) & 0xFF, dio2_mask & 0xFF,
            (dio3_mask >> 8) & 0xFF, dio3_mask & 0xFF
        ]
        self._spi_cmd(OP_SET_DIO_IRQ_PARAMS, params)

    def clear_irq(self, mask: int = IRQ_ALL):
        self._spi_cmd(OP_CLEAR_IRQ_STATUS, [(mask >> 8) & 0xFF, mask & 0xFF])

    def get_irq_status(self) -> int:
        # Returns 2 bytes: IRQ status
        data = self._spi_cmd_read(OP_GET_IRQ_STATUS, [], 2)
        return (data[0] << 8) | data[1]

    # -----------------------------
    # TX/RX commands
    # -----------------------------

    def set_rx(self, timeout_ms: int):
        """Set RX with timeout; units are 15.625 µs (multiply ms by 64)."""
        tOut = int(timeout_ms * 64)
        params = [(tOut >> 16) & 0xFF, (tOut >> 8) & 0xFF, tOut & 0xFF]
        # Ensure pins are in RX state
        GPIO.output(TXEN_PIN, GPIO.LOW)
        if RXEN_PIN != -1:
            GPIO.output(RXEN_PIN, GPIO.HIGH)
        self._spi_cmd(OP_SET_RX, params)

    def set_tx(self, timeout_ms: int = 0):
        """Set TX with optional timeout; 0 means no timeout."""
        tOut = int(timeout_ms * 64)
        params = [(tOut >> 16) & 0xFF, (tOut >> 8) & 0xFF, tOut & 0xFF]
        # TX enable
        GPIO.output(TXEN_PIN, GPIO.HIGH)
        if RXEN_PIN != -1:
            GPIO.output(RXEN_PIN, GPIO.LOW)
        self._spi_cmd(OP_SET_TX, params)

    def write_buffer(self, offset: int, payload: bytes | list[int]):
        """Write payload into radio buffer at given offset."""
        if isinstance(payload, bytes):
            data = list(payload)
        else:
            data = payload
        self._spi_cmd(OP_WRITE_BUFFER, [offset] + data)

    def read_buffer(self, offset: int, length: int) -> bytes:
        """Read length bytes from radio buffer starting at offset."""
        # ReadBuffer returns data immediately after sending dummy bytes
        data = self._spi_cmd_read(OP_READ_BUFFER, [offset, 0x00], length)
        return bytes(data)

    def get_rx_buffer_status(self):
        """Return (payload_length, rx_start_buffer_pointer)."""
        data = self._spi_cmd_read(OP_GET_RX_BUFFER_STATUS, [], 2)
        payload_len = data[0]
        start_ptr = data[1]
        return payload_len, start_ptr

    def get_packet_status(self):
        """Return (rssi_pkt, snr_pkt, signal_rssi_pkt) raw values."""
        data = self._spi_cmd_read(OP_GET_PACKET_STATUS, [], 3)
        # Raw register format: rssiPkt, snrPkt, signalRssiPkt
        return data[0], data[1], data[2]

    # -----------------------------
    # Convenience and lifecycle
    # -----------------------------

    def monitor_busy(self, duration=2.0):
        start = time.time()
        while time.time() - start < duration:
            print(f"{time.time()-start:.3f}s BUSY={GPIO.input(BUSY_PIN)}")
            time.sleep(0.01)

    def close(self):
        try:
            # Sleep mode: cold start on next wake
            self._spi_cmd(OP_SET_SLEEP, [0x00])
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
        Configure LoRa and listen for packets, mirroring Waveshare's flow:
        - Packet type, frequency, modulation, packet params, sync word
        - IRQs mapped to DIO1
        - RX with timeout
        - Poll DIO1 and read buffer on RX_DONE
        """

        # Configure for LoRa using your mixins
        self.set_packet_type_lora()
        self.set_frequency(freq_hz)
        self.set_modulation_params(sf=sf, bw_hz=bw_hz, cr=cr)
        self.set_packet_params(preamble_len=preamble_len,
                               explicit=True,
                               payload_len=payload_len,
                               crc_on=True,
                               iq_inverted=False)
        # Waveshare uses two-byte sync word 0x34, 0x44; mixin method may accept int
        self.set_sync_word(sync_word)

        # IRQ setup
        self.set_dio_irq_params(rx_done=True, timeout=True, crc_err=True)
        self.clear_irq()

        # Enter RX with timeout
        self.set_rx(timeout_ms)

        print(f"Listening on {freq_hz/1e6:.3f} MHz, SF{sf}, BW {bw_hz} Hz, CR 4/{cr}, payload {payload_len} bytes")

        try:
            while True:
                if GPIO.input(DIO1_PIN) == 1:
                    irq = self.get_irq_status()
                    # Clear immediately to avoid stale flags
                    self.clear_irq()

                    if irq & IRQ_RX_DONE:
                        # Get buffer status to know length and start pointer
                        plen, ptr = self.get_rx_buffer_status()
                        # Bound read to configured payload_len
                        length = min(plen, payload_len)
                        data = self.read_buffer(ptr, length)

                        # Optional: packet status
                        rssi_raw, snr_raw, sig_rssi_raw = self.get_packet_status()
                        rssi = -rssi_raw / 2.0
                        snr = snr_raw / 4.0
                        sig_rssi = -sig_rssi_raw / 2.0

                        print(f"RX_DONE: len={length}, RSSI={rssi:.1f} dBm, SNR={snr:.2f} dB, signalRSSI={sig_rssi:.1f} dBm")
                        print(f"Payload bytes: {list(data)}")

                        # Re-arm RX
                        self.set_rx(timeout_ms)

                    elif irq & IRQ_TIMEOUT:
                        print("RX timeout; re-arming RX")
                        self.set_rx(timeout_ms)

                    elif irq & IRQ_CRC_ERR:
                        print("CRC error; re-arming RX")
                        self.set_rx(timeout_ms)

                # Small sleep to avoid busy-spin
                time.sleep(0.001)

        except KeyboardInterrupt:
            print("Stopped listening")
        finally:
            # Put TX/RX pins to safe state
            GPIO.output(TXEN_PIN, GPIO.LOW)
            if RXEN_PIN != -1:
                GPIO.output(RXEN_PIN, GPIO.LOW)

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

                # Send GetStatus (0xC0) with one dummy byte
                resp = spi.xfer2([0xC0, 0x00])
                spi.close()

                # If response is not all zeros, assume chip is alive
                if any(resp):
                    print(f"SPI device /dev/spidev{bus}.{dev} responded: {resp}")
                    return dev
                else:
                    print(f"SPI device /dev/spidev{bus}.{dev} gave no response")
            except Exception as e:
                print(f"Error probing /dev/spidev{bus}.{dev}: {e}")
        return None
