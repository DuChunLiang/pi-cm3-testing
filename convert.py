#!/usr/bin/python
# -*- coding:utf-8 -*-


class Convert:  # 转换
    def __init__(self):
        self.hexmap = {
            "0000": "0",
            "0001": "1",
            "0010": "2",
            "0011": "3",
            "0100": "4",
            "0101": "5",
            "0110": "6",
            "0111": "7",
            "1000": "8",
            "1001": "9",
            "1010": "A",
            "1011": "B",
            "1100": "C",
            "1101": "D",
            "1110": "E",
            "1111": "F",
        }

    def addone(self, mods):
        assert isinstance(mods, list)
        tmods = mods.copy()
        if tmods:
            if tmods[0] == 0:
                tmods[0] = 1
                return (tmods)
            else:
                return ([0] + self.addone(tmods[1:]))
        return ([])

    def convertToBinary(self, num, site=64):
        assert -2 ** (site - 1) <= num < 2 ** (site - 1), "the %d is not in range [%d,%d)" % (
            num, -2 ** (site - 1), 2 ** (site - 1))
        mod = []
        quotient = abs(num)
        if quotient == 0:
            mod = [0]
        else:
            while quotient:
                mod.append(quotient % 2)
                quotient = quotient // 2
        mod += [0] * (site - len(mod) - 1)
        # if negative
        if num < 0:
            # not
            mod = [0 if i else 1 for i in mod]
            # add 1
            mod = self.addone(mod)
            # add sign
            mod += [1]
        else:
            mod += [0]
        return ("".join([str(i) for i in reversed(mod)]))

    def convertToHex(self, code):
        clen = len(code)
        mod = clen % 4
        if mod != 0:
            if code[0] == 0:
                code = "0" * (4 - mod) + code
            else:
                code = "1" * (4 - mod) + code
        out = []
        for i in range(0, len(code), 4):
            out.append(self.hexmap[code[i:i + 4]])
        hex_str = "".join(out)
        return self.hexstr_to_bytes(hex_str)

    @staticmethod
    def hexstr_to_bytes(hexstr):
        return list(bytearray.fromhex(hexstr))
        # r_l = []
        # for i in range(int(len(hexstr) / 2)):
        #     s = i*2
        #     e = s+2
        #     r = int(hexstr[s:e], 16)
        #     r_l.append(r)
        # return bytes(r_l)

    @staticmethod
    def bytes_to_hexstr(bytes):
        r = ""
        for b in bytes:
            s = "%02X" % b
            r += s
        return r

    @staticmethod
    def dict_to_list(temp_list=None, _dict=None):
        bit_list = []
        if temp_list is not None:
            for v in temp_list:
                bit_list.append(_dict[v])
        return bit_list