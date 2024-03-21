# -*- encoding=utf8 -*-
import os
import sys
from time import sleep

# 追加模块搜索路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from src.burn import burn_run
from config.config import logging
from src.monitor import monitor_run
from src.class_list import T1, Ace1
from src.WeComRobot import WeComRobot
from src.start_test import test_run, stop_reboot, wait_reboot
from src.read_task import eRead_test_task, eRead_monitor_time, eRead_software_link
from src.tool import waitEnter, check_device, waitPid, open_sub, input_notice, download_software, open_close_sub

def main():
    print("启动中......")
    # 重新开关usbHub
    open_sub()
    # 测试机器预检
    waitEnter(60)
    print("")
    # 实力企业微信机器人
    wcr = WeComRobot("https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=7eb31fcb-8f84-433d-b391-aac56547c880")
    # 是否发送企业微信通知
    sending = False
    # 读取任务表
    devTest = eRead_test_task()
    # 启动监控
    _type, _type2, value = eRead_monitor_time()
    if _type and not _type2:
        # 单独启动监控
        monitor_run()
        wcr.message("监控启动完成通知", [input_notice(['null', 'null', 'null', 'null', "测试监控启动成功", 'info'])])
        exit()
    # 检查启动选项
    if len(devTest) <= 0 and not _type:
        print("您未选择机器测试，也没选择启动功能项！！")
        exit()
    # 检查设备机型
    if len(devTest) >= 1:
        if not check_device(devTest[0]['Device'], 200):
            logging.error("启动测试失败，第一台设备不在线无法获取机型，请确保第一台设备Device在线")
            exit()
    models = ""
    if waitPid(devTest[0]['Device'], "init", 65) != "":
        models = str(os.popen("adb -s {} shell getprop ro.product.model".format(devTest[0]['Device'])).read()).replace(" ", "").replace("\n", "")

    # 检查测试链接
    testLink = eRead_software_link()
    if models not in testLink:
        logging.warning("测试软件不适用该机型，请检查！！")
        exit()

    # 下载文件
    dowLink = ""
    # 是否存在刷机项目
    burnType = False
    for dev in devTest:
        if "刷机" in str(dev['Nodes']):
            burnType = True
            # 下载文件 传入软件链接
            _type, dowLink = download_software(eRead_software_link())
            # 判断下载文件状态
            if not _type and sending:
                messageList = [input_notice(['null', 'null', 'null', 'null', str(dowLink), 'red'])]
                wcr.message("烧录告警通知", messageList)
            if not _type:
                exit()
            break

    # 刷机时停止 重启等测试
    if burnType:
        # 停止重启开关机等测试
        stop_reboot(devTest)
    # 刷机
    hubNumber = 0
    # 企业微信发送消息列表
    messageList = []
    for dev in devTest:
        if "刷机" not in str(dev['Nodes']): continue
        # 打开当前机器连接hub
        hubNumber = open_close_sub(dev['HubNumber'], hubNumber)
        sleep(5)
        # 执行烧录
        _type, value = burn_run(dev['Device'], dowLink)
        if not _type:
            messageList.append(input_notice(
                [str(dev['Ids']), str(dev['Sign']), str(dev['Device']), str(dev['BeginName']), str(value), 'red']))
        else:
            messageList.append(input_notice(
                [str(dev['Ids']), str(dev['Sign']), str(dev['Device']), str(dev['BeginName']), str(value), 'info']))
    # 完成后企业微信通知
    if sending and burnType: wcr.message("烧录完成通知", messageList)

    if burnType:
        wait_reboot(len(devTest))
        open_sub()

    # 启动测试
    if "XPT11" in models:
        test_run(T1, sending, wcr)
    elif "XTA11" in models:
        test_run(Ace1, sending, wcr)
    else:
        logging.warning("请新建机型")
    # 启动监控
    if _type and _type2:
        # 启动测试 启动监控
        monitor_run()
        wcr.message("监控启动完成通知", [input_notice(['null', 'null', 'null', 'null', "测试监控启动成功", 'info'])])


main()
