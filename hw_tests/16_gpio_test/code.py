# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 16 — AS7343 GPIO

Tests the AS7343 GPIO pin with hardware verification via a feedback wire.

GPIO wiring:
  AS7343 breakout GPIO pin → board.D9

  IMPORTANT — open-drain behaviour:
    The AS7343 GPIO is open-drain: it can actively pull the line LOW but
    cannot drive it HIGH.  "High" output is achieved by releasing the
    open-drain driver and relying on an external (or internal) pull-up.
    board.D9 is configured with Pull.UP so it reads HIGH whenever the
    AS7343 GPIO is released.

Part 1 — Output mode
  AS7343 GPIO configured as output (gpio_output_mode = True).
  gpio_value True  → open-drain released → D9 reads HIGH  (pass)
  gpio_value False → open-drain active   → D9 reads LOW   (pass)

Part 2 — Inversion
  gpio_inverted = True reverses the polarity:
  gpio_value True  + inverted → pin LOW   (pass)
  gpio_value False + inverted → pin HIGH  (pass)

Part 3 — Input mode
  AS7343 GPIO configured as input (gpio_output_mode = False).
  D9 switched to output and driven from the board; AS7343 reads back
  the driven level via gpio_value.

All three parts will FAIL if the feedback wire is not connected.

Expected output (wire connected):
  RESULT: PASS
Expected output (wire absent):
  All "Pin reads" / "AS7343 reads" lines will show wrong state → FAIL
  RESULT: FAIL
"""

# ruff: noqa: E501

import time

import board
import digitalio

from adafruit_as7343 import AS7343

FEEDBACK_PIN = board.D9  # wire this to AS7343 GPIO

print("AS7343 GPIO Test")
print("================")
print(f"Feedback pin: board.D9 connected to AS7343 GPIO")
print()

i2c = board.I2C()

try:
    sensor = AS7343(i2c)
    print("AS7343 initialized OK")
except RuntimeError as e:
    print(f"ERROR: {e}")
    print("RESULT: FAIL")
    raise SystemExit

fb = digitalio.DigitalInOut(FEEDBACK_PIN)

all_passed = True
pass_high = False
pass_low = False
pass_inv_high = False
pass_inv_low = False
pass_in_high = False
pass_in_low = False

# ── Part 1: Output mode ───────────────────────────────────────────────────────

print("Part 1: Output Mode Test")

# Feedback as input with pull-up (provides HIGH when AS7343 open-drain released)
fb.direction = digitalio.Direction.INPUT
fb.pull = digitalio.Pull.UP

sensor.gpio_output_mode = True
sensor.gpio_inverted = False

# HIGH output (open-drain released — pull-up holds pin HIGH)
sensor.gpio_value = True
time.sleep(0.005)
pin_state = fb.value
pass_high = pin_state is True
print(
    f"  gpio_value=True  → D9: {'HIGH' if pin_state else 'LOW'}  {'PASS' if pass_high else 'FAIL'}"
)
if not pass_high:
    all_passed = False

# LOW output (open-drain active — pulls pin LOW)
sensor.gpio_value = False
time.sleep(0.005)
pin_state = fb.value
pass_low = pin_state is False
print(
    f"  gpio_value=False → D9: {'HIGH' if pin_state else 'LOW'}  {'PASS' if pass_low else 'FAIL'}"
)
if not pass_low:
    all_passed = False

print()

# ── Part 2: Inversion ─────────────────────────────────────────────────────────

print("Part 2: Inversion Test")

sensor.gpio_inverted = True

# Inverted + value True → should drive LOW
sensor.gpio_value = True
time.sleep(0.005)
pin_state = fb.value
pass_inv_high = pin_state is False  # inverted: value=True → LOW
print(
    f"  Inverted + gpio_value=True  → D9: {'HIGH' if pin_state else 'LOW'}  {'PASS' if pass_inv_high else 'FAIL'}"
)
if not pass_inv_high:
    all_passed = False

# Inverted + value False → should release (HIGH via pull-up)
sensor.gpio_value = False
time.sleep(0.005)
pin_state = fb.value
pass_inv_low = pin_state is True  # inverted: value=False → HIGH
print(
    f"  Inverted + gpio_value=False → D9: {'HIGH' if pin_state else 'LOW'}  {'PASS' if pass_inv_low else 'FAIL'}"
)
if not pass_inv_low:
    all_passed = False

sensor.gpio_inverted = False  # restore for Part 3

print()

# ── Part 3: Input mode ────────────────────────────────────────────────────────

print("Part 3: Input Mode Test")

sensor.gpio_output_mode = False  # AS7343 GPIO now an input
time.sleep(0.005)

# Drive D9 as output from the board
fb.pull = None
fb.direction = digitalio.Direction.OUTPUT

# Board drives HIGH → AS7343 should read HIGH
fb.value = True
time.sleep(0.005)
read_val = sensor.gpio_value
pass_in_high = read_val is True
print(
    f"  D9 drives HIGH → AS7343 gpio_value: {'HIGH' if read_val else 'LOW'}  {'PASS' if pass_in_high else 'FAIL'}"
)
if not pass_in_high:
    all_passed = False

# Board drives LOW → AS7343 should read LOW
fb.value = False
time.sleep(0.005)
read_val = sensor.gpio_value
pass_in_low = read_val is False
print(
    f"  D9 drives LOW  → AS7343 gpio_value: {'HIGH' if read_val else 'LOW'}  {'PASS' if pass_in_low else 'FAIL'}"
)
if not pass_in_low:
    all_passed = False

# Release D9
fb.direction = digitalio.Direction.INPUT
fb.pull = digitalio.Pull.UP
fb.deinit()

# ── Summary ───────────────────────────────────────────────────────────────────

print()
print("Summary:")
print(f"  Output mode: {'PASS' if pass_high and pass_low         else 'FAIL'}")
print(f"  Inversion:   {'PASS' if pass_inv_high and pass_inv_low else 'FAIL'}")
print(f"  Input mode:  {'PASS' if pass_in_high and pass_in_low   else 'FAIL'}")
print()
print(f"RESULT: {'PASS' if all_passed else 'FAIL'}")

print("~~END~~")
