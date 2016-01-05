#! /usr/bin/env python
"""
    parseATRhtml: convert an ATR in a (HTML) human readable format
    Copyright (C) 2009-2012   Ludovic Rousseau

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

from parseATR import parseATR, atr_display_html

header = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN"
 "http://www.w3.org/TR/1998/REC-html40-19980424/strict.dtd">

<html>
<head>
<title>ATR Parsing</title>
<style type="text/css">
span.data{color: Dodgerblue;}
span.format{color: Darkmagenta;}
</style>
</head>
<body>
<table border="1">"""

footer = """</table>
</body>
</html>"""


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        ATR = " ".join(sys.argv[1:])
    else:
        # ATR = "3B A7 00 40 18 80 65 A2 08 01 01 52"
        ATR = "3F FF 95 00 FF 91 81 71 A0 47 00 44 4E 41 53 50 30 31 31 20 52 65 76 42 30 36 4E"
    atr = parseATR(ATR)
    # print "ATR:", ATR
    html = atr_display_html(atr)

    print header
    print "<p>ATR: " + ATR + "<p>"
    print html
    print footer
