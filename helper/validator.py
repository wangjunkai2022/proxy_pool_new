# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     _validators
   Description :   定义proxy验证方法
   Author :        JHao
   date：          2021/5/25
-------------------------------------------------
   Change Activity:
                   2023/03/10: 支持带用户认证的代理格式 username:password@ip:port
                   2025/5/16  添加socks代理效验，分别效验http、https网站
                   2025/5/18  修改代理检测方法
-------------------------------------------------
"""
__author__ = 'jinting'

import re
from requests import head
from util.six import withMetaclass
from util.singleton import Singleton
from handler.configHandler import ConfigHandler
from util.webRequest import WebRequest

conf = ConfigHandler()

HEADER = {'User-Agent': WebRequest().user_agent,
          'Accept': '*/*',
          'Connection': 'keep-alive',
          'Accept-Language': 'zh-CN,zh;q=0.8'}

IP_REGEX = re.compile(r"(.*:.*@)?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}")


class ProxyValidator(withMetaclass(Singleton)):
    pre_validator = []
    # http代理连接http网站
    http_validator = []
    # http代理连接https网站
    httptohttps_validator = []
    # https代理连接https网站
    https_validator = []
    # socks4代理连接http网站
    socks4_validator = []
    # socks4代理连接https网站
    socks4tohttps_validator = []
    # socks5代理连接http网站
    socks5_validator = []
    # socks5代理连接https网站
    socks5tohttps_validator = []

    @classmethod
    def addPreValidator(cls, func):
        cls.pre_validator.append(func)
        return func

    @classmethod
    def addHttpValidator(cls, func):
        cls.http_validator.append(func)
        return func

    @classmethod
    def addHttptohttpsValidator(cls, func):
        cls.httptohttps_validator.append(func)
        return func

    @classmethod
    def addHttpsValidator(cls, func):
        cls.https_validator.append(func)
        return func

    @classmethod
    def addSocks4Validator(cls, func):
        cls.socks4_validator.append(func)
        return func

    @classmethod
    def addSocks4tohttpsValidator(cls, func):
        cls.socks4tohttps_validator.append(func)
        return func

    @classmethod
    def addSocks5Validator(cls, func):
        cls.socks5_validator.append(func)
        return func

    @classmethod
    def addSocks5tohttpsValidator(cls, func):
        cls.socks5tohttps_validator.append(func)
        return func

@ProxyValidator.addPreValidator
def formatValidator(proxy):
    """检查代理格式"""
    return True if IP_REGEX.fullmatch(proxy) else False


@ProxyValidator.addHttpValidator
def httpTimeOutValidator(proxy):
    """
    http检测超时 http代理连接http网站
    """
    proxies = {"http": "http://{proxy}".format(proxy=proxy), "https": "http://{proxy}".format(proxy=proxy)}
    try:
        r = head(conf.httpUrl, headers=HEADER, proxies=proxies, timeout=conf.verifyTimeout)
        return True if r.status_code == 200 else False
    except Exception as e:
        return False

@ProxyValidator.addHttptohttpsValidator
def httptohttpsTimeOutValidator(proxy):
    """
    https检测超时  http代理连接https网站
    """
    proxies = {"http": "http://{proxy}".format(proxy=proxy), "https": "http://{proxy}".format(proxy=proxy)}
    try:
        r = head(conf.httpsUrl, headers=HEADER, proxies=proxies, timeout=conf.verifyTimeout, verify=False)
        return True if r.status_code == 200 else False
    except Exception as e:
        return False

@ProxyValidator.addHttpsValidator
def httpsTimeOutValidator(proxy):
    """
    https检测超时  https代理连接https网站
    """
    proxies = {"http": "https://{proxy}".format(proxy=proxy), "https": "https://{proxy}".format(proxy=proxy)}
    try:
        r = head(conf.httpsUrl, headers=HEADER, proxies=proxies, timeout=conf.verifyTimeout, verify=False)
        return True if r.status_code == 200 else False
    except Exception as e:
        return False

@ProxyValidator.addSocks4Validator
def socks4TimeOutValidator(proxy):
    """
    socks4检测超时 socks4代理连接http网站
    """
    proxies = {"http": "socks4://{proxy}".format(proxy=proxy), "https": "socks4://{proxy}".format(proxy=proxy)}
    try:
        r = head(conf.httpUrl, headers=HEADER, proxies=proxies, timeout=conf.verifyTimeout)
        return True if r.status_code == 200 else False
    except Exception as e:
        return False

@ProxyValidator.addSocks4tohttpsValidator
def socks4tohttpsTimeOutValidator(proxy):
    """
    socks4检测超时 socks4代理连接https网站
    """
    proxies = {"http": "socks4://{proxy}".format(proxy=proxy), "https": "socks4://{proxy}".format(proxy=proxy)}
    try:
        r = head(conf.httpsUrl, headers=HEADER, proxies=proxies, timeout=conf.verifyTimeout)
        return True if r.status_code == 200 else False
    except Exception as e:
        return False

@ProxyValidator.addSocks5Validator
def socks5TimeOutValidator(proxy):
    """
    socks5检测超时 socks5代理连接http网站
    """
    proxies = {"http": "socks5h://{proxy}".format(proxy=proxy), "https": "socks5h://{proxy}".format(proxy=proxy)}
    try:
        r = head(conf.httpUrl, headers=HEADER, proxies=proxies, timeout=conf.verifyTimeout)
        return True if r.status_code == 200 else False
    except Exception as e:
        return False


@ProxyValidator.addSocks5tohttpsValidator
def socks5tohttpsTimeOutValidator(proxy):
    """
    socks5检测超时  socks5代理连接https网站
     """
    proxies = {"http": "socks5h://{proxy}".format(proxy=proxy), "https": "socks5h://{proxy}".format(proxy=proxy)}
    try:
        r = head(conf.httpsUrl, headers=HEADER, proxies=proxies, timeout=conf.verifyTimeout)
        return True if r.status_code == 200 else False
    except Exception as e:
        return False


@ProxyValidator.addHttpValidator
def customValidatorExample(proxy):
    """自定义validator函数，校验代理是否可用, 返回True/False"""
    return True