# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 03 — AS7343 gain settings

Tests all 13 gain settings (0.5× to 2048×) and verifies:
- Gain readback matches set value
- F4 channel (515 nm green) readings increase with gain until saturation

NeoPixels are set to moderate brightness to give headroom for low gains
without immediately saturating at high gains.

Expected output:
  RESULT: PASS
"""

import time

import board
import neopixel

from adafruit_as7343 import AS7343, Channel, Gain, SmuxMode

NEOPIXEL_COUNT = 5

GAIN_LABELS = {
    Gain.X0_5: "0.5X",
    Gain.X1: "1X",
    Gain.X2: "2X",
    Gain.X4: "4X",
    Gain.X8: "8X",
    Gain.X16: "16X",
    Gain.X32: "32X",
    Gain.X64: "64X",
    Gain.X128: "128X",
    Gain.X256: "256X",
    Gain.X512: "512X",
    Gain.X1024: "1024X",
    Gain.X2048: "2048X",
}

print("AS7343 Gain Test")
print("================")

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

# Use shorter integration time to avoid saturation at high gains
# (ATIME+1)×(ASTEP+1)×2.78µs = 10×1000×2.78µs ≈ 27.8 ms
sensor.atime = 9
sensor._astep = 999

# Moderate NeoPixel brightness to give gain range room
print("NeoPixels ON (moderate)...")
pixels.fill((64, 64, 64))
pixels.show()
time.sleep(0.1)

print()
print(f"{'Gain':<8} {'F4 Reading'}")
print(f"{'----':<8} {'----------'}")

all_readbacks_ok = True
readings = []

for g in range(13):
    # Set gain
    sensor.gain = g

    # Verify readback
    readback = sensor.gain
    if readback != g:
        all_readbacks_ok = False

    # Take a fresh measurement
    try:
        sensor.read_timeout = 2000
        channels = sensor.all_channels
        f4 = channels[Channel.F4]
    except TimeoutError:
        print(f"{GAIN_LABELS[g]:<8} TIMEOUT")
        readings.append(0)
        continue

    readings.append(f4)
    print(f"{GAIN_LABELS[g]:<8} {f4}")

# --- Turn NeoPixels off ---
pixels.fill((0, 0, 0))
pixels.show()
print()

# --- Evaluate ---
print(f"Readback verification: {'PASS' if all_readbacks_ok else 'FAIL'}")

# 2× gain should produce more signal than 1× gain
scaling_ok = readings[Gain.X2] > readings[Gain.X1]

# Count how many of the 12 gain transitions show an increase (allow saturation)
increasing = sum(1 for i in range(1, 13) if readings[i] > readings[i - 1])
trend_ok = increasing >= 10

print(f"Gain scaling check: {'PASS' if (scaling_ok and trend_ok) else 'FAIL'}")
print(f"  ({increasing}/12 transitions showed increasing readings)")

all_pass = all_readbacks_ok and scaling_ok and trend_ok
print(f"RESULT: {'PASS' if all_pass else 'FAIL'}")

print("~~END~~")
