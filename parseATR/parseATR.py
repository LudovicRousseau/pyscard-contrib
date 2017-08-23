#! /usr/bin/env python
"""
    parseATR: convert an ATR in a human readable format
    Copyright (C) 2009-2016   Ludovic Rousseau

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

from __future__ import print_function
import re

ATR_PROTOCOL_TYPE_T0 = 0
ATR_MAX_PROTOCOLS = 7
T = -1


class ParseAtrException(Exception):
    """ Base class for exceptions in this module """

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


def toHexString(bytes):
    """Returns a hex list

    Args:
        bytes: list of bytes (integers)
    Returns:
        string representing the bytes in hexadecimal

    >>> toHexString([1,2,3, 10, 255])
    '01 02 03 0A FF'
    """
    return " ".join(["%02X" % b for b in bytes])


def toASCIIString(bytes):
    """Returns a string.

    Args:
        bytes: list of bytes (integers)
    Returns:
        string representing the list of bytes in ASCII. Non ASCII
        characters are replaced with .

    >>> toASCIIString([72, 101, 108, 108, 111, 32, 119, 111, 114, 108, 100, 33])
    'Hello world!'
    """
    ascii = ""
    for b in bytes:
        if b > 31 and b < 127:
            ascii += chr(b)
        else:
            ascii += '.'
    return ascii


def normalize(atr):
    """Transform an ATR in list of integers.
    valid input formats are
    "3B A7 00 40 18 80 65 A2 08 01 01 52"
    "3B:A7:00:40:18:80:65:A2:08:01:01:52"

    Args:
        atr: string
    Returns:
        list of bytes

    >>> normalize("3B:A7:00:40:18:80:65:A2:08:01:01:52")
    [59, 167, 0, 64, 24, 128, 101, 162, 8, 1, 1, 82]
    """
    atr = atr.replace(":", "")
    atr = atr.replace(" ", "")

    res = list()
    while len(atr) >= 2:
        byte, atr = atr[:2], atr[2:]
        res.append(byte)
    if len(atr) > 0:
        raise ParseAtrException('warning: odd string, remainder: %r' % atr)

    atr = [int(x, 16) for x in res]
    return atr


def int2bin(i, padding=8):
    """Converts an integer into its binary representation

    Args:
        i: integer value
        padding: minimum number of digits (default value 8)
    Returns:
        string representation of i in binary

    >>> int2bin(2015)
    '11111011111'
    >>> int2bin(42)
    '00101010'
    """
    b = ""
    while i > 0:
        b = str(i % 2) + b
        i >>= 1
    b = "0" * (padding - len(b)) + b
    return b


def parseATR(atr_txt):
    """Parses an ATR

    Args:
        atr_txt: ATR as a hex bytes string
    Returns:
        dictionary of field and values

    >>> parseATR("3B A7 00 40 18 80 65 A2 08 01 01 52")
    {'hbn': 7, 'TB1': 0, 'TC2': 24, 'TS': 59, 'T0': 167,
     'atr': [59, 167, 0, 64, 24, 128, 101, 162, 8, 1, 1, 82],
     'hb': [128, 101, 162, 8, 1, 1, 82], 'TD1': 64, 'pn': 2}
    """
    atr_txt = normalize(atr_txt)
    atr = {}

    # the ATR itself as a list of integers
    atr["atr"] = atr_txt

    # store TS and T0
    atr["TS"] = atr_txt[0]
    atr["T0"] = TDi = atr_txt[1]
    hb_length = atr["T0"] & 15
    pointer = 1
    # protocol number
    pn = 1

    # store number of historical bytes
    atr["hbn"] = TDi & 0xF

    while (pointer < len(atr_txt)):
        # Check TAi is present
        if ((TDi | 0xEF) == 0xFF):
            pointer += 1
            atr["TA%d" % pn] = atr_txt[pointer]

        # Check TBi is present
        if ((TDi | 0xDF) == 0xFF):
            pointer += 1
            atr["TB%d" % pn] = atr_txt[pointer]

        # Check TCi is present
        if ((TDi | 0xBF) == 0xFF):
            pointer += 1
            atr["TC%d" % pn] = atr_txt[pointer]

        # Check TDi is present
        if ((TDi | 0x7F) == 0xFF):
            pointer += 1
            atr["TD%d" % pn] = TDi = atr_txt[pointer]
            if ((TDi & 0x0F) != ATR_PROTOCOL_TYPE_T0):
                atr["TCK"] = True
            pn += 1
        else:
            break

    # Store number of protocols
    atr["pn"] = pn

    # Store historical bytes
    atr["hb"] = atr_txt[pointer + 1: pointer + 1 + hb_length]

    # Store TCK
    last = pointer + 1 + hb_length
    if "TCK" in atr:
        try:
            atr["TCK"] = atr_txt[last]
        except IndexError:
            atr["TCK"] = -1
        last += 1

    if len(atr_txt) > last:
        atr["extra"] = atr_txt[last:]

    if len(atr["hb"]) < hb_length:
        missing = hb_length - len(atr["hb"])
        if missing > 1:
            (t1, t2) = ("s", "are")
        else:
            (t1, t2) = ("", "is")
        atr["warning"] = "ATR is truncated: %d byte%s %s missing" % (missing, t1, t2)

    return atr


def TA1(v):
    """Parse TA1 value

    Args:
        v: TA1
    Returns:
        value according to ISO 7816-3

    >>> TA1(0x11)
    ['Fi=%s, Di=%s, %g cycles/ETU (%d bits/s at 4.00 MHz, %d bits/s for fMax=%d MHz)', (372, 1, 372, 10752, 13440, 5)]
    """
    Fi = (372, 372, 558, 744, 1116, 1488, 1860, "RFU", "RFU", 512, 768, 1024,
          1536, 2048, "RFU", "RFU")
    Di = ("RFU", 1, 2, 4, 8, 16, 32, 64, 12, 20, "RFU", "RFU", "RFU", "RFU",
          "RFU", "RFU")
    FMax = (4, 5, 6, 8, 12, 16, 20, "RFU", "RFU", 5, 7.5, 10, 15, 20, "RFU",
            "RFU")
    F = v >> 4
    D = v & 0xF

    text = "Fi=%s, Di=%s"
    args = (Fi[F], Di[D])
    if "RFU" in [Fi[F], Di[D]]:
        text += ", INVALID VALUE"
    else:
        value = Fi[F] / Di[D]
        text += ", %g cycles/ETU (%d bits/s at 4.00 MHz, %d bits/s for fMax=%d MHz)"
        args += (value, 4000000 / value, FMax[F] * 1000000 / value, FMax[F])

    return [text, args]


def TA2(v):
    """Parse TA2 value

    Args:
        v: TA2
    Returns:
        value according to ISO 7816-3

    >>> TA2(1)
    'Protocol to be used in spec mode: T=1 - Capable to change - defined by interface bytes'
    """
    F = v >> 4
    D = v & 0xF
    text = ["Protocol to be used in spec mode: T=%s" % (D)]
    if (F & 0x8):
        text.append(" - Unable to change")
    else:
        text.append(" - Capable to change")

    if (F & 0x1):
        text.append(" - implicity defined")
    else:
        text.append(" - defined by interface bytes")

    return ''.join(text)


def TA3(v):
    """Parse TA3 value

    Args:
        v: TA3
    Returns:
        value according to ISO 7816-3
    """
    return TAn(3, v)


def TA4(v):
    """Parse TA4 value

    Args:
        v: TA4
    Returns:
        value according to ISO 7816-3
    """
    return TAn(4, v)


def TA5(v):
    """Parse TA5 value

    Args:
        v: TA5
    Returns:
        value according to ISO 7816-3
    """
    return TAn(5, v)


def TAn(i, v):
    """Parse TAi (3 <= i <= 5)

    Args:
        i: i
        v: value of TAi
    Returns:
        value according to ISO 7816-3
    """
    XI = ("not supported", "state L", "state H", "no preference")
    if (T == 1):
        text = "IFSC: %s"
        args = (v)
    else:
        F = v >> 6
        D = v % 64
        Class = ["(3G) "]

        if (D & 0x1):
            Class.append("A 5V ")
        if (D & 0x2):
            Class.append("B 3V ")
        if (D & 0x4):
            Class.append("C 1.8V ")
        if (D & 0x8):
            Class.append("D RFU ")
        if (D & 0x10):
            Class.append("E RFU")

        text = "Clock stop: %s - Class accepted by the card: %s"
        args = (XI[F], ''.join(Class))
    return [text, args]


def TB1(v):
    """Parse TB1 value

    Args:
        v: TB1
    Returns:
        value according to ISO 7816-3
    """
    I_tab = { 0: "25 milliAmperes",
             1: "50 milliAmperes",
             2: "100 milliAmperes",
             3: "RFU"
            }
    I = (v >> 5) & 3
    PI = v & 0x1F
    if (PI == 0):
        text = "VPP is not electrically connected"
    else:
        text = "Programming Param P: %d Volts, I: %s" % (PI, I_tab[I])
    return text


def TB2(v):
    """Parse TB2 value

    Args:
        v: TB2
    Returns:
        value according to ISO 7816-3
    """
    text = ["Programming param PI2 (PI1 should be ignored): %d" % v, ]
    if ((v > 49) or (v < 251)):
        text.append(" (dV)")
    else:
        text.append(" is RFU")
    return ''.join(text)


def TB3(v):
    """Parse TB3 value

    Args:
        v: TB3
    Returns:
        value according to ISO 7816-3
    """
    return TBn(3, v)


def TB4(v):
    """Parse TB4 value

    Args:
        v: TB4
    Returns:
        value according to ISO 7816-3
    """
    return TBn(4, v)


def TB5(v):
    """Parse TB5 value

    Args:
        v: TB5
    Returns:
        value according to ISO 7816-3
    """
    return TBn(5, v)


def TBn(i, v):
    """Parse TBi (3 <= i <= 5)

    Args:
        i: i
        v: value of TBi
    Returns:
        value according to ISO 7816-3
    """
    text = "Undocumented"
    args = list()
    if (T == 1):
        BWI = v >> 4
        CWI = v % 16

        text = "Block Waiting Integer: %d - Character Waiting Integer: %d"
        args = (BWI, CWI)
    else:
        if (i > 2 and T == 15):
            # see ETSI TS 102 221 V8.3.0 (2009-08)
            # Smart Cards; UICC-Terminal interface;
            # Physical and logical characteristics (Release 8)
            texts = {0x00: "No additional global interface parameters supported",
                     0x88: "Secure Channel supported as defined in TS 102 484",
                     0x8C: "Secured APDU - Platform to Platform required as defined in TS 102 484",
                     0x82: "eUICC-related functions supported",
                     0x90: "Low Impedance drivers and protocol available on the I/O line available (see clause 7.2.1)",
                     0xA0: "UICC-CLF interface supported as defined in TS 102 613",
                     0xC0: "Inter-Chip USB UICC-Terminal interface supported as defined in TS 102 600"}
            text = texts.get(v, "RFU")
    return [text, args]


def TC1(v):
    """Parse TC1 value

    Args:
        v: TC1
    Returns:
        value according to ISO 7816-3
    """
    text = "Extra guard time: %d"
    args = v
    if (v == 255):
        text += " (special value)"
    return [text, args]


def TC2(v):
    """Parse TC2 value

    Args:
        v: TC2
    Returns:
        value according to ISO 7816-3
    """
    return "Work waiting time: 960 x %d x (Fi/F)" % v


def TC3(v):
    """Parse TC3 value

    Args:
        v: TC3
    Returns:
        value according to ISO 7816-3
    """
    return TCn(3, v)


def TC4(v):
    """Parse TC4 value

    Args:
        v: TC4
    Returns:
        value according to ISO 7816-3
    """
    return TCn(4, v)


def TC5(v):
    """Parse TC5 value

    Args:
        v: TC5
    Returns:
        value according to ISO 7816-3
    """
    return TCn(5, v)


def TCn(i, v):
    """Parse TCi (3 <= i <= 5)

    Args:
        i: i
        v: value of TCi
    Returns:
        value according to ISO 7816-3
    """
    text = list()
    args = list()
    if (T == 1):
        text.append("Error detection code: %s")
        if (v == 1):
            args = "CRC"
        else:
            if (v == 0):
                args = "LRC"
            else:
                args = "RFU"
    return [''.join(text), args]


def TD1(v):
    """Parse TD1 value

    Args:
        v: TD1
    Returns:
        value according to ISO 7816-3
    """
    return TDn(1, v)


def TD2(v):
    """Parse TD2 value

    Args:
        v: TD2
    Returns:
        value according to ISO 7816-3
    """
    return TDn(2, v)


def TD3(v):
    """Parse TD3 value

    Args:
        v: TD3
    Returns:
        value according to ISO 7816-3
    """
    return TDn(3, v)


def TD4(v):
    """Parse TD4 value

    Args:
        v: TD4
    Returns:
        value according to ISO 7816-3
    """
    return TDn(4, v)


def TD5(v):
    """Parse TD5 value

    Args:
        v: TD5
    Returns:
        value according to ISO 7816-3
    """
    return TDn(5, v)


def TDn(i, v):
    """Parse TDi (1 <= i <= 5)

    Args:
        i: i
        v: value of TDi
    Returns:
        value according to ISO 7816-3
    """
    global T
    Y = v >> 4
    T = v & 0xF
    text = "Y(i+1) = b%s, Protocol T=%d"
    args = (int2bin(Y, 4), T)

    return [text, args]


def life_cycle_status(lcs):
    """Life Cycle Status
    # Table 13 - Life cycle status byte
    # ISO 7816-4:2004, page 21

    Args:
        lcs: Life Cycle Status

    Returns:
        Text value

    >>> life_cycle_status(5)
    'Operational state (activated)'
    """
    text = "Unknown"

    if lcs > 15:
        text = "Proprietary"

    if lcs == 0:
        text = "No information given"
    if lcs == 1:
        text = "Creation state"
    if lcs == 3:
        text = "Initialisation state"
    if lcs in [4, 6]:
        text = "Operational state (deactivated)"
    if lcs in [5, 7]:
        text = "Operational state (activated)"
    if lcs in [12, 13, 14, 15]:
        text = "Termination state"

    return text


def data_coding(dc):
    """Data Coding

    # Table 87 - Second software function table (data coding byte)
    # ISO 7816-4:2004, page 60

    Args:
        dc: data coding

    Returns:
        Text value

    """
    text = list()

    if dc & 128:
        text.append("        - EF of TLV structure supported\n")

    # get bits 6 and 7
    text.append("        - Behaviour of write functions: ")
    v = (dc & (64 + 32)) >> 5
    t = ["one-time write\n", "proprietary\n", "write OR\n", "write AND\n"]
    text.append(t[v])

    text.append("        - Value 'FF' for the first byte of BER-TLV tag fields: ")
    if dc & 16:
        text.append("in")
    text.append("valid\n")

    text.append("        - Data unit in quartets: %d\n" % (dc & 15))

    return ''.join(text)


def selection_methods(sm):
    """Selection Methods

    # Table 86 - First software function table (selection methods)
    # ISO 7816-4:2004, page 60

    Args:
        sm: Selection Methods

    Returns:
        Text value
    """
    text = list()

    if sm & 1:
        text.append("        - Record identifier supported\n")

    if sm & 2:
        text.append("        - Record number supported\n")

    if sm & 4:
        text.append("        - Short EF identifier supported\n")

    if sm & 8:
        text.append("        - Implicit DF selection\n")

    if sm & 16:
        text.append("        - DF selection by file identifier\n")

    if sm & 32:
        text.append("        - DF selection by path\n")

    if sm & 64:
        text.append("        - DF selection by partial DF name\n")

    if sm & 128:
        text.append("        - DF selection by full DF name\n")

    return ''.join(text)


def selection_mode(sm):
    """Selection Mode

    # Table 87 - Second software function table (data coding byte)
    # ISO 7816-4:2004, page 60

    Args:
        sm: Selection Mode

    Returns:
        Text value
    """
    text = list()

    if sm & 1:
        text.append("        - Record identifier supported\n")

    if sm & 2:
        text.append("        - Record number supported\n")

    if sm & 4:
        text.append("        - Short EF identifier supported\n")

    if sm & 8:
        text.append("        - Implicit DF selection\n")

    if sm & 16:
        text.append("        - DF selection by file identifier\n")

    if sm & 32:
        text.append("        - DF selection by path\n")

    if sm & 64:
        text.append("        - DF selection by partial DF name\n")

    if sm & 128:
        text.append("        - DF selection by full DF name\n")

    return ''.join(text)


def command_chaining(cc):
    """Command Chaining

    # Table 88 - Third software function table (command chaining,
    # length fields and logical channels)
    # ISO 7816-4:2004, page 61

    Args:
        cc: Command Chaining

    Returns:
        Text value
    """
    text = list()

    if cc & 128:
        text.append("        - Command chaining\n")

    if cc & 64:
        text.append("        - Extended Lc and Le fields\n")

    if cc & 32:
        text.append("        - RFU (should not happen)\n")

    v = (cc >> 3) & 3
    t = ["No logical channel\n", "by the interface device\n", "by the card\n",
         "by the interface device and card\n"]
    text.append("        - Logical channel number assignment: " + t[v])

    text.append("        - Maximum number of logical channels: %d\n" % (1 + cc & 7))

    return ''.join(text)


def card_service(cs):
    """Card Service

    # Table 85 - Card service data byte
    # ISO 7816-4:2004, page 59

    Args:
        ccs Card Service

    Returns:
        Text value
    """
    text = list()

    if cs & 128:
        text.append("        - Application selection: by full DF name\n")

    if cs & 64:
        text.append("        - Application selection: by partial DF name\n")

    if cs & 32:
        text.append("        - BER-TLV data objects available in EF.DIR\n")

    if cs & 16:
        text.append("        - BER-TLV data objects available in EF.ATR\n")

    text.append("        - EF.DIR and EF.ATR access services: ")
    v = (cs >> 1) & 7
    if v == 4:
        text.append("by READ BINARY command\n")
    elif v == 2:
        text.append("by GET DATA command\n")
    elif v == 0:
        text.append("by GET RECORD(s) command\n")
    else:
        text.append("reverved for future use\n")

    if cs & 1:
        text.append("        - Card without MF\n")
    else:
        text.append("        - Card with MF\n")

    return ''.join(text)


def safe_get(historical_bytes, number):
    """Get bytes from historical bytes without crashing if not enough
    bytes are provided

    Args:
        historical_bytes
        number

    Returns:
        list of values

    >>> safe_get([1,2,3], 2)
    [1, 2]

    >>> safe_get([1,2,3], 4)
    [1, 2, 3, 0]
    """
    result = list()
    for i in range(number):
        try:
            v = historical_bytes[i]
        except IndexError:
            v = 0
        result.append(v)
    return result


def compact_tlv(atr, historical_bytes):
    """Compact TLV

    Args:
        historical_bytes

    Returns:
        list of text values

    >>> compact_tlv({}, [101, 162, 8, 1, 1, 82])
    ['    Tag: 6, Len: 5 (%s)\\n      Data: %s "%s"\\n', ('pre-issuing data', 'A2 08 01 01 52', '....R')]
    """
    text = ""
    tlv = historical_bytes.pop(0)

    # return if we have NO historical bytes
    if tlv is None:
        return text

    tag = int(tlv / 16)
    len = tlv % 16

    text = list()
    args = list()

    text.append("    Tag: %d, Len: %d (%%s)\n" % (tag, len))

    if tag == 1:
        args.append("country code, ISO 3166-1")
        text.append("      Country code: %s\n")
        args.append(toHexString(historical_bytes[:len]))

    elif tag == 2:
        args.append("issuer identification number, ISO 7812-1")
        text.append("      Issuer identification number: %s\n")
        args.append(toHexString(historical_bytes[:len]))

    elif tag == 3:
        args.append("card service data byte")
        try:
            cs = historical_bytes[0]
        except IndexError:
            warning = "Error in the ATR: expecting 1 byte and got 0\n"
            text.append(warning)
            atr["warning"] = warning
        else:
            text.append("      Card service data byte: %d\n%s")
            args += (cs, card_service(cs))

    elif tag == 4:
        args.append("initial access data")
        text.append("      Initial access data: %s \"%s\"\n")
        args.append(toHexString(historical_bytes[:len]))
        args.append(toASCIIString(historical_bytes[:len]))

    elif tag == 5:
        args.append("card issuer's data")
        text.append("      Card issuer data: %s \"%s\"\n")
        args.append(toHexString(historical_bytes[:len]))
        args.append(toASCIIString(historical_bytes[:len]))

    elif tag == 6:
        args.append("pre-issuing data")
        text.append("      Data: %s \"%s\"\n")
        args.append(toHexString(historical_bytes[:len]))
        args.append(toASCIIString(historical_bytes[:len]))

    elif tag == 7:
        args.append("card capabilities")
        if len == 1:
            try:
                sm = historical_bytes[0]
            except IndexError:
                warning = "Error in the ATR: expecting 1 byte and got 0\n"
                text.append(warning)
                atr["warning"] = warning
            else:
                text.append("      Selection methods: %d\n%s")
                args.append(sm)
                args.append(selection_mode(sm))
        elif len == 2:
            (sm, dc) = safe_get(historical_bytes, 2)
            text.append("      Selection methods: %d\n%s")
            args.append(sm)
            args.append(selection_methods(sm))
            text.append("      Data coding byte: %d\n%s")
            args.append(dc)
            args.append(data_coding(dc))
        elif len == 3:
            (sm, dc, cc) = safe_get(historical_bytes, 3)
            text.append("      Selection methods: %d\n%s")
            args.append(sm)
            args.append(selection_mode(sm))
            text.append("      Data coding byte: %d\n%s")
            args.append(dc)
            args.append(data_coding(dc))
            text.append("      Command chaining, length fields and logical channels: %d\n%s")
            args.append(cc)
            args.append(command_chaining(cc))
        else:
            text.append("      wrong ATR")

    elif tag == 8:
        args.append("status indicator")
        if len == 1:
            lcs = historical_bytes[0]
            text.append("      LCS (life card cycle): %d\n")
            args.append(lcs)
        elif len == 2:
            (sw1, sw2) = safe_get(historical_bytes, 2)
            text.append("      SW: %s")
            args.append("%02X %02X" % (sw1, sw2))
        elif len == 3:
            (lcs, sw1, sw2) = safe_get(historical_bytes, 3)
            text.append("      LCS (life card cycle): %d\n")
            args.append(lcs)
            text.append("      SW: %s")
            args.append("%02X %02X" % (sw1, sw2))

    elif tag == 15:
        args.append("application identifier")
        text.append("      Application identifier: %s \"%s\"\n")
        args.append(toHexString(historical_bytes[:len]))
        args.append(toASCIIString(historical_bytes[:len]))

    else:
        args.append("unknown")
        text.append("      Value: %s \"%s\"\n")
        args.append(toHexString(historical_bytes[:len]))
        args.append(toASCIIString(historical_bytes[:len]))

    # consume len bytes of historic
    del historical_bytes[0:len]

    return [''.join(text), tuple(args)]


def analyse_histrorical_bytes(atr, historical_bytes):
    """Analyse Historical Bytes

    Args:
        historical_bytes: list of bytes

    Returns:
        list

    >>> analyse_histrorical_bytes({}, [128, 101, 162, 8, 1, 1, 82])
    ['  Category indicator byte: 0x80', [' (compact TLV data object)\\n Tag: 6, Len: 5 (%s)\\n Data: %s "%s"\\n', ('pre-issuing data', 'A2 08 01 01 52', '....R')]]
    """
    text = list()
    args = list()

    # return if we have NO historical bytes
    if len(historical_bytes) == 0:
        return ""

    hb_category = historical_bytes.pop(0)

    left = "  Category indicator byte: 0x%02X" % hb_category

    if hb_category == 0x00:
        text.append(" (compact TLV data object)\n")

        if len(historical_bytes) < 3:
            warning = "Error in the ATR: expecting 3 bytes and got %d" % len(historical_bytes)
            text.append(warning)
            atr["warning"] = warning
            return ''.join(text)

        # get the 3 last bytes
        status = historical_bytes[-3:]
        del historical_bytes[-3:]

        while len(historical_bytes) > 0:
            [t, a] = compact_tlv(atr, historical_bytes)
            text.append(t)
            args += a

        (lcs, sw1, sw2) = status[:3]
        text.append("    Mandatory status indicator (3 last bytes)\n")
        text.append("      LCS (life card cycle): %d (%s)\n")
        args += (lcs, life_cycle_status(lcs))
        text.append("      SW: %s (%s)")
        args.append("%02X %02X" % (sw1, sw2))
        args.append("")  # Chipcard::PCSC::Card::ISO7816Error("$sw1 $sw2"))

    elif hb_category == 0x80:
        text.append(" (compact TLV data object)\n")
        while len(historical_bytes) > 0:
            [t, a] = compact_tlv(atr, historical_bytes)
            text.append(t)
            args += a

    elif hb_category == 0x10:
        text.append(" (next byte is the DIR data reference)\n")
        data_ref = historical_bytes.pop(0)
        text.append("   DIR data reference: %d")
        args.append(data_ref)

    elif hb_category in (0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88,
                         0x89, 0x8A, 0x8B, 0x8C, 0x8D, 0x8E, 0x8F):
        text.append(" (Reserved for future use)")

    else:
        text.append(" (proprietary format) \"%s\"")
        args.append(toASCIIString(historical_bytes))

    return [left, ["".join(text), tuple(args)]]


def compute_tck(atr):
    """Computes TCK (ATR checksum)

    Args:
        atr: list of bytes

    Returns:
        TCK value
    """
    # do not include TS byte
    s = atr["atr"][0]
    for e in atr["atr"]:
        s ^= e
    # remove TCK
    s ^= atr["atr"][-1]
    return s


def colorize_line(line, left, right):
    """Colorize a line

    Args:
        line: a tuple of 2 elements with
         - a line with substitution strings (%s, %d, %g)
         - the values of substitution
        left: string to add before the substitution
        right: string to add after the substitution

    Returns:
        Text

    >>> colorize_line(['foo%sbar', 1], 'a', 'b')
    'fooa1bbar'
    """
    if isinstance(line, str):
        return line

    template = line[0]
    for text in ["%s", "%d", "%g"]:
        template = template.replace(text, left + text + right)
    flattened = template % line[1]
    return flattened


def colorize_txt(l):
    """Colorize a text line using ANSI colors

    args:
        l: line or 2 elements tuple

    Returns:
        colorized line
    """
    magenta = "\033[35m"
    normal = "\033[0m"
    blue = "\033[34m"
    text = l[0]
    if len(l) > 1:
        text += " --> " + magenta
        for line in l[1:]:
            colored_line = colorize_line(line, blue, magenta)
            text += colored_line
        text += normal
    return text


def atr_display_txt(atr):
    """Parse an ATR for a text display

    Args:
        atr: ATR

    Returns:
        Text
    """
    return atr_display(atr, colorize_txt)

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }


def html_escape(text):
    """Produce entities within text.

    Args:
        text: text containing special HTML characters

    Returns:
        same text with HTML character replaced by their HTML equivalent

    >>> html_escape("&")
    '&amp;'
    """
    L = list()
    for c in text:
        L.append(html_escape_table.get(c, c))
    return "".join(L)


def colorize_html(l):
    """Colorize a text line using HTML colors

    args:
        l: line or 2 elements tuple

    Returns:
        colorized line
    """
    left = '<span class="data">'
    right = '</span>'

    text = '<tr><th>' + html_escape(l[0]) + '</th>'
    if len(l) > 1:
        t = ""
        for line in l[1:]:
            colored_line = colorize_line(line, left, right)
            t += colored_line

        if '\n' in t:
            lines = t.split('\n');
            lines_out = []
            for line in lines:
                count = 0
                while True:
                    if line[:2] == '  ':
                        count += 1
                        line = line[2:]
                    else:
                        break
                lines_out.append("<span class=\"marge\"></span>" * count + line)
            t = '<br />'.join(lines_out)
        text += '<th><span class="format">' + t + '</span></th></tr>'
    else:
        text += '<th></th>'
    return text


def atr_display_html(atr):
    """Parse an ATR for a text display

    Args:
        atr: ATR

    Returns:
        Text in HTML format
    """
    return atr_display(atr, colorize_html)


def atr_display(atr, colorize):
    """Parse an ATR for a given output

    Args:
        atr: ATR
        colorize: colorization function

    Returns:
        Text
    """
    text = list()
    TS = {0x3B: "Direct Convention", 0x3F: "Inverse Convention"}
    text.append(["TS = 0x%02X" % atr["TS"], TS.get(atr["TS"], "Invalid")])

    Y1 = atr["T0"] >> 4
    K = atr["T0"] & 0xF
    text.append(["T0 = 0x%02X" % atr["T0"],
                 ["Y(1): b%s, K: %d (historical bytes)",
                  (int2bin(Y1, padding=4), K)]])

    for i in (1, 2, 3, 4, 5):
        separator = False
        for p in ("A", "B", "C", "D"):
            key = "T%s%d" % (p, i)
            if key in atr:
                v = atr[key]
                t = [" T%s(%d) = 0x%02X" % (p, i, v)]
                t.append(eval("%s(%d)" % (key, v)))
                text.append(t)
                separator = True
        if separator:
            text.append(["----"])

    if "hb" in atr:
        t = ["Historical bytes"]
        t.append(toHexString(atr["hb"]))
        text.append(t)

        t = analyse_histrorical_bytes(atr, atr["hb"])
        if t:
            text.append(t)

    if "TCK" in atr:
        t = ["TCK = 0x%02X " % atr["TCK"]]
        tck = compute_tck(atr)
        if tck == atr["TCK"]:
            t.append("correct checksum")
        else:
            t.append("WRONG CHECKSUM, expected 0x%02X" % tck)
        text.append(t)

    if "extra" in atr:
        text.append(["Extra bytes", toHexString(atr["extra"])])

    return "\n".join([colorize(t) for t in text])


def match_atr(atr, atr_file=None):
    """Try to find card description for a given ATR.

    Args:
        atr: ATR
        atr_file: file containing a list of known ATRs

    Returns:
        list of card descriptions

    >>> match_atr('3B A7 00 40 18 80 65 A2 08 01 01 52')
    Using: /Users/rousseau/.cache/smartcard_list.txt
    ['Gemplus GPK8000', 'GemSAFE Smart Card (8K)', '3B A7 00 40 .. 80 65 A2 08 .. .. ..', 'Gemplus GemSAFE Smart Card (8K)']
    """

    cards = match_atr_differentiated(atr, atr_file)

    # return only the card descriptions to be backward compatible
    result = list()
    for key in cards:
        result += cards[key]

    return result


def match_atr_differentiated(atr, atr_file=None):
    """Try to find card description for a given ATR.

    Args:
        atr: ATR
        atr_file: file containing a list of known ATRs

    Returns:
        A dictionnary containing the matching ATR and corresponding card
        descriptions

    >>> match_atr_differentiated('3B A7 00 40 18 80 65 A2 08 01 01 52')
    Using: /Users/rousseau/.cache/smartcard_list.txt
    {'3B A7 00 40 .. 80 65 A2 08 .. .. ..': ['Gemplus GemSAFE Smart Card (8K)'], '3B A7 00 40 18 80 65 A2 08 01 01 52': ['Gemplus GPK8000', 'GemSAFE Smart Card (8K)']}
    """
    cards = dict()
    atr = toHexString(normalize(atr))

    if atr_file is None:
        import os
        db_list = list()

        try:
            cache = os.environ['XDG_CACHE_HOME']
        except KeyError:
            cache = os.environ['HOME'] + "/.cache"
        db_list.append(cache + "/smartcard_list.txt")

        db_list += [os.environ['HOME'] + "/.smartcard_list.txt",
                    "/usr/local/pcsc/smartcard_list.txt",
                    "/usr/share/pcsc/smartcard_list.txt",
                    "/usr/local/share/pcsc/smartcard_list.txt"]
        for atr_file in db_list:
            try:
                file = open(atr_file)
                print("Using:", atr_file)
                break
            except:
                pass
    else:
        file = open(atr_file)

    # find a . * or [ in the ATR to know if we must use a RE or not
    re_match = re.compile("[\\.\\*\\[]")

    for line in file:
        if line.startswith("#") or line.startswith("\t") or line == "\n":
            continue
        line = line.rstrip("\n")

        # does the ATR in the file uses a RE?
        if re_match.search(line):
            # use the RE engine (slow)
            found = re.match(line + "$", atr)
        else:
            # use string compare (fast)
            found = line == atr

        if found:
            # found the ATR
            key = line
            cards[key] = list()
            for desc in file:
                if desc == "\n":
                    break
                # get all the possible card descriptions
                cards[key].append(desc.strip())
    file.close()
    return cards

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        ATR = " ".join(sys.argv[1:])
    else:
        # ATR = "3B A7 00 40 18 80 65 A2 08 01 01 52"
        ATR = "3F FF 95 00 FF 91 81 71 A0 47 00 44 4E 41 53 50 30 31 31 20 52 65 76 42 30 36 4E"
    atr = parseATR(ATR)
    print("ATR:", toHexString(normalize(ATR)))
    text = atr_display_txt(atr)
    print(text)
    if "warning" in atr:
        red = "\033[31m"
        normal = "\033[0m"
        print(red + "Error: " + atr["warning"] + normal)
    print()

    card = match_atr_differentiated(ATR)
    if card:
        # exact match
        if ATR in card:
            print("Exact match:", ATR)
            for d in card[ATR]:
                print("\t", d)

            # remove the entry so it is not displayed as "RE match"
            del card[ATR]

        # RE match
        for atr in card:
            print("Possibly identified card:", atr)
            for d in card[atr]:
                print("\t", d)
    else:
        print("Unknown card")
