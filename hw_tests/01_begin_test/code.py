# SPDX-FileCopyrightText: Copyright (c) 2026 Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Hardware test 01 — AS7343 begin / ID verification

Tests:
- I2C communication with AS7343
- Part ID verification (expect 0x81)
- Aux ID and Revision ID readback

Expected output:
  RESULT: PASS
"""

import board

from adafruit_as7343 import AS7343

print("================================")
print("AS7343 Begin Test")
print("================================")

i2c = board.I2C()

try:
    sensor = AS7343(i2c)
    print("AS7343 initialized OK")
except RuntimeError as e:
    print(f"ERROR: {e}")
    print("RESULT: FAIL")
    raise SystemExit

# Read chip information registers
part_id = sensor.part_id
aux_id = sensor.aux_id
rev_id = sensor.revision_id

print(f"Part ID:     0x{part_id:02X}")
print(f"Aux ID:      0x{aux_id:02X}")
print(f"Revision ID: 0x{rev_id:02X}")
print("--------------------------------")

if part_id == 0x81:
    print("Part ID verified: PASS")
    print("RESULT: PASS")
else:
    print(f"Part ID mismatch! Expected 0x81, got 0x{part_id:02X}")
    print("RESULT: FAIL")

print("~~END~~")
