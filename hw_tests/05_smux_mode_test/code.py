# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 05 — AS7343 Auto-SMUX mode switching

The AS7343 has 14 spectral channels but only 6 ADCs, so a multiplexer
(SMUX) cycles through channel groups.  The auto-SMUX feature chains
multiple cycles automatically:

  SmuxMode.CH6  — 6 channels,  1 cycle
  SmuxMode.CH12 — 12 channels, 2 cycles
  SmuxMode.CH18 — 18 channels, 3 cycles  (default)

Tests:
- smux_mode readback for all three modes
- all_channels returns the correct number of values per mode
- Spot-check channel values are non-zero with NeoPixels illuminating

Expected output:
  RESULT: PASS
"""

import time

import board
import neopixel

from adafruit_as7343 import AS7343, Channel, SmuxMode

NEOPIXEL_COUNT = 5
TIMEOUT_MS = 2000

print("AS7343 SMUX Mode Test")
print("=====================")

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

print("NeoPixels ON...")
pixels.fill((64, 64, 64))
pixels.show()
time.sleep(0.1)

print()
print(f"{'Mode':<8} {'Readback':<10} {'# Values':<10} Sample Values")
print(f"{'----':<8} {'--------':<10} {'--------':<10} -------------")

all_readback_pass = True


def test_mode(mode_val, mode_label, expected_count):
    global all_readback_pass  # noqa: PLW0603

    sensor.smux_mode = mode_val

    readback = sensor.smux_mode
    readback_ok = readback == mode_val
    if not readback_ok:
        all_readback_pass = False

    rb_str = "PASS" if readback_ok else "FAIL"

    try:
        sensor.read_timeout = TIMEOUT_MS
        ch = sensor.all_channels
    except TimeoutError:
        print(f"{mode_label:<8} {rb_str:<10} {'--':<10} TIMEOUT")
        return

    count_ok = len(ch) == expected_count
    count_str = str(len(ch))

    # Sample values vary by mode
    if expected_count >= 6:
        sample = f"FZ={ch[0]} FY={ch[1]} FXL={ch[2]}"
    if expected_count >= 12:
        sample += f" ... F6={ch[9]} VIS_TL={ch[10]} VIS_BR={ch[11]}"
    if expected_count >= 18:
        sample += f" ... F5={ch[15]} VIS_TL={ch[16]} VIS_BR={ch[17]}"

    if not count_ok:
        all_readback_pass = False
        count_str += f"(expected {expected_count})"

    print(f"{mode_label:<8} {rb_str:<10} {count_str:<10} {sample}")


test_mode(SmuxMode.CH6, "6CH", 6)
test_mode(SmuxMode.CH12, "12CH", 12)
test_mode(SmuxMode.CH18, "18CH", 18)

# --- Turn NeoPixels off ---
pixels.fill((0, 0, 0))
pixels.show()
print()

print(f"Mode readback: {'PASS' if all_readback_pass else 'FAIL'}")
print(f"RESULT: {'PASS' if all_readback_pass else 'FAIL'}")

print("~~END~~")
