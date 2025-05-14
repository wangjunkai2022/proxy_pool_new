# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     check
   Description :   执行代理校验
   Author :        JHao
   date：          2019/8/6
-------------------------------------------------
   Change Activity:
                   2019/08/06: 执行代理校验
                   2021/05/25: 分别校验http和https
                   2022/08/16: 获取代理Region信息
                   2025/5/14: 获取代理匿名信息
                              修复代理Region信息
                              添加socks代理效验
-------------------------------------------------
"""
__author__ = 'JHao'

from requests import RequestException

from util.six import Empty
from threading import Thread
from datetime import datetime
from util.webRequest import WebRequest
from handler.logHandler import LogHandler
from helper.validator import ProxyValidator
from handler.proxyHandler import ProxyHandler
from handler.configHandler import ConfigHandler
import requests
import json


class DoValidator(object):
    """ 执行校验 """

    conf = ConfigHandler()

    @classmethod
    def validator(cls, proxy, work_type):
        """
        校验入口
        Args:
            proxy: Proxy Object
            work_type: raw/use
        Returns:
            Proxy Object
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 各类型代理校验
        results = {
            "http": cls.httpValidator(proxy),
            "https": False,
            "socks4": cls.socks4Validator(proxy),
            "socks5": cls.socks5Validator(proxy),
        }

        # HTTPS 仅在 HTTP 成功的前提下检查
        if results["http"]:
            results["https"] = cls.httpsValidator(proxy)

        # 初始化属性
        proxy.check_count += 1
        proxy.last_time = now
        proxy.last_status = any(results.values())
        proxy.proxy_type = [ptype for ptype, valid in results.items() if valid]

        # 匿名性检测
        if results["http"] or results["https"]:
            proxy.anonymous = cls.anonymousValidator(proxy.proxy, results["https"])

        # 成功或失败计数更新
        if proxy.last_status:
            proxy.fail_count = max(proxy.fail_count - 1, 0)
            if work_type == "raw" and cls.conf.proxyRegion:
                proxy.region = cls.region_get(proxy.proxy)
        else:
            proxy.fail_count += 1
        return proxy

    @classmethod
    def httpValidator(cls, proxy):
        for func in ProxyValidator.http_validator:
            if not func(proxy.proxy):
                return False
        return True

    @classmethod
    def httpsValidator(cls, proxy):
        for func in ProxyValidator.https_validator:
            if not func(proxy.proxy):
                return False
        return True

    @classmethod
    def socks4Validator(cls, proxy):
        for func in ProxyValidator.socks4_validator:
            if not func(proxy.proxy):
                return False
        return True

    @classmethod
    def socks5Validator(cls, proxy):
        for func in ProxyValidator.socks5_validator:
            if not func(proxy.proxy):
                return False
        return True

    @classmethod
    def preValidator(cls, proxy):
        for func in ProxyValidator.pre_validator:
            if not func(proxy):
                return False
        return True

    @classmethod
    @DeprecationWarning
    def regionGetter(cls, proxy):
        try:
            # 地址已失效
            url = 'https://searchplugin.csdn.net/api/v1/ip/get?ip=%s' % proxy.proxy.split(':')[0]
            r = WebRequest().get(url=url, retry_time=1, timeout=2).json
            return r['data']['address']
        except:
            return 'error'

    @classmethod
    def region_get(cls, proxy):
        try:
            r = requests.get('https://whois.pconline.com.cn/ipJson.jsp?ip=%s&json=true' % proxy.split(':')[0])
            return json.loads(r.text.strip())['addr']
        except Exception as e:
            print(f"region_get: {str(e)}")
            return '未知或请求失败'

    # 0 透明代理
    # 1 普通匿名代理
    # 2 高匿代理
    @classmethod
    def anonymousValidator(cls, proxy_addr: str, https: bool, timeout: float = 5.0) -> int:
        """
        判断代理的匿名等级：
        0 = Transparent（透明代理）
        1 = Anonymous（匿名代理）
        2 = Elite（高匿代理）
       -1 = Error（检测失败）
        """
        # 1. 构造 URL 与 proxies dict
        scheme = 'https' if https else 'http'
        url = f'{scheme}://httpbin.org/ip'
        proxies = {scheme: proxy_addr}
        try:
            # 2. 发起请求
            resp = requests.get(url, proxies=proxies, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            # 3. 解析返回值
            origin = data.get('origin', '')
            headers = {k.lower(): v for k, v in resp.headers.items()}
            # 4. 判断真实 IP 是否泄露
            #    如果 origin 中包含逗号，说明经过了多次转发，或真实 IP 未被隐藏
            if ',' in origin:
                return 0  # 透明代理
            # 5. 判断是否存在代理标识头
            proxy_headers = ['via', 'proxy-connection', 'x-forwarded-for', 'forwarded']
            if any(h in headers for h in proxy_headers):
                return 1  # 匿名代理
            # 6. 否则即为高匿代理
            return 2
        except (RequestException, ValueError, KeyError):
            # 网络错误 / JSON 解析错误 / 头部缺失等
            return -1

class _ThreadChecker(Thread):
    """ 多线程检测 """

    def __init__(self, work_type, target_queue, thread_name):
        Thread.__init__(self, name=thread_name)
        self.work_type = work_type
        self.log = LogHandler("checker")
        self.proxy_handler = ProxyHandler()
        self.target_queue = target_queue
        self.conf = ConfigHandler()

    def run(self):
        self.log.info("{}ProxyCheck - {}: start".format(self.work_type.title(), self.name))
        while True:
            try:
                proxy = self.target_queue.get(block=False)
            except Empty:
                self.log.info("{}ProxyCheck - {}: complete".format(self.work_type.title(), self.name))
                break
            proxy = DoValidator.validator(proxy, self.work_type)
            if self.work_type == "raw":
                self.__ifRaw(proxy)
            else:
                self.__ifUse(proxy)
            self.target_queue.task_done()

    def __ifRaw(self, proxy):
        if proxy.last_status:
            if self.proxy_handler.exists(proxy):
                self.log.info('RawProxyCheck - {}: {} [{}] exist'.format(self.name, proxy.proxy.ljust(23), proxy.proxy_type))
            else:
                self.log.info('RawProxyCheck - {}: {} [{}] pass'.format(self.name, proxy.proxy.ljust(23), proxy.proxy_type))
                self.proxy_handler.put(proxy)
        else:
            self.log.info('RawProxyCheck - {}: {} fail'.format(self.name, proxy.proxy.ljust(23)))

    def __ifUse(self, proxy):
        if proxy.last_status:
            self.log.info('UseProxyCheck - {}: {} [{}] pass'.format(self.name, proxy.proxy.ljust(23), proxy.proxy_type))
            self.proxy_handler.put(proxy)
        else:
            if proxy.fail_count > self.conf.maxFailCount:
                self.log.info('UseProxyCheck - {}: {} fail, count {} delete'.format(self.name,
                                                                                    proxy.proxy.ljust(23),
                                                                                    proxy.fail_count))
                self.proxy_handler.delete(proxy)
            else:
                self.log.info('UseProxyCheck - {}: {} fail, count {} keep'.format(self.name,
                                                                                  proxy.proxy.ljust(23),
                                                                                  proxy.fail_count))
                self.proxy_handler.put(proxy)


def Checker(tp, queue):
    """
    run Proxy ThreadChecker
    :param tp: raw/use
    :param queue: Proxy Queue
    :return:
    """
    thread_list = list()
    for index in range(20):
        thread_list.append(_ThreadChecker(tp, queue, "thread_%s" % str(index).zfill(2)))

    for thread in thread_list:
        thread.setDaemon(True)
        thread.start()

    for thread in thread_list:
        thread.join()
