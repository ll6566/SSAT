import os
import sys
import queue
import threading
from time import sleep


# 追加模块搜索路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.tool import cmd_to_file, query_update_folder, getMtkLog_keywords
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
    flashCmd = flashTool + ' -c firmware-upgrade -b -d {} -s {}'.format(daFile, scatterFile)

    # 执行cmd命令并输出txt
    cmdType, value = cmd_to_file(flashCmd, "flashRead.txt", 300)
    if not cmdType:
        logging.error("%s 烧写版本超时，进行下一台设备刷机" % dev)
        message.put("烧写版本超时")
        _type.put(False)
        return

    # 获取MTK最新日志
    newTimeFolder = query_update_folder(r'C:\ProgramData\SP_FT_Logs')

    if newTimeFolder is None:
        logging.warning("未能获取到MTK烧录器中最新的日志文件")
    else:
        # 检查是否烧录成功
        if not getMtkLog_keywords(newTimeFolder):
            logging.error("%s 烧写失败，没找到烧录成功关键词，进行下一台设备刷机" % dev)
            message.put("烧写失败，没找到烧录成功关键词")
            _type.put(False)
            return

    logging.info("烧写完成%s" % str(dev))
    message.put("烧写成功")
    _type.put(True)


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
    logging.info("%s::正在进入烧录模式【重启】..." % dev)
    os.system('adb -s %s shell reboot -p' % dev)
    logging.info("%s::烧录中...." % dev)

    t.join()

    logging.info("%s烧录完成正在重启中...." % dev)
    sleep(10)
    return _type.get(), message.get()


def burn_run(dev, dowLink):
    """
    MTK & 展锐烧录方法
    """
    zr = ["XTW31"]
    mtk = ["XPT11", "XTA11"]
    models = str(os.popen("adb -s {} shell getprop ro.product.model".format(str(dev))).read()).replace(" ", "").replace(
        "\n", "")
    if models in zr:
        logging.error("还没添加展锐烧录")
        exit()
    elif models in mtk:
        #  烧录
        _type, value = mtk_burn_run(dev, dowLink)
        return _type, value
    else:
        logging.error("刷机机型方法还没添加")
        exit()
