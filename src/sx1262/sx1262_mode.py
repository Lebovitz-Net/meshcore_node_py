# sx1262_mode.py
class SX1262Mode:
    def enter_rx_continuous(self):
        """Enter continuous RX mode."""
        # SetRx opcode = 0x82, continuous mode = [0x00, 0x00, 0x00]
        return self._spi_cmd(0x82, [0x00, 0x00, 0x00])

    def enter_rx_window(self, timeout_ms: int):
        """Enter RX mode with timeout."""
        # Timeout units: 15.625 µs steps
        t = int(timeout_ms / 15.625)
        return self._spi_cmd(0x82, list(t.to_bytes(3, 'big')))

    def enter_tx(self, payload: bytes, timeout_ms: int = 0):
        """Transmit payload with optional timeout."""
        # First write payload into FIFO
        self.send(payload)
        # Then trigger TX with timeout
        t = int(timeout_ms / 15.625)
        return self._spi_cmd(0x83, list(t.to_bytes(3, 'big')))

    def sleep(self):
        """Put radio into sleep mode."""
        # SetSleep opcode = 0x84
        return self._spi_cmd(0x84, [0x00])

    def standby(self):
        """Put radio into standby mode."""
        # SetStandby opcode = 0x80, RC oscillator = 0x00
        return self._spi_cmd(0x80, [0x00])
