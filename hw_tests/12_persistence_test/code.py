# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 12 — AS7343 persistence filter

Two-part test:

Part 1 — Register readback
  Writes and reads back all valid persistence values (0–15).

Part 2 — Hardware timing verification
  Counts how many measurement cycles elapse before the STATUS AINT bit (bit 3)
  is asserted for persistence=1 and persistence=8, then verifies:
    a) persistence=1  triggers AINT (within timeout)
    b) persistence=8  triggers AINT (within timeout)
    c) persistence=8 takes more cycles than persistence=1

  The AINT bit is read from the STATUS register; no INT pin is required.

  Measurement strategy:
    SP_EN is kept asserted so the sensor runs continuously.
    After each AVALID we latch + read channels (to clear AVALID) and then
    check the STATUS register for AINT — without accessing all_channels
    which would clear STATUS.

  Calibration:
    A baseline (NeoPixels OFF) and peak (NeoPixels ON white) reading are
    taken to derive a HIGH threshold at baseline + 20% of range.

Expected output:
  RESULT: PASS
"""

import time

import board
import neopixel

from adafruit_as7343 import AS7343, Gain, SmuxMode

NEOPIXEL_COUNT = 5
MAX_CYCLES = 50
_DATA_0_L = 0x95  # first channel data register


def _read_burst_ch0(sensor):
    """Burst-read 6 channels; return FZ (channel 0) count without touching STATUS."""
    buf = bytearray(13)
    buf[0] = _DATA_0_L
    with sensor.i2c_device as i2c:
        i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
    return buf[1] | (buf[2] << 8)


def count_cycles_to_aint(sensor, max_cycles=MAX_CYCLES):
    """
    Count measurement cycles until STATUS AINT (bit 3) fires.
    SP_EN must already be asserted before calling.
    Returns cycle count, or max_cycles+1 on timeout.
    """
    cycles = 0
    while cycles < max_cycles:
        # Wait for AVALID
        deadline = time.monotonic() + 2.0
        while not sensor.data_ready:
            if time.monotonic() > deadline:
                return max_cycles + 1
            time.sleep(0.001)

        # Latch + read (clears AVALID; chip starts next cycle)
        _ = sensor._astatus
        _read_burst_ch0(sensor)
        cycles += 1

        # Check AINT bit (bit 3 of STATUS) — do NOT clear STATUS here
        if sensor.status & 0x08:
            break

    return cycles


print("AS7343 Persistence Test")
print("=======================")
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
timing_passed = True

# ── Part 1: Register readback ─────────────────────────────────────────────────

print("Part 1: Register Readback")
print(f"{'Value':<10} {'Readback':<10} {'Status'}")
print(f"{'-----':<10} {'--------':<10} {'------'}")

for val in range(16):
    sensor.persistence = val
    rb = sensor.persistence
    ok = rb == val
    if not ok:
        readback_passed = False
    print(f"{val:<10} {rb:<10} {'PASS' if ok else 'FAIL'}")

print()
print(f"Register readback: {'PASS' if readback_passed else 'FAIL'}")
print()

# ── Part 2: Hardware timing verification ─────────────────────────────────────

print("Part 2: Hardware Timing Verification")
print()

# Configure for fast measurements
sensor.smux_mode = SmuxMode.CH6
sensor.gain = Gain.X16
sensor.atime = 9
sensor._astep = 599

# Calibration
print("Calibration:")

pixels.fill((0, 0, 0))
pixels.show()
time.sleep(0.05)
sensor.spectral_measurement_enabled = True
deadline = time.monotonic() + 2.0
while not sensor.data_ready:
    if time.monotonic() > deadline:
        print("ERROR: Timeout during calibration (dark)")
        print("RESULT: FAIL")
        raise SystemExit
    time.sleep(0.001)
_ = sensor._astatus
baseline = _read_burst_ch0(sensor)
sensor.spectral_measurement_enabled = False
print(f"  NeoPixels OFF (FZ baseline): {baseline}")

pixels.fill((255, 255, 255))
pixels.show()
time.sleep(0.05)
sensor.spectral_measurement_enabled = True
deadline = time.monotonic() + 2.0
while not sensor.data_ready:
    if time.monotonic() > deadline:
        print("ERROR: Timeout during calibration (lit)")
        print("RESULT: FAIL")
        raise SystemExit
    time.sleep(0.001)
_ = sensor._astatus
peak = _read_burst_ch0(sensor)
sensor.spectral_measurement_enabled = False
print(f"  NeoPixels ON  (FZ peak):     {peak}")

span = peak - baseline
threshold = baseline + span // 5  # baseline + 20% of range
print(f"  HIGH threshold (base+20%):   {threshold}")
print()

if span < 100:
    print("ERROR: Insufficient light range for persistence test")
    print("RESULT: FAIL")
    raise SystemExit

# Program threshold (high only — readings with NeoPixels on will exceed it)
sensor.spectral_threshold_high = threshold
sensor.threshold_channel = 0

print("Counting Cycles to AINT:")
print(f"{'Persistence':<14} {'Cycles':<8} {'Status'}")
print(f"{'-----------':<14} {'------':<8} {'------'}")

# ── Persistence = 1 ──
pixels.fill((255, 255, 255))
pixels.show()
time.sleep(0.02)

sensor.persistence = 1
sensor.clear_status()
sensor.spectral_interrupt_enabled = True
sensor.spectral_measurement_enabled = True  # start continuous measurement

count1 = count_cycles_to_aint(sensor)
sensor.spectral_measurement_enabled = False
sensor.spectral_interrupt_enabled = False

pass1 = 0 < count1 <= MAX_CYCLES
print(f"{'1':<14} {count1:<8} {'PASS' if pass1 else 'FAIL'}")
if not pass1:
    timing_passed = False

# ── Persistence = 8 ──
pixels.fill((255, 255, 255))
pixels.show()
time.sleep(0.02)

sensor.persistence = 8
sensor.clear_status()
sensor.spectral_interrupt_enabled = True
sensor.spectral_measurement_enabled = True

count8 = count_cycles_to_aint(sensor)
sensor.spectral_measurement_enabled = False
sensor.spectral_interrupt_enabled = False

pass8 = 0 < count8 <= MAX_CYCLES
print(f"{'8':<14} {count8:<8} {'PASS' if pass8 else 'FAIL'}")
if not pass8:
    timing_passed = False

pixels.fill((0, 0, 0))
pixels.show()
print()

# ── Verification ──────────────────────────────────────────────────────────────

print("Verification:")
print(f"  a) persistence=1 triggers AINT:   {'PASS' if pass1 else 'FAIL'}")
print(f"  b) persistence=8 triggers AINT:   {'PASS' if pass8 else 'FAIL'}")

order_pass = count8 > count1
print(
    f"  c) Higher persistence = more cycles "
    f"({count8} > {count1}): {'PASS' if order_pass else 'FAIL'}"
)
if not order_pass:
    timing_passed = False

print()
print(f"Register readback: {'PASS' if readback_passed else 'FAIL'}")
print(f"Timing test:       {'PASS' if timing_passed   else 'FAIL'}")
print(f"RESULT: {'PASS' if readback_passed and timing_passed else 'FAIL'}")

print("~~END~~")
