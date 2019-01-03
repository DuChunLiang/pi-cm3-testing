#!/usr/bin/env python

import sys
import can
import time
import struct
from udstools import IsoTp
from config import Common


# uds交互服务
class UdsServer:
    def __init__(self):
        can.rc['interface'] = 'socketcan'
        can.rc['channel'] = 'can0'
        can_bus = can.interface.Bus()
        id_source = int("0x0CDA%02XF1" % Common.can_addr, 16)
        id_target = int("0x0CDAF1%02X" % Common.can_addr, 16)
        self.tp = IsoTp(can_bus, id_source=id_source, id_target=id_target, extended_id=True)

    @staticmethod
    def str_to_hex(s):
        return ''.join([hex(ord(c)).replace('0x', '') for c in s]).upper()

    def send(self, data):
        # print("send: ", data)
        self.tp.send_pdu(bytearray.fromhex(data))

        res_data = self.tp.get_pdu()
        # print("result: ", binascii.b2a_hex(res_data))
        time.sleep(0.05)
        return res_data


if __name__ == "__main__":
    us = UdsServer()
    get_res = us.send(sys.argv[1])
    mio_val = struct.unpack(">I", get_res[3:7])[0]
    print('---', mio_val)
