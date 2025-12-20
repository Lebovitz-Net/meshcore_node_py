#!/usr/bin/env python3
import time
import spidev
import RPi.GPIO as GPIO

from sx1262.sx1262_constants import (
    # commands
    SET_STANDBY, SET_REGULATOR_MODE, SET_PACKET_TYPE, SET_BUFFER_BASE_ADDRESS,
    SET_DIO2_RF_SWITCH_CTRL, SET_DIO_IRQ_PARAMS,
    SET_RF_FREQUENCY, SET_MODULATION_PARAMS, SET_PACKET_PARAMS,
    SET_SYNC_WORD, SET_RX, CLEAR_IRQ_STATUS, GET_IRQ_STATUS,
    GET_RX_BUFFER_STATUS, READ_BUFFER, GET_PACKET_STATUS,
    # modes
    STDBY_RC, REG_MODE_LDO, PACKET_TYPE_LORA,
    # IRQ
    IRQ_RX_DONE, IRQ_CRC_ERR, IRQ_TIMEOUT, IRQ_ALL,
    # LoRa params
    LORA_BW_62_5_KHZ, LORA_BW_125_KHZ,
    LORA_CR_4_5, LORA_HEADER_EXPLICIT,
    LORA_CRC_ON, LORA_IQ_NORMAL,
    MESHTASTIC_SYNCWORD,
    RX_BASE_DEFAULT, TX_BASE_DEFAULT,
)

class SX1262:
    def __init__(self, spi_bus=0, spi_dev=0, busy_pin=20, irq_pin=16, reset_pin=18):
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_dev)
        self.spi.max_speed_hz = 1_000_000
        self.spi.mode = 0

        self.busy_pin = busy_pin
        self.irq_pin = irq_pin
        self.reset_pin = reset_pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.busy_pin, GPIO.IN)
        GPIO.setup(self.irq_pin, GPIO.IN)
        GPIO.setup(self.reset_pin, GPIO.OUT)

        self.reset()
        print("SX1262 reset")

        self.base_init()

    # ---------- low-level ----------

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
        resp = self.spi.xfer2(buf + [0x00] * read_len)
        return resp

    # ---------- required init sequence ----------

    def base_init(self):
        # 1) Standby RC
        self.spi_cmd([SET_STANDBY, STDBY_RC])
        # 2) Regulator mode LDO
        self.spi_cmd([SET_REGULATOR_MODE, REG_MODE_LDO])
        # 3) Packet type LoRa
        self.spi_cmd([SET_PACKET_TYPE, PACKET_TYPE_LORA])
        # 4) Buffer base addresses
        self.spi_cmd([SET_BUFFER_BASE_ADDRESS, RX_BASE_DEFAULT, TX_BASE_DEFAULT])
        # 5) DIO2 as RF switch
        self.spi_cmd([SET_DIO2_RF_SWITCH_CTRL, 0x01])
        # 6) DIO IRQ params (RX_DONE, CRC_ERR, TIMEOUT -> DIO1)
        irq_mask = IRQ_RX_DONE | IRQ_CRC_ERR | IRQ_TIMEOUT
        self.spi_cmd([
            SET_DIO_IRQ_PARAMS,
            (irq_mask >> 8) & 0xFF, irq_mask & 0xFF,
            (irq_mask >> 8) & 0xFF, irq_mask & 0xFF,  # DIO1
            0x00, 0x00,                               # DIO2
            0x00, 0x00,                               # DIO3
        ])
        print("SX1262 base init done")

    # ---------- LoRa config ----------

    def set_frequency(self, freq_hz):
        frf = int(freq_hz * (1 << 25) / 32_000_000)
        self.spi_cmd([
            SET_RF_FREQUENCY,
            (frf >> 24) & 0xFF,
            (frf >> 16) & 0xFF,
            (frf >> 8) & 0xFF,
            frf & 0xFF,
        ])

    def set_modulation_params(self, sf=7, bw_hz=62_500, cr=5):
        bw_map = {
            7_800: 0x00, 10_400: 0x08, 15_600: 0x01, 20_800: 0x09,
            31_250: 0x02, 41_700: 0x0A, 62_500: 0x03, 125_000: 0x04,
            250_000: 0x05, 500_000: 0x06,
        }
        bw_code = bw_map.get(bw_hz, LORA_BW_125_KHZ)
        cr_map = {5: LORA_CR_4_5, 6: 0x02, 7: 0x03, 8: 0x04}
        cr_code = cr_map.get(cr, LORA_CR_4_5)
        ldro = 0x00  # leave off for now
        self.spi_cmd([
            SET_MODULATION_PARAMS,
            (sf << 4) & 0xF0,
            bw_code & 0x1F,
            cr_code & 0x07,
            ldro,
        ])

    def set_packet_params(self, preamble_len=8, payload_len=255,
                          crc_on=True, iq_inverted=False):
        hdr_type = LORA_HEADER_EXPLICIT
        crc = LORA_CRC_ON if crc_on else 0x00
        iq = 0x01 if iq_inverted else LORA_IQ_NORMAL
        self.spi_cmd([
            SET_PACKET_PARAMS,
            (preamble_len >> 8) & 0xFF,
            preamble_len & 0xFF,
            hdr_type & 0x01,
            payload_len & 0xFF,
            crc & 0x01,
            iq & 0x01,
        ])

    def set_sync_word(self, sync=MESHTASTIC_SYNCWORD):
        self.spi_cmd([
            SET_SYNC_WORD,
            (sync >> 8) & 0xFF,
            sync & 0xFF,
        ])

    def clear_irq(self, mask=IRQ_ALL):
        self.spi_cmd([
            CLEAR_IRQ_STATUS,
            (mask >> 8) & 0xFF,
            mask & 0xFF,
        ])

    def get_irq_status(self):
        resp = self.spi_cmd([GET_IRQ_STATUS], 3)
        return (resp[1] << 8) | resp[2]

    def get_rx_buffer_status(self):
        resp = self.spi_cmd([GET_RX_BUFFER_STATUS], 3)
        plen = resp[1]
        ptr = resp[2]
        return plen, ptr

    def read_buffer(self, offset, length):
        # For simplicity, use READ_BUFFER with dummy + read_len
        cmd = [READ_BUFFER, offset & 0xFF, 0x00]
        resp = self.spi_cmd(cmd, read_len=length)
        return resp[3:] if len(resp) > 3 else []

    def set_rx(self, timeout_ms=0):
        if timeout_ms == 0:
            period = 0xFFFFFF
        else:
            period = int((timeout_ms / 1000.0) / 0.000015625)
            if period > 0xFFFFFF:
                period = 0xFFFFFF
        self.spi_cmd([
            SET_RX,
            (period >> 16) & 0xFF,
            (period >> 8) & 0xFF,
            period & 0xFF,
        ])

    def get_rssi_snr(self):
        resp = self.spi_cmd([GET_PACKET_STATUS], 3)
        rssi = -resp[1] / 2.0
        snr_raw = resp[2]
        if snr_raw & 0x80:
            snr_raw -= 256
        snr = snr_raw / 4.0
        return rssi, snr

    # ---------- top-level listen ----------

    def configure_lora(self, freq_hz, sf, bw_hz, cr,
                       preamble_len, sync_word,
                       crc_on=True, iq_inverted=False):
        self.set_frequency(freq_hz)
        self.set_modulation_params(sf=sf, bw_hz=bw_hz, cr=cr)
        self.set_packet_params(preamble_len=preamble_len,
                               payload_len=255,
                               crc_on=crc_on,
                               iq_inverted=iq_inverted)
        self.set_sync_word(sync_word)
        self.clear_irq()

    def listen(self, freq_hz=910_525_000, sf=7, bw_hz=62_500, cr=5,
               preamble_len=8, sync_word=MESHTASTIC_SYNCWORD,
               crc_on=True, iq_inverted=False):
        self.configure_lora(freq_hz, sf, bw_hz, cr,
                            preamble_len, sync_word,
                            crc_on, iq_inverted)
        self.set_rx(0)

        print(f"Listening on {freq_hz/1e6:.3f} MHz, SF{sf}, BW {bw_hz}, CR 4/{cr}")
        try:
            while True:
                irq = self.get_irq_status()
                if irq:
                    self.clear_irq()
                    if irq & IRQ_RX_DONE:
                        plen, ptr = self.get_rx_buffer_status()
                        if plen > 0:
                            data = self.read_buffer(ptr, plen)
                            rssi, snr = self.get_rssi_snr()
                            print(f"RX_DONE len={plen}, payload={list(data)}, "
                                  f"RSSI={rssi:.1f} dBm, SNR={snr:.1f} dB")
                        self.set_rx(0)
                    elif irq & IRQ_CRC_ERR:
                        plen, ptr = self.get_rx_buffer_status()
                        if plen > 0:
                            data = self.read_buffer(ptr, plen)
                            rssi, snr = self.get_rssi_snr()
                            print(f"CRC_ERR len={plen}, raw={list(data)}, "
                                  f"RSSI={rssi:.1f} dBm, SNR={snr:.1f} dB")
                        self.set_rx(0)
                    elif irq & IRQ_TIMEOUT:
                        print("RX TIMEOUT, rearming")
                        self.set_rx(0)
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("Stopped listening")
        finally:
            self.spi.close()
            GPIO.cleanup()


if __name__ == "__main__":
    radio = SX1262(spi_bus=0, spi_dev=0, busy_pin=20, irq_pin=16, reset_pin=18)
    radio.listen(
        freq_hz=910_525_000,
        sf=7,
        bw_hz=62_500,
        cr=5,
        preamble_len=8,
        sync_word=MESHTASTIC_SYNCWORD,
        crc_on=True,
        iq_inverted=False,
    )
