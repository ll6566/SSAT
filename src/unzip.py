import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.tool import renew_file

# 下载解压工具
renew_file("https://github.com/ll6566/SSAT/releases/download/v2.2.2/utils.zip")
# if os.path.exists(sys.argv[1] + r"\utils"):
#     shutil.rmtree(sys.argv[1] + r"\utils")
# try:
#     patoolib.extract_archive(sys.argv[1] + r"\toolFile\utils.zip", outdir=sys.argv[1])
# except Exception as e:
#     print(e)
#     print("工具解压失败！！")
#     exit()