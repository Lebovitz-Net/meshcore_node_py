# sx1262_cmds.py
import time
import spidev
import RPi.GPIO as GPIO

BUSY_PIN = 20  # adjust if needed

class SX1262Cmds:
    """Low-level SPI command helpers and convenience wrappers for SX1262."""

    # IRQ masks
    IRQ_TX_DONE   = 0x0001
    IRQ_RX_DONE   = 0x0040
    IRQ_TIMEOUT   = 0x0080
    IRQ_CRC_ERR   = 0x0020
    IRQ_ALL       = 0xFFFF

    # Opcodes
    OP_SET_STANDBY         = 0x80
    OP_SET_RX              = 0x82
    OP_SET_TX              = 0x83
    OP_SET_SLEEP           = 0x84
    OP_SET_DIO_IRQ_PARAMS  = 0x08
    OP_CLEAR_IRQ_STATUS    = 0x02
    OP_GET_IRQ_STATUS      = 0x12
    OP_GET_STATUS          = 0xC0

    def _wait_busy(self):
        while GPIO.input(BUSY_PIN) == 1:
            time.sleep(0.001)

    def _spi_cmd(self, opcode: int, params=None):
        if params is None:
            params = []
        self._wait_busy()
        frame = [opcode] + params
        return self.spi.xfer2(frame)

    def _spi_cmd_read(self, opcode: int, params=None, read_len=1):
        if params is None:
            params = []
        self._wait_busy()
        frame = [opcode] + params + ([0x00] * read_len)
        resp = self.spi.xfer2(frame)
        return resp[-read_len:]

    # Convenience wrappers
    def set_standby(self, mode=0x00):
        return self._spi_cmd(self.OP_SET_STANDBY, [mode])

    def set_sleep(self):
        return self._spi_cmd(self.OP_SET_SLEEP, [0x00])

    def set_rx(self, timeout_ms: int):
        tOut = int(timeout_ms * 64)
        params = [(tOut >> 16) & 0xFF, (tOut >> 8) & 0xFF, tOut & 0xFF]
        return self._spi_cmd(self.OP_SET_RX, params)

    def set_tx(self, timeout_ms: int = 0):
        tOut = int(timeout_ms * 64)
        params = [(tOut >> 16) & 0xFF, (tOut >> 8) & 0xFF, tOut & 0xFF]
        return self._spi_cmd(self.OP_SET_TX, params)

    def clear_irq(self, mask: int = IRQ_ALL):
        return self._spi_cmd(self.OP_CLEAR_IRQ_STATUS, [(mask >> 8) & 0xFF, mask & 0xFF])

    def get_irq_status(self) -> int:
        data = self._spi_cmd_read(self.OP_GET_IRQ_STATUS, [], 2)
        return (data[0] << 8) | data[1]

    def get_status(self) -> int:
        data = self._spi_cmd_read(self.OP_GET_STATUS, [], 1)
        return data[0]
