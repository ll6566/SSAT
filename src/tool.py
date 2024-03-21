# -*- encoding=utf8 -*-
import os
import sys
import shutil
import patoolib

# 追加模块搜索路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import pynput
import threading
import subprocess
from time import sleep
from src.serialwrite import relay_control
from config.config import logging, root_path
from src.read_task import eRead_dev_type, eRead_sub_com


def adb_change(dev, timeOut):
    """
    函数功能: 监控adb的变化
    返回值: True or False
    """
    # 初始化设备离线
    online1 = False
    for i in range(timeOut):
        try:
            read = os.popen("adb devices").read()
            if str(dev) in read:
                # 标识在线
                online1 = True
        except:
            continue
    for i in range(int(timeOut)):
        try:
            online2 = False
            read = os.popen("adb devices").read()
            if str(dev) in read:
                online2 = True
            # 当初始化adb状态发生变化时 返回True
            if online1 != online2:
                return True
            sleep(1)
        except:
            continue
    # 指定时间期间adb无变化这返回False
    return False


def adb_continuous(dev, timeOut):
    """
        函数功能:连续检测adb在线
        返回值: True or False
        """
    for i in range(int(timeOut)):
        print("\r确认设备状态中...(%ds)" % (timeOut - (i + 1)), end="")
        try:
            res = subprocess.run("adb devices", shell=True, stdout=subprocess.PIPE, encoding="utf-8")
            # 4秒后 device不在线则返回False
            if i >= 4 and str(dev) not in res.stdout:
                print("\r确认设备状态中...(%ds)" % (timeOut - (i + 1)))
                return False
            sleep(1)
        except:
            return False
    # 指定时间期间一直在线，则返回True
    print("\r确认设备状态中...(%ds)" % int(0))
    return True


def check_device(dev, timeOut):
    """
    函数功能: 检查device是否在线
    返回值: True or False
    """
    print("")
    for i in range(int(timeOut)):
        print("\r检查设备在线状态中...(%ds)" % (timeOut - (i + 1)), end="")
        res = subprocess.run("adb devices", shell=True, stdout=subprocess.PIPE, encoding="utf-8")
        if str(dev) in res.stdout:
            print("\r检查设备在线状态中...(%ds)" % (timeOut - (i + 1)))
            return True
        sleep(1)
    return False


# 倒计时点击Enter标识
eventsSign = False


def keyEvents():
    """启动监控键盘事件"""
    global eventsSign
    try:
        with pynput.keyboard.Events() as event:
            for i in event:  # 遍历事件
                if str(i.key) == "Key.enter":
                    raise ValueError("主动抛出异常")
    except ValueError:
        eventsSign = True


def countdown(time):
    """倒计时等待点击Enter"""
    for i in range(int(time)):
        if eventsSign:
            return
        print(
            "\r已完成设备状态查询，请手动确认是否继续执行测试任务，确认请点击【回车键Enter】。(倒计时结束自动退出)(%ds)" % (
                    time - (i + 1)), end="")
        sleep(1)
    print("\r未主动确认设备状态，已自动退出")
    exit()


def waitPid(dev, wrap, timeOut):
    for i in range(timeOut):
        sleep(1)
        print("\r检查{}进程中...({}s)".format(wrap, (timeOut - (i + 1))), end="")
        try:
            read = os.popen('adb -s {} shell "ps | grep {}"'.format(str(dev), wrap)).read()
            if read != "":
                return read
        except Exception as e:
            print(e)
            continue

    print("")
    return ""


def waitEnter(time):
    """启动预检"""
    print("正在预检设备状态中....")
    # 检查设备在线
    tDevList, fDevList = eRead_dev_type()
    for pri in range(3):
        print("\n")
    print("【设备状态预检】: ")
    print("设备device                物理机位置    测试项目    hub端口    自动化步骤")
    print("\n")
    for td in tDevList:
        print(td['设备device'] + "       " + td['物理机位置'] + "     " + td['测试项目'] + "      " + str(
            td['hub端口']) + "        " + td['自动化步骤'] + "            ")
    print("\n")
    for fd in fDevList:
        print(fd['设备device'] + "       " + fd['物理机位置'] + "     " + fd['测试项目'] + "      " + str(
            fd['hub端口']) + "        " + fd['自动化步骤'] + "            ")
    print("\n")
    print("共计：\033[1;32m在线【{}】\033[0m  \033[1;31m离线【{}】\033[0m".format(len(tDevList), len(fDevList)))
    for pri in range(3): print("\n")
    # 启动监控键盘事件线程
    tke = threading.Thread(target=keyEvents)
    # 设置守护线程，主线程执行完毕后，自动结束子线程
    tke.daemon = True
    tke.start()
    # 启动倒计时
    countdown(time)


def input_notice(info):
    cnt = {
        "Ids": info[0],
        "label": info[1],
        "Device": info[2],
        "BeginName": info[3],
        "Message": info[4],
        "type": info[5]
    }
    return cnt


def open_close_sub(devHub, hubNumber):
    com1, com2 = eRead_sub_com()
    if str(devHub) == "1":
        if hubNumber != 1:
            # 关闭hub1
            relay_control(com1, 0)
            # 关闭hub2
            relay_control(com2, 0)
            sleep(2)
            # 打开hub1
            relay_control(com1, 1)
            return 1
    else:
        if hubNumber != 2:
            # 关闭hub1
            relay_control(com1, 0)
            # 关闭hub2
            relay_control(com2, 0)
            sleep(2)
            # 打开hub2
            relay_control(com2, 1)
            return 2


def open_sub():
    """重新打开两个hub"""
    com1, com2 = eRead_sub_com()
    relay_control(com1)
    relay_control(com2)
    for i in range(5):
        sleep(1)
        print("\r重新开关usbHub中.....%s" % str(5 - (i + 1)), end="")
    relay_control(com1, 1)
    relay_control(com2, 1)
    print("")
    sleep(2)


def inspect_screen_state(dev):
    """
    函数功能: 检查device是否亮屏
    返回值: True or False
    """
    res = subprocess.run("adb -s {} shell dumpsys window policy".format(dev), shell=True, stdout=subprocess.PIPE,
                         encoding="utf-8").stdout
    if 'SCREEN_STATE_ON' in res:
        return True
    else:
        return False


def download_software(downloadLink):
    """
    下载软件方法
    downloadLink 软件链接
    """
    patList = os.environ.get('Path')
    wgetPath = root_path + "utils\\wget\\bin"
    if wgetPath not in patList:
        logging.info("正在将wget加入系统环境变量中...")
        os.environ['Path'] = os.pathsep.join([wgetPath, patList])

    # 软件文件名称
    fileName = root_path + "data\\" + downloadLink.split('/')[-1]
    # 软件文件名称去除.7z
    softwarePath = fileName.split('.7z')[0]

    download = 'wget {} -P {} --no-check-certificate'.format(downloadLink, root_path + "data")
    try:
        if not os.path.exists(fileName):
            logging.info("软件未下载，开始下载...")
            subprocess.run(download, shell=True)
    except:
        return False, "下载软件失败"

    # 检查是否存在此文件，存在递归删除目录下所有文件
    if os.path.exists(softwarePath):
        logging.info("正在删除旧文件...")
        shutil.rmtree(softwarePath)

    try:
        logging.info("正在解压文件....")
        patoolib.extract_archive(fileName, outdir=root_path + "data")
    except Exception as e:
        print(e)
        return False, "解压文件失败"
    if os.path.exists(softwarePath + '\\items.ini'):
        logging.info("正在修改items文件.....")
        with open(softwarePath + '\\items.ini', 'r') as f:
            line_list = f.readlines()
        line_list.insert(line_list.index("items.end\n"), "persist.sys.seewo.develop.adb                   1\n")
        line_list.insert(line_list.index("items.end\n"), "ro.seewo.usb.adb                    1\n")
        with open(softwarePath + '\\items.ini', 'w', newline='\n') as f:
            f.writelines(line_list)

        # logging.info("正在删除Checksum.ini文件....")
        # if os.path.exists(softwarePath + '\\Checksum.ini'):
        #     os.remove(softwarePath + '\\Checksum.ini')
    return True, softwarePath


def renew_file(link):
    """
    更新文件
    """
    patList = os.environ.get('Path')
    wgetPath = root_path + "utils\\wget\\bin"
    if wgetPath not in patList:
        os.environ['Path'] = os.pathsep.join([wgetPath, patList])
    # 定义项目文件的根目录
    filePath = os.path.dirname(os.path.dirname(root_path))
    download = 'wget {} -P {} --no-check-certificate'.format(link, filePath)
    # 压缩文件路径
    compressFilePath = filePath + "\\" + str(link).split('/')[-1]
    try:
        print(compressFilePath)
        if not os.path.exists(compressFilePath):
            logging.info("软件未下载，开始下载...")
            subprocess.run(download, shell=True)
    except:
        return False, "下载软件失败"

    try:
        logging.info("正在解压文件....")
        patoolib.extract_archive(compressFilePath, outdir=filePath)
    except Exception as e:
        print(e)
        return False, "解压文件失败"