#!/usr/bin/env python
# -*- coding:utf-8 -*-

import cantools
import time
import spidev
import can
import json
import uds_server
from convert import Convert
from config import Constant, Common, RuleConfig
from validate import Validate, ValidateDataOp
import RPi.GPIO as GPIO
import threading
import struct


GPIO.setmode(GPIO.BCM)      # 使用BCM引还脚编号，此外有 GPIO.BOARD
GPIO.setwarnings(False)
GPIO.setup(Constant.get_val(Constant.vb), GPIO.OUT)
GPIO.setup(Constant.get_val(Constant.vb1), GPIO.OUT)
GPIO.setup(Constant.get_val(Constant.vb2), GPIO.OUT)
GPIO.setup(Constant.get_val(Constant.amp_5), GPIO.OUT)
GPIO.setup(Constant.get_val(Constant.amp_12), GPIO.OUT)
GPIO.setup(Constant.get_val(Constant.amp_19), GPIO.OUT)
GPIO.setup(Constant.get_val(Constant.fq1_ctrl), GPIO.OUT)
GPIO.setup(Constant.get_val(Constant.fq1_ctrl_r), GPIO.OUT)
GPIO.setup(Constant.get_val(Constant.fq2_ctrl), GPIO.OUT)
GPIO.setup(Constant.get_val(Constant.fq2_ctrl_r), GPIO.OUT)
GPIO.setup(19, GPIO.OUT)


# 日志
class Log:
    def __init__(self, serial_code=""):
        if len(serial_code) > 0:
            self.file_path = "test_logs/test_%s.log" % serial_code
        else:
            self.file_path = "test_logs/test.log"

    # 写日志
    def write_log(self, content=""):
        print(content)
        content = "%s\r\n" % content
        f = open(self.file_path, "a")
        f.write(content)
        f.close()

    # 清空日志文件
    def empty_log(self):
        f = open(self.file_path, "w")
        f.write("")
        f.close()


# 电源控制
class PCM:
    def __init__(self, gpio=None):
        self.gpio = Constant.get_val(gpio)

    # 打开电源
    def pin_off(self):
        if self.gpio is not None:
            GPIO.output(self.gpio, 0)
            # print(self.gpio, 0)

    # 关闭电源
    def pin_on(self):
        if self.gpio is not None:
            GPIO.output(self.gpio, 1)
            # print(self.gpio, 1)

    # 批量开关操作
    @staticmethod
    def batch_switch(on_dict):
        for p in dict(on_dict).items():
            # print('gpio', p[0])
            if p[1]:
                PCM(p[0]).pin_on()
                # print("%s %s" % (p, "开"))
            else:
                PCM(p[0]).pin_off()
                # print("%s %s" % (p, "关"))


# 电压控制
class VCM:
    def __init__(self):
        pass

    # 模块电压
    @staticmethod
    def set_modul_vol(mod_dict):
        Common.relay_matrix[Constant.relay_module_index] = Convert.dict_to_list(Constant.vol_list, dict(mod_dict))

    # 2路频率信号电压
    @staticmethod
    def set_rate_vol(vol_dict):
        Common.relay_matrix[Constant.relay_rate_index] = Convert.dict_to_list(Constant.vol_list, dict(vol_dict))


# 电阻切换电路模块
class RCM:
    def __init__(self):
        pass

    # 继电器电阻切换电路
    @staticmethod
    def set_relay_matrix(rtd_dict):
        Common.relay_matrix[Constant.relay_r_index] = Convert.dict_to_list(Constant.relay_rtd_list, dict(rtd_dict))

    # IM218 模块接口端子切换
    @staticmethod
    def set_i_terminal(i_terminal_dict):
        Common.relay_matrix[Constant.i_terminal_index] = Convert.dict_to_list(Constant.i_terminal_list,
                                                                              dict(i_terminal_dict))


# 继电器矩阵模块
class RelayM:
    def __init__(self, relay_m_rule):
        self.relay_m_rule = dict(relay_m_rule)

    def set(self):
        matrix = list(self.relay_m_rule['matrix'])
        rtd = self.relay_m_rule['rtd']
        vol = self.relay_m_rule['vol']
        # 设置继电器矩阵模块电压
        # print("设置继电器矩阵模块电压:", vol)
        VCM.set_modul_vol(vol)
        # 设置继电器矩阵模块电阻
        # print("设置继电器矩阵模块电阻:", rtd)
        RCM.set_relay_matrix(rtd)

        # 设置继电器开关
        for i in range(len(matrix)):
            Common.relay_matrix[i] = matrix[i]


# 频率输出模块
class FQM:
    def __init__(self, fqm_rul):
        self._fqm_rul = fqm_rul

    # 切换电阻
    @staticmethod
    def _rtd_switch(switch, fq_gpio):
        # name = "fq1_ctrl"
        rtd_gpio = Constant.fq1_ctrl
        if fq_gpio == Constant.get_val(Constant.fq2_ctrl_r):
            # name = "fq2_ctrl"
            rtd_gpio = Constant.fq2_ctrl
        if switch:
            # print("%s 打开" % name)
            PCM(rtd_gpio).pin_on()
        else:
            # print("%s 关闭" % name)
            PCM(rtd_gpio).pin_off()

    # 输出fq1频率量
    def send_fq1(self):
        fq1_dict = dict(self._fqm_rul)["fq1"]

        fq1_gpio = Constant.get_val(Constant.fq1_ctrl_r)
        fq1_switch = fq1_dict['switch']
        fq1_rate = int(fq1_dict['rate'])
        fq1_rtd = fq1_dict['rtd']

        if fq1_switch:
            # 设置频率信号电阻
            self._rtd_switch(fq1_rtd, fq1_gpio)
            p = GPIO.PWM(fq1_gpio, fq1_rate)
            p.start(50)
            print("fq1 gpio=%s rate=%s" % (fq1_gpio, fq1_rate))

        while True:
            if not Common.pwm_is_run:
                break

    # 输出fq2频率量
    def send_fq2(self):
        fq2_dict = dict(self._fqm_rul)["fq2"]
        fq2_gpio = Constant.get_val(Constant.fq2_ctrl_r)
        fq2_switch = fq2_dict['switch']
        fq2_rate = fq2_dict['rate']
        fq2_rtd = fq2_dict['rtd']

        if fq2_switch:
            # 设置频率信号电阻
            self._rtd_switch(fq2_rtd, fq2_gpio)
            p = GPIO.PWM(fq2_gpio, fq2_rate)
            p.start(50)
            print("fq2 gpio=%s rate=%s" % (fq2_gpio, fq2_rate))

        while True:
            if not Common.pwm_is_run:
                break


# SPI数据模块
class SpiM:
    def __init__(self, baudrate=10000):
        self.spi = spidev.SpiDev()
        self.spi.open(1, 0)
        self.spi.max_speed_hz = baudrate

    def send(self):

        GPIO.output(19, 0)
        time.sleep(0.1)
        val = ""
        for i in range(-1, (len(Common.relay_matrix) + 1) * -1, -1):
            for j in range(-1, -9, -1):
                val += str(Common.relay_matrix[i][j])

        data = Convert().convertToHex(val)
        # print('spi write:', data)
        self.spi.writebytes(data)
        GPIO.output(19, 1)
        time.sleep(0.1)

    def send_data(self, data):
        # print('spi write:', data)
        GPIO.output(19, 0)
        time.sleep(0.1)
        self.spi.writebytes(data)
        GPIO.output(19, 1)
        time.sleep(0.1)


# ADC采集电压模块
class AdcM:
    def __init__(self, adc_gpio=Constant.read_adc):
        # self.adc = pyb.ADC(Pin(adc_gpio))
        self.adc = ""

    # ADC 采样放大倍数切换电路
    @staticmethod
    def switch_circuit(apm_on_dict):
        PCM.batch_switch(apm_on_dict)

    # 采集电压
    def collection(self, name, tab_v, amp):
        v = 0
        vmax = 0
        vmin = 4095
        for i in range(10):
            n_v = int(self.adc.read())
            if n_v > vmax:
                vmax = n_v

            if n_v < vmin:
                vmin = n_v

            v += n_v  # 采集电压
            time.sleep(0.1)

        v -= (vmax + vmin)

        v_rate = 1
        adc_read_v = v / 8
        adc_vol = round(v / (4095 * 8) * 3.3, 2)
        if "vol1" == name or "vol2" == name:
            if tab_v > 4:
                adc_vol += 0.1
            v_rate = 8
        elif "relay" == name:
            v_rate = Constant.amp_rate_dict[amp]
        print("%s 电压: %s[%s %s] %s" % (name, str(adc_vol * v_rate), adc_read_v, str(adc_vol), v_rate))
        return adc_vol * v_rate


# Can总线处理模块
class CanM:
    def __init__(self):
        can.rc['interface'] = 'socketcan'
        can.rc['channel'] = 'can0'
        self.can_bus = can.interface.Bus()
        self.db = cantools.database.load_file('dbc/IM218.dbc')

    # 发送can信息
    def send_can(self, can_id=None, can_data=None, extended_id=False):
        try:
            msg = can.Message(arbitration_id=can_id, data=bytearray.fromhex(can_data), extended_id=extended_id)
            self.can_bus.send(msg)
            time.sleep(0.001)
            # print("can信息发送:", time.time(), hex(can_id), '#', can_data, extended_id)
        except Exception as e:
            print(e)

    # 接收can信息
    def recv_can(self):
        try:
            while True:
                bo = self.can_bus.recv(timeout=10)
                if bo is not None:
                    frame_id = bo.arbitration_id
                    data = (bo.data + bytearray([0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))[:8]
                    Common.can_recv_dict[frame_id] = data   # 记录收到的can信息
                    Common.can_addr = frame_id & 0xF    # 获取报文ID中的地址值
                    if Constant.check_meter == Constant.IM_218:
                        ValidateDataOp(db=self.db).im218_info_handing(frame_id=frame_id, data=data, len=bo.dlc)
                        self.check_start_up(frame_id=frame_id)  # 检查模块启动
                        # print("can recv: %03X#%s" % (frame_id, data))
        except Exception:
            Common.error_record['Can'] = "can connect error"
            time.sleep(5)
            print("restart connect recv can")
            self.recv_can()

    # 检查模块启动
    def check_start_up(self, frame_id=None):
        frame_id = frame_id - Common.can_addr
        # 判断是否有重启或复位
        if frame_id == 0x0:
            # 启动模块
            self.send_can(can_id=0x040, can_data="01")
            time.sleep(0.5)
            self.send_can(can_id=0x040, can_data="07")
            time.sleep(0.5)


# 检查模块
class CheckM:
    def __init__(self, rule):
        self.rule = rule

    # 获取设置的电压
    @staticmethod
    def _get_set_vol(vol_dict):
        correct_vol = 0
        for v in dict(vol_dict).items():
            if v[1] == 1:
                correct_vol = v[0]
                break
        return int(correct_vol)

    # 获取设置的amp值
    @staticmethod
    def _get_set_amp(_dict):
        key = ""
        for v in dict(_dict).items():
            if v[1] == 1:
                key = v[0]
                break
        if len(key) <= 0:
            key = "amp_2"
        return key

    def check_vol(self, vol_gpio, correct_vol=0.0):
        offset = 0
        name = ""
        if vol_gpio == Constant.vol1_adc:
            name = "vol1"
            offset = self.rule[Constant.adc]['vol1_offset']

        elif vol_gpio == Constant.vol2_adc:
            name = "vol2"
            offset = self.rule[Constant.adc]['vol2_offset']

        elif vol_gpio == Constant.oc_adc:
            name = "oc"
            offset = self.rule[Constant.adc]['oc_offset']

        elif vol_gpio == Constant.read_adc:
            name = "relay"
            offset = self.rule[Constant.adc]['relay_offset']
        # 获取amp数值
        amp = self._get_set_amp(self.rule[Constant.adc]['amp'])
        vol = AdcM(vol_gpio).collection(name, correct_vol, amp)

        if correct_vol > 0:
            if vol < (int(correct_vol) - int(offset)) or vol > (int(correct_vol) + int(offset)):
                content = "name:%s now_vol:%s correct_vol:%s 电压不正确\r\n" % (name, vol, correct_vol)
                Log().write_log(content=content)


# 温度
class Tem:
    def __init__(self, us):
        self.us = us

    # 获取温度
    def get_tem(self):
        # uds协议获取can信息
        res_uds_data = self.us.send(data="22040408")
        val = round(struct.unpack(">I", res_uds_data[3:7])[0] * 0.1)
        return val


# 启动测试
class StartUp:
    def __init__(self, rule, canm):
        self.rule = rule
        self.canm = canm
        Common.can_recv_dict = {}
        Common.uds_recv_dict = {}

    def write(self):
        rule = self.rule

        # ADC 采样放大倍数切换电路
        if Constant.adc in rule:
            # print("设置ADC采样放大倍数切换电路:")
            AdcM.switch_circuit(rule[Constant.adc]['amp'])
            time.sleep(unitDelay)

        # 接口端子电阻切换
        if Constant.i_terminal in rule:
            # print("接口端子电阻切换:")
            RCM.set_i_terminal(rule[Constant.i_terminal]['data'])
            time.sleep(unitDelay)

        # 继电器矩阵
        if Constant.relay_m in rule:
            # print("继电器矩阵:")
            RelayM(rule[Constant.relay_m]).set()
            SpiM().send()  # Spi发送继电器信息
            time.sleep(unitDelay)
            SpiM().send()  # Spi发送继电器信息
            time.sleep(unitDelay)

        # 重置电源
        if Constant.pcm_reset in rule:
            time.sleep(5)
        #     pcm_list = list(rule[Constant.pcm_reset])
        #     for pcm in pcm_list:
        #         PCM.batch_switch(pcm)
        #         time.sleep(5)
        # can
        if Constant.can in rule:
            can_dict = dict(rule[Constant.can])
            for c in can_dict.items():
                if "|" in c[0]:
                    can_id = int(str(c[0]).split("|")[0])
                else:
                    can_id = int(c[0])
                can_id += Common.can_addr
                extended_id = False
                if "IC" in Constant.check_meter:
                    extended_id = True
                self.canm.send_can(can_id=can_id, can_data=c[1], extended_id=extended_id)
            time.sleep(unitDelay)

        # can接受数据规定范围
        if Constant.can_val_range in rule:
            Common.can_val_range = dict(rule[Constant.can_val_range])

        # uds
        if Constant.uds in rule:
            uds_dict = dict(rule[Constant.uds])
            us = uds_server.UdsServer(can_bus=self.canm.can_bus)  # 初始化uds服务
            for key in sorted(uds_dict):
                # uds协议获取can信息
                res_uds_data = us.send(data=uds_dict[key])
                keys = str(key).split("|")
                mouth = keys[0]
                mark = keys[1]
                if "val" in mark:
                    Common.uds_recv_dict[mouth] = res_uds_data
            us.close()
            time.sleep(unitDelay)

        # 频率信号
        if Constant.fqm in rule:
            Common.pwm_is_run = True
            # print("频率信号:")
            # print("设置频率电压: ", rule[Constant.fqm]['vol'])
            VCM.set_rate_vol(rule[Constant.fqm]['vol'])  # 设置发送频率信号电压
            # SpiM().send()  # Spi发送继电器信息
            time.sleep(unitDelay)

            # t_fq1 = threading.Thread(target=FQM(rule[Constant.fqm]).send_fq1, name="threading-fq1")
            # t_fq1.setDaemon(True)
            # t_fq2 = threading.Thread(target=FQM(rule[Constant.fqm]).send_fq2, name="threading-fq2")
            # t_fq2.setDaemon(True)
            # t_fq1.start()
            # t_fq2.start()

    def read(self):
        rule = self.rule

        # 验证报文数据
        Validate().analysis(sign=rule['sign'])

        Common.im218_is_out_duty = False
        Common.pwm_is_run = False

        # # 检查电压
        # CheckM(rule).check_vol(Constant.vol1_adc)
        # CheckM(rule).check_vol(Constant.vol2_adc)
        # CheckM(rule).check_vol(Constant.oc_adc)
        # CheckM(rule).check_vol(Constant.read_adc, 1.5)

    # 复位
    def reset(self):
        # 复位595
        SpiM().send_data([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        # 复位adc电压倍数
        PCM(Constant.amp_5).pin_off()
        PCM(Constant.amp_12).pin_off()
        PCM(Constant.amp_19).pin_off()

        if Constant.check_meter == Constant.IM_218:
            # 关闭20路out开关
            can_id = 0xC0 + Common.can_addr
            for i in range(2):
                self.canm.send_can(can_id=can_id, can_data="0000000000000000")
                time.sleep(0.1)


# 获取串码
def get_serial_code(meter="IC216", canm=None):
    serial_code = b''
    if meter == Constant.IC_216:
        send_frame_id = 0x660
        recv_frame_id = 0x7E0
        address_data = 'F60000000027FFE0'
        length = 'F507000000000000'

    elif meter == Constant.IC_218:
        send_frame_id = 0x660
        recv_frame_id = 0x7E0
        address_data = 'F6000000E0FF0700'
        length = 'F507000000000000'
    else:
        send_frame_id = 0x661
        recv_frame_id = 0x7E1
        address_data = 'F6000000E0FF0700'
        length = 'F507000000000000'

    # 创建链接
    while True:
        canm.send_can(can_id=send_frame_id, can_data='FF00000000000000')
        time.sleep(0.2)
        if recv_frame_id in Common.can_recv_dict:
            if 255 == Common.can_recv_dict[recv_frame_id][0]:
                # print("connect success")
                break

    # 获取串码
    canm.send_can(can_id=send_frame_id, can_data=address_data)
    while True:
        canm.send_can(can_id=send_frame_id, can_data=length)
        time.sleep(0.5)
        if recv_frame_id in Common.can_recv_dict:
            if b'\xff\xff\xff\xff\xff\xff\xff\xff' != Common.can_recv_dict[recv_frame_id]:
                serial_code += Common.can_recv_dict[recv_frame_id]
            else:
                break
    # 退出boot
    canm.send_can(can_id=send_frame_id, can_data='CF00000000000000')
    canm.send_can(can_id=send_frame_id, can_data='FE00000000000000')
    if len(serial_code) > 0:
        serial_code = serial_code.replace(b'\xff', b'')
        serial_code = Convert.bytes_to_hexstr(serial_code)
    else:
        serial_code = ""
    return serial_code


# 运行测试程序
def run():
    start_time = time.time()
    try:
        while True:
            print("\r\nPress Enter Start Testing:")
            input()

            Common.can_recv_dict = {}
            Common.uds_recv_dict = {}

            check_rule = RuleConfig.rule_ic216
            if Constant.check_meter == Constant.IC_216:
                check_rule = RuleConfig.rule_ic216
                print("检测IC216")
            elif Constant.check_meter == Constant.IC_218:
                check_rule = RuleConfig.rule_ic218
                print("检测IC218")
            elif Constant.check_meter == Constant.IM_218:
                check_rule = RuleConfig.rule_im218
                print("检测IM218")
            elif Constant.check_meter == Constant.IM_228:
                check_rule = RuleConfig.rule_im228
                print("检测IM228")
            json_rule = json.loads(check_rule)

            # 电源
            if Constant.pcm in json_rule:
                PCM.batch_switch(json_rule[Constant.pcm]['data'])
                time.sleep(0.5)

            # 等待启动
            while True:
                check_id = 0x380 + Common.can_addr
                if check_id in Common.can_recv_dict:
                    time.sleep(1)
                    break

            canm = CanM()   # 初始化can
            serial_code = ""
            # serial_code = get_serial_code(meter=Constant.check_meter, canm=canm)
            # print("serial_code:", serial_code)

            # 开始检测
            root_list = json_rule['ROOT']
            for root in root_list:
                if len(Common.error_record) > 0:
                    break
                describe = root['describe']
                run_count = int(root['runCount'])
                delay = int(root['delay'])/1000.0
                global unitDelay
                unitDelay = int(root['unitDelay'])/1000.0
                for i in range(1, run_count+1):
                    if len(Common.error_record) > 0:
                        break

                    # 获取实时温度
                    us = uds_server.UdsServer(can_bus=canm.can_bus)
                    tem = Tem(us=us).get_tem()
                    us.close()
                    print("\r\n%s 第%s次 温度%s℃" % (describe, i, tem))

                    rule_list = root['ruleList']
                    for rule in rule_list:
                        start_up = StartUp(rule=rule, canm=canm)
                        start_up.reset()
                        start_up.write()
                        start_up.read()
                        # time.sleep(20)
                        start_up.reset()
                        if len(Common.error_record) > 0:
                            break
                    time.sleep(delay)

            if len(Common.error_record) > 0:
                log_msg = "The test failed, 错误位置:\r\n"
                if "Can" in Common.error_record:
                    log_msg += "Can连接异常"
                elif Constant.log_model:
                    for e in sorted(Common.error_record.items()):
                        key = e[0]
                        val = e[1]
                        log_msg += "%s %s\r\n" % (key, val)
                else:
                    for e in sorted(Common.error_record.items()):
                        key = e[0]
                        val = e[1]
                        if key in Constant.check_terminal_dict:
                            log_msg += "%s %s\r\n" % (Constant.check_terminal_dict[key], val)
            else:
                log_msg = "The test successfully"
            Log(serial_code).empty_log()   # 清空日志文件
            Log(serial_code).write_log(content=log_msg)
            PCM(Constant.vb).pin_off()
            print("check completed %ss" % int(time.time()-start_time))
    except Exception as e:
        print(e)


def start_thread():
    thread_name = "threading-canRecv"
    t_d = threading.Thread(target=CanM().recv_can, name=thread_name)
    t_d.setDaemon(True)

    thread_name = "threading-run"
    t_s = threading.Thread(target=run, name=thread_name)
    t_s.setDaemon(True)

    t_d.start()
    t_s.start()

    t_d.join()


if __name__ == "__main__":
    start_thread()
