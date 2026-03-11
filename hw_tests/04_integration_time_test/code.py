# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 04 — AS7343 integration time settings

Tests ATIME and ASTEP register readback and verifies that longer integration
times produce proportionally higher F4 channel readings.

Integration time formula:
  t_int = (ATIME + 1) × (ASTEP + 1) × 2.78 µs

Test configurations:
  Short  — ATIME=9,  ASTEP=299  ≈   8.3 ms
  Medium — ATIME=29, ASTEP=599  ≈  50.0 ms  (driver default)
  Long   — ATIME=99, ASTEP=999  ≈ 278.0 ms

Expected output:
  RESULT: PASS
"""

import time

import board
import neopixel

from adafruit_as7343 import AS7343, Channel, Gain

NEOPIXEL_COUNT = 5

# (label, atime, astep, expected_ms)
TEST_CONFIGS = [
    ("Short", 9, 299, 8.3),
    ("Medium", 29, 599, 50.0),
    ("Long", 99, 999, 278.0),
]

print("AS7343 Integration Time Test")
print("============================")

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

# Moderate gain to avoid saturation across all integration lengths
sensor.gain = Gain.X64

print("NeoPixels ON (moderate), Gain 64X...")
pixels.fill((64, 64, 64))
pixels.show()
time.sleep(0.1)

print()
print(f"{'Setting':<10} {'ATIME':>5}  {'ASTEP':>5}  {'Calc ms':>9}  {'F4 Reading':>10}")
print(f"{'-------':<10} {'-----':>5}  {'-----':>5}  {'-------':>9}  {'----------':>10}")

all_readbacks_ok = True
readings = []

for label, atime, astep, expected_ms in TEST_CONFIGS:
    # Set integration time registers
    sensor.atime = atime
    sensor._astep = astep

    # Verify readback
    atime_rb = sensor.atime
    astep_rb = sensor._astep
    if atime_rb != atime or astep_rb != astep:
        all_readbacks_ok = False

    calc_ms = sensor.integration_time_ms

    # Long integration needs extra timeout headroom (3 SMUX cycles)
    timeout = int(calc_ms * 3 * 1.5) + 500
    try:
        sensor.read_timeout = timeout
        channels = sensor.all_channels
        f4 = channels[Channel.F4]
    except TimeoutError:
        print(f"{label:<10} {atime:>5}  {astep:>5}  {calc_ms:>9.1f}  TIMEOUT")
        readings.append(0)
        continue

    readings.append(f4)
    print(f"{label:<10} {atime:>5}  {astep:>5}  {calc_ms:>9.1f}  {f4:>10}")

# --- Turn NeoPixels off ---
pixels.fill((0, 0, 0))
pixels.show()
print()

# --- Evaluate ---
print(f"ATIME/ASTEP readback: {'PASS' if all_readbacks_ok else 'FAIL'}")

# Readings must increase: Short < Medium < Long
if len(readings) == 3:
    scaling_ok = (readings[0] < readings[1]) and (readings[1] < readings[2])
else:
    scaling_ok = False

status = "PASS" if scaling_ok else "FAIL"
print(f"Integration scaling:  {status}  (longer time = higher reading)")
if len(readings) == 3:
    print(f"  Short={readings[0]}  Medium={readings[1]}  Long={readings[2]}")

all_pass = all_readbacks_ok and scaling_ok
print(f"RESULT: {'PASS' if all_pass else 'FAIL'}")

print("~~END~~")
