# -*- encoding=utf8 -*-
import os
import sys


# 追加模块搜索路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import time
import base64
import hashlib
import requests
from config.config import *
from src.read_task import eRead_user_notes

# 数据格式
# thisTime = time.strftime('%Y-%m-%d %H:%M:%S')
txt = "\t\t\t\t"
tabL = txt.expandtabs(2)

"""
企业微信机器人封装，实例传入企业微信机器人连接
创建日期：2024年1月22日
"""

class WeComRobot(object):
    def __init__(self, url):
        """初始化属性"""
        self.url = url

    # 图片发送
    def image_message(self, imagePath):
        """
        图片发送
        """
        with open(imagePath, 'rb') as f:
            # 转换图片为base64格式
            base64_data = base64.b64encode(f.read())
            image_data = str(base64_data, 'utf-8')

        with open(imagePath, 'rb') as f:
            # 获取图片的md5值
            md = hashlib.md5()
            md.update(f.read())
            image_md5 = md.hexdigest()

        headers = {"Content-Type": 'application/json'}
        data = {
            'msgtype': 'image',
            'image': {
                'base64': image_data,
                'md5': image_md5
            }
        }
        # 发送请求
        res = requests.post(self.url, headers=headers, json=data)
        if res.status_code == 200:
            logging.info("send message sucessed")
            return "send message sucessed"
        else:
            logging.info(res)
            return res

    # 图文发送
    def image_text_message(self, contents):
        """
        图片文字发送
        cc = [{
            "title": "测试1",
            "description": "测试22",
            "url": "www.qq.com",
            "picurl": r"D:\_python_script\mtKoptimizeTest\test_pic_msg1.png"
        }]
        """
        headers = {"Content-Type": 'application/json'}
        data = {
            "msgtype": "news",
            "news": {
                "articles": contents
            }
        }
        # 发送请求
        res = requests.post(self.url, headers=headers, json=data)
        if res.status_code == 200:
            logging.info("send message sucessed")
            return "send message sucessed"
        else:
            logging.info(res)
            return res

    """
    文件发送
    上传的文件限制：
    ~!要求文件大小在5B~20M之间
    """

    # 企业机器人发送信息频率，20条/一分钟
    def files(self, filePath):
        """
        发送文件
        :return:
        """
        data = {'file': open(filePath, 'rb')}
        # 请求id_url(将文件上传微信临时平台),返回media_id
        # https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key=(企业微信机器人key)&type=file
        id_url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key=%s' \
                 '&type=file' % str(self.url).split("=")[-1]
        response = requests.post(url=id_url, files=data)
        logging.info(response.text)
        json_res = response.json()
        media_id = json_res['media_id']
        data = {"msgtype": "file",
                "file": {"media_id": media_id}
                }
        # 发送文件
        result = requests.post(url=self.url, json=data)
        if result.status_code == 200:
            logging.info("send image message sucessed")
        else:
            logging.info(result)

    def message(self, messageType, contents):
        """
        发送短信---->
        title = "大标题"，
        contents = [
            {
                "Ids": "排位编号",
                "label": "标签"
                "Device": "Device",
                "Message": "消息",
                "BeginName": "消息",
                "type": "[comment：灰色,red: 红色,info: 绿色,warning: 黄色]"
            }
        ]
        """
        inputs = {
            "title": "暂无备注信息",
            "content": contents
        }
        testUser, testNotes = eRead_user_notes()
        if testNotes is not None: inputs['title'] = str(testNotes)
        if testUser is None: testUser = "默认测试用户"
        # 拼接信息
        #  <font>%s</font>" % inputs['title'] +
        # + "\n节点: " + "<font color=\"red\">%s</font>" % messageType +
        infos = "标题: " + inputs[
            'title'] + "\n节点: " + messageType + "\n用户: " + "<font color=\"comment\">%s</font>" % str(
            testUser) + "\n时间: " + "<font color=\"comment\">%s</font>" % str(time.strftime('%Y-%m-%d %H:%M:%S')) + "\n"
        # # 拼接信息
        # infos = "<font color=\"comment\">Title: </font> %s" % inputs['title'] + "\n<font color=\"comment\">User: </font>" + str(testUser) + "\n<font color=\"comment\">Time: </font> " + str(time.strftime('%Y-%m-%d %H:%M:%S')) + "\n"
        for text in inputs['content']:
            infos += ">设备工位: <font color=\"comment\">{}</font> \n 设备标签: <font color=\"comment\">{}</font> \n 设备序号: <font color=\"comment\">{}</font> \n 测试项目: <font color=\"comment\">{}</font> \n 通知信息: <font color=\"{}\">{}</font>\n\n".format(text['Ids'],text['label'],text['Device'],text['BeginName'],text['type'],text['Message'])

        # 发送请求
        data = {
            "msgtype": "markdown",
            "markdown": {"content": infos},
            "mentioned_list": ["杨刚", "@all"],
            "mentioned_mobile_list": ["18974710587", "@all"]
        }
        res = requests.post(url=self.url, json=data)
        if res.status_code == 200:
            logging.info("send message succeed")
            return "send message succeed"
        else:
            logging.info(res)
            return res


if __name__ == '__main__':
    # a = WeComRobot("https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=aa8ae2ef-5527-4cf4-abdb-40accd33ecb7")
    # a.image_message(r"D:\_python_script\mtKoptimizeTest\test_pic_msg1.png")
    pass
