# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 17 — AS7343 status register

Tests:
  - sensor.status  — raw STATUS register (0x93) read
  - sensor.clear_status() — write-to-clear all STATUS flags

Bit layout of STATUS:
  bit 0  SINT  — system interrupt
  bit 2  FINT  — FIFO threshold interrupt
  bit 3  AINT  — spectral threshold interrupt
  bit 5  CINT  — calibration interrupt
  bit 7  ASAT  — analogue saturation

To generate a readable AINT flag the test:
  1. Sets very low thresholds (low=10, high=100) so that any real reading
     from bright NeoPixels will exceed the high threshold.
  2. Enables spectral interrupts and takes a measurement.
  3. Reads and decodes STATUS — AINT should be set.
  4. Calls clear_status() and reads STATUS again — flags should be clear.

Expected output:
  RESULT: PASS
"""

import time

import board
import neopixel

from adafruit_as7343 import AS7343, Gain

NEOPIXEL_COUNT = 5


def print_status(status):
    print(f"  Raw:  0x{status:02X}")
    print(
        f"  Bits: SINT={int(bool(status & 0x01))} "
        f"FINT={int(bool(status & 0x04))} "
        f"AINT={int(bool(status & 0x08))} "
        f"CINT={int(bool(status & 0x20))} "
        f"ASAT={int(bool(status & 0x80))}"
    )


print("AS7343 Status Test")
print("==================")
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

test_pass = True

# ── Initial status read ───────────────────────────────────────────────────────

print("Initial status:")
print_status(sensor.status)
print()

# ── Generate activity to set AINT ────────────────────────────────────────────

print("After measurement (high gain + bright NeoPixels, low threshold):")

pixels.fill((255, 255, 255))
pixels.show()
time.sleep(0.05)

sensor.gain = Gain.X2048

# Very low thresholds so any lit reading easily crosses them
sensor.spectral_threshold_low = 10
sensor.spectral_threshold_high = 100
sensor.spectral_interrupt_enabled = True

sensor.spectral_measurement_enabled = True
time.sleep(0.1)

deadline = time.monotonic() + 3.0
while not sensor.data_ready:
    if time.monotonic() > deadline:
        print("  TIMEOUT waiting for data")
        test_pass = False
        break
    time.sleep(0.01)

status = sensor.status  # read BEFORE clear_status()
print_status(status)
print()

# ── Clear status ──────────────────────────────────────────────────────────────

print("After clear_status():")
sensor.spectral_measurement_enabled = False
sensor.clear_status()
status_after = sensor.status
print_status(status_after)
print()

# ── Clean up ──────────────────────────────────────────────────────────────────

pixels.fill((0, 0, 0))
pixels.show()
sensor.spectral_interrupt_enabled = False

# ── Summary ───────────────────────────────────────────────────────────────────

print(f"Status API: {'PASS' if test_pass else 'FAIL'}")
print(f"RESULT: {'PASS' if test_pass else 'FAIL'}")

print("~~END~~")
