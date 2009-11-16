#! /usr/bin/env python
"""
    stress_test.py
    Copyright (C) 2009   Ludovic Rousseau

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

import sys
import string
import parseATR

List = "/usr/local/share/pcsc/smartcard_list.txt"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        List = sys.argv[1]

    for atr in open(List):
        if atr[0] != "3":
            continue
        if "[" in atr:
            continue
        if "." in atr:
            continue
        if "?" in atr:
            continue

        # remove traling newline
        atr = atr.rstrip()
        print "ATR:", atr

        try:
            txt = parseATR.atr_display_txt(parseATR.parseATR(atr))
        except parseATR.ParseAtrException, e:
            print e
        else:
            print txt

        print
