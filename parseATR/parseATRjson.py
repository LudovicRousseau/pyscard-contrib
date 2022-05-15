#! /usr/bin/env python3
"""
    parseATRjson: convert an ATR in a (JSON) human readable format
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

from parseATR import parseATR, simplifyDescription
import json
import pprint

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        ATR = " ".join(sys.argv[1:])
    else:
        # ATR = "3B A7 00 40 18 80 65 A2 08 01 01 52"
        ATR = "3F FF 95 00 FF 91 81 71 A0 47 00 44 4E 41 53 50 30 31 31 20 52 65 76 42 30 36 4E"
    atr = parseATR(ATR)
    # print "ATR:", ATR

    print("ATR:", ATR)

    print("\nPython pretty print dump")
    pp = pp = pprint.PrettyPrinter(indent=2, compact=True)
    pp.pprint(atr)

    print("\nJSON dump")
    print(json.dumps(atr, indent=2, sort_keys=True))
 
    print("\nSimplified description")
    atr2 = simplifyDescription(atr)
    pp.pprint(atr2)

    print("\nJSON dump")
    print(json.dumps(atr2, indent=2, sort_keys=True))
