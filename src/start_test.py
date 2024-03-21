# -*- encoding=utf8 -*-
import os
import sys


# 追加模块搜索路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import threading
from time import sleep
from config.config import logging
from src.class_list import T1, Ace1
from src.read_task import eRead_test_task, eRead_wifi_ssid_password
from src.tool import check_device,input_notice, adb_continuous


def wait_reboot(sign):
    """
    等待重启，只有一台设备时，时间增长
    """
    if sign == 1:
        for times in range(140):
            print("\r因您的测试设备只有一台，所以将等待140s保证正常开机(%ds)" % (140 - (times + 1)), end="")
            sleep(1)
    else:
        for times in range(60):
            print("\r等待60s确保机器都正常开机...(%ds)" % (60 - (times + 1)), end="")
            sleep(1)
    print("\r等待重启完成")


def stop_run(classType,dev,beginName):
    testClass = classType(device=dev, beginName=beginName, ssid="", password="",account="", preconditions="")
    if not adb_continuous(dev, 15):
        testClass.stop_test()


def stop_reboot(devList):
    """
    执行刷机项目之前停止可能影响测试项
    """
    # 刷机前停止【重启测试、重启+相机、开关机测试、恢复出厂设置测试】
    stopList = ["重启测试", "重启+相机", "开关机测试", "恢复出厂设置"]
    stopDevice = [dev for dev in devList if dev['BeginName'] in stopList]
    # 启动测试list
    stopList = []

    logging.info("正在停止【重启测试、重启+相机、开关机测试、恢复出厂设置测试】等测试...")
    for stopDev in stopDevice:
        models = os.popen("adb -s {} shell getprop ro.product.model".format(stopDev['Device'])).read()
        models = str(models).replace(" ", "").replace("\n", "")
        if "XPT11" in models:
            t = threading.Thread(target=stop_run, args=(T1,stopDev["Device"],stopDev["BeginName"]))
            stopList.append(t)
        elif "XTA11" in models:
            t = threading.Thread(target=stop_run, args=(Ace1,stopDev["Device"],stopDev["BeginName"]))
            stopList.append(t)
        else:
            print("添加停止重启测试项失败，没有改机型")
    # 多线程执行停止测试任务
    for t in stopList:
        t.join()
        t.start()
    print("停止测试完成")
    return True

def test_run(classType, sending, wcr):
    """
    测试启动方法
    classType 机型类
    sending 发送企业微信通知标识
    """
    # 获取wifi信息
    ssid, password = eRead_wifi_ssid_password()
    devList = eRead_test_task()
    # 企业微信发送消息列表
    messageList = []
    rfType = False
    for dev in devList:
        if "恢复出厂设置" not in str(dev['Nodes']): continue
        if not rfType:
            # 停止重启开关机等测试
            stop_reboot(devList)
        rfType = True
        testClass = classType(device=dev['Device'], beginName="", ssid="", password="", account="", preconditions="")
        # 恢复出厂设置
        _type, value = testClass.restore_factory()
        messageList.append(input_notice(
            [str(dev['Ids']), str(dev['Sign']), str(dev['Device']), str(dev['BeginName']), str(value), 'info']))
    # 完成后企业微信通知
    if sending and rfType: wcr.message("恢复出厂设置完成通知", messageList)

    # 企业微信发送消息列表
    messageList = []
    skipGuideType = False
    for dev in devList:
        if "跳过引导" not in str(dev['Nodes']): continue
        skipGuideType = True
        testClass = classType(device=dev['Device'], beginName=dev['BeginName'], ssid=ssid, password=password,
                              account=dev['Account'], preconditions=dev['Preconditions'])
        testClass.close_app_control()
        if not check_device(dev['Device'], 60):
            messageList.append(input_notice(
                [str(dev['Ids']), str(dev['Sign']), str(dev['Device']), str(dev['BeginName']), "关闭应用管控后重启，device"
                                                                                               "不在线", 'red']))
            continue
        for launcher in range(60):
            sleep(1)
            read = os.popen("adb -s {} shell dumpsys window |findstr mCurrentFocus".format(str(dev['Device']))).read()
            if "com.seewo.studystation.login.ui.activity.PrivacyAgreeActivity" in read:
                sleep(2)
                break
        logging.info("重启后已进入桌面")
        # 跳过开机引导
        _type, value = testClass.skip_guide()
        if not _type:
            messageList.append(
                input_notice(
                    [str(dev['Ids']), str(dev['Sign']), str(dev['Device']), str(dev['BeginName']), str(value), 'red']))
            continue
        else:
            messageList.append(
                input_notice(
                    [str(dev['Ids']), str(dev['Sign']), str(dev['Device']), str(dev['BeginName']), str(value), 'info']))
    # 完成后企业微信通知
    if sending and skipGuideType: wcr.message("跳过引导完成通知", messageList)

    # 企业微信发送消息列表
    messageList = []
    loginType = False
    for dev in devList:
        if "登录账号" not in str(dev['Nodes']): continue
        loginType = True
        testClass = classType(device=dev['Device'], beginName=dev['BeginName'], ssid=ssid, password=password,
                              account=dev['Account'], preconditions=dev['Preconditions'])
        # 登录账号
        _type, value = testClass.login_account()
        if not _type:
            messageList.append(input_notice(
                [str(dev['Ids']), str(dev['Sign']), str(dev['Device']), str(dev['BeginName']), str(value), 'red']))
            continue
        else:
            messageList.append(input_notice(
                [str(dev['Ids']), str(dev['Sign']), str(dev['Device']), str(dev['BeginName']), str(value), 'info']))
        if dev['Account'] is None: continue
        # 登录账号完成后推荐设置
        testClass.login_open_setting()
    # 完成后企业微信通知
    if sending and loginType: wcr.message("登录完成通知", messageList)

    # 企业微信发送消息列表
    messageList = []
    startType = False
    for dev in devList:
        if "启动测试" not in str(dev['Nodes']): continue
        startType = True
        testClass = classType(device=dev['Device'], beginName=dev['BeginName'], ssid=ssid, password=password,
                              account=dev['Account'], preconditions=dev['Preconditions'])
        # 设置前置条件
        testClass.preconditions_set()
        # 启动测试
        _type, value = testClass.start()
        if not _type:
            messageList.append(input_notice(
                [str(dev['Ids']), str(dev['Sign']), str(dev['Device']), str(dev['BeginName']), str(value), 'red']))
            continue
        else:
            messageList.append(input_notice(
                [str(dev['Ids']), str(dev['Sign']), str(dev['Device']), str(dev['BeginName']), str(value), 'info']))

    # 完成后企业微信通知
    if sending and startType: wcr.message("启动测试完成通知", messageList)

    # 企业微信发送消息列表
    messageList = []
    stopType = False
    for dev in devList:
        if "停止测试" not in str(dev['Nodes']): continue
        stopType = True
        testClass = classType(device=dev['Device'], beginName=dev['BeginName'], ssid=ssid, password=password,
                              account=dev['Account'], preconditions=dev['Preconditions'])
        # 停止测试
        _type, value = testClass.stop_test()
        if not _type:
            messageList.append(input_notice(
                [str(dev['Ids']), str(dev['Sign']), str(dev['Device']), str(dev['BeginName']), str(value), 'red']))
            continue
        else:
            messageList.append(input_notice(
                [str(dev['Ids']), str(dev['Sign']), str(dev['Device']), str(dev['BeginName']), str(value), 'info']))
        # 完成后企业微信通知
    if sending and stopType: wcr.message("停止测试完成通知", messageList)
