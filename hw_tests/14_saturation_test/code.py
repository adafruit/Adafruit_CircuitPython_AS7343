# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 14 — AS7343 saturation detection

Tests the saturation flag API:
  - sensor.analog_saturated  (STATUS2 bit 3 — analogue front-end saturated)
  - sensor.digital_saturated (STATUS2 bit 4 — ADC counter hit max value)

Two conditions are tested:

  Low-light  — NeoPixels OFF, 64× gain, 50 ms integration
    Neither saturation flag should be set; F4 reading should be < 65535.

  High-light — NeoPixels ON full white, 2048× gain, 278 ms integration
    At least digital saturation is expected (F4 reading near / at 65535).
    Analog saturation may also assert.

The test PASSes as long as both measurements complete without timeout
and the API calls return without error.  The saturation state is printed
for informational purposes.

Expected output:
  RESULT: PASS
"""

import time

import board
import neopixel

from adafruit_as7343 import AS7343, Channel, Gain

NEOPIXEL_COUNT = 5

print("AS7343 Saturation Test")
print("======================")
print()

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

api_ok = True

# ── Low-light test ────────────────────────────────────────────────────────────

print("Low-light test (NeoPixels OFF, 64× gain, ~50 ms integration):")

pixels.fill((0, 0, 0))
pixels.show()
time.sleep(0.1)

sensor.gain = Gain.X64
sensor.atime = 29
sensor._astep = 599

try:
    sensor.read_timeout = 2000
    channels = sensor.all_channels
    low_reading = channels[Channel.F4]
    low_analog = sensor.analog_saturated
    low_digital = sensor.digital_saturated

    print(f"  F4 reading:        {low_reading}")
    print(f"  Analog saturated:  {'YES' if low_analog  else 'NO'}")
    print(f"  Digital saturated: {'YES' if low_digital else 'NO'}")

    if low_analog or low_digital:
        print("  WARNING: saturation flagged in low-light conditions")

except TimeoutError:
    print("  TIMEOUT waiting for data")
    api_ok = False

print()

# ── High-light test ───────────────────────────────────────────────────────────

print("High-light test (NeoPixels ON full white, 2048× gain, ~278 ms integration):")

pixels.fill((255, 255, 255))
pixels.show()
time.sleep(0.1)

sensor.gain = Gain.X2048
sensor.atime = 99
sensor._astep = 999

# 3 SMUX cycles × 278 ms + margin
try:
    sensor.read_timeout = 3000
    channels = sensor.all_channels
    high_reading = channels[Channel.F4]
    high_analog = sensor.analog_saturated
    high_digital = sensor.digital_saturated

    print(f"  F4 reading:        {high_reading}")
    print(f"  Analog saturated:  {'YES' if high_analog  else 'NO'}")
    print(f"  Digital saturated: {'YES' if high_digital else 'NO'}")

    if high_reading == 65535:
        print("  (Reading at max — digital saturation expected)")

except TimeoutError:
    print("  TIMEOUT waiting for data")
    api_ok = False

pixels.fill((0, 0, 0))
pixels.show()

print()
print(f"API functional: {'PASS' if api_ok else 'FAIL'}")
print(f"RESULT: {'PASS' if api_ok else 'FAIL'}")

print("~~END~~")
