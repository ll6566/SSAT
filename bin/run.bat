@echo off
cd /d %~dp0
cd ..
if not exist "venv" (
	echo "����ִ�� 'envir_config.bat' ��װ����Python���⻷�� "
	cmd
)
set pythonExe=%cd%\venv\Scripts\python.exe
%pythonExe% %cd%\src\main.py
pause