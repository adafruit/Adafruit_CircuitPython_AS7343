# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 11 — AS7343 threshold register readback

Tests spectral_threshold_low and spectral_threshold_high readback
across the full 16-bit range, plus an independence check that writing
one threshold does not clobber the other.

No NeoPixels or ambient light required — pure register I/O.

Expected output:
  RESULT: PASS
"""

import board

from adafruit_as7343 import AS7343

TEST_VALUES = [0, 1000, 32768, 65535]

print("AS7343 Threshold Test")
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

# ── Low threshold readback ────────────────────────────────────────────────────

print("Low Threshold Readback:")
print(f"  {'Value':<12} {'Readback':<12} {'Status'}")
print(f"  {'-----':<12} {'--------':<12} {'------'}")

for val in TEST_VALUES:
    sensor.spectral_threshold_low = val
    rb = sensor.spectral_threshold_low
    ok = rb == val
    if not ok:
        all_passed = False
    print(f"  {val:<12} {rb:<12} {'PASS' if ok else 'FAIL'}")

print()

# ── High threshold readback ───────────────────────────────────────────────────

print("High Threshold Readback:")
print(f"  {'Value':<12} {'Readback':<12} {'Status'}")
print(f"  {'-----':<12} {'--------':<12} {'------'}")

for val in TEST_VALUES:
    sensor.spectral_threshold_high = val
    rb = sensor.spectral_threshold_high
    ok = rb == val
    if not ok:
        all_passed = False
    print(f"  {val:<12} {rb:<12} {'PASS' if ok else 'FAIL'}")

print()

# ── Independence test ─────────────────────────────────────────────────────────

print("Independence test:")
low_val = 1234
high_val = 5678

sensor.spectral_threshold_low = low_val
sensor.spectral_threshold_high = high_val

read_low = sensor.spectral_threshold_low
read_high = sensor.spectral_threshold_high

print(f"  Set  low={low_val}, high={high_val}")
print(f"  Read low={read_low}, high={read_high}")

indep_pass = (read_low == low_val) and (read_high == high_val)
if not indep_pass:
    all_passed = False
print(f"  {'PASS' if indep_pass else 'FAIL'}")
print()

print(f"Threshold readback: {'PASS' if all_passed else 'FAIL'}")
print(f"RESULT: {'PASS' if all_passed else 'FAIL'}")

print("~~END~~")
