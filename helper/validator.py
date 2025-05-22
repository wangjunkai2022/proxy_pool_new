# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     _validators
   Description :   定义proxy验证方法  异步
   Author :        JHao
   date：          2021/5/25
-------------------------------------------------
   Change Activity:
                   2023/03/10: 支持带用户认证的代理格式 username:password@ip:port
                   2025/5/16  添加socks代理效验，分别效验http、https网站
                   2025/5/18  修改代理检测方法
                   2025/5/20  异步重构提升性能
-------------------------------------------------
"""
__author__ = 'jinting'

import re
import ssl

from util.six import withMetaclass
from util.singleton import Singleton
from handler.configHandler import ConfigHandler
from util.webRequest import WebRequest
import aiohttp
from aiohttp_socks import ProxyType, ProxyConnector  # 新增SOCKS支持

conf = ConfigHandler()

HEADER = {'User-Agent': WebRequest().user_agent,
          'Accept': '*/*',
          'Connection': 'keep-alive',
          'Accept-Language': 'zh-CN,zh;q=0.8'}

IP_REGEX = re.compile(r"(.*:.*@)?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}")

# 设置会话超时时间为30秒
SESSION_TIMEOUT = aiohttp.ClientTimeout(total=30)


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


# 新增代理连接器创建函数
def create_socks_connector(proxy, proxy_type, useSsl=False):
    """创建代理连接器"""
    try:
        host, port = proxy.split(':')
        if  useSsl:
            return ProxyConnector(proxy_type=proxy_type, host=host, port=int(port), proxy_ssl=ssl.create_default_context(), ssl=False)
        else:
            return ProxyConnector(proxy_type=proxy_type, host=host, port=int(port))
    except Exception as e:
        print(f"创建代理连接器失败: {str(e)}")
        return None


@ProxyValidator.addHttpValidator
async def httpTimeOutValidator(proxy):
    """http检测超时 http代理连接http网站"""
    connector = create_socks_connector(proxy, ProxyType.HTTP)
    if not connector:
        return False
    async with aiohttp.ClientSession(connector=connector, timeout=SESSION_TIMEOUT) as session:
        try:
            async with session.head(conf.httpUrl, headers=HEADER, timeout=conf.verifyTimeout) as resp:
                return resp.status == 200
        except:
            return False


@ProxyValidator.addHttptohttpsValidator
async def httptohttpsTimeOutValidator(proxy):
    """https检测超时  http代理连接https网站"""
    connector = create_socks_connector(proxy, ProxyType.HTTP)
    if not connector:
        return False

    async with aiohttp.ClientSession(connector=connector, timeout=SESSION_TIMEOUT) as session:
        try:
            async with session.head(conf.httpsUrl, headers=HEADER, timeout=conf.verifyTimeout) as resp:
                return resp.status == 200
        except:
            return False


@ProxyValidator.addHttpsValidator
async def httpsTimeOutValidator(proxy):
    """https检测超时  https代理连接https网站"""
    connector = create_socks_connector(proxy, ProxyType.HTTP, True)
    if not connector:
        return False

    async with aiohttp.ClientSession(connector=connector, timeout=SESSION_TIMEOUT) as session:
        try:
            async with session.head(conf.httpsUrl, headers=HEADER, timeout=conf.verifyTimeout) as resp:
                return resp.status == 200
        except:
            return False


@ProxyValidator.addSocks4Validator
async def socks4TimeOutValidator(proxy):
    """socks4检测超时 socks4代理连接http网站"""
    connector = create_socks_connector(proxy, ProxyType.SOCKS4)
    if not connector:
        return False

    async with aiohttp.ClientSession(connector=connector, timeout=SESSION_TIMEOUT) as session:
        try:
            async with session.head(conf.httpUrl, headers=HEADER, timeout=conf.verifyTimeout) as resp:
                return resp.status == 200
        except:
            return False


@ProxyValidator.addSocks4tohttpsValidator
async def socks4tohttpsTimeOutValidator(proxy):
    """socks4检测超时 socks4代理连接https网站"""
    connector = create_socks_connector(proxy, ProxyType.SOCKS4)
    if not connector:
        return False

    async with aiohttp.ClientSession(connector=connector, timeout=SESSION_TIMEOUT) as session:
        try:
            async with session.head(conf.httpsUrl, headers=HEADER, ssl=False, timeout=conf.verifyTimeout) as resp:
                return resp.status == 200
        except:
            return False

@ProxyValidator.addSocks5Validator
async def socks5TimeOutValidator(proxy):
    """socks5检测超时 socks5代理连接http网站"""
    connector = create_socks_connector(proxy, ProxyType.SOCKS5)
    if not connector:
        return False

    async with aiohttp.ClientSession(connector=connector, timeout=SESSION_TIMEOUT) as session:
        try:
            async with session.head(conf.httpUrl, headers=HEADER, timeout=conf.verifyTimeout) as resp:
                return resp.status == 200
        except:
            return False


@ProxyValidator.addSocks5tohttpsValidator
async def socks5tohttpsTimeOutValidator(proxy):
    """socks5检测超时  socks5代理连接https网站"""
    connector = create_socks_connector(proxy, ProxyType.SOCKS5)
    if not connector:
        return False

    async with aiohttp.ClientSession(connector=connector, timeout=SESSION_TIMEOUT) as session:
        try:
            async with session.head(conf.httpsUrl, headers=HEADER, ssl=False, timeout=conf.verifyTimeout) as resp:
                return resp.status == 200
        except:
            return False


# 示例自定义校验器 异步
@ProxyValidator.addHttpValidator
async def customValidatorExample(proxy):
    """自定义validator函数，校验代理是否可用, 返回True/False"""
    return True