@echo off
cd /d %~dp0
::显示当前路径
::echo %cd%
cd ..
::显示上级目录路径
::echo %cd%

echo 正在创建Python虚拟环境...
python -m venv venv

echo 正在激活虚拟环境中...
call "./venv/Scripts/activate"


set pythonExe=%cd%\venv\Scripts\python.exe

%pythonExe% -m pip install --upgrade pip

::echo 复制模块包中...
::set new_packages=%cd%\utils\site-packages
::set packages=%cd%\venv\Lib\site-packages
::xcopy /s /e /y /q %new_packages% %packages%

echo 正在下载三方模块...
pip install uiautomator2==2.16.25
pip install openpyxl==3.1.2
pip install pyserial==3.5
pip install patool==2.1.1
pip install pynput==1.7.6
pip install requests==2.31.0
pip list

echo 正在创建工具包...
%pythonExe% %cd%\src\unzip.py

echo 初始化已完成！！

pause
