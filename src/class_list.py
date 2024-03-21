# -*- encoding=utf8 -*-
import os
import sys
import subprocess

# 追加模块搜索路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from time import sleep
from config.config import U2 as u2
from config.config import logging, root_path
from src.tool import check_device, inspect_screen_state, waitPid


class AutoTest(object):
    def __init__(self, device, beginName, ssid, password, account, preconditions=10):

        # monkey测试路径
        self.monkeyBlackListPath = root_path + r"utils\monkey\black_list.txt"
        self.monkeyPath = root_path + r"utils\monkey\monkey测试.bat"
        self.monkeySlideScreenPath = root_path + r"utils\monkey\频繁滑屏操作.bat"
        self.monkeyClickPath = root_path + r"utils\monkey\频繁点击操作.bat"
        self.monkeyAppPath = root_path + r"utils\monkey\频繁APP切换.bat"

        # 安装app路径
        self.appPathList = root_path + r'utils\top50App\50AppList'
        self.appListExcelPath = root_path + r'utils\top50App\all_app_list_50.xlsx'

        # 安装应用list
        self.appPaths = []
        for root, dirs, files in os.walk(self.appPathList):
            self.appPaths = [os.path.join(root, file) for file in files]
        # adb
        self.device = device
        # 测试任务
        self.beginName = beginName
        # WIFI SSID
        self.ssid = ssid
        # WIFI PASSWORD
        self.password = password
        self.text_sougou = ["我知道了", "允许", "同意并继续"]
        # login账号
        self.account = account
        # app安装数量
        self.preconditions = preconditions

    def stop(self, testSign):
        """
        停止测试方法
        """
        # 点掉ACE重启后弹出的日志警告
        os.system("adb -s %s shell input tap 1361 705" % self.device)
        if testSign == 1:
            try:
                os.system("adb -s %s shell am start com.elink.autotest/.MainActivity" % self.device)
            except:
                return False
        else:
            try:
                os.system("adb -s %s shell am start com.emdoor.pressure.tester/.MainActivity" % self.device)
            except:
                return False
        sleep(1)
        os.system("adb -s %s shell input tap 1200 1150" % self.device)
        os.system("adb -s %s shell input tap 1200 1150" % self.device)
        os.system("adb -s %s shell input tap 1200 1150" % self.device)
        sleep(1)
        for i in range(3):
            if not check_device(self.device, 200): return False
            try:
                d = u2.connect(self.device)
                if d(text="退出应用").exists(): d(text="退出应用").click()
                break
            except:
                sleep(10)
                continue
        return True

    def stop_test(self):
        """
        停止测试方法
        """
        logging.info("正在停止{}的测试任务，{}".format(self.device, self.beginName))
        if "monkey" in self.beginName:
            if not check_device(self.device, 200): return False, "停止测试失败，设备不在线"
            read = waitPid(self.device, "monkey", 60)
            monkeyPids = []
            for i in read.split("\n"):
                if len(i.split(" ")) > 1:
                    monkeyPids.append(list(filter(lambda x: x != "", i.split(" ")))[1])
            for monkeyPid in monkeyPids:
                os.popen("adb -s {} shell kill {}".format(self.device, str(monkeyPid)))

            if waitPid(self.device, "monkey", 1) == "":
                os.system("adb -s %s shell input keyevent 3" % self.device)
                return True, "停止测试成功"

        for stopNumber in range(3):
            if not check_device(self.device, 200): return False, "停止测试失败，设备不在线"
            if not inspect_screen_state(self.device): os.system('adb -s {} shell input keyevent 26'.format(self.device))
            # 平板压力测试2可测试项目
            stopTest2 = ['重启+相机', 'CAMERA老化', '频繁相机切换', '频繁相机拍照', '频繁相机录像', '频繁开关相机',
                         '相机_MONKEY', 'GPU测试']

            # 平板压力测试2包
            pressure = os.popen('adb -s %s shell "pm list packages | grep com.emdoor.pressure.tester"' % str(self.device)).read()

            testSign = 1
            # GPU测试停止方法
            if self.beginName == "GPU测试":
                self.stop(testSign)
                return True, "停止{}测试成功".format(str(self.beginName))
            # 平板压力测试1停止测试
            elif self.beginName not in stopTest2 or pressure == "":
                read = waitPid(self.device, "com.elink.autotest", 60)
            else:
                testSign = 2
                read = waitPid(self.device, "com.emdoor.pressure.tester", 60)
            """
            实际使用中，情况多变，可能会多等待60-120s，但是能够确保已经正常将测试停止
            """
            if read != "":
                try:
                    # 如停止时出现异常则重新停止，重试3次截止
                    if not self.stop(testSign): continue
                    break
                except Exception as e:
                    logging.error(e)
                    continue
            else:
                return False, "停止{}测试失败，获取不到“平板压力测试工具”进程".format(str(self.beginName))
        return True, "停止{}测试成功".format(str(self.beginName))

    def start(self):
        logging.info("启动测试中...")
        if "monkey" in self.beginName:
            self.run_monkey_test()
            return True, str(self.beginName) + "启动成功"
        self.run_app_test()
        return True, str(self.beginName) + "启动成功"

    def skip_guide(self):
        """
        跳过初始引导、连接wifi
        """
        # 检查屏幕是否点亮
        read = os.popen("adb -s %s shell dumpsys window policy" % self.device).read()
        if 'SCREEN_STATE_ON' not in read: os.system('adb -s %s shell input keyevent 26' % self.device)

        d = u2.connect(self.device)

        # 同意第一个协议(欢迎使用希沃学习机)
        for i in range(5):
            if d(resourceId="com.seewo.studystation.launcher:id/privacyAgreeCheckBox").exists:
                d(resourceId="com.seewo.studystation.launcher:id/privacyAgreeCheckBox").click()
                sleep(2)
            if d(resourceId="com.seewo.studystation.launcher:id/privacyAgreeButton").exists:
                d(resourceId="com.seewo.studystation.launcher:id/privacyAgreeButton").click()
                sleep(2)
            if d(resourceId="com.seewo.studystation.launcher:id/textViewAgree").exists:
                d(resourceId="com.seewo.studystation.launcher:id/textViewAgree").click()
                sleep(2)
            else:
                break

        # 等待播放完动画，点击现在出发
        sleep(30)
        d(text="现在出发").wait(timeout=80)
        if d(text="现在出发").exists: d(text="现在出发").click()
        sleep(2)

        # 连接WIFI
        for runIndex in range(3):
            logging.info("正在连接WIFI【{}】".format(str(runIndex + 1)))
            for i in range(5):
                try:
                    if not d(text=self.ssid).exists(timeout=5):
                        d.swipe(0.5, 0.6, 0.2, 0.2)
                        sleep(1)
                        continue
                except Exception as e:
                    logging.warning("出错了！测试仍在继续：")
                    logging.warning(e)
                    continue
                try:
                    d(text=self.ssid).click()
                except Exception as e:
                    logging.warning("出错了！测试仍在继续：")
                    logging.warning(e)
                    continue
                sleep(5)
                d(text="请输入密码").click()
                sleep(2)
                # 点掉搜狗输入法弹框
                for sgc in range(3):
                    for text in self.text_sougou:
                        if d(text=text).exists:
                            d(text=text).click()
                            sleep(2)
                            break

                d(text="请输入密码").set_text(self.password)
                sleep(2)
                d.press('back')
                sleep(2)
                d(resourceId="com.seewo.eclass.startupsettings:id/textViewPositive").click(offset=(0.5, 0.2))
                sleep(2)
                break

            if not d(resourceId="com.seewo.eclass.startupsettings:id/netSettingNextButton").exists(timeout=30):
                logging.error("WIFI连接失败，正在重新连接WIFI(3/{})...".format(str(runIndex + 2)))
                # 重试
                for sw in range(10):
                    d.swipe(0.5, 0.6, 0.8, 0.8)
                continue

            d(resourceId="com.seewo.eclass.startupsettings:id/netSettingNextButton").click()
            sleep(3)
            return True, "跳过引导、连接WIFI成功"
        return False, "连接WIFI失败"

    def login_account(self):
        d = u2.connect(self.device)
        # 判断是否有账号没有账号自动登录工厂模式
        if self.account is None:
            d(resourceId="com.seewo.studystation.launcher:id/loadingContainView").wait_gone(timeout=60)
            sleep(3)
            d(text="密码登录").click()
            sleep(3)
            d(text="请输入密码").click()
            sleep(3)
            # 点掉搜狗输入法弹框
            for sgc in range(3):
                for text in self.text_sougou:
                    if d(text=text).exists:
                        d(text=text).click()
                        sleep(2)
                        break
            d(text="请输入密码").set_text("0123345")
            sleep(3)
            d(resourceId="com.seewo.studystation.launcher:id/imageButtonLogin").click()
            sleep(5)
            return True, "登录账号成功"

        # 登录正式账号
        d(resourceId="com.seewo.studystation.launcher:id/loadingContainView").wait_gone(timeout=60)
        sleep(2)
        d(text="密码登录").click()
        sleep(2)
        d(text="请输入家长手机号").click()
        # 点掉搜狗输入法弹框
        for sgc in range(3):
            for text in self.text_sougou:
                if d(text=text).exists:
                    d(text=text).click()
                    sleep(2)
                    break
        sleep(2)
        d(text="请输入家长手机号").set_text(self.account)
        sleep(2)
        d(text="请输入密码").click()
        sleep(2)
        # 点掉搜狗输入法弹框
        for sgc in range(3):
            for text in self.text_sougou:
                if d(text=text).exists:
                    d(text=text).click()
                    sleep(2)
                    break
        d(text="请输入密码").set_text("Seewo@123456")
        sleep(2)
        d(resourceId="com.seewo.studystation.launcher:id/privacyCheckbox").click()
        sleep(2)
        d.press('back')
        sleep(2)
        d(resourceId="com.seewo.studystation.launcher:id/imageButtonLogin").click()
        sleep(2)
        if not d(text="密码登陆"):
            logging.info("账号登陆成功")
            return True, "账号登陆成功"
        else:
            logging.info("账号登陆失败")
            return False, "账号登陆失败"

    def close_app_control(self):
        logging.info("正在关闭应用管控....（期间会机器重启）")
        cmd_close_app_control = "adb -s {} shell am broadcast -a com.seewo.action.APP_PERMISSION_CONTROL --ez enable " \
                                "false com.cvte.logtool".format(self.device)
        subprocess.run(cmd_close_app_control, shell=True)
        sleep(2)
        subprocess.run("adb -s {} reboot".format(self.device), shell=True)
        sleep(5)
        return True

    def login_open_setting(self):
        """
        【次函数修改概率较高】
        登录账号后开启设置（护眼助手等）
        """
        d = u2.connect()
        sleep(2)
        for forIndex in range(3):
            try:
                # logging.info("开启纸质护眼")
                if d(resourceId="com.seewo.studystation.guide:id/paper_button_next").exists(timeout=10):
                    d(resourceId="com.seewo.studystation.guide:id/paper_button_next").click()

                # logging.info("开启距离监测")
                if d(resourceId="com.seewo.studystation.guide:id/distance_button_next").exists(timeout=10):
                    d(resourceId="com.seewo.studystation.guide:id/distance_button_next").click()
                    sleep(2)
                    if d(resourceId="com.seewo.studystation.sitting:id/privacyAgreeCheckBox").exists(timeout=10):
                        d(resourceId="com.seewo.studystation.sitting:id/privacyAgreeCheckBox").click()
                        sleep(2)
                        d(resourceId="com.seewo.studystation.sitting:id/privacySwitcher")[0].click()
                        sleep(2)
                        if d(resourceId="com.seewo.studystation.sitting:id/privacySwitcher").count > 1:
                            d(resourceId="com.seewo.studystation.sitting:id/privacySwitcher")[1].click()
                            sleep(2)
                        d(text="同意").click()

                # logging.info("开启坐姿监测")
                if d(resourceId="com.seewo.studystation.guide:id/postureOpenButton").exists(timeout=10):
                    d(resourceId="com.seewo.studystation.guide:id/postureOpenButton").click()
                    sleep(3)
                    if d(resourceId="com.seewo.studystation.sitting:id/privacyAgreeCheckBox").exists(timeout=10):
                        d(resourceId="com.seewo.studystation.sitting:id/privacyAgreeCheckBox").click()
                        sleep(2)
                        d(resourceId="com.seewo.studystation.sitting:id/privacySwitcher")[0].click()
                        sleep(2)
                        d(resourceId="com.seewo.studystation.sitting:id/privacySwitcher")[1].click()
                        sleep(2)
                        d(text="同意").click()

                # logging.info("开启坐姿监测")
                if d(resourceId="com.seewo.studystation.guide:id/keepOpenButton").exists(timeout=10):
                    d(resourceId="com.seewo.studystation.guide:id/keepOpenButton").click()
                    sleep(3)
                    if d(resourceId="com.seewo.studystation.keep:id/privacyAgreeCheckBox").exists(timeout=10):
                        d(resourceId="com.seewo.studystation.keep:id/privacyAgreeCheckBox").click()
                        sleep(2)
                        d(resourceId="com.seewo.studystation.keep:id/privacySwitcher")[0].click()
                        sleep(2)
                        d(resourceId="com.seewo.studystation.keep:id/privacySwitcher")[1].click()
                        sleep(2)
                        d(text="同意").click()

                # logging.info("开启语音唤醒")
                if d(resourceId="com.seewo.studystation.guide:id/speechOpenButton").exists(timeout=10):
                    d(resourceId="com.seewo.studystation.guide:id/speechOpenButton").click()
                    sleep(3)
                    if d(resourceId="com.seewo.studystation.speech:id/privacyAgreeCheckBox").exists(timeout=10):
                        d(resourceId="com.seewo.studystation.speech:id/privacyAgreeCheckBox").click()
                        sleep(2)
                        d(resourceId="com.seewo.studystation.speech:id/privacySwitcher")[0].click()
                        sleep(2)
                        d(resourceId="com.seewo.studystation.speech:id/privacySwitcher")[1].click()
                        sleep(2)
                        d(text="同意").click()
                break
            except uiautomator2.exceptions.GatewayError as ueg:
                logging.error(ueg)
                logging.error("登录账号后设置推荐设置失败，重试")
                continue

        if d(text="跳过").exists(timeout=5):
            d(text="跳过").click()
        self.skip_guide_login()
        return True, "登录账号后设置推荐功能成功"

    def skip_guide_login(self):
        """
        登录账号后打开日志等
        """
        d = u2.connect(self.device)
        sleep(3)
        d.press('back')
        sleep(2)
        d.press('home')
        sleep(2)
        logging.info("正在打开MTK日志...")
        d.shell("am start -n com.debug.loggerui/.MainActivity")
        sleep(3)
        d(resourceId="com.debug.loggerui:id/startStopToggleButton").click()
        sleep(6)
        if d(text="确定").exists:
            d(text="确定").click()
        sleep(2)
        d.press('home')

    @staticmethod
    def installApp(Device, App):
        cmdi = "adb -s {} install {}".format(Device, App)
        res = False
        process = subprocess.Popen(cmdi, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            output, unused_err = process.communicate(timeout=300)
            logging.info("安装完成%s" % str(output.decode("utf-8")))
            res = True
        except Exception as e:
            process.kill()
            logging.error("安装失败,安装超时！%s" % e)
        finally:
            return res

    def preconditions_set(self):
        if "无" in str(self.preconditions): return True
        # 安装APP
        if "安装三方APP" in str(self.preconditions):
            for i in range(int(str(self.preconditions).split(":")[1])):
                try:
                    logging.info("************开始安装第 {} 个apk**************".format(str(i + 1)))
                    if not self.installApp(self.device, self.appPaths[i]): self.installApp(self.device,
                                                                                           self.appPaths[i])
                except:
                    logging.error("启动monkey测试时安装app数量超出拥有数量")
                    break
        elif "电量控制3~10" in str(self.preconditions):
            d = u2.connect(self.device)
            if d(text='确定').exists(): d(text='确定').click()

            # 打开平板压力测试工具
            d.shell("am start com.emdoor.pressure.tester/.MainActivity")
            d(text="平板压力测试2").wait(timeout=10.0)
            # 设置允许充电量
            d(resourceId="com.emdoor.pressure.tester:id/setValue1").click()
            sleep(1)
            d(text="3").click()
            sleep(1)
            d(text="确定").click()
            # 设置禁充电量
            d(resourceId="com.emdoor.pressure.tester:id/setValue2").click()
            sleep(1)
            d(text="1").click()
            sleep(1)
            d(text="0").click()
            sleep(1)
            d(text="确定").click()
            # 勾选
            d(resourceId="com.emdoor.pressure.tester:id/boxBattery").click()
            sleep(1)
            d(text="电池电量管控").click()
            sleep(1)
            d.press('back')
        return True

    def run_monkey_test(self):
        """
        启动Monkey测试
        """
        # 启动monkey测试
        if self.beginName == "monkey随机":
            subprocess.Popen([self.monkeyPath, self.device, self.monkeyBlackListPath])
            return True, "monkey随机测试启动成功"
        elif self.beginName == "monkey滑动":
            subprocess.Popen([self.monkeySlideScreenPath, self.device, self.monkeyBlackListPath])
            return True, "monkey滑动测试启动成功"
        elif self.beginName == "monkey点击":
            subprocess.Popen([self.monkeyClickPath, self.device, self.monkeyBlackListPath])
            return True, "monkey点击测试启动成功"
        elif self.beginName == "monkeyApp":
            subprocess.Popen([self.monkeyAppPath, self.device, self.monkeyBlackListPath])
            return True, "monkeyApp测试启动成功"

    def set_test_time(self):
        """
        启动项目增加时长滑动坐标
        """
        return 400, 1150, 400, 1000

    def set_test_gpu(self, d):
        # 将应用设置为全屏
        # 打开设置
        d.shell("am start com.seewo.eclass.settings")
        # 滑动到应用程序
        for i in range(5):
            if d(text="应用程序").exists(): break
            d.swipe_ext('up', box=(200, 100, 200, 900))
        if d(text="应用程序").exists(): d(text="应用程序").click()
        sleep(1)
        if d(text="应用列表").exists(): d(text="应用列表").click()
        sleep(1)
        for i in range(5):
            if d(text="StabilityTest").exists(): break
            d.swipe_ext('up', scale=0.9)
        d(text="StabilityTest").click()
        sleep(1)
        d(text="横屏").right().click()
        sleep(2)
        d.press('home')
        sleep(2)

    def run_app_test(self):
        d = u2.connect(self.device)
        if d(text='确定').exists(): d(text='确定').click()
        # GPU测试应用安装
        if self.beginName == "GPU测试":
            # 安装测试APP
            gpuTestBoot = root_path + 'utils\StabilityTest_2.7.apk'
            os.system("adb -s {} install {}".format(self.device, gpuTestBoot))
            self.set_test_gpu(d)
        # 打开平板压力测试工具2
        d.shell("am start com.emdoor.pressure.tester/.MainActivity")
        sleep(3)
        if d(text="平板压力测试2").exists():
            # 滚动出测试项
            for i in range(5):
                if d(text=self.beginName).exists(): break
                d.swipe_ext('up', scale=0.9)

        # 测试工具2没找到的来测试工具1找
        if not d(text=self.beginName).exists():
            if d(text="退出应用").exists(): d(text="退出应用").click()
            sleep(2)
            # 打开平板压力测试工具1
            d.shell("am start com.elink.autotest/.MainActivity")
            sleep(4)
            # 滚动出测试项
            for i in range(10):
                if d(text=self.beginName).exists(): break
                d.swipe_ext('up', scale=0.9)
        if not d(text=self.beginName).exists():
            if d(text="退出应用").exists(): d(text="退出应用").click()
            return False, "启动测试失败,测试工具1 && 测试工具2中均未找到测试项"
        appTestList = [
            {"CAMERA老化": "com.elink.autotest:id/setCamera6"},
            {"频繁相机切换": "com.elink.autotest:id/set3Camera"},
            {"填空间测试": "com.elink.autotest:id/setSdcardRWSpace"},
            {"LCD+频繁录播老化": "com.elink.autotest:id/setLcd"},
            {"多线程读写测试": "com.elink.autotest:id/setSdcardRWMulti"},
            {"频繁音频": "com.elink.autotest:id/setAudio"},
            {"频繁视频": "com.elink.autotest:id/setVideo"},
            {"大文件读写测试": "com.elink.autotest:id/setSdcardRWBig"},
            {"小文件读写测试": "com.elink.autotest:id/setSdcardRWSmall"},
            {"单文件读写测试": "com.elink.autotest:id/setSdcardRW"}
        ]
        # 设置测试时长
        for app in appTestList:
            for key, value in app.items():
                if key == self.beginName:
                    sleep(2)
                    # 设置测试时间
                    if d(resourceId=value).exists():
                        d(resourceId=value).click()
                        # 24 * 7 / 2 = 84
                        sa, sb, sc, ad = self.set_test_time()
                        for i in range(84):
                            d.swipe(sa, sb, sc, ad)
                        d(resourceId="com.elink.autotest:id/ok_button").click()
        sleep(2)
        # 点击测试
        if d(text=self.beginName).exists():
            d(text=self.beginName).click()
        sleep(4)
        if d(text="确定").exists(): d(text="确定").click()
        sleep(3)
        if self.beginName == "GPU测试":
            sleep(1)
            if d(text="CONTINUE").exists(): d(text="CONTINUE").click()
            sleep(1)
            if d(text="CPU+GPU STABILITY TEST").exists(): d(text="CPU+GPU STABILITY TEST").click()
            sleep(1)
            if d(text="PROCEED").exists(): d(text="PROCEED").click()
        try:
            if d(text='开始').exists(): d(text='开始').click()
            if d(text='继续').exists(): d(text='复位').click()
            if d(text='开始').exists(): d(text='开始').click()
        except u2.exceptions.UiObjectNotFoundError:
            logging.error("%s启动测试失败" % self.device)
            return False, "启动测试失败"
        return True, "app测试启动成功"

    def restore_factory(self):
        """
        恢复出厂设置
        """
        os.system("adb -s %s shell am start com.android.settings" % str(self.device))
        sleep(2)
        d = u2.connect(str(self.device))
        if d(text="确定").exists(): d(text="确定").click()
        for i in range(3):
            d.swipe_ext('up', scale=0.9)
            if d(text="系统").exists(): break

        d(text="系统").click()
        sleep(1)
        d(text="重置选项").click()
        sleep(1)
        d(text="清除所有数据（恢复出厂设置）").click()
        sleep(1)
        d(className="android.widget.Button").click()
        sleep(1)
        d(className="android.widget.Button").click()
        return True, "恢复出厂设置完成"


class T1(AutoTest):
    def set_test_gpu(self, d=None):
        pass

    pass


class Ace1(AutoTest):
    """
    需要修改方法为有如下
    烧录方法
    flash()
    启动烧录方法
    burn_run()
    停止测试方法
    stop()

    """

    def login_account(self):
        d = u2.connect(self.device)
        # 判断是否有账号没有账号自动登录工厂模式
        if self.account is None:
            d(resourceId="com.seewo.studystation.launcher:id/loadingContainView").wait_gone(timeout=60)
            sleep(3)
            d(text="密码登录").click()
            sleep(3)
            d(text="请输入密码").click()
            sleep(3)
            # 点掉搜狗输入法弹框
            for sgc in range(3):
                for text in self.text_sougou:
                    if d(text=text).exists:
                        d(text=text).click()
                        sleep(2)
                        break
            d(text="请输入密码").set_text("0123345")
            d.press('back')
            sleep(2)
            d(resourceId="com.seewo.studystation.launcher:id/imageButtonLogin").click()
            sleep(5)
            return True, "登录账号成功"

        # 登录正式账号
        d(resourceId="com.seewo.studystation.launcher:id/loadingContainView").wait_gone(timeout=60)
        sleep(2)
        d(text="密码登录").click()
        sleep(2)
        d(text="请输入家长手机号").click()
        # 点掉搜狗输入法弹框
        for sgc in range(3):
            for text in self.text_sougou:
                if d(text=text).exists:
                    d(text=text).click()
                    sleep(2)
                    break
        sleep(2)
        d(text="请输入家长手机号").set_text(self.account)
        sleep(2)
        d(text="请输入密码").click()
        sleep(2)
        # 点掉搜狗输入法弹框
        for sgc in range(3):
            for text in self.text_sougou:
                if d(text=text).exists:
                    d(text=text).click()
                    sleep(2)
                    break
        d(text="请输入密码").set_text("Seewo@123456")
        sleep(2)
        d.press('back')
        sleep(2)
        d(resourceId="com.seewo.studystation.launcher:id/privacyCheckbox").click()
        sleep(2)
        d(resourceId="com.seewo.studystation.launcher:id/imageButtonLogin").click()
        sleep(2)
        if not d(text="密码登陆"):
            logging.info("账号登陆成功")
            return True, "账号登陆成功"
        else:
            logging.info("账号登陆失败")
            return False, "账号登陆失败"

    def login_open_setting(self):
        """
        登录账号后开启设置（护眼助手等）
        """
        d = u2.connect(self.device)
        sleep(2)
        os.system("adb -s %s shell input tap 1100 950" % self.device)
        if d(resourceId="com.seewo.studystation.guide:id/openButton").exists(timeout=5):
            d(resourceId="com.seewo.studystation.guide:id/openButton").click()
            sleep(3)
        logging.info("同意各种协议")
        if d(resourceId="com.seewo.studystation.guide:id/privacyAgreeCheckBox").exists(timeout=5):
            d(resourceId="com.seewo.studystation.guide:id/privacyAgreeCheckBox").click()
            sleep(2)
        d.click(0.248, 0.656)
        sleep(2)
        d.click(0.249, 0.694)
        sleep(2)
        d.click(0.251, 0.732)
        sleep(2)
        logging.info("同意")
        if d(resourceId="com.seewo.studystation.guide:id/privacyAgreeButton").exists(timeout=5):
            d(resourceId="com.seewo.studystation.guide:id/privacyAgreeButton").click()
            sleep(3)
        logging.info("选择桌面模式")
        if d(resourceId="com.seewo.studystation.guide:id/rightModeView").exists(timeout=5):
            d(resourceId="com.seewo.studystation.guide:id/rightModeView").click()
            sleep(3)
        logging.info("下一步")
        if d(resourceId="com.seewo.studystation.guide:id/desktop_button_next").exists(timeout=5):
            d(resourceId="com.seewo.studystation.guide:id/desktop_button_next").click()
            sleep(3)

        if d(text="我知道了").exists(timeout=5):
            d(text="我知道了").click()
            if d(text="允许").exists(timeout=5):
                d(text="允许").click()

        if d(text="跳过").exists(timeout=5):
            d(text="跳过").click()
            sleep(3)
            d.press('back')
            sleep(2)
            d.press('home')
            sleep(2)
        self.skip_guide_login()
        return True, "登录账号后设置推荐功能成功"

    def stop(self, testSign):
        """
        停止测试方法
        """
        # 点掉ACE重启后弹出的日志警告
        os.system("adb -s %s shell input tap 1307 647" % self.device)
        if testSign == 1:
            try:
                os.system("adb -s %s shell am start com.elink.autotest/.MainActivity" % self.device)
            except:
                return False
        else:
            try:
                os.system("adb -s %s shell am start com.emdoor.pressure.tester/.MainActivity" % self.device)
            except:
                return False
        sleep(1)
        os.system("adb -s %s shell am start com.elink.autotest/.MainActivity" % self.device)
        sleep(1)
        os.system("adb -s %s shell input tap 1200 1050" % self.device)
        os.system("adb -s %s shell input tap 1200 1050" % self.device)
        os.system("adb -s %s shell input tap 1200 1050" % self.device)
        sleep(1)
        for i in range(3):
            if not check_device(self.device, 200): return False
            try:
                d = u2.connect(self.device)
                if d(text="退出应用").exists(): d(text="退出应用").click()
                break
            except:
                sleep(10)
                continue
        return True

    def set_test_time(self):
        return 400, 1030, 400, 900
