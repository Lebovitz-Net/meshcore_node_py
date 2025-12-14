# sx1262_rx.py
import time
import spidev
import RPi.GPIO as GPIO

# Pin mapping for Waveshare SX1262 HAT
RST_PIN  = 18
BUSY_PIN = 20
DIO1_PIN = 16

class SX1262:
    # IRQ masks
    IRQ_TX_DONE   = 0x0001
    IRQ_RX_DONE   = 0x0040
    IRQ_TIMEOUT   = 0x0080
    IRQ_CRC_ERR   = 0x0020
    IRQ_ALL       = 0xFFFF

    # Opcodes
    OP_SET_STANDBY         = 0x80
    OP_SET_RX              = 0x82
    OP_CLEAR_IRQ_STATUS    = 0x02
    OP_GET_IRQ_STATUS      = 0x12
    OP_GET_STATUS          = 0xC0
    OP_SET_PACKET_TYPE     = 0x8A
    OP_SET_RF_FREQUENCY    = 0x86
    OP_SET_MOD_PARAMS      = 0x8B
    OP_SET_PKT_PARAMS      = 0x8C
    OP_WRITE_REGISTER      = 0x0D
    OP_GET_RX_BUFFER_STATUS = 0x13

    def __init__(self, spi_bus=0, spi_dev=0, max_speed=500000):
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_dev)
        self.spi.max_speed_hz = max_speed
        self.spi.mode = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RST_PIN, GPIO.OUT)
        GPIO.setup(BUSY_PIN, GPIO.IN)
        GPIO.setup(DIO1_PIN, GPIO.IN)

        # Reset chip
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.01)

        print("SX1262 initialized")

    def _wait_busy(self):
        while GPIO.input(BUSY_PIN) == 1:
            time.sleep(0.001)

    def _spi_cmd(self, opcode, params=None):
        if params is None:
            params = []
        self._wait_busy()
        return self.spi.xfer2([opcode] + params)

    def _spi_cmd_read(self, opcode, params=None, read_len=1):
        if params is None:
            params = []
        self._wait_busy()
        frame = [opcode] + params + ([0x00] * read_len)
        resp = self.spi.xfer2(frame)
        return resp[-read_len:]

    # --- Config methods ---
    def set_packet_type_lora(self):
        self._spi_cmd(self.OP_SET_PACKET_TYPE, [0x01])

    def set_frequency(self, freq_hz):
        frf = int(freq_hz * (1 << 25) / 32_000_000)
        self._spi_cmd(self.OP_SET_RF_FREQUENCY, list(frf.to_bytes(4, 'big')))

    def set_modulation_params(self, sf=7, bw_hz=125000, cr=5):
        bw_map = {7800:0x00,10400:0x01,15600:0x02,20800:0x03,
                  31250:0x04,41700:0x05,62500:0x06,125000:0x07,
                  250000:0x08,500000:0x09}
        bw_code = bw_map.get(bw_hz, 0x07)
        cr_map = {5:0x01,6:0x02,7:0x03,8:0x04}
        cr_code = cr_map.get(cr, 0x01)
        ldro = 0x00
        self._spi_cmd(self.OP_SET_MOD_PARAMS, [sf & 0x0F, bw_code & 0x0F, cr_code & 0x0F, ldro])

    def set_packet_params(self, preamble_len=8, payload_len=64, crc_on=True, explicit=True):
        header_type = 0x00 if explicit else 0x01
        crc = 0x01 if crc_on else 0x00
        iq = 0x00
        self._spi_cmd(self.OP_SET_PKT_PARAMS, [
            (preamble_len >> 8) & 0xFF,
            preamble_len & 0xFF,
            header_type,
            payload_len & 0xFF,
            crc,
            iq
        ])

    def set_sync_word(self, word=0x3444):
        # WriteRegister opcode = 0x0D, address 0x0740
        self._spi_cmd(self.OP_WRITE_REGISTER,
                      [0x07,0x40,(word>>8)&0xFF,word&0xFF])

    # --- RX helpers ---
    def set_rx(self, timeout_ms=0):
        tOut = int(timeout_ms * 64)
        params = [(tOut >> 16) & 0xFF, (tOut >> 8) & 0xFF, tOut & 0xFF]
        self._spi_cmd(self.OP_SET_RX, params)

    def clear_irq(self, mask=IRQ_ALL):
        self._spi_cmd(self.OP_CLEAR_IRQ_STATUS, [(mask >> 8) & 0xFF, mask & 0xFF])

    def get_irq_status(self):
        data = self._spi_cmd_read(self.OP_GET_IRQ_STATUS, [], 2)
        return (data[0] << 8) | data[1]

    def get_rx_buffer_status(self):
        resp = self._spi_cmd_read(self.OP_GET_RX_BUFFER_STATUS, [0x00], 2)
        return resp[0], resp[1]

    # --- Example listen loop ---
    def listen(self, freq_hz=915_000_000, sf=7, bw_hz=125_000, cr=5):
        """
        Continuous receive mode with automatic IRQ clearing and re‑arming.
        Call with (freq_hz, sf, bw_hz, cr) just like before.
        """

        # Configure radio
        self.set_packet_type_lora()
        self.set_frequency(freq_hz)
        self.set_modulation_params(sf=sf, bw_hz=bw_hz, cr=cr)
        self.set_packet_params(8, True, 255, True)
        self.set_sync_word(0x3444)  # ✅ public sync word

        # Clear stale IRQs
        self.clear_irq()

        # Enter continuous RX (timeout=0)
        self.set_rx(0)

        print(f"Listening continuously on {freq_hz/1e6:.3f} MHz, SF{sf}, BW {bw_hz} Hz, CR 4/{cr}")

        try:
            while True:
                irq = self.get_irq_status()
                if irq:
                    self.clear_irq()

                    if irq & self.IRQ_RX_DONE:
                        plen, ptr = self.get_rx_buffer_status()
                        if plen > 0:
                            data = self.read_buffer(ptr, plen)
                            print(f"RX_DONE: len={plen}, ptr={ptr}, payload={list(data)}")
                        else:
                            print("RX_DONE: empty packet")
                        self.set_rx(0)  # re‑arm continuous RX

                    elif irq & self.IRQ_CRC_ERR:
                        plen, ptr = self.get_rx_buffer_status()
                        if plen > 0:
                            data = self.read_buffer(ptr, plen)
                            print(f"CRC error, raw payload={list(data)}")
                        else:
                            print("CRC error, no payload")
                        self.set_rx(0)

                    elif irq & self.IRQ_TIMEOUT:
                        print("RX timeout, re‑arming RX")
                        self.set_rx(0)

                time.sleep(0.05)

        except KeyboardInterrupt:
            print("Stopped listening")


if __name__ == "__main__":
    radio = SX1262()
    radio.listen(910525000, 7, 62500, 5)
