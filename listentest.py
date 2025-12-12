from sx1262.sx1262 import SX1262

if __name__ == "__main__":
    radio = SX1262(spi_bus=0, spi_dev=0, max_speed=500000)

    radio.listen(
        freq_hz=910_525_000,
        sf=7,
        bw_hz=62_500,
        cr=5,
        preamble_len=8,
        payload_len=64,
        sync_word=0x12
    )
