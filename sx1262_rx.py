#!/usr/bin/env python3
import time
import spidev
import lgpio
import threading

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
    # SX1262 command for instantaneous RSSI (from datasheet)
GET_RSSI_INST = 0x15  # add this to your constants if not present

class SX1262:
    def __init__(self, spi_bus=0, spi_dev=0,
                 busy_pin=20, irq_pin=16, reset_pin=18,
                 nss_pin=21):   # CS on GPIO21 (pin 40, as traced)

        self.busy_pin = busy_pin
        self.irq_pin = irq_pin
        self.reset_pin = reset_pin
        self.nss_pin = nss_pin
        # self.dio2_pin = 26  # RF switch control line on your board

        # --- GPIO setup via lgpio ---
        # Use gpiochip0 (main Pi GPIO controller)
        self.gpio_chip = lgpio.gpiochip_open(0)

        # BUSY and IRQ are inputs
        lgpio.gpio_claim_input(self.gpio_chip, self.busy_pin)
        lgpio.gpio_claim_input(self.gpio_chip, self.irq_pin)

        # RESET and NSS are outputs, default high
        lgpio.gpio_claim_output(self.gpio_chip, self.reset_pin, 1)
        lgpio.gpio_claim_output(self.gpio_chip, self.nss_pin, 1)
        # removed DIO2 setup, as it's not used by the board
        # DIO2 as a controllable GPIO for RF switch (if needed)
        # lgpio.gpio_claim_output(self.gpio_chip, self.dio2_pin, 0)

        # --- SPI setup ---
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_dev)   # CE0/CE1 unused but harmless
        self.spi.max_speed_hz = 1_000_000
        self.spi.mode = 0

        # --- Reset the radio ---
        self.reset()
        print("SX1262 reset")

        # --- Run Semtech bring-up sequence ---
        self.base_init()
        self.start_rssi_monitor(interval = 5)

    # ---------- low-level ----------

    def get_rssi_inst(self):
        """
        Instantaneous RSSI while in RX mode.
        Returns RSSI in dBm.
        """
        resp = self.spi_cmd([GET_RSSI_INST], 1)
        # resp[0] = status, resp[1] = rssi (but we asked for 1 extra byte,
        # so total len == 2; status is first, rssi is second)
        rssi_raw = resp[1]
        rssi_dbm = -rssi_raw / 2.0
        return rssi_dbm


    def start_rssi_monitor(self, interval=5):
        def loop():
            while True:
                try:
                    rssi = self.get_rssi_inst()
                    print(f"[RSSI Monitor] InstRSSI={rssi:.1f} dBm")
                except Exception as e:
                    print("RSSI monitor error:", e)
                time.sleep(interval)

        t = threading.Thread(target=loop, daemon=True)
        t.start()



    def _read_pin(self, pin):
        return lgpio.gpio_read(self.gpio_chip, pin)

    def _write_pin(self, pin, value):
        lgpio.gpio_write(self.gpio_chip, pin, 1 if value else 0)

    def _wait_busy(self):
        for _ in range(5000):  # ~5 seconds max
            if not self._read_pin(self.busy_pin):
                return
            time.sleep(0.001)
        raise RuntimeError("BUSY stuck high — check wiring and power")

    def reset(self):
        # Drive RESET low briefly, then high
        self._write_pin(self.reset_pin, 0)
        time.sleep(0.01)
        self._write_pin(self.reset_pin, 1)
        time.sleep(0.01)

    def spi_cmd(self, buf, read_len=0):
        # Wait for BUSY to clear *before* selecting
        self._wait_busy()

        # Assert CS (active low)
        self._write_pin(self.nss_pin, 0)

        try:
            resp = self.spi.xfer2(buf + [0x00] * read_len)
        finally:
            # Deassert CS
            self._write_pin(self.nss_pin, 1)

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
        # Semtech order is: TX base, then RX base.
        # Your constants RX_BASE_DEFAULT / TX_BASE_DEFAULT are already defined:
        #   TX_BASE_DEFAULT = 0x00
        #   RX_BASE_DEFAULT = 0x00 (or whatever you use)
        self.spi_cmd([SET_BUFFER_BASE_ADDRESS, TX_BASE_DEFAULT, RX_BASE_DEFAULT])

        # 5) DIO2 as RF switch (chip-side RF switch control)
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
        # Same calc as Waveshare: freq * 2^25 / 32e6
        frf = int(freq_hz * (1 << 25) / 32_000_000)
        self.spi_cmd([
            SET_RF_FREQUENCY,
            (frf >> 24) & 0xFF,
            (frf >> 16) & 0xFF,
            (frf >> 8) & 0xFF,
            frf & 0xFF,
        ])

    def set_modulation_params(self, sf=7, bw_hz=62_500, cr=5):
        # Map Hz to chip BW code; fall back to 125 kHz if unknown.
        bw_map = {
            7_800: 0x00, 10_400: 0x08, 15_600: 0x01, 20_800: 0x09,
            31_250: 0x02, 41_700: 0x0A, 62_500: 0x03, 125_000: 0x04,
            250_000: 0x05, 500_000: 0x06,
        }
        bw_code = bw_map.get(bw_hz, LORA_BW_125_KHZ)

        # CR codes – use your constants when possible
        cr_map = {5: LORA_CR_4_5, 6: 0x02, 7: 0x03, 8: 0x04}
        cr_code = cr_map.get(cr, LORA_CR_4_5)

        # LDRO OFF for now; you can add auto-LDRO later
        ldro = 0x00

        # SF goes into upper nibble according to datasheet
        sf_field = (sf << 4) & 0xF0

        self.spi_cmd([
            SET_MODULATION_PARAMS,
            sf_field,
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
        # 3 bytes: status, IRQ high, IRQ low.
        resp = self.spi_cmd([GET_IRQ_STATUS], 3)
        # If you *ever* want the full 16-bit mask:
        # return (resp[1] << 8) | resp[2]
        return resp

    def get_rx_buffer_status(self):
        resp = self.spi_cmd([GET_RX_BUFFER_STATUS], 3)
        plen = resp[1]
        ptr = resp[2]
        return plen, ptr

    def read_buffer(self, offset, length):
        """
        READ_BUFFER (0x1E) expects:
          TX: [opcode, offset, 0x00, 0, 0, ..., 0]
          RX: [status, dummy, payload...]
        So:
          - send 1 dummy byte before payload
          - ask for length+1 dummy/payload bytes
          - discard status + dummy, return exactly 'length' bytes
        """
        cmd = [READ_BUFFER, offset & 0xFF, 0x00]
        resp = self.spi_cmd(cmd, read_len=length + 1)
        # resp[0] = status, resp[1] = ?, resp[2] = first payload byte?
        # Using the same pattern as other commands where data starts at resp[1],
        # but here we have opcode + address bytes shifting things, so we skip 3.
        return resp[3:3 + length]

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
        print(f"configure lora freq {freq_hz} bw {bw_hz} sf {sf} cr {cr} sync {hex(sync_word)}")
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
        self.set_rx(0)  # continuous RX

        # --- DEBUG: Check radio state after SET_RX ---
        status = self.spi_cmd([0xC0], 1)
        print("Status:", hex(status[0]))

        try:
            while True:
                resp = self.get_irq_status()
                # Only low byte contains the IRQ bits we care about
                irq = resp[2]
                if irq:
                    print(f"Raw IRQ word: 0x{((resp[1] << 8) | resp[2]):04x}")
                    print("IRQ low byte:", hex(irq))

                    self.clear_irq()

                    if irq & IRQ_RX_DONE:
                        plen, ptr = self.get_rx_buffer_status()
                        print(f"RX_DONE: plen={plen}, ptr={ptr}")
                        if plen > 0:
                            data = self.read_buffer(ptr, plen)
                            rssi, snr = self.get_rssi_snr()
                            print(
                                f"RX_DONE len={plen}, payload={list(data)}, "
                                f"RSSI={rssi:.1f} dBm, SNR={snr:.1f} dB"
                            )
                        # Re-enter RX
                        self.set_rx(0)

                    elif irq & IRQ_CRC_ERR:
                        plen, ptr = self.get_rx_buffer_status()
                        print(f"CRC_ERR: plen={plen}, ptr={ptr}")
                        if plen > 0:
                            data = self.read_buffer(ptr, plen)
                            rssi, snr = self.get_rssi_snr()
                            print(
                                f"CRC_ERR len={plen}, raw={list(data)}, "
                                f"RSSI={rssi:.1f} dBm, SNR={snr:.1f} dB"
                            )
                        self.set_rx(0)

                    elif irq & IRQ_TIMEOUT:
                        print("IRQ_TIMEOUT")
                        self.set_rx(0)

                time.sleep(0.05)
        except KeyboardInterrupt:
            print("Stopped listening")
        finally:
            # Clean up SPI and GPIO
            self.spi.close()
            lgpio.gpiochip_close(self.gpio_chip)


if __name__ == "__main__":
    # Use the GPIO mapping you traced on your board
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
