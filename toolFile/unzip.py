import sys
import os
import patoolib
import shutil

if os.path.exists(sys.argv[1] + r"\utils"):
    shutil.rmtree(sys.argv[1] + r"\utils")
try:
    patoolib.extract_archive(sys.argv[1] + r"\toolFile\utils.zip", outdir=sys.argv[1])
except Exception as e:
    print(e)
    print("工具解压失败！！")
    exit()