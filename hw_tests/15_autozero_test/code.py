# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 15 — AS7343 auto-zero configuration

Tests the auto-zero frequency register (AZ_CONFIG, 0xDE):
  - auto_zero_frequency property write / readback
  - All four test values: 0, 1, 127, 255

Auto-zero compensates for temperature-induced offset drift:
  0   — disabled (not recommended)
  1   — every measurement cycle
  127 — every 127th cycle
  255 — only before the very first measurement (driver default)

No NeoPixels or ambient light required — pure register I/O.

Expected output:
  RESULT: PASS
"""

import time

import board

from adafruit_as7343 import AS7343

TEST_VALUES = [0, 1, 127, 255]

print("AS7343 Auto-Zero Test")
print("=====================")
print()

i2c = board.I2C()

try:
    sensor = AS7343(i2c)
    print("AS7343 initialized OK")
except RuntimeError as e:
    print(f"ERROR: {e}")
    print("RESULT: FAIL")
    raise SystemExit

all_passed = True

print("Auto-Zero Frequency Readback:")
print(f"{'Value':<10} {'Readback':<10} {'Status'}")
print(f"{'-----':<10} {'--------':<10} {'------'}")

for val in TEST_VALUES:
    sensor.auto_zero_frequency = val
    time.sleep(0.01)
    rb = sensor.auto_zero_frequency
    ok = rb == val
    if not ok:
        all_passed = False
    print(f"{val:<10} {rb:<10} {'PASS' if ok else 'FAIL'}")

print()
print(f"Auto-zero readback: {'PASS' if all_passed else 'FAIL'}")
print(f"RESULT: {'PASS' if all_passed else 'FAIL'}")

print("~~END~~")
