# ---------------------------------------------
# SX1262 Command Opcodes
# ---------------------------------------------
SET_SLEEP                  = 0x84
SET_STANDBY                = 0x80
SET_FS                     = 0xC1
SET_TX                     = 0x83
SET_RX                     = 0x82
STOP_TIMER_ON_PREAMBLE     = 0x9F
SET_RX_DUTY_CYCLE          = 0x94
SET_CAD                    = 0xC5
SET_TX_CONTINUOUS_WAVE     = 0xD1
SET_TX_INFINITE_PREAMBLE   = 0xD2
SET_REGULATOR_MODE         = 0x96
CALIBRATE                  = 0x89
CALIBRATE_IMAGE            = 0x98
SET_PA_CONFIG              = 0x95
SET_RX_TX_FALLBACK_MODE    = 0x93

WRITE_REGISTER             = 0x0D
READ_REGISTER              = 0x1D
WRITE_BUFFER               = 0x0E
READ_BUFFER                = 0x1E

SET_DIO_IRQ_PARAMS         = 0x08
GET_IRQ_STATUS             = 0x12
CLEAR_IRQ_STATUS           = 0x02

SET_DIO2_RF_SWITCH_CTRL    = 0x9D
SET_DIO3_TCXO_CTRL         = 0x97

SET_RF_FREQUENCY           = 0x86
SET_PACKET_TYPE            = 0x8A
GET_PACKET_TYPE            = 0x11

SET_MODULATION_PARAMS      = 0x8B
SET_PACKET_PARAMS          = 0x8C
SET_BUFFER_BASE_ADDRESS    = 0x8F

SET_SYNC_WORD              = 0x0B
GET_PACKET_STATUS          = 0x15
GET_RX_BUFFER_STATUS       = 0x13

# ---------------------------------------------
# Packet Types
# ---------------------------------------------
PACKET_TYPE_GFSK           = 0x00
PACKET_TYPE_LORA           = 0x01

# ---------------------------------------------
# Standby Modes
# ---------------------------------------------
STDBY_RC                   = 0x00
STDBY_XOSC                 = 0x01

# ---------------------------------------------
# Regulator Modes
# ---------------------------------------------
REG_MODE_LDO               = 0x00
REG_MODE_DCDC              = 0x01

# ---------------------------------------------
# IRQ Masks
# ---------------------------------------------
IRQ_TX_DONE                = 0x0001
IRQ_RX_DONE                = 0x0002
IRQ_PREAMBLE_DETECTED      = 0x0004
IRQ_SYNCWORD_VALID         = 0x0008
IRQ_HEADER_VALID           = 0x0010
IRQ_HEADER_ERR             = 0x0020
IRQ_CRC_ERR                = 0x0040
IRQ_CAD_DONE               = 0x0080
IRQ_CAD_DETECTED           = 0x0100
IRQ_TIMEOUT                = 0x0200

IRQ_ALL                    = 0xFFFF

# ---------------------------------------------
# LoRa Bandwidth Codes (Semtech)
# ---------------------------------------------
LORA_BW_7_8_KHZ            = 0x00
LORA_BW_10_4_KHZ           = 0x08
LORA_BW_15_6_KHZ           = 0x01
LORA_BW_20_8_KHZ           = 0x09
LORA_BW_31_25_KHZ          = 0x02
LORA_BW_41_7_KHZ           = 0x0A
LORA_BW_62_5_KHZ           = 0x03
LORA_BW_125_KHZ            = 0x04
LORA_BW_250_KHZ            = 0x05
LORA_BW_500_KHZ            = 0x06

# ---------------------------------------------
# LoRa Coding Rates
# ---------------------------------------------
LORA_CR_4_5                = 0x01
LORA_CR_4_6                = 0x02
LORA_CR_4_7                = 0x03
LORA_CR_4_8                = 0x04

# ---------------------------------------------
# Header Types
# ---------------------------------------------
LORA_HEADER_EXPLICIT       = 0x00
LORA_HEADER_IMPLICIT       = 0x01

# ---------------------------------------------
# CRC Modes
# ---------------------------------------------
LORA_CRC_OFF               = 0x00
LORA_CRC_ON                = 0x01

# ---------------------------------------------
# IQ Modes
# ---------------------------------------------
LORA_IQ_NORMAL             = 0x00
LORA_IQ_INVERTED           = 0x01

# ---------------------------------------------
# Default Sync Words
# ---------------------------------------------
LORA_SYNCWORD_PUBLIC       = 0x3444
LORA_SYNCWORD_PRIVATE      = 0x1424
MESHTASTIC_SYNCWORD        = 0x3444  # matches your test setup

# ---------------------------------------------
# Buffer Base Addresses
# ---------------------------------------------
RX_BASE_DEFAULT            = 0x00
TX_BASE_DEFAULT            = 0x80

# ---------------------------------------------
# Frequency Conversion
# ---------------------------------------------
FREQ_STEP                  = 32_000_000 / (1 << 25)   # ~0.953674 Hz
