#!/usr/bin/env python3
import time
import lgpio

PIN = 21   # GPIO21 = physical pin 40

chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(chip, PIN, 0)

print("Toggling GPIO21 (pin 40) every 0.5 seconds...")
state = 0

try:
    while True:
        state ^= 1
        lgpio.gpio_write(chip, PIN, state)
        print("GPIO21 =", state)
        time.sleep(0.5)
except KeyboardInterrupt:
    print("Stopping.")
finally:
    lgpio.gpio_write(chip, PIN, 0)
    lgpio.gpiochip_close(chip)
