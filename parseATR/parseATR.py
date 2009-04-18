#! /usr/bin/env python
"""
    parseATR: convert an ATR in a human readable format
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

import smartcard.util

ATR_PROTOCOL_TYPE_T0 = 0
ATR_MAX_PROTOCOLS = 7
T = -1

def normalize(atr):
    """ transform an ATR in list of integers
    valid input formats are
    "3B A7 00 40 18 80 65 A2 08 01 01 52"
    "3B:A7:00:40:18:80:65:A2:08:01:01:52"
    """
    atr = atr.replace(":", " ")
    atr = atr.split(" ")
    atr = map(lambda x: int(x,16), atr)
    return atr

def int2bin(i, padding = 8):
    """ convert an integer into its binary representation """
    b = ""
    while i > 0:
        b = str(i % 2) + b
        i >>= 1
    b = "0" * (padding-len(b)) +b
    return b

def parseATR(atr_txt):
    atr_txt = normalize(atr_txt)
    atr = {}
    # store TS and T0
    atr["TS"] = atr_txt[0]
    atr["T0"] = TDi = atr_txt[1]
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
    atr["hb"] = atr_txt[pointer+1:]

    # Store TCK
    if (atr.has_key("TCK")):
        atr["TCK"] = atr_txt[pointer]

    return atr

def TA1(v):
    Fi = (372, 372, 558, 744, 1116, 1488, 1860, "RFU", "RFU", 512, 768, 1024, 1536, 2048, "RFU", "RFU")
    Di = ("RFU", 1, 2, 4, 8, 16, 32, "RFU", 12, 20, "RFU", "RFU", "RFU", "RFU", "RFU", "RFU")
    F = v >> 4
    D = v & 0xF
    value = Fi[F]/Di[D]
    return "Fi=%s, Di=%s, %g cycles/ETU (%d bits/s at 3.57 MHz)" % (Fi[F], Di[D], value, 3571200/value)

def TA2(v):
    F = v >> 4
    D = v & 0xF
    text = "Protocol to be used in spec mode: T=%s" % (D),
    if (F & 0x8):
        text = text + " - Unable to change",
    else:
        text = text + " - Capable to change",

    if (F & 0x1):
        text = text + " - implicity defined"
    else:
        text = text + " - defined by interface bytes"

    return text

def TA3(v):
    return TAn(3, v)

def TA4(v):
    return TAn(4, v)
    
def TAn(i, v):
    XI = ("not supported", "state L", "state H", "no preference")
    if (T == 1):
        text = "IFSC: %s" % v
    else:
        F = v >> 6
        D = v % 64
        Class = "(3G) "

        if (D & 0x1):
            Class += "A 5V "
        if (D & 0x2):
            Class += "B 3V "
        if (D & 0x4):
            Class += "C 1.8V "
        if (D & 0x8):
            Class += "D RFU "
        if (D & 0x10):
            Class += "E RFU"

        text = "Clock stop: %s - Class accepted by the card: %s" % (XI[F],Class)
    return text

def TB1(v):
    I = v >> 5
    PI = v & 0x1F
    if (PI == 0):
        text = "VPP is not electrically connected"
    else:
        text = "Programming Param P: %d Volts, I: %d milliamperes" % (PI, I)
    return text

def TB2(v):
    text = "Programming param PI2 (PI1 should be ignored): %d" % v,
    if ((v>49) or (v<251)):
        text += " (dV)"
    else:
        text += " is RFU"
    return text

def TB3(v):
    return TBn(3, v)

def TB4(v):
    return TBn(4, v)

def TBn(i, v):
    text = ""
    if (T == 1):
        BWI = v >> 4
        CWI = v % 16
        
        text = "Block Waiting Integer: %d - Character Waiting Integer: %d" % (BWI, CWI)
    return text

def TC1(v):
    text = "Extra guard time:", v,
    if (v == 255):
        text += "(special value)"
    return text

def TC2(v):
    return "Work waiting time: 960 x %d x (Fi/F)" % v

def TC3(v):
    return TCn(3, v)

def TC4(v):
    return TCn(4, v)

def TCn(i, v):
    text = ""
    if (T == 1):
        text = "Error detection code: ",
        if (v == 1):
            text += "CRC";
        else:
            if (v == 0):
                text += "LRC"
            else:
                text += "RFU"
    return text

def TD1(v):
    return TDn(1, v)

def TD2(v):
    return TDn(2, v)

def TD3(v):
    return TDn(3, v)

def TD4(v):
    return TDn(4, v)

def TDn(i, v):
    global T
    Y = v >> 4
    T = v & 0xF
    text = "Y(i+1) = b%s, Protocol T=%d" % (int2bin(Y,4), T)
    return text

def compact_tlv(historical_bytes):
    text = ""
    tlv = historical_bytes.pop(0)

    # return if we have NO historical bytes
    if tlv == None:
        return text

    tag = tlv / 16
    len = tlv % 16
    
    if tag == 1:
        text += " (country code, ISO 3166-1)"
        text += "      Country code: " + smartcard.util.toHexString(historical_bytes[:len], smartcard.util.HEX)

    elif tag == 2:
        text += " (issuer identification number, ISO 7812-1)";
        text += "      Issuer identification number: "  + smartcard.util.toHexString(historical_bytes[:len], smartcard.util.HEX)

    elif tag == 3:
        text += " (card service data byte)"
        cs = historical_bytes.pop(0)
        if cs == None:
            text += "      Error in the ATR: expecting 1 byte and got 0"
        else:
            text += "      Card service data byte: %d" % cs
            text += cs(cs)
            
    elif tag == 4:
        text += " (initial access data)"
        text += "      Initial access data: " + smartcard.util.toHexString(historical_bytes[:len], smartcard.util.HEX)
        
    elif tag == 5:
        text += " (card issuer's data)"
        text += "      Card issuer data: " + smartcard.util.toHexString(historical_bytes[:len], smartcard.util.HEX)

    elif tag == 6:
        text += " (pre-issuing data)"
        text += "      Data: " + smartcard.util.toHexString(historical_bytes[:len], smartcard.util.HEX)

    elif tag == 7:
        text += " (card capabilities)"
        if len == 1:
            sm = historical_bytes.pop(0)
            text += "      Selection methods: %d" % sm
            text += sm(sm)
        elif len == 2:
            sm = historical_bytes.pop(0)
            dc = historical_bytes.pop(0)
            text += "      Selection methods: %d" % sm
            text += sm(sm)
            text += "      Data coding byte: %d" % dc
            text += dc(dc)
        elif len == 3:
            sm = historical_bytes.pop(0)
            dc = historical_bytes.pop(0)
            cc = historical_bytes.pop(0)
            text += "      Selection methods: %d" % sm
            text += sm(sm)
            text += "      Data coding byte: %d" % dc
            text += dc(dc)
            text += "      Command chaining, length fields and logical channels: %d" % cc
            text += cc(cc)
        else:
            text += "      wrong ATR"

    elif tag == 8:
        text += " (status indicator)"
        if len == 1:
            lcs = historical_bytes.pop(0)
            text += "      LCS (life card cycle): %d" % lcs
        elif len == 2:
            sw1 = historical_bytes.pop(0)
            sw2 = historical_bytes.pop(0)
            text += "      SW: %02X %02X" % (sw1, sw2)
        elif len == 3:
            lcs = historical_bytes.pop(0)
            sw1 = historical_bytes.pop(0)
            sw2 = historical_bytes.pop(0)
            text += "      LCS (life card cycle): %d" % lcs
            text += "      SW: %02X %02X" % (sw1, sw2)
    
    elif tag == 15:
        text += " (application identifier)"
        text += "      Application identifier: " + smartcard.util.toHexString(historical_bytes[:len], smartcard.util.HEX)

    else:
        text += " (unknown)"
        text += "      Value: " + smartcard.util.toHexString(historical_bytes[:len], smartcard.util.HEX)

    return text

def analyse_histrorical_bytes(historical_bytes):
    text = ""
    hb_category = historical_bytes.pop(0)

    # return if we have NO historical bytes
    if hb_category == None:
        return text
    
    if hb_category == 0x00:
        text += " (compact TLV data object)\n";

        if historical_bytes.length() < 3:
            text += "    Error in the ATR: expecting 3 bytes and got %d" % historical_bytes.length()
            return text

        # get the 3 last bytes
        status = historical_bytes[-3:]
        del historical_bytes[-3:]

        while len(historical_bytes) > 0:
            text += compact_tlv(historical_bytes)

        (lcs, sw1, sw2) = status[:3]
        text += "    Mandatory status indicator (3 last bytes)\n";
        text += "      LCS (life card cycle): %d (%s)" % (lcs, lcs(lcs))
        text +=  "      SW: %02X%02X (%s)" % (sw1, sw1, "") #Chipcard::PCSC::Card::ISO7816Error("$sw1 $sw2"))

    elif hb_category == 0x80:
        text += " (compact TLV data object)"
        while len(historical_bytes) > 0:
            text += compact_tlv(historical_bytes)

    elif hb_category == 0x10:
        text += " (next byte is the DIR data reference)"
        data_ref = historical_bytes.pop(0)
        text += "   DIR data reference: %d", data_ref

    elif hb_category in (0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x8B, 0x8C, 0x8D, 0x8E, 0x8F):
        text += " (Reserved for future use)";

    else:
        text += " (proprietary format)";

    return text

def atr_display_txt(atr):
    TS = {0x3B: "Direct Convention", 0x3F: "Inverse Convention"}
    print "TS = 0x%02X --> %s" % (atr["TS"], TS[atr["TS"]])

    Y1 = atr["T0"] >> 4
    K = atr["T0"] & 0xF
    print "T0 = 0x%02X, Y(1): b%s, K: %d (historical bytes)" % (atr["T0"], int2bin(Y1, padding = 4), K)

    for i in (1, 2, 3, 4):
        separator = False
        for p in ("A", "B", "C", "D"):
            key = "T%s%d" % (p, i)
            if (atr.has_key(key)):
                v = atr[key]
                print " T%s(%d) = 0x%02X -->" % (p, i, v),
                print eval("%s(%d)" % (key, v))
                separator = True
        if separator:
            print "----"

    if (atr.has_key("hb")):
        print "Historical bytes: ",
        for b in atr["hb"]:
            print "0x%02X" % b,
        print analyse_histrorical_bytes(atr["hb"])
            
if __name__ == "__main__":
    atr = parseATR("3B A7 00 40 18 80 65 A2 08 01 01 52")
    #atr = parseATR("3F FF 95 00 FF 91 81 71 A0 47 00 44 4E 41 53 50 30 31 31 20 52 65 76 42")
    atr_display_txt(atr)
