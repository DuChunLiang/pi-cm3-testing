#!/usr/bin/env python

import sys
import can
import time
import struct
from udstools import IsoTp
from config import Common


# uds交互服务
class UdsServer:
    def __init__(self, can_bus=None):
        id_source = int("0x0CDA%02XF1" % Common.can_addr, 16)
        id_target = int("0x0CDAF1%02X" % Common.can_addr, 16)
        # print("id_source:", hex(id_source), "id_target:", hex(id_target), "can_addr:", Common.can_addr)
        self.tp = IsoTp(can_bus, id_source=id_source, id_target=id_target, extended_id=True)

    @staticmethod
    def str_to_hex(s):
        return ''.join([hex(ord(c)).replace('0x', '') for c in s]).upper()

    def send(self, data):
        # print("uds_send: ", data)
        self.tp.send_pdu(bytearray.fromhex(data))

        res_data = self.tp.get_pdu()
        # print("uds_result: ", res_data)
        time.sleep(0.5)
        return res_data

    def close(self):
        self.tp.close()


# if __name__ == "__main__":
#     Common.can_addr = int(sys.argv[1])
#     us = UdsServer()
#     get_res = us.send(sys.argv[2])
#     mio_val = struct.unpack(">I", get_res[3:7])[0]
#     print('---', mio_val)
