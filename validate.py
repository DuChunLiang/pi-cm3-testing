#!/usr/bin/env python
# -*- coding:utf-8 -*-

import cantools
import struct
from convert import Convert
from config import Constant, Common


class Validate:  # 验证
    def __init__(self):
        self.data_dict = {}
        self.error_dict = {}
        self.meter = Constant.check_meter
        self.db = cantools.database.load_file('dbc/IM218.dbc')
        # self.data = b'\x55\x55\x55\x03\x00\x10\x00\x00'

    def analysis(self, sign=""):
        # data = b'\x55\x55\x55\x00\x55\x10\x55\x00'
        # data = b'\xaa\xaa\xaa\x00\xa2\x10\x00\x00'
        # data = b'\x00\x00\x00\x44\x00\x10\x00\x00'
        # data = b'\x00\x00\x00\x88\x00\x10\x00\x00'
        # data = b'\x55\x55\x55\x03\x00\x10\x00\x00'

        self.data_dict = {}
        if self.meter == Constant.IC_216:
            frame_id = 0xFFF0301
            if frame_id in Common.can_recv_dict:
                self.validate_ic216(frame_id=frame_id, data=Common.can_recv_dict[frame_id], sign=sign)
        elif self.meter == Constant.IC_218:
            frame_id = 0xFFF0301
            if frame_id in Common.can_recv_dict:
                self.validate_ic218(frame_id=frame_id, data=Common.can_recv_dict[frame_id], sign=sign)
        elif self.meter == Constant.IM_218:
            self.validate_im218(sign=sign)

    # IM218测试检测
    def validate_im218(self, sign=""):
        group_sign = sign[0:4]
        # print("im218检测")

        # print("can_val_range:", Common.can_val_range)
        # 从can接受的报文中解析数据
        if len(Common.can_recv_dict) > 0:
            al = Common.can_addr
            # AL1和AL2测试
            if group_sign == '0001':
                if sign == "0001_0":
                    if al != 5:
                        self.error_dict["AL"] = "%s[5]" % al

                if sign == "0001_1":
                    if al != 7:
                        self.error_dict["AL"] = "%s[7]" % al

                if sign == "0001_2":
                    if al != 3:
                        self.error_dict["AL"] = "%s[3]" % al

            # AIN1和AIN2测试
            if group_sign == '0003':
                frame_id = 0x100 + al
                if frame_id in Common.can_recv_dict:
                    data = Common.can_recv_dict[frame_id]
                    ain1 = struct.unpack("<H", data[0:2])[0] * 0.05
                    ain2 = struct.unpack("<H", data[2:4])[0] * 0.05

                    print("ain1:", ain1, "ain2:", ain2)

                    ain1_min = Common.can_val_range['ain1'][0]
                    ain1_max = Common.can_val_range['ain1'][1]
                    ain2_min = Common.can_val_range['ain2'][0]
                    ain2_max = Common.can_val_range['ain2'][1]

                    if ain1 < ain1_min or ain1 > ain1_max:
                        self.error_dict["AIN1"] = "%s[%s %s]" % (ain1, ain1_min, ain1_max)

                    if ain1 < ain1_min or ain1 > ain1_max:
                        self.error_dict["AIN2"] = "%s[%s %s]" % (ain2, ain2_min, ain2_max)

            # WK1和WK2测试
            if group_sign == '0004':
                frame_id = 0x80 + al
                if frame_id in Common.can_recv_dict:
                    data = Common.can_recv_dict[frame_id]
                    res = self.db.decode_message(0x80, data)
                    wk1 = int(res['wk1_state'])
                    wk2 = int(res['wk2_state'])
                    print("wk1", wk1, "wk2", wk2)
                    wk1_min = Common.can_val_range['WK1'][0]
                    wk1_max = Common.can_val_range['WK1'][1]
                    wk2_min = Common.can_val_range['WK2'][0]
                    wk2_max = Common.can_val_range['WK2'][1]

                    if wk1 < wk1_min or wk1 > wk1_max:
                        self.error_dict["WK1"] = "%s[%s %s]" % (wk1, wk1_min, wk1_max)

                    if wk2 < wk2_min or wk2 > wk2_max:
                        self.error_dict["wk2"] = "%s[%s %s]" % (wk2, wk2_min, wk2_max)

            # 2路频率测试
            if group_sign == '0007':
                fq1 = 0
                fq2 = 0
                if "FQ1" in Common.im218_fq_dict:
                    fq1 = Common.im218_fq_dict['FQ1']
                if "FQ2" in Common.im218_fq_dict:
                    fq2 = Common.im218_fq_dict['FQ2']

                fq1_range = Common.can_val_range['FQ1']
                fq2_range = Common.can_val_range['FQ2']
                print("fq1", fq1, "fq2", fq2)
                if fq1 < fq1_range[0] or fq1 > fq1_range[1]:
                    self.error_dict["FQ1"] = "%s[%s %s]" % (fq1, fq1_range[0], fq1_range[1])

                if fq2 < fq2_range[0] or fq2 > fq2_range[1]:
                    self.error_dict["FQ1"] = "%s[%s %s]" % (fq2, fq2_range[0], fq2_range[1])

        # 从uds返回的报文中解析数据
        if len(Common.uds_recv_dict) > 0:
            # print("uds_recv_dict", Common.uds_recv_dict)
            for key in sorted(Common.uds_recv_dict):
                mouth = key
                data = Common.uds_recv_dict[key]
                # print("uds_data:", data)
                val = struct.unpack(">I", data[3:7])[0]
                print(mouth, "uds_val:", val)
                # 8路AI测试
                if group_sign == '0002':
                    index = int(mouth[2:])
                    in_odd = Common.can_val_range['IN_ODD']
                    in_even = Common.can_val_range['IN_EVEN']
                    if index % 2 == 0:
                        if val < in_even[0] or val > in_even[1]:
                            self.error_dict[mouth] = "%s[%s %s]" % (val, in_even[0], in_even[1])
                    else:
                        if val < in_odd[0] or val > in_odd[1]:
                            self.error_dict[mouth] = "%s[%s %s]" % (val, in_odd[0], in_odd[1])

                # 4路OUT1-OUT4测试
                if group_sign == '0005':
                    out_ran = Common.can_val_range[mouth]
                    if val < out_ran[0] or val > out_ran[1]:
                        self.error_dict[mouth] = "%s[%s %s]" % (val, out_ran[0], out_ran[1])

                # 16路OUT5-OUT20测试
                if group_sign == '0006':
                    index = int(mouth[3:])
                    out_odd = Common.can_val_range['OUT_ODD']
                    out_even = Common.can_val_range['OUT_EVEN']
                    if index % 2 == 0:
                        if val < out_even[0] or val > out_even[1]:
                            self.error_dict[mouth] = "%s[%s %s]" % (val, out_even[0], out_even[1])
                    else:
                        if val < out_odd[0] or val > out_odd[1]:
                            self.error_dict[mouth] = "%s[%s %s]" % (val, out_odd[0], out_odd[1])

        print("validate:", self.error_dict.__str__(), "\r\n")
        # Common.error_record.update(self.error_dict)

    # IC218测试检测
    def validate_ic216(self, frame_id=None, data="", sign="0004_2"):
        print("ic216检测")
        if frame_id == 0xFFF0301:
            for i in range(len(data)):
                binary = Convert().convertToBinary(num=data[i], site=9)
                self.evaluate(i, binary)

            # 32路开关量检测
            if sign == Constant.test_sign_0001_1 or sign == Constant.test_sign_0001_2:
                for d in self.data_dict.items():
                    key = str(d[0])
                    val = int(d[1])
                    if "IN" in key:
                        index = int(key.split("_")[1])
                        if index < 25 or index > 32:
                            if index % 2 == 0:
                                if sign == Constant.test_sign_0001_1:
                                    if val == 1:
                                        self.error_dict[key] = val
                                else:
                                    if val == 0:
                                        self.error_dict[key] = val
                            else:
                                if sign == Constant.test_sign_0001_1:
                                    if val == 0:
                                        self.error_dict[key] = val
                                else:
                                    if val == 1:
                                        self.error_dict[key] = val
            # 8路开关量检测
            if sign == Constant.test_sign_0002_1 or sign == Constant.test_sign_0002_2:
                for d in self.data_dict.items():
                    key = str(d[0])
                    val = int(d[1])
                    if key in ['IN_27', 'IN_28', 'IN_29', 'IN_30', 'IN_31', 'IN_32']:
                        index = int(key.split("_")[1])
                        if index % 2 == 0:
                            if sign == Constant.test_sign_0002_1:
                                if val == 1:
                                    self.error_dict[key] = val
                            else:
                                if val == 0:
                                    self.error_dict[key] = val
                        else:
                            if sign == Constant.test_sign_0002_1:
                                if val == 0:
                                    self.error_dict[key] = val
                            else:
                                if val == 1:
                                    self.error_dict[key] = val
            # 2路开关量检测
            if sign == Constant.test_sign_0003_1 or sign == Constant.test_sign_0003_2:
                in_25 = int(self.data_dict['IN_25'])
                in_26 = int(self.data_dict['IN_26'])

                if sign == Constant.test_sign_0003_1:
                    if in_25 == 0:
                        self.error_dict['IN_25'] = 0
                    if in_26 == 0:
                        self.error_dict['IN_26'] = 0

                else:
                    if in_25 == 1:
                        self.error_dict['IN_25'] = 1
                    if in_26 == 1:
                        self.error_dict['IN_26'] = 1
            # 8路输出口检测
            if sign == Constant.test_sign_0004_1 or sign == Constant.test_sign_0004_2:
                for d in self.data_dict.items():
                    key = str(d[0])
                    val = int(d[1])
                    if "OUT" in key:
                        index = int(key.split("_")[1])
                        if index % 2 == 0:
                            if sign == Constant.test_sign_0004_2:
                                if val == 1:
                                    self.error_dict[key] = val
                        else:
                            if sign == Constant.test_sign_0004_1:
                                if val == 1:
                                    self.error_dict[key] = val

            Common.error_record.update(self.error_dict)

    # IC218测试检测
    def validate_ic218(self, frame_id=None, data="", sign="0004_2"):
        if frame_id == 0xFFF0301:
            for i in range(len(data)):
                binary = Convert().convertToBinary(num=data[i], site=9)
                self.evaluate(i, binary)
            # 24路开关量检测
            if sign == Constant.test_sign_0001_1 or sign == Constant.test_sign_0001_2:
                for d in self.data_dict.items():
                    key = str(d[0])
                    val = int(d[1])
                    if "IN" in key:
                        index = int(key.split("_")[1])
                        if index < 25:
                            if index % 2 == 0:
                                if sign == Constant.test_sign_0001_1:
                                    if val == 1:
                                        self.error_dict[key] = val
                                else:
                                    if val == 0:
                                        self.error_dict[key] = val
                            else:
                                if sign == Constant.test_sign_0001_1:
                                    if val == 0:
                                        self.error_dict[key] = val
                                else:
                                    if val == 1:
                                        self.error_dict[key] = val
            # 6路开关量检测
            if sign == Constant.test_sign_0002_1 or sign == Constant.test_sign_0002_2:
                for d in self.data_dict.items():
                    key = str(d[0])
                    val = int(d[1])
                    if key in ['IN_27', 'IN_28', 'IN_29', 'IN_30', 'IN_31', 'IN_32']:
                        index = int(key.split("_")[1])
                        if index % 2 == 0:
                            if sign == Constant.test_sign_0002_1:
                                if val == 1:
                                    self.error_dict[key] = val
                            else:
                                if val == 0:
                                    self.error_dict[key] = val
                        else:
                            if sign == Constant.test_sign_0002_1:
                                if val == 0:
                                    self.error_dict[key] = val
                            else:
                                if val == 1:
                                    self.error_dict[key] = val
            # 2路开关量检测
            if sign == Constant.test_sign_0003_1 or sign == Constant.test_sign_0003_2:
                in_25 = int(self.data_dict['IN_25'])
                in_26 = int(self.data_dict['IN_26'])

                if sign == Constant.test_sign_0003_1:
                    if in_25 == 0:
                        self.error_dict['IN_25'] = 0
                    if in_26 == 0:
                        self.error_dict['IN_26'] = 0

                else:
                    if in_25 == 1:
                        self.error_dict['IN_25'] = 1
                    if in_26 == 1:
                        self.error_dict['IN_26'] = 1
            # 8路输出口检测
            if sign == Constant.test_sign_0004_1 or sign == Constant.test_sign_0004_2:
                for d in self.data_dict.items():
                    key = str(d[0])
                    val = int(d[1])
                    if "OUT" in key:
                        index = int(key.split("_")[1])
                        if index <= 4:
                            if index % 2 == 0:
                                if sign == Constant.test_sign_0004_2:
                                    if val == 1:
                                        self.error_dict[key] = val
                            else:
                                if sign == Constant.test_sign_0004_1:
                                    if val == 1:
                                        self.error_dict[key] = val

            Common.error_record.update(self.error_dict)

    def evaluate(self, i, binary):
        s = ((i + 1) * 8) - 7
        e = ((i + 1) * 8) + 1
        b_i = 8
        if i == 0:
            for j in range(s, e):
                key = "IN_%s" % j
                self.data_dict[key] = binary[b_i]
                b_i -= 1
        elif i == 1:
            for j in range(s, e):
                key = "IN_%s" % j
                self.data_dict[key] = binary[b_i]
                b_i -= 1
        elif i == 2:
            for j in range(s, e):
                key = "IN_%s" % j
                self.data_dict[key] = binary[b_i]
                b_i -= 1
        elif i == 3:
            for j in range(s, e):
                key = "IN_%s" % j
                self.data_dict[key] = binary[b_i]
                b_i -= 1
        elif i == 4:
            for j in range(s, e):
                key = "IN_%s" % j
                self.data_dict[key] = binary[b_i]
                b_i -= 1
        elif i == 5:
            for j in range(1, 9):
                key = "WU_%s" % j
                self.data_dict[key] = binary[b_i]
                b_i -= 1
        elif i == 6:
            for j in range(1, 9):
                key = "OUT_%s" % j
                self.data_dict[key] = binary[b_i]
                b_i -= 1
        elif i == 7:
            self.data_dict["CAN_WAKE_UP_STATE"] = binary[b_i]


# 验证相关消息处理
class ValidateDataOp:

    def __init__(self, db=None):
        self.db = db

    # im218模块相关can信息处理
    def im218_info_handing(self, frame_id=None, data=None, len=None):
        # print("recv can:", hex(frame_id), data)
        # 获取模块频率量
        self._get_im218_fq(frame_id=frame_id, data=data, len=len)

    # 获取模块频率量
    def _get_im218_fq(self, frame_id=None, data=None, len=None):
        frame_id -= Common.can_addr
        if frame_id == 0x200:
            res = self.db.decode_message(frame_id, data)
            ton_toff_0 = int(res['ifreq1_ton_toff_1'])
            ton_toff_1 = int(res['ifreq1_ton_toff_2'])
            ton_toff_2 = int(res['ifreq1_ton_toff_3'])
            ton_toff_3 = int(res['ifreq1_ton_toff_4'])
            # ton_toff_4 = int(res['ifreq1_ton_toff_5'])
            # ton_toff_5 = int(res['ifreq1_ton_toff_6'])

            if len == 2:
                ton = ton_toff_0
                toff = ton_toff_1
            else:
                ton = int("%02X%02X" % (ton_toff_1, ton_toff_0), 16)
                toff = int("%02X%02X" % (ton_toff_3, ton_toff_2), 16)
            # else:
            #     ton = int("%02X%02X%02X" % (ton_toff_2, ton_toff_1, ton_toff_0), 16)
            #     toff = int("%02X%02X%02X" % (ton_toff_5, ton_toff_4, ton_toff_3), 16)

            Common.im218_fq_dict["FQ1"] = 1000000/(ton+toff)

        elif frame_id == 0x280:
            res = self.db.decode_message(frame_id, data)
            ton_toff_0 = int(res['ifreq2_ton_toff_1'])
            ton_toff_1 = int(res['ifreq2_ton_toff_2'])
            ton_toff_2 = int(res['ifreq2_ton_toff_3'])
            ton_toff_3 = int(res['ifreq2_ton_toff_4'])
            # ton_toff_4 = int(res['ifreq2_ton_toff_5'])
            # ton_toff_5 = int(res['ifreq2_ton_toff_6'])

            if len == 2:
                ton = ton_toff_0
                toff = ton_toff_1
            else:
                ton = int("%02X%02X" % (ton_toff_1, ton_toff_0), 16)
                toff = int("%02X%02X" % (ton_toff_3, ton_toff_2), 16)
            # else:
            #     ton = int("%02X%02X%02X" % (ton_toff_2, ton_toff_1, ton_toff_0), 16)
            #     toff = int("%02X%02X%02X" % (ton_toff_5, ton_toff_4, ton_toff_3), 16)

            Common.im218_fq_dict["FQ2"] = 1000000/(ton+toff)
