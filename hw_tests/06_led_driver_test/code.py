# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 06 — AS7343 LED driver

Tests the integrated LED driver on the AS7343 breakout:
- Enable/disable via led_enabled property
- led_current_ma readback at several set points (4, 50, 100, 258 mA)
- Ramp demo at the end (loop) so the IR LED can be observed with a camera

NeoPixels are kept OFF throughout — the AS7343's own LED is under test.

Expected output:
  RESULT: PASS
  (followed by a continuous current ramp)
"""

import time

import board
import neopixel

from adafruit_as7343 import AS7343

NEOPIXEL_COUNT = 5

# Test currents in mA
TEST_CURRENTS = [4, 50, 100, 258]

print("AS7343 LED Driver Test")
print("======================")
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

enable_test_ok = True
current_test_ok = True

# --- Test enable/disable ---
print("LED Enable/Disable: Testing...")

sensor.led_enabled = True
time.sleep(0.05)
print("  led_enabled = True:  OK")

sensor.led_enabled = False
time.sleep(0.05)
print("  led_enabled = False: OK")

print()

# --- Test current readback ---
print("LED Current Settings:")
print(f"{'Set (mA)':<12} {'Read (mA)':<14} {'Status'}")
print(f"{'--------':<12} {'---------':<14} {'------'}")

for set_ma in TEST_CURRENTS:
    sensor.led_current_ma = set_ma
    time.sleep(0.01)
    read_ma = sensor.led_current_ma

    # Hardware steps in 2 mA increments; allow ±2 mA tolerance
    diff = abs(read_ma - set_ma)
    pass_this = diff <= 2

    if not pass_this:
        current_test_ok = False

    status = "PASS" if pass_this else f"FAIL (diff={diff}mA)"
    print(f"{set_ma:<12} {read_ma:<14} {status}")

print()
print(f"Current readback: {'PASS' if current_test_ok else 'FAIL'}")

all_pass = enable_test_ok and current_test_ok
print(f"RESULT: {'PASS' if all_pass else 'FAIL'}")

print("~~END~~")

# --- Ramp demo ---
print()
print("Starting LED current ramp demo (4–258 mA, ~2 s up / ~2 s down)...")
print("Point a camera at the AS7343 IR LED to observe. Ctrl-C to stop.")

sensor.led_current_ma = 4
sensor.led_enabled = True

while True:
    # Ramp up: 4 → 258 mA
    for ma in range(4, 260, 2):
        sensor.led_current_ma = ma
        time.sleep(0.015)
    # Ramp down: 258 → 4 mA
    for ma in range(258, 2, -2):
        sensor.led_current_ma = ma
        time.sleep(0.015)
