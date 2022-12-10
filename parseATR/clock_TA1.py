#! /usr/bin/env python3
"""
    clock_TA1: compute baud rate from TA1 and clock speed
    Copyright (C) 2022   Ludovic Rousseau

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import pprint
from parseATR import TA1_v

clocks = (3700000, 4800000, 12000000)

all_TA1 = dict()
pp = pprint.PrettyPrinter(indent=4)

for clock in clocks:
    for TA1 in range(0, 256):
        v = TA1_v(TA1)
        if not "RFU" in v:
            (Fi, Di, value, FMax) = v
            if clock < FMax * 1000000:
                all_TA1[(TA1, clock)] = int(clock / value)

# pp.pprint(all_TA1)

all_speeds = dict()
for k, v in all_TA1.items():
    all_speeds[v] = list()

for k, v in all_TA1.items():
    TA1, clock = k
    all_speeds[v].append(("0x%02X" % TA1, clock / 1000000))

pp.pprint(all_speeds)
