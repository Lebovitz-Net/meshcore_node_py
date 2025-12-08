# sx1262_status.py
class SX1262Status:
    def get_irq_status(self) -> int:
        """Read IRQ flags."""
        # GetIrqStatus opcode = 0x12 (datasheet)
        resp = self._spi_cmd(0x12, [0x00, 0x00])
        return (resp[1] << 8) | resp[2]

    def clear_irq_status(self, mask: int = 0xFFFF):
        """Clear IRQ flags."""
        # ClearIrqStatus opcode = 0x02
        return self._spi_cmd(0x02, [(mask >> 8) & 0xFF, mask & 0xFF])

    def get_rssi(self) -> int:
        """Read RSSI value (last packet)."""
        # GetPacketStatus opcode = 0x14
        resp = self._spi_cmd(0x14, [0x00])
        # RSSI is in resp[1], offset per datasheet
        return resp[1]

    def get_snr(self) -> int:
        """Read SNR value (last packet)."""
        # GetPacketStatus opcode = 0x14
        resp = self._spi_cmd(0x14, [0x00])
        # SNR is in resp[2], offset per datasheet
        return resp[2]

    def get_device_status(self) -> int:
        """Read device status."""
        # GetStatus opcode = 0xC0
        resp = self._spi_cmd(0xC0, [0x00])
        return resp[1]
