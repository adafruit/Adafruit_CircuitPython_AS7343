# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 13 — AS7343 threshold channel register

Two-part test:

Part 1 — Register readback
  Writes channels 0–5 to the SP_TH_CH register and verifies readback.

  NOTE: Per hardware testing, SP_TH_CH does NOT affect which channel the
  threshold comparator actually monitors — comparisons always target CH0
  regardless of this setting.  The register read/write does work correctly.

Part 2 — Threshold comparison (always CH0)
  Calibrates a HIGH threshold between the dark and lit readings of CH0,
  then counts measurement cycles to AINT for two conditions:

    Test A — NeoPixels ON  (CH0 > threshold) → AINT should fire
    Test B — NeoPixels OFF (CH0 < threshold) → AINT should NOT fire (timeout)

Measurement strategy:
  SP_EN is kept asserted between cycles so the persistence counter is not
  reset by a stop/start.  STATUS is read inside the loop but only cleared
  at the top of each `all_channels` access — to avoid that interaction
  we drive SP_EN directly and read STATUS manually (same as test 12).

Expected output:
  RESULT: PASS
"""

import time

import board
import neopixel

from adafruit_as7343 import AS7343, Gain, SmuxMode

NEOPIXEL_COUNT = 5
MAX_CYCLES = 25
_DATA_0_L = 0x95


# ---------------------------------------------------------------------------
# Continuous-mode cycle counter (same pattern as test 12)
# ---------------------------------------------------------------------------


def _read_burst_ch0(sensor):
    """Burst-read 6 channels and return FZ (channel 0) without touching STATUS."""
    buf = bytearray(13)
    buf[0] = _DATA_0_L
    with sensor.i2c_device as i2c:
        i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
    return buf[1] | (buf[2] << 8)


def count_cycles_to_aint(sensor, max_cycles=MAX_CYCLES):
    """
    Count consecutive measurement cycles until STATUS AINT (bit 3) is set.
    SP_EN must be asserted before calling; it is left asserted on return.
    Returns cycle count, or max_cycles + 1 on timeout.
    """
    cycles = 0
    while cycles < max_cycles:
        deadline = time.monotonic() + 2.0
        while not sensor.data_ready:
            if time.monotonic() > deadline:
                return max_cycles + 1
            time.sleep(0.001)

        _ = sensor._astatus  # latch data, clears AVALID
        _read_burst_ch0(sensor)  # read channels (advances chip)
        cycles += 1

        if sensor.status & 0x08:  # AINT fired
            break

    return cycles


# ---------------------------------------------------------------------------
# Main test
# ---------------------------------------------------------------------------

print("AS7343 Threshold Channel Test")
print("=============================")
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

readback_passed = True
hardware_passed = True

# ── Part 1: Register readback ─────────────────────────────────────────────────

print("Part 1: Register Readback")
print(f"{'Channel':<10} {'Readback':<10} {'Status'}")
print(f"{'-------':<10} {'--------':<10} {'------'}")

for ch in range(6):
    sensor.threshold_channel = ch
    rb = sensor.threshold_channel
    ok = rb == ch
    if not ok:
        readback_passed = False
    print(f"{ch:<10} {rb:<10} {'PASS' if ok else 'FAIL'}")

print()
print(f"Register readback: {'PASS' if readback_passed else 'FAIL'}")
print()

# ── Part 2: Threshold comparison (always CH0) ─────────────────────────────────

print("Part 2: Threshold Comparison (always CH0)")
print()

sensor.smux_mode = SmuxMode.CH6
sensor.gain = Gain.X4
sensor.atime = 29
sensor._astep = 599

# Calibration
print("Calibration:")

pixels.fill((0, 0, 0))
pixels.show()
time.sleep(0.1)

sensor.spectral_measurement_enabled = True
deadline = time.monotonic() + 2.0
while not sensor.data_ready:
    if time.monotonic() > deadline:
        print("ERROR: Timeout during calibration (dark)")
        print("RESULT: FAIL")
        raise SystemExit
    time.sleep(0.001)
_ = sensor._astatus
ch0_off = _read_burst_ch0(sensor)
sensor.spectral_measurement_enabled = False
print(f"  NeoPixels OFF (CH0): {ch0_off}")

pixels.fill((0, 0, 255))
pixels.show()
time.sleep(0.1)

sensor.spectral_measurement_enabled = True
deadline = time.monotonic() + 2.0
while not sensor.data_ready:
    if time.monotonic() > deadline:
        print("ERROR: Timeout during calibration (lit)")
        print("RESULT: FAIL")
        raise SystemExit
    time.sleep(0.001)
_ = sensor._astatus
ch0_on = _read_burst_ch0(sensor)
sensor.spectral_measurement_enabled = False
print(f"  NeoPixels ON  (CH0): {ch0_on}")

threshold = ch0_off + (ch0_on - ch0_off) // 3
print(f"  Threshold:           {threshold}")
print()

if (ch0_on - ch0_off) < 50:
    print("ERROR: Insufficient light range for threshold test")
    print("RESULT: FAIL")
    raise SystemExit

# Configure thresholds and persistence
sensor.spectral_interrupt_enabled = False
sensor.spectral_threshold_low = 0
sensor.spectral_threshold_high = threshold
sensor.persistence = 4
sensor.threshold_channel = 0

# ── Test A: NeoPixels ON → CH0 > threshold → AINT should fire ────────────────

print("Test A: NeoPixels ON (CH0 > threshold)")
pixels.fill((0, 0, 255))
pixels.show()
time.sleep(0.1)

sensor.clear_status()
sensor.spectral_interrupt_enabled = True
sensor.spectral_measurement_enabled = True

cycles_a = count_cycles_to_aint(sensor)

sensor.spectral_measurement_enabled = False
sensor.spectral_interrupt_enabled = False

pass_a = cycles_a < MAX_CYCLES
print(f"  Cycles to AINT: {cycles_a}  {'PASS' if pass_a else 'FAIL'}")
if not pass_a:
    hardware_passed = False

# ── Test B: NeoPixels OFF → CH0 < threshold → AINT should NOT fire ───────────

print("Test B: NeoPixels OFF (CH0 < threshold)")
pixels.fill((0, 0, 0))
pixels.show()
time.sleep(0.1)

sensor.clear_status()
sensor.spectral_interrupt_enabled = True
sensor.spectral_measurement_enabled = True

cycles_b = count_cycles_to_aint(sensor)

sensor.spectral_measurement_enabled = False
sensor.spectral_interrupt_enabled = False

pass_b = cycles_b >= MAX_CYCLES
print(f"  Cycles to AINT: {cycles_b}  {'(timeout) PASS' if pass_b else 'FAIL'}")
if not pass_b:
    hardware_passed = False

pixels.fill((0, 0, 0))
pixels.show()

# ── Summary ───────────────────────────────────────────────────────────────────

print()
print("Verification:")
print(f"  a) Light ON triggers AINT:   {'PASS' if pass_a else 'FAIL'}")
print(f"  b) Light OFF no trigger:     {'PASS' if pass_b else 'FAIL'}")
print()
print("Note: SP_TH_CH register r/w works but does NOT")
print("      affect threshold comparison (always CH0)")
print()
print(f"Register readback: {'PASS' if readback_passed else 'FAIL'}")
print(f"Hardware test:     {'PASS' if hardware_passed else 'FAIL'}")
print(f"RESULT: {'PASS' if readback_passed and hardware_passed else 'FAIL'}")

print("~~END~~")
