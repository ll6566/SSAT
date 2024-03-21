# -*- coding: utf-8 -*-
import os
import sys

# 追加模块搜索路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import threading
from config.config import *
from datetime import datetime
from src.WeComRobot import WeComRobot
from src.tool import input_notice, adb_change
from src.read_task import eRead_test_task, eRead_monitor_time, eRead_test_activity, eRead_test_task_dormant


def inspect_public(devs):
    """
    公共检查方法
    adb在线状态
    测试进程在线状态
    返回：
    是否完成检查
    是否发送通知
    通知信息
    """
    # 检查adb是否在线
    adbRead = os.popen("adb devices").read()
    if str(devs['Device']) not in adbRead:
        return True, True, input_notice(
            [str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']), "ADB离线，暂无法确认测试状态", 'red'])
    # 检查测试工具是否存在
    # 跳过工具进程检查项
    skips = ["GPU测试"]
    if str(devs['BeginName']) not in skips: return False, False, ""
    autoPid = os.popen('adb -s {} shell "ps | grep com.elink.autotest"'.format(devs['Device'])).read()
    auto2Pid = os.popen('adb -s {} shell "ps | grep com.emdoor.pressure.tester"'.format(devs['Device'])).read()
    if autoPid == "" and auto2Pid == "":
        return True, True, input_notice(
            [str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']), "自动化测试APK进程不存在", 'red'])
    return False, False, ""


def inspect_activity(devs):
    """
    通过activity判定测试状态
    返回：
    是否检测完成
    检测状态
    检测消息
    """
    # 检查activity状态
    activityS = eRead_test_activity()
    for aca in activityS:
        for key, value in aca.items():
            if devs['BeginName'] in key:
                acs = str(value).split(",")
                sleep(3)
                activity = os.popen(
                    "adb -s {} shell dumpsys window |findstr mCurrentFocus".format("ACE1Pro202402020022")).read()
                for ac in acs:
                    if ac in str(activity).strip():
                        return True, False, input_notice(
                            [str(devs['Ids']), str(devs['Sign']), str(devs['Device']), str(devs['BeginName']),"%s测试中" % str(devs['BeginName']),'info'])
                return True, True, input_notice([str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']),"%s测试停止" % str(devs['BeginName']), 'red'])

    return False, False, ""


def inspect_special(devs):
    """
    特殊监控, 查看adb的变化
    重启等
    """
    if adb_change(devs['Device'], 300): return False, input_notice(
        [str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']), "%s测试中" % devs['BeginName'], 'info'])
    return True, input_notice(
        [str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']), "%s停止" % devs['BeginName'], 'red'])


def inspect_dormant():
    """
    获取所有休眠中的机器
    """
    a = []
    devList = eRead_test_task_dormant()
    for devs in devList:
        a.append(input_notice([str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']), "休眠中，未测试", 'warning']))
    return a


def inspect(devs):
    """
    特殊测试项；判定测试状态
    返回：
    是否发送通知
    消息
    """
    # 检查monkey测试状态
    if "monkey" in devs['BeginName']:
        read = os.popen("adb devices").read()
        if str(devs['Device']) not in read:
            return True, input_notice(
                [str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']), "monkey测试adb不在线", 'red'])

        monkeyPid = os.popen('adb -s {} shell "ps | grep monkey"'.format(str(devs))).read()
        # monkey已掉线
        if monkeyPid == "":
            return True, input_notice(
                [str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']), "monkey进程不存在", 'red'])

        return False, input_notice([str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']), "monkey测试中", 'info'])
    else:
        # 排除特殊测试项
        if devs['BeginName'] != "开关机测试" and devs['BeginName'] != "重启+相机" and devs[
            'BeginName'] != "重启测试" and devs['BeginName'] != "恢复出厂设置":
            # 检查公共状态
            _type, _type2, value = inspect_public(devs)
            if _type: return _type2, value

            # 检查activity状态
            _type, _type2, value = inspect_activity(devs)
            if _type: return _type2, value

            # 检查特殊测试项测试状态
            if "休眠测试" == devs['BeginName']:
                screen_state = ""
                screenRead = os.popen("adb -s {} shell dumpsys window policy".format(devs['Device'])).read()
                # 亮屏
                if 'SCREEN_STATE_ON' in screenRead: screen_state = "SCREEN_STATE_ON"
                # 息屏
                if 'SCREEN_STATE_OFF' in screenRead: screen_state = "SCREEN_STATE_OFF"
                for screen_state_i in range(40):
                    screenRead = os.popen("adb -s {} shell dumpsys window policy".format(devs['Device'])).read()
                    if screen_state not in screenRead:
                        return False, input_notice(
                            [str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']), "休眠测试中", 'info'])
                    sleep(1)
                return True, input_notice(
                    [str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']), "休眠测试停止", 'red'])
            elif "蓝牙开关测试" == devs['BeginName']:
                bluetoothRead = os.popen(
                    "adb -s {} shell settings get global bluetooth_on".format(devs['Device'])).read()
                for screen_state_i in range(40):
                    bluetoothRead2 = os.popen(
                        "adb -s {} shell settings get global bluetooth_on".format(devs['Device'])).read()
                    if bluetoothRead not in bluetoothRead2:
                        return False, input_notice(
                            [str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']), "蓝牙开关测试中", 'info'])
                    sleep(1)
                return True, input_notice(
                    [str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']), "蓝牙开关测试停止", 'red'])
            elif "WIFI开关测试" == devs['BeginName']:
                wifiRead = os.popen("adb -s {} shell settings get global wifi_on".format(devs['Device'])).read()
                for screen_state_i in range(40):
                    wifiRead2 = os.popen("adb -s {} shell settings get global wifi_on".format(devs['Device'])).read()
                    if wifiRead not in wifiRead2:
                        return False, input_notice(
                            [str(devs['Ids']), str(devs['Sign']), str(devs['Device']), "WIFI开关测试中",str(devs['BeginName']), 'info'])
                    sleep(1)
                return True, input_notice(
                    [str(devs['Ids']), str(devs['Sign']), str(devs['Device']),str(devs['BeginName']), "WIFI开关测试停止", 'red'])
        else:
            # 重启等可能存在adb不在线监控
            _type, value = inspect_special(devs)
            return _type, value


def analysis_Time(time):
    """格式化时间，返回秒"""
    if "H" in time:
        time = str(time).replace("H", "")
        time = int(time) * 60 * 60
        return int(time)
    elif "Min" in time:
        time = str(time).replace("Min", "")
        time = int(time) * 60
        return int(time)
    else:
        return int(3600)


# 启动每个小时检查一次监控
def monitor_H():
    # 获取监控时间
    _type, _type2, value = eRead_monitor_time()
    # 实例企业微信机器人传入机器人url
    wcr = WeComRobot(
        "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=7eb31fcb-8f84-433d-b391-aac56547c880")
    while True:
        # 是否发送通知
        send = False
        # 通知内容
        sendC = []
        testList = eRead_test_task()
        logging.info("正在检查设备测试状态...")
        for divs in testList:
            # 检查
            _type, read = inspect(divs)
            sendC.append(read)
            if _type:
                send = True
        if send:
            # 发送企业微信通知
            sendC += inspect_dormant()
            wcr.message("稳定性测试-时报", sendC)
        # 每个小时检查一次
        for timeout in range(analysis_Time(value)):
            sleep(1)
            print("\r距离下次，时检，时间还有%sS" % str(analysis_Time(value) - (timeout + 1)), end="")


# 启动天自动发送测试报告
def monitor_D():
    while True:
        current_time = datetime.now().strftime("%H:%M")
        if current_time == "09:00" or current_time == "09:01" or current_time == "09:02":
            # 实例企业微信机器人传入机器人url
            wcr = WeComRobot(
                "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=7eb31fcb-8f84-433d-b391-aac56547c880")
            # 通知内容
            sendC = []
            testList = eRead_test_task()
            for divs in testList:
                # 检查
                _type, read = inspect(divs)
                sendC.append(read)
            sendC += inspect_dormant()
            wcr.message("稳定性测试-日报", sendC)
        for timeout in range(60):
            sleep(1)


def monitor_run():
    # 启动监控
    t1 = threading.Thread(target=monitor_H, args=())
    t1.start()
    t2 = threading.Thread(target=monitor_D, args=())
    t2.start()
