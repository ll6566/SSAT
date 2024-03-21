import os
import sys
import queue
import threading
import subprocess
from time import sleep

# 追加模块搜索路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from config.config import root_path, logging


def mtk_flash(dev, message, _type, softwarePath):
    """
    烧录方法
    dev 设备device
    message 烧录消息
    _type 烧录状态
    softwarePath 烧录软件地址
    """
    # MTK烧录工具Path
    flashTool = root_path + r"utils\SP_Flash_Tool\flash_tool.exe"
    # MTK烧录工具配置文件binPath
    daFile = root_path + r"utils\SP_Flash_Tool\MTK_ALLInOne_DA.bin"
    # 软件Path
    scatterFile = softwarePath + '\\MT6771_Android_scatter.txt'
    # 执行烧录命令
    # -c firmware-upgrade -b -d {} -s {} --disable_storage_life_cycle_check
    flashCmd = flashTool + ' -c firmware-upgrade -b -d {} -s {}'.format(daFile,scatterFile)
    process = subprocess.Popen(flashCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logging.info("烧录指令启动..")
    try:
        output, unused_err = process.communicate(timeout=300)
        logging.info("烧写完成%s" % str(output.decode()))
        message.put("烧写完成")
        _type.put(True)
    except Exception as e:
        process.kill()
        logging.error("%s 烧写版本超时，进行下一台设备刷机" % dev)
        logging.error("%s 烧录失败信息：%s" % (dev, e))
        message.put("烧写版本超时")
        _type.put(False)


def mtk_burn_run(dev, softwarePath):
    message = queue.Queue()
    _type = queue.Queue()
    # 烧录启动
    t = threading.Thread(target=mtk_flash, args=(dev, message, _type, softwarePath,))
    t.start()

    # 查看刷机时机器屏幕是否唤醒
    res = os.popen("adb -s {} shell dumpsys window policy".format(dev)).read()
    if 'SCREEN_STATE_ON' not in res: os.system('adb -s %s shell input keyevent 26' % dev)

    sleep(8)
    logging.info("%s重启,正在进入烧录模式..." % dev)
    os.system('adb -s %s shell reboot -p' % dev)
    logging.info("%s烧录中...." % dev)

    t.join()

    logging.info("%s烧录完成正在重启中...." % dev)
    sleep(10)
    return _type.get(), message.get()


def burn_run(dev,dowLink):
    """
    MTK & 展锐烧录方法
    """
    zr = ["XTW31"]
    mtk = ["XPT11", "XTA11"]
    models = str(os.popen("adb -s {} shell getprop ro.product.model".format(str(dev))).read()).replace(" ", "").replace("\n", "")
    if models in zr:
        print("还没添加展锐烧录")
        exit()
    elif models in mtk:
        #  烧录
        _type, value = mtk_burn_run(dev, dowLink)
        return _type, value
    else:
        print("刷机机型方法还没添加")
        exit()
