@echo off
cd /d %~dp0
cd ..
if not exist "venv" (
	echo "请先执行 'envir_config.bat' 安装配置Python虚拟环境 "
	cmd
)
set pythonExe=%cd%\venv\Scripts\python.exe
%pythonExe% %cd%\src\main.py
pause