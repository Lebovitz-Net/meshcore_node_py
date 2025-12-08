# sx1262_config.py
class SX1262Config:
    def set_frequency(self, freq_hz: float):
        """Set carrier frequency in Hz."""
        frf = int(freq_hz * (1 << 25) / 32_000_000)
        # SetRfFrequency opcode = 0x86, followed by 4 bytes MSB first
        return self._spi_cmd(0x86, list(frf.to_bytes(4, 'big')))

    def set_modulation_params(self, sf: int, bw_hz: int, cr: int):
        """Set LoRa modulation parameters (SF, BW, CR)."""
        bw_map = {
            7800: 0x00, 10400: 0x01, 15600: 0x02, 20800: 0x03,
            31250: 0x04, 41700: 0x05, 62500: 0x06, 125000: 0x07,
            250000: 0x08, 500000: 0x09
        }
        bw_code = bw_map.get(bw_hz, 0x07)
        cr_map = {5: 0x01, 6: 0x02, 7: 0x03, 8: 0x04}
        cr_code = cr_map.get(cr, 0x01)
        ldro = 0x00
        # SetModulationParams opcode = 0x8B
        return self._spi_cmd(0x8B, [sf & 0x0F, bw_code & 0x0F, cr_code & 0x0F, ldro])

    def set_packet_params(self, preamble_len: int, explicit=True,
                          payload_len=64, crc_on=True, iq_inverted=False):
        """Set LoRa packet parameters."""
        header_type = 0x00 if explicit else 0x01
        crc = 0x01 if crc_on else 0x00
        iq = 0x01 if iq_inverted else 0x00
        # SetPacketParams opcode = 0x8C
        return self._spi_cmd(0x8C, [
            (preamble_len >> 8) & 0xFF,
            preamble_len & 0xFF,
            header_type,
            payload_len & 0xFF,
            crc,
            iq
        ])

    def set_packet_type_lora(self):
        """Select LoRa packet type."""
        # SetPacketType opcode = 0x8A, LoRa type = 0x01
        return self._spi_cmd(0x8A, [0x01])


    def set_sync_word(self, word: int):
        """Set LoRa sync word (0x34 public, 0x12 private)."""
        # WriteRegister opcode = 0x0D
        # Sync word registers: 0x0740 (MSB), 0x0741 (LSB)
        return self._spi_cmd(0x0D, [0x07, 0x40, (word >> 8) & 0xFF, word & 0xFF])
