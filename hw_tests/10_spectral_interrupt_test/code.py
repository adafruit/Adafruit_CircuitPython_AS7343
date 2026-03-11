# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 10 — AS7343 spectral threshold interrupts

Tests spectral threshold interrupt functionality using self-calibrated
thresholds based on ambient vs. NeoPixel-illuminated conditions.

What is tested:
  - STATUS register AINT bit (bit 3) asserts when reading crosses threshold
  - AINT bit clears after clear_status()
  - INT pin (board.D8, active low) goes LOW when AINT fires
  - INT pin returns HIGH after clear_status()

INT pin wiring:
  AS7343 breakout INT pin → board.D8
  The pin is configured as a digital input with an internal pull-up so an
  unwired / floating D8 will read HIGH (no interrupt) rather than randomly
  toggling.  The INT-pin checks will FAIL if the wire is absent, which is
  the expected outcome until it is connected.

Expected output (both wires present):
  RESULT: PASS
Expected output (INT pin not yet wired):
  Status register section: PASS
  INT pin section:         FAIL
  RESULT: FAIL
"""

import time

import board
import digitalio
import neopixel

from adafruit_as7343 import AS7343, Gain, SmuxMode

NEOPIXEL_COUNT = 5
INT_PIN = board.D8  # AS7343 INT (active low) connected here
_DATA_0_L = 0x95


def _single_measurement(sensor):
    """
    Run one complete measurement cycle in 6-channel mode without disturbing
    the STATUS register (unlike all_channels which clears it).
    Returns the FZ channel (index 0) count.
    """
    sensor.spectral_measurement_enabled = False
    time.sleep(0.01)
    sensor.clear_status()
    sensor.spectral_measurement_enabled = True

    deadline = time.monotonic() + 2.0
    while not sensor.data_ready:
        if time.monotonic() > deadline:
            raise TimeoutError("Measurement timeout")
        time.sleep(0.005)

    _ = sensor._astatus
    buf = bytearray(13)
    buf[0] = _DATA_0_L
    with sensor.i2c_device as i2c:
        i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
    sensor.spectral_measurement_enabled = False

    return buf[1] | (buf[2] << 8)  # FZ = channel 0, little-endian


print("AS7343 Spectral Interrupt Test")
print("==============================")
print(f"INT pin: board.D8 (active low)")
print()

# --- Hardware init ---
pixels = neopixel.NeoPixel(board.NEOPIXEL, NEOPIXEL_COUNT, brightness=1.0, auto_write=False)
pixels.fill((0, 0, 0))
pixels.show()

int_pin = digitalio.DigitalInOut(INT_PIN)
int_pin.direction = digitalio.Direction.INPUT
int_pin.pull = digitalio.Pull.UP  # active-low; HIGH = idle, LOW = interrupt

i2c = board.I2C()

try:
    sensor = AS7343(i2c)
    print("AS7343 initialized OK")
except RuntimeError as e:
    print(f"ERROR: {e}")
    print("RESULT: FAIL")
    raise SystemExit

# Configure for consistent readings
sensor.smux_mode = SmuxMode.CH6
sensor.gain = Gain.X4
sensor.atime = 29
sensor._astep = 599

status_test_pass = True
int_pin_pass = True

# ── Calibration ───────────────────────────────────────────────────────────────

print("Calibration:")

pixels.fill((0, 0, 0))
pixels.show()
time.sleep(0.1)
baseline = _single_measurement(sensor)
print(f"  NeoPixels OFF (FZ): {baseline}")

pixels.fill((0, 0, 255))  # blue — good FZ response
pixels.show()
time.sleep(0.1)
peak = _single_measurement(sensor)
print(f"  NeoPixels ON  (FZ): {peak}")

span = peak - baseline
low_thresh = baseline + span // 4
high_thresh = baseline + (3 * span // 4)
print(f"  Low threshold:      {low_thresh}")
print(f"  High threshold:     {high_thresh}")
print()

if span < 50:
    print("ERROR: Insufficient light range for threshold test")
    print("RESULT: FAIL")
    raise SystemExit

# Program thresholds
sensor.spectral_threshold_low = low_thresh
sensor.spectral_threshold_high = high_thresh
sensor.persistence = 0  # fire immediately
sensor.threshold_channel = 0

sensor.clear_status()
time.sleep(0.01)

# Check INT pin is idle (HIGH) before enabling interrupts
int_idle = int_pin.value  # True = HIGH = idle
print(
    f"INT pin before enabling interrupts: {'HIGH (idle, good)' if int_idle else 'LOW (unexpected)'}"
)
if not int_idle:
    print("  Warning: INT pin already asserted before test started")
print()

sensor.spectral_interrupt_enabled = True

# ── High threshold test (NeoPixels ON) ───────────────────────────────────────

print("High threshold test (NeoPixels ON, reading should exceed high_thresh):")
pixels.fill((0, 0, 255))
pixels.show()
time.sleep(0.05)

# Prime the pipeline with one discarded cycle
sensor.clear_status()
sensor.spectral_measurement_enabled = True
deadline = time.monotonic() + 2.0
while not sensor.data_ready:
    if time.monotonic() > deadline:
        print("  ERROR: Timeout on prime cycle")
        status_test_pass = False
        break
    time.sleep(0.005)

_ = sensor._astatus
buf = bytearray(13)
buf[0] = _DATA_0_L
with sensor.i2c_device as i2c:
    i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
sensor.clear_status()

# Measurement cycle under test
deadline = time.monotonic() + 2.0
while not sensor.data_ready:
    if time.monotonic() > deadline:
        print("  ERROR: Timeout")
        status_test_pass = False
        break
    time.sleep(0.005)

_ = sensor._astatus
buf = bytearray(13)
buf[0] = _DATA_0_L
with sensor.i2c_device as i2c:
    i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
fz_reading = buf[1] | (buf[2] << 8)

raw_status = sensor.status  # read BEFORE clearing
aint_set = bool(raw_status & 0x08)
int_low = not int_pin.value  # True when pin is LOW (interrupt active)

print(f"  FZ reading:  {fz_reading}  (high_thresh={high_thresh})")

# STATUS AINT bit
print(f"  AINT bit:    {'SET' if aint_set else 'CLEAR'}", end="")
status_ok = aint_set and (fz_reading > high_thresh)
print(f"  {'PASS' if status_ok else 'FAIL'}")
if not status_ok:
    status_test_pass = False

# INT pin
print(f"  INT pin:     {'LOW (active)' if int_low else 'HIGH (idle)'}", end="")
int_ok = int_low and (fz_reading > high_thresh)
print(f"  {'PASS' if int_ok else 'FAIL'}")
if not int_ok:
    int_pin_pass = False

# Verify both clear after clear_status()
sensor.spectral_measurement_enabled = False
sensor.clear_status()
time.sleep(0.005)
aint_after = bool(sensor.status & 0x08)
int_after = not int_pin.value  # should be False (pin HIGH) after clear
print(
    f"  AINT after clear: {'SET (unexpected)' if aint_after else 'CLEAR'}  "
    f"{'PASS' if not aint_after else 'FAIL'}"
)
print(
    f"  INT  after clear: {'LOW (unexpected)' if int_after else 'HIGH'}  "
    f"{'PASS' if not int_after else 'FAIL'}"
)
if aint_after:
    status_test_pass = False
if int_after:
    int_pin_pass = False

print()

# ── Low threshold test (NeoPixels OFF) ───────────────────────────────────────

print("Low threshold test (NeoPixels OFF, reading should be below low_thresh):")
pixels.fill((0, 0, 0))
pixels.show()
time.sleep(0.05)

# Prime
sensor.clear_status()
sensor.spectral_measurement_enabled = True
deadline = time.monotonic() + 2.0
while not sensor.data_ready:
    if time.monotonic() > deadline:
        print("  ERROR: Timeout on prime cycle")
        status_test_pass = False
        break
    time.sleep(0.005)

_ = sensor._astatus
buf = bytearray(13)
buf[0] = _DATA_0_L
with sensor.i2c_device as i2c:
    i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
sensor.clear_status()

# Test cycle
deadline = time.monotonic() + 2.0
while not sensor.data_ready:
    if time.monotonic() > deadline:
        print("  ERROR: Timeout")
        status_test_pass = False
        break
    time.sleep(0.005)

_ = sensor._astatus
buf = bytearray(13)
buf[0] = _DATA_0_L
with sensor.i2c_device as i2c:
    i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
fz_reading = buf[1] | (buf[2] << 8)

raw_status = sensor.status
aint_set = bool(raw_status & 0x08)
int_low = not int_pin.value

print(f"  FZ reading:  {fz_reading}  (low_thresh={low_thresh})")

# STATUS AINT bit
print(f"  AINT bit:    {'SET' if aint_set else 'CLEAR'}", end="")
status_ok = aint_set and (fz_reading < low_thresh)
print(f"  {'PASS' if status_ok else 'FAIL'}")
if not status_ok:
    status_test_pass = False

# INT pin
print(f"  INT pin:     {'LOW (active)' if int_low else 'HIGH (idle)'}", end="")
int_ok = int_low and (fz_reading < low_thresh)
print(f"  {'PASS' if int_ok else 'FAIL'}")
if not int_ok:
    int_pin_pass = False

# Verify both clear after clear_status()
sensor.spectral_measurement_enabled = False
sensor.clear_status()
time.sleep(0.005)
aint_after = bool(sensor.status & 0x08)
int_after = not int_pin.value
print(
    f"  AINT after clear: {'SET (unexpected)' if aint_after else 'CLEAR'}  "
    f"{'PASS' if not aint_after else 'FAIL'}"
)
print(
    f"  INT  after clear: {'LOW (unexpected)' if int_after else 'HIGH'}  "
    f"{'PASS' if not int_after else 'FAIL'}"
)
if aint_after:
    status_test_pass = False
if int_after:
    int_pin_pass = False

print()

# ── Clean up and summary ──────────────────────────────────────────────────────

sensor.spectral_interrupt_enabled = False
int_pin.deinit()
pixels.fill((0, 0, 0))
pixels.show()

print("Summary:")
print(f"  Status register (AINT): {'PASS' if status_test_pass else 'FAIL'}")
print(f"  INT pin (board.D8):     {'PASS' if int_pin_pass     else 'FAIL'}")
print()
print(f"RESULT: {'PASS' if status_test_pass and int_pin_pass else 'FAIL'}")

print("~~END~~")
