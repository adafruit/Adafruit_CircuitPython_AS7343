# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 07 — AS7343 flicker detection

Tests the flicker detection API:
  - flicker_detection_enabled property (enable / disable)
  - flicker_status raw register read
  - flicker_frequency decoded result

Two observations are printed:
  a) NeoPixels ON dim  — DC light source, expect NONE or indeterminate
  b) NeoPixels OFF     — ambient light; may detect 100/120 Hz mains flicker
     if overhead fluorescent / LED lighting is present

The test PASSES as long as the API calls complete without error; the
actual frequency reading is informational because it depends on the
ambient light environment.

Expected output:
  RESULT: PASS
"""

import time

import board
import neopixel

from adafruit_as7343 import AS7343, FlickerFreq

NEOPIXEL_COUNT = 5

_FLICKER_NAMES = {
    FlickerFreq.NONE: "NONE",
    FlickerFreq.HZ100: "100 Hz",
    FlickerFreq.HZ120: "120 Hz",
}

print("AS7343 Flicker Detection Test")
print("=============================")
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

# --- API test: enable / disable ---
print("API Test:")

sensor.flicker_detection_enabled = True
print("  flicker_detection_enabled = True:  OK")

sensor.flicker_detection_enabled = False
print("  flicker_detection_enabled = False: OK")

print()

# --- Observation 1: NeoPixels ON dim (DC source) ---
print("Flicker detection with NeoPixels ON (dim):")
pixels.fill((32, 32, 32))
pixels.show()

sensor.flicker_detection_enabled = True
time.sleep(0.5)  # let detection stabilise

raw_status = sensor.flicker_status
freq = sensor.flicker_frequency
print(f"  Raw status:  0x{raw_status:02X}")
print(f"  Frequency:   {_FLICKER_NAMES.get(freq, 'UNKNOWN')}")
print()

# --- Observation 2: NeoPixels OFF (ambient only) ---
print("Flicker detection with NeoPixels OFF (ambient):")
pixels.fill((0, 0, 0))
pixels.show()
time.sleep(0.5)

raw_status = sensor.flicker_status
freq = sensor.flicker_frequency
print(f"  Raw status:  0x{raw_status:02X}")
print(f"  Frequency:   {_FLICKER_NAMES.get(freq, 'UNKNOWN')}")
print()

sensor.flicker_detection_enabled = False

print("API functional: PASS")
print("RESULT: PASS")

print("~~END~~")
