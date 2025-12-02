# sx1262.py
import RPi.GPIO as GPIO
import serial
import time

class SX1262:
    """
    Driver for SX1262 LoRa HAT using UART + GPIO control pins.
    Provides send, read, and shutdown methods for integration
    with higher-level transports.
    """

    def __init__(self, serial_port="/dev/ttyS0", baudrate=9600,
                 reset_pin=22, busy_pin=27, m0_pin=17, m1_pin=18):
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.reset_pin = reset_pin
        self.busy_pin = busy_pin
        self.m0_pin = m0_pin
        self.m1_pin = m1_pin
        # print(f"[SX1262] Setting up GPIO pins {self.reset_pin}")
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.reset_pin, GPIO.OUT)
        GPIO.setup(self.busy_pin, GPIO.IN)
        GPIO.setup(self.m0_pin, GPIO.OUT)
        GPIO.setup(self.m1_pin, GPIO.OUT)

        # Reset the chip
        GPIO.output(self.reset_pin, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.reset_pin, GPIO.HIGH)

        # Setup UART
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=1)
        except serial.SerialException as e:
            raise RuntimeError(f"Failed to open {self.serial_port}: {e}")

    def send(self, data: bytes):
        """
        Send a packet over LoRa.
        """
        GPIO.output(self.m0_pin, GPIO.LOW)  # normal mode
        GPIO.output(self.m1_pin, GPIO.LOW)
        time.sleep(0.05)
        self.ser.write(data)

    def read(self) -> bytes:
        """
        Read a packet if available.
        """
        if self.ser.in_waiting > 0:
            return self.ser.read(self.ser.in_waiting)
        return b""

    def shutdown(self):
        """
        Clean up GPIO and close serial.
        """
        if self.ser and self.ser.is_open:
            self.ser.close()
        GPIO.cleanup()  # resets all pins you’ve touched
