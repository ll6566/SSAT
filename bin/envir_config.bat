@echo off
cd /d %~dp0
::��ʾ��ǰ·��
::echo %cd%
cd ..
::��ʾ�ϼ�Ŀ¼·��
::echo %cd%

echo ���ڴ���Python���⻷��...
python -m venv venv

echo ���ڼ������⻷����...
call "./venv/Scripts/activate"


set pythonExe=%cd%\venv\Scripts\python.exe

%pythonExe% -m pip install --upgrade pip

::echo ����ģ�����...
::set new_packages=%cd%\utils\site-packages
::set packages=%cd%\venv\Lib\site-packages
::xcopy /s /e /y /q %new_packages% %packages%

echo ������������ģ��...
pip install uiautomator2==2.16.25
pip install openpyxl==3.1.2
pip install pyserial==3.5
pip install patool==2.1.1
pip install pynput==1.7.6
pip install requests==2.31.0
pip list

echo ���ڴ������߰�...
%pythonExe% %cd%\src\unzip.py

echo ��ʼ������ɣ���

pause
