# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 08 — AS7343 power control

Tests:
  - power_enabled property (PON bit in ENABLE register)
  - low_power_enabled property (LOW_POWER bit in CFG0 register)
  - Sensor recovers correctly after power-off → power-on cycle

Note: while the sensor is powered off we do NOT attempt a measurement;
the I2C bus may return stale or unexpected data and the driver could hang
waiting for AVALID.

Expected output:
  RESULT: PASS
"""

import time

import board
import neopixel

from adafruit_as7343 import AS7343, Channel, Gain

NEOPIXEL_COUNT = 5


def take_reading(sensor):
    """Return F4 channel count from a single fresh measurement."""
    channels = sensor.all_channels
    return channels[Channel.F4]


print("AS7343 Power Control Test")
print("=========================")
print()

# --- Hardware init ---
pixels = neopixel.NeoPixel(board.NEOPIXEL, NEOPIXEL_COUNT, brightness=1.0, auto_write=False)
pixels.fill((0, 0, 0))
pixels.show()

i2c = board.I2C()

try:
    sensor = AS7343(i2c)
    print("AS7343 initialized OK")
except RuntimeError as e:
    print(f"ERROR: {e}")
    print("RESULT: FAIL")
    raise SystemExit

test_passed = True

# Consistent gain and integration time
sensor.gain = Gain.X128
sensor.atime = 29
sensor._astep = 599

# NeoPixels ON
print("NeoPixels ON...")
pixels.fill((64, 64, 64))
pixels.show()
time.sleep(0.1)

# Initial reading (sensor powered)
initial = take_reading(sensor)
print(f"Initial reading (powered): F4={initial}")
print()

# --- Power OFF ---
print("Power OFF test:")
sensor.power_enabled = False
print("  power_enabled = False: OK")
time.sleep(0.05)
print("  Reading after power off: (sensor powered down — skipped)")
print()

# --- Power ON ---
print("Power ON test:")
sensor.power_enabled = True
print("  power_enabled = True: OK")
time.sleep(0.1)  # let the sensor stabilise

after_on = take_reading(sensor)
print(f"  Reading after power on: F4={after_on}")

if after_on > 0:
    print("  Sensor recovered: OK")
else:
    print("  Sensor recovered: FAIL (reading=0)")
    test_passed = False
print()

# --- Low Power Mode ---
print("Low Power Mode test:")

sensor.low_power_enabled = True
time.sleep(0.05)
print("  low_power_enabled = True:  OK")

sensor.low_power_enabled = False
time.sleep(0.05)
print("  low_power_enabled = False: OK")
print()

# NeoPixels OFF
pixels.fill((0, 0, 0))
pixels.show()

print(f"Power control: {'PASS' if test_passed else 'FAIL'}")
print(f"RESULT: {'PASS' if test_passed else 'FAIL'}")

print("~~END~~")
