# -*- encoding=utf8 -*-
import os
import sys

# 追加模块搜索路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import time
import serial
import binascii
import serial.tools.list_ports
from config.config import logging


def existing(com):
    com_list = []
    for a in list(serial.tools.list_ports.comports()):  # 获取继电器com
        info = a.description.split()
        if info[1] == "CH341A":
            serialPort = a.name
            com_list.append(serialPort)
    if not com_list:
        logging.warning("设备未检测到继电器端口存在")
        return
    if com in com_list:
        return True
    else:
        logging.info("com端口不匹配(%s),本地端口：%s" % (com, com_list))


def relay_control(com, state=0):
    """USB继电器控制
    com 继电器端口号
    state 1继电器吸合 0 继电器释放"""

    baudRate = 9600  # 波特率
    on = bytes.fromhex('A0 01 03 A4')  # A0 01 03 A4 开启电源输出，并反馈状态A0 01 00 A2
    off = bytes.fromhex('A0 01 02 A3')  # A0 01 03 A3 关闭电源输出，并反馈状态A0 01 00 A1

    if existing(com):
        s = serial.Serial(com, baudRate, timeout=0.5)
        try:
            if state:
                s.write(on)
            else:
                s.write(off)
        except:
            logging.info("继电器写值异常")
            s.close()
            return
        time.sleep(1)
        n = s.inWaiting()
        if n:
            data = str(binascii.b2a_hex(s.read(n)))[2:-1]
            # logging.info("继电器状态正确 %s" % data)
            s.close()
            return True
        else:
            time.sleep(10)
            s.write(bytes.fromhex("A0 01 05 A6"))
            time.sleep(1)
            n = s.inWaiting()
            data = str(binascii.b2a_hex(s.read(n)))[2:-1]
            if data == "a00101a2a00101a2" and state:
                # logging.info("继电器状态正确")
                s.close()
                return True
            elif data == "a00101a2a00101a1" and not state:
                # logging.info("继电器状态正确")
                s.close()
                return True
            else:
                logging.warning("继电器返回异常:%s " % data)
                s.close()
                return


if __name__ == '__main__':
    relay_control("COM532", 1)
