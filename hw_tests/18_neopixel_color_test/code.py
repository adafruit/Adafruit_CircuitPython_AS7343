# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 18 — AS7343 NeoPixel colour response

Verifies that the AS7343 spectral channels respond correctly to different
primary colours produced by the 5 on-board NeoPixels.

For each colour the average count of the "expected-high" channels must
exceed the average count of the "expected-low" channels:

  RED   (255, 0, 0)   dominant: F6 640 nm, F7 690 nm
                      weak:     FZ 450 nm, F2 425 nm, F3 475 nm

  GREEN (0, 255, 0)   dominant: F4 515 nm, FY 555 nm, F5 550 nm
                      weak:     FZ 450 nm, F2 425 nm, F3 475 nm
                      (NeoPixel green LEDs have some red bleed so we
                       compare against the clearly unresponsive blue channels)

  BLUE  (0, 0, 255)   dominant: FZ 450 nm, F2 425 nm, F3 475 nm
                      weak:     F6 640 nm, F7 690 nm

128× gain is used to keep readings well below saturation with 5 NeoPixels.

Expected output:
  RESULT: PASS
"""

import time

import board
import neopixel

from adafruit_as7343 import AS7343, Channel, Gain

NEOPIXEL_COUNT = 5


def read_colour(sensor, pixels, r, g, b):
    """Set pixels to (r,g,b), settle, return 18-channel reading list."""
    pixels.fill((r, g, b))
    pixels.show()
    time.sleep(0.2)
    return sensor.all_channels


def avg(readings, indices):
    return sum(readings[i] for i in indices) / len(indices)


def test_colour(name, readings, high_channels, low_channels, desc):
    high_avg = avg(readings, high_channels)
    low_avg = avg(readings, low_channels)
    passed = high_avg > low_avg

    # Print key channels
    ch = readings
    print(f"  F2(425nm)={ch[Channel.F2]}  F3(475nm)={ch[Channel.F3]}  FZ(450nm)={ch[Channel.FZ]}")
    print(f"  F4(515nm)={ch[Channel.F4]}  FY(555nm)={ch[Channel.FY]}  F5(550nm)={ch[Channel.F5]}")
    print(f"  F6(640nm)={ch[Channel.F6]}  F7(690nm)={ch[Channel.F7]}  F8(745nm)={ch[Channel.F8]}")
    print(
        f"  Dominant: {desc}  —  high_avg={high_avg:.0f}  low_avg={low_avg:.0f}  "
        f"{'PASS' if passed else 'FAIL'}"
    )
    if not passed:
        print(f"  (high_avg {high_avg:.0f} should be > low_avg {low_avg:.0f})")
    return passed


print("AS7343 NeoPixel Colour Test")
print("===========================")
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

sensor.gain = Gain.X128

all_pass = True

# ── RED ───────────────────────────────────────────────────────────────────────

print("RED (255, 0, 0):")
red_readings = read_colour(sensor, pixels, 255, 0, 0)
red_high = [Channel.F6, Channel.F7]
red_low = [Channel.FZ, Channel.F2, Channel.F3]
if not test_colour("RED", red_readings, red_high, red_low, "F6, F7 (red channels)"):
    all_pass = False

print()

# ── GREEN ─────────────────────────────────────────────────────────────────────

print("GREEN (0, 255, 0):")
green_readings = read_colour(sensor, pixels, 0, 255, 0)
green_high = [Channel.F4, Channel.FY, Channel.F5]
green_low = [Channel.FZ, Channel.F2, Channel.F3]
if not test_colour("GREEN", green_readings, green_high, green_low, "F4, FY, F5 (green channels)"):
    all_pass = False

print()

# ── BLUE ──────────────────────────────────────────────────────────────────────

print("BLUE (0, 0, 255):")
blue_readings = read_colour(sensor, pixels, 0, 0, 255)
blue_high = [Channel.FZ, Channel.F2, Channel.F3]
blue_low = [Channel.F6, Channel.F7]
if not test_colour("BLUE", blue_readings, blue_high, blue_low, "FZ, F2, F3 (blue channels)"):
    all_pass = False

# ── Clean up ──────────────────────────────────────────────────────────────────

pixels.fill((0, 0, 0))
pixels.show()

print()
print(f"Colour response: {'PASS' if all_pass else 'FAIL'}")
print(f"RESULT: {'PASS' if all_pass else 'FAIL'}")

print("~~END~~")
