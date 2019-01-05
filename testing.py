#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import time
import spidev
import RPi.GPIO as GPIO
from convert import Convert

GPIO.setmode(GPIO.BCM)      # 使用BCM引还脚编号，此外有 GPIO.BOARD
GPIO.setwarnings(False)
GPIO.setup(40, GPIO.OUT)
GPIO.setup(41, GPIO.OUT)


# 公共变量
class CPO:
    # 继电器矩阵 1-7 电阻矩阵控制
    # 8 供模块输入脚用可变电压控制
    # 9 继电器矩阵的电阻切换电路控制
    # 10 供2路频率信号用可变电压控制
    # 11 1-4 OUT_CTRL 5-8 COM_CTRL

    relay_matrix = [[0, 0, 0, 0, 0, 0, 0, 0],  # HC1_CTRL
                    [0, 0, 0, 0, 0, 0, 0, 0],  # HC2_CTRL
                    [0, 0, 0, 0, 0, 0, 0, 0],  # HC3_CTRL
                    [0, 0, 0, 0, 0, 0, 0, 0],  # HC4_CTRL
                    [0, 0, 0, 0, 0, 0, 0, 0],  # HC5_CTRL
                    [0, 0, 0, 0, 0, 0, 0, 0],  # HC6_CTRL
                    [0, 0, 0, 0, 0, 0, 0, 0],  # HC7_CTRL
                    [0, 0, 0, 0, 0, 0, 0, 0],  # HC8_CTRL
                    [0, 0, 0, 0, 0, 0, 0, 0],  # HC9_CTRL
                    [0, 0, 0, 0, 0, 0, 0, 0],  # HC10_CTRL
                    [0, 0, 0, 0, 0, 0, 0, 0]]  # HC11_CTRL


# 电源控制
class Testing:
    def __init__(self):
        self.spiM = SpiM()

    def start_test(self):
        while True:
            x = 0
            y = 0
            CPO.relay_matrix[x][y] = 1
            print(CPO.relay_matrix)
            self.spiM.send()
            time.sleep(1)

            CPO.relay_matrix[x][y] = 0
            print(CPO.relay_matrix)
            time.sleep(0.5)

            self.spiM.send()

    def op(self, x, y, val):
        CPO.relay_matrix[x][y] = val
        self.spiM.send()
        print(CPO.relay_matrix)
        time.sleep(1)

    @staticmethod
    def gpio_out(gpio, val):
        GPIO.setup(gpio, GPIO.OUT)
        if val == "0":
            GPIO.output(gpio, 0)
            print(gpio, "low", GPIO.input(gpio))
        else:
            GPIO.output(gpio, 1)
            print(gpio, "high", GPIO.input(gpio))

        # GPIO.cleanup()

    # @staticmethod
    # def gpio_in(gpio, val):
    #     GPIO.setup(gpio, GPIO.OUT)
    #     if val == "0":
    #         GPIO.output(gpio, 0)
    #         print(gpio, "low", GPIO.input(gpio))
    #     else:
    #         GPIO.output(gpio, 1)
    #         print(gpio, "high", GPIO.input(gpio))

        # GPIO.cleanup()


# SPI数据模块
class SpiM:
    def __init__(self, baudrate=1000):
        self.spi = spidev.SpiDev()
        self.spi.open(1, 0)
        self.spi.max_speed_hz = baudrate
        # self.spi.lsbfirst = True
        # self.spi.mode = 0b00

    def send(self):
        GPIO.setup(18, GPIO.OUT)
        GPIO.output(18, 0)
        time.sleep(0.1)
        val = ""
        for i in range(-1, (len(CPO.relay_matrix) + 1) * -1, -1):
            for j in range(-1, -9, -1):
                val += str(CPO.relay_matrix[i][j])

        data = Convert().convertToHex(val)
        print('spi write:', data)
        self.spi.writebytes(data)
        GPIO.output(18, 1)
        time.sleep(0.1)
        GPIO.cleanup()

    def read(self, count):
        data = self.spi.read(11)
        print("%s spi read: %s" % (count, data))


class PWM:
    def __init__(self):
        pass

    def start(self, fq=1, rate=0, d=50):
        if fq == 1:
            fq_gpio = 40
        else:
            fq_gpio = 41

        p = GPIO.PWM(fq_gpio, rate)
        p.start(d)

        print("fq%s rate=%s" % (fq, rate))
        count = 0
        while True:
            count += 1


t = Testing()
# t.op(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
t.gpio_out(int(sys.argv[1]), sys.argv[2])

# pwm = PWM()
# pwm.start(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))

