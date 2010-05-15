#! /usr/bin/env python
"""
    stress_test.py
    Copyright (C) 2009-2010   Ludovic Rousseau

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


def stress(atr_list):
    for atr in open(atr_list):
        if not atr.startswith("3"):
            continue
        if "[" in atr:
            continue

        atr = atr.replace('.', '0')

        # remove traling newline
        atr = atr.rstrip()
        print "ATR:", atr

        try:
            txt = parseATR.atr_display_txt(parseATR.parseATR(atr))
        except parseATR.ParseAtrException, e:
            print e
        else:
            print txt
            card = parseATR.match_atr(atr)
            if card:
                print "Possibly identified card:", "\n\t".join(card)
            else:
                print "Unknown card"

        print

if __name__ == "__main__":
    if len(sys.argv) > 1:
        List = sys.argv[1]

    stress(List)
