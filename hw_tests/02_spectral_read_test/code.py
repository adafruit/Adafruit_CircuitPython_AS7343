# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 02 — AS7343 spectral read

Tests 18-channel spectral reading using the 5 on-board NeoPixels as the
illumination source.

Steps:
1. Read a dark baseline (NeoPixels OFF)
2. Turn NeoPixels on full white
3. Read all 18 channels
4. Verify readings are non-zero and higher than the baseline

Expected output:
  RESULT: PASS
"""

import time

import board
import neopixel

from adafruit_as7343 import AS7343, Channel

NEOPIXEL_COUNT = 5

print("AS7343 Spectral Read Test")
print("=========================")

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

# Sensor defaults to 18-channel mode

# --- Step 1: Dark baseline ---
print("NeoPixels OFF — baseline reading...")
pixels.fill((0, 0, 0))
pixels.show()
time.sleep(0.1)

baseline = sensor.all_channels

# --- Step 2: NeoPixels ON white ---
print("NeoPixels ON white...")
pixels.fill((255, 255, 255))
pixels.show()
time.sleep(0.2)  # settle

# --- Step 3: Illuminated reading ---
print("Reading all 18 channels...")
readings = sensor.all_channels

# --- Step 4: Print results ---
print()
print("Channel readings (18-channel mode):")

ch = readings  # short alias
print(
    f"Cycle 1: FZ={ch[Channel.FZ]}  FY={ch[Channel.FY]}  "
    f"FXL={ch[Channel.FXL]}  NIR={ch[Channel.NIR]}  "
    f"VIS_TL={ch[Channel.VIS_TL_0]}  VIS_BR={ch[Channel.VIS_BR_0]}"
)
print(
    f"Cycle 2: F2={ch[Channel.F2]}  F3={ch[Channel.F3]}  "
    f"F4={ch[Channel.F4]}  F6={ch[Channel.F6]}  "
    f"VIS_TL={ch[Channel.VIS_TL_1]}  VIS_BR={ch[Channel.VIS_BR_1]}"
)
print(
    f"Cycle 3: F1={ch[Channel.F1]}  F7={ch[Channel.F7]}  "
    f"F8={ch[Channel.F8]}  F5={ch[Channel.F5]}  "
    f"VIS_TL={ch[Channel.VIS_TL_2]}  VIS_BR={ch[Channel.VIS_BR_2]}"
)

# --- Step 5: Turn NeoPixels off ---
pixels.fill((0, 0, 0))
pixels.show()

# --- Step 6: Validate ---
print()
has_nonzero = any(v > 0 for v in readings)
has_change = any(readings[i] > baseline[i] for i in range(18))

if has_nonzero and has_change:
    print("RESULT: PASS")
else:
    if not has_nonzero:
        print("Error: all readings are zero!")
    if not has_change:
        print("Error: no change detected from baseline!")
    print("RESULT: FAIL")

print("~~END~~")
