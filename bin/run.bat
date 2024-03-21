@echo off
cd /d %~dp0
cd ..
if exist "venv" (
	echo "已经安装好python虚拟环境"
) else (
	echo "请先执行 'envir_config.bat' 安装配置Python虚拟环境 "
)
set pythonExe=%cd%\venv\Scripts\python.exe
%pythonExe% %cd%\src\main.py
pause