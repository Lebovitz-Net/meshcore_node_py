#!/usr/bin/env python3
import spidev, RPi.GPIO as GPIO, time

class SX1262:
    # IRQ masks
    IRQ_RX_DONE   = 0x0001
    IRQ_TIMEOUT   = 0x0002
    IRQ_CRC_ERR   = 0x0004

    def __init__(self, spi_bus=0, spi_dev=0, busy_pin=24, irq_pin=23, reset_pin=22):
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_dev)
        self.spi.max_speed_hz = 5000000
        self.spi.mode = 0

        self.busy_pin = busy_pin
        self.irq_pin = irq_pin
        self.reset_pin = reset_pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.busy_pin, GPIO.IN)
        GPIO.setup(self.irq_pin, GPIO.IN)
        GPIO.setup(self.reset_pin, GPIO.OUT)

        self.reset()
        print("SX1262 initialized")

    def _wait_busy(self):
        while GPIO.input(self.busy_pin):
            time.sleep(0.001)

    def reset(self):
        GPIO.output(self.reset_pin, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(self.reset_pin, GPIO.HIGH)
        time.sleep(0.01)

    def spi_cmd(self, buf, read_len=0):
        self._wait_busy()
        resp = self.spi.xfer2(buf + [0x00]*read_len)
        return resp

    def set_packet_type_lora(self):
        self.spi_cmd([0x8A, 0x01])  # SetPacketType LoRa

    def set_frequency(self, freq_hz):
        frf = int((freq_hz << 25) / 32000000)
        buf = [0x86,
               (frf >> 24) & 0xFF,
               (frf >> 16) & 0xFF,
               (frf >> 8) & 0xFF,
               frf & 0xFF]
        self.spi_cmd(buf)

    def set_modulation_params(self, sf=7, bw_hz=125000, cr=5):
        bw_map = {7800:0x00, 10400:0x08, 15600:0x01, 20800:0x09,
                  31200:0x02, 41700:0x0A, 62500:0x03, 125000:0x04,
                  250000:0x05, 500000:0x06}
        bw_code = bw_map.get(bw_hz, 0x04)
        cr_code = {5:0x01, 6:0x02, 7:0x03, 8:0x04}.get(cr, 0x01)
        self.spi_cmd([0x8B, sf<<4, bw_code, cr_code, 0x00])

    def set_packet_params(self, preamble_len=8, explicit=True,
                          payload_len=255, crc_on=True):
        hdr_type = 0x00 if explicit else 0x01
        crc_type = 0x01 if crc_on else 0x00
        buf = [0x8C,
               (preamble_len >> 8) & 0xFF,
               preamble_len & 0xFF,
               hdr_type,
               payload_len,
               crc_type,
               0x00]  # IQ normal
        self.spi_cmd(buf)

    def set_sync_word(self, sync=0x3444):
        self.spi_cmd([0x0B, (sync >> 8) & 0xFF, sync & 0xFF])

    def clear_irq(self):
        self.spi_cmd([0x02, 0xFF, 0xFF])

    def get_irq_status(self):
        resp = self.spi_cmd([0x12], 3)
        return (resp[1] << 8) | resp[2]

    def get_rx_buffer_status(self):
        resp = self.spi_cmd([0x13], 3)
        plen = resp[1]
        ptr = resp[2]
        return plen, ptr

    def read_buffer(self, offset, length):
        frame = [0x1E, offset, 0x00] + [0x00]*length
        resp = self.spi_cmd(frame, 0)
        return resp[3:3+length]

    def set_rx(self, timeout_ms=0):
        # timeout=0 => continuous RX
        period = 0xFFFFFF if timeout_ms == 0 else int(timeout_ms/15.625)
        buf = [0x82,
               (period >> 16) & 0xFF,
               (period >> 8) & 0xFF,
               period & 0xFF]
        self.spi_cmd(buf)

    def listen(self, freq_hz=915000000, sf=7, bw_hz=125000, cr=5):
        self.set_packet_type_lora()
        self.set_frequency(freq_hz)
        self.set_modulation_params(sf=sf, bw_hz=bw_hz, cr=cr)
        self.set_packet_params(8, True, 255, True)
        self.set_sync_word(0x3444)

        self.clear_irq()
        self.set_rx(0)  # continuous

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
                        self.set_rx(0)
                    elif irq & self.IRQ_CRC_ERR:
                        plen, ptr = self.get_rx_buffer_status()
                        if plen > 0:
                            data = self.read_buffer(ptr, plen)
                            print(f"CRC error, raw payload={list(data)}")
                        else:
                            print("CRC error, no payload")
                        self.set_rx(0)
                    elif irq & self.IRQ_TIMEOUT:
                        # print("RX timeout, re‑arming RX")
                        self.set_rx(0)
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("Stopped listening")

if __name__ == "__main__":
    radio = SX1262(spi_bus=0, spi_dev=0, busy_pin=20, irq_pin=16, reset_pin=18)
    radio.listen(910525000, 7, 62500, 5)
