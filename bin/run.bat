@echo off
cd /d %~dp0
cd ..
if exist "venv" (
	echo "�Ѿ���װ��python���⻷��"
) else (
	echo "����ִ�� 'envir_config.bat' ��װ����Python���⻷�� "
)
set pythonExe=%cd%\venv\Scripts\python.exe
%pythonExe% %cd%\src\main.py
pause