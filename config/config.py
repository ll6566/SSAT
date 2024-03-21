# -*- encoding=utf8 -*-
import logging
import os
import sys
from time import sleep

# 追加模块搜索路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import uiautomator2 as u2
# 根目录路径
root_path = str(os.path.dirname(sys.executable)).replace(r"venv\Scripts", "")
if not os.path.exists(root_path + 'logs'):
    os.mkdir(root_path + 'logs')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s-%(levelname)s_%(message)s')
file_handler = logging.FileHandler(root_path + 'logs\\logs.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)
logging = logging


class U2:
    """
    重写u2
    """
    @staticmethod
    def connect(dev):
        try:
            d = u2.connect(dev)
            # 诱发错误事件
            d(text="test").exists(timeout=1)
            return u2.connect(dev)
        except:
            os.system("adb -s %s uninstall com.github.uiautomator" % str(dev))
        finally:
            sleep(2)
            return u2.connect(dev)
