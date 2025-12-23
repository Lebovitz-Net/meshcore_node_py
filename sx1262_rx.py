#!/usr/bin/env python3
import time
import spidev
import lgpio
import threading

# -----------------------------
# SX1262 COMMAND CONSTANTS
# -----------------------------
SET_STANDBY            = 0x80
SET_REGULATOR_MODE     = 0x96
SET_PACKET_TYPE        = 0x8A
SET_BUFFER_BASE_ADDRESS= 0x8F
SET_DIO2_RF_SWITCH_CTRL= 0x9D
SET_DIO_IRQ_PARAMS     = 0x08
SET_RF_FREQUENCY       = 0x86
SET_MODULATION_PARAMS  = 0x8B
SET_PACKET_PARAMS      = 0x8C
SET_SYNC_WORD          = 0x0B
SET_RX                 = 0x82
CLEAR_IRQ_STATUS       = 0x02
GET_IRQ_STATUS         = 0x12
GET_RX_BUFFER_STATUS   = 0x13
READ_BUFFER            = 0x1E
GET_PACKET_STATUS      = 0x14
GET_RSSI_INST          = 0x15
GET_PACKET_TYPE_CMD    = 0x03   # Correct opcode

# -----------------------------
# MODES / CONSTANTS
# -----------------------------
STDBY_RC               = 0x00
REG_MODE_LDO           = 0x01
PACKET_TYPE_LORA       = 0x01

IRQ_RX_DONE            = 0x0001
IRQ_CRC_ERR            = 0x0002
IRQ_TIMEOUT            = 0x0004
IRQ_ALL                = 0xFFFF

LORA_HEADER_EXPLICIT   = 0x00
LORA_CRC_ON            = 0x01
LORA_IQ_NORMAL         = 0x00

TX_BASE_DEFAULT        = 0x00
RX_BASE_DEFAULT        = 0x00

MESHTASTIC_SYNCWORD    = 0x1424

# -----------------------------
# MAIN SX1262 CLASS
# -----------------------------
class SX1262:
    def __init__(self, spi_bus=0, spi_dev=0,
                 busy_pin=20, irq_pin=16, reset_pin=18,
                 nss_pin=21):

        self.busy_pin = busy_pin
        self.irq_pin = irq_pin
        self.reset_pin = reset_pin
        self.nss_pin = nss_pin

        # GPIO
        self.gpio_chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_input(self.gpio_chip, self.busy_pin)
        lgpio.gpio_claim_input(self.gpio_chip, self.irq_pin)
        lgpio.gpio_claim_output(self.gpio_chip, self.reset_pin, 1)
        lgpio.gpio_claim_output(self.gpio_chip, self.nss_pin, 1)

        # SPI
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_dev)
        self.spi.no_cs = True
        self.spi.max_speed_hz = 1_000_000
        self.spi.mode = 0

        # Reset & init
        self.reset()
        print("SX1262 reset")
        self.base_init()

        # Background RSSI monitor
        self.start_rssi_monitor(interval=5)

    # -----------------------------
    # TIMING (NO BUSY LINE)
    # -----------------------------
    def _wait_busy(self):
        # Board ties BUSY low → use fixed delay
        time.sleep(0.01)
        return True

    # -----------------------------
    # GPIO HELPERS
    # -----------------------------
    def _read_pin(self, pin):
        return lgpio.gpio_read(self.gpio_chip, pin)

    def _write_pin(self, pin, value):
        lgpio.gpio_write(self.gpio_chip, pin, 1 if value else 0)

    # -----------------------------
    # RESET
    # -----------------------------
    def reset(self):
        self._write_pin(self.reset_pin, 0)
        time.sleep(0.01)
        self._write_pin(self.reset_pin, 1)
        time.sleep(0.02)

    # -----------------------------
    # SPI COMMAND
    # -----------------------------
    def spi_cmd(self, buf, read_len=0):
        self._wait_busy()

        self._write_pin(self.nss_pin, 0)
        try:
            resp = self.spi.xfer2(buf + [0x00] * read_len)
        finally:
            self._write_pin(self.nss_pin, 1)

        # Allow chip to digest command
        time.sleep(0.005)
        return resp

    # -----------------------------
    # BACKGROUND RSSI MONITOR
    # -----------------------------
    def get_rssi_inst(self):
        resp = self.spi_cmd([GET_RSSI_INST], 1)
        rssi_raw = resp[1]
        return -rssi_raw / 2.0

    def start_rssi_monitor(self, interval=5):
        def loop():
            while True:
                try:
                    print(f"[RSSI] {self.get_rssi_inst():.1f} dBm")
                except Exception as e:
                    print("RSSI error:", e)
                time.sleep(interval)

        threading.Thread(target=loop, daemon=True).start()

    # -----------------------------
    # BASE INIT
    # -----------------------------
    def base_init(self):
        self.spi_cmd([SET_STANDBY, STDBY_RC])
        self.spi_cmd([SET_REGULATOR_MODE, REG_MODE_LDO])
        self.spi_cmd([SET_PACKET_TYPE, PACKET_TYPE_LORA])

        # Correct order: TX base, then RX base
        self.spi_cmd([SET_BUFFER_BASE_ADDRESS, TX_BASE_DEFAULT, RX_BASE_DEFAULT])

        self.spi_cmd([SET_DIO2_RF_SWITCH_CTRL, 0x01])

        irq_mask = IRQ_RX_DONE | IRQ_CRC_ERR | IRQ_TIMEOUT
        self.spi_cmd([
            SET_DIO_IRQ_PARAMS,
            (irq_mask >> 8) & 0xFF, irq_mask & 0xFF,
            (irq_mask >> 8) & 0xFF, irq_mask & 0xFF,
            0x00, 0x00,
            0x00, 0x00,
        ])

        print("SX1262 base init done")

    # -----------------------------
    # LORA CONFIG
    # -----------------------------
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
        bw_code = bw_map.get(bw_hz, 0x04)
        cr_map = {5: 0x01, 6: 0x02, 7: 0x03, 8: 0x04}
        cr_code = cr_map.get(cr, 0x01)

        sf_field = (sf << 4) & 0xF0
        ldro = 0x00

        self.spi_cmd([
            SET_MODULATION_PARAMS,
            sf_field,
            bw_code & 0x1F,
            cr_code & 0x07,
            ldro,
        ])

    def set_packet_params(self, preamble_len=8, payload_len=255,
                          crc_on=True, iq_inverted=False):
        crc = LORA_CRC_ON if crc_on else 0x00
        iq = LORA_IQ_NORMAL if not iq_inverted else 0x01

        self.spi_cmd([
            SET_PACKET_PARAMS,
            (preamble_len >> 8) & 0xFF,
            preamble_len & 0xFF,
            LORA_HEADER_EXPLICIT,
            payload_len & 0xFF,
            crc,
            iq,
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

    # -----------------------------
    # RX CONTROL
    # -----------------------------
    def set_rx(self, timeout_ms=0):
        if timeout_ms == 0:
            period = 0xFFFFFF
        else:
            period = int((timeout_ms / 1000.0) / 0.000015625)
            period = min(period, 0xFFFFFF)

        self.spi_cmd([
            SET_RX,
            (period >> 16) & 0xFF,
            (period >> 8) & 0xFF,
            period & 0xFF,
        ])

        time.sleep(0.05)

    # -----------------------------
    # IRQ / PACKET HANDLING
    # -----------------------------
    def get_irq_status(self):
        return self.spi_cmd([GET_IRQ_STATUS], 3)

    def get_rx_buffer_status(self):
        resp = self.spi_cmd([GET_RX_BUFFER_STATUS], 3)
        return resp[1], resp[2]

    def read_buffer(self, offset, length):
        cmd = [READ_BUFFER, offset & 0xFF, 0x00]
        resp = self.spi_cmd(cmd, read_len=length + 1)
        return resp[3:3 + length]

    def get_rssi_snr(self):
        resp = self.spi_cmd([GET_PACKET_STATUS], 3)
        rssi = -resp[1] / 2.0
        snr_raw = resp[2]
        if snr_raw & 0x80:
            snr_raw -= 256
        return rssi, snr_raw / 4.0

    # -----------------------------
    # LISTEN LOOP
    # -----------------------------
    def configure_lora(self, freq_hz, sf, bw_hz, cr,
                       preamble_len, sync_word,
                       crc_on=True, iq_inverted=False):

        print(f"Config LoRa: freq={freq_hz} bw={bw_hz} sf={sf} cr={cr}")
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

        ptype = self.spi_cmd([GET_PACKET_TYPE_CMD], 1)
        print("Packet type:", hex(ptype[1]))

        self.configure_lora(freq_hz, sf, bw_hz, cr,
                            preamble_len, sync_word,
                            crc_on, iq_inverted)

        self.set_rx(0)
        print("After SET_RX, polling status for 1 second:")
        for _ in range(20):
            status = self.spi_cmd([0xC0], 1)
            print("  Status:", hex(status[0]))
            time.sleep(0.05)


        print("Listening...")

        try:
            while True:
                resp = self.get_irq_status()
                irq = resp[2]

                if irq:
                    irq_word = (resp[1] << 8) | resp[2]
                    print(f"IRQ: 0x{irq_word:04X}")
                    self.clear_irq()

                    if irq & IRQ_RX_DONE:
                        plen, ptr = self.get_rx_buffer_status()
                        print(f"RX_DONE: plen={plen}, ptr={ptr}")

                        if plen > 0:
                            data = self.read_buffer(ptr, plen)
                            rssi, snr = self.get_rssi_snr()
                            print(f"Payload={list(data)} RSSI={rssi:.1f} SNR={snr:.1f}")

                        self.set_rx(0)

                    elif irq & IRQ_CRC_ERR:
                        print("CRC_ERR")
                        self.set_rx(0)

                    elif irq & IRQ_TIMEOUT:
                        print("TIMEOUT")
                        self.set_rx(0)

                time.sleep(0.05)

        except KeyboardInterrupt:
            print("Stopped listening")
        finally:
            self.spi.close()
            lgpio.gpiochip_close(self.gpio_chip)


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    radio = SX1262(
        spi_bus=0,
        spi_dev=0,
        busy_pin=20,
        irq_pin=16,
        reset_pin=18,
        nss_pin=21,
    )

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
