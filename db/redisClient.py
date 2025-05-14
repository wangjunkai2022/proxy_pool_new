# -*- coding: utf-8 -*-
"""
-----------------------------------------------------
   File Name：     redisClient.py
   Description :   封装Redis相关操作
   Author :        JHao
   date：          2019/8/9
------------------------------------------------------
   Change Activity:
                   2019/08/09: 封装Redis相关操作
                   2020/06/23: 优化pop方法, 改用hscan命令
                   2021/05/26: 区别http/https代理
------------------------------------------------------
"""
__author__ = 'JHao'

from redis.exceptions import TimeoutError, ConnectionError, ResponseError
from redis.connection import BlockingConnectionPool
from handler.logHandler import LogHandler
from random import choice
from redis import Redis
import json


class RedisClient(object):
    """
    Redis client

    Redis中代理存放的结构为hash：
    key为ip:port, value为代理属性的字典;

    """

    def __init__(self, **kwargs):
        """
        init
        :param host: host
        :param port: port
        :param password: password
        :param db: db
        :return:
        """
        self.name = ""
        kwargs.pop("username")
        self.__conn = Redis(connection_pool=BlockingConnectionPool(decode_responses=True,
                                                                   timeout=5,
                                                                   socket_timeout=5,
                                                                   **kwargs))

    def get(self, proxy_type, region, anonymous):
        """
        返回一个代理
        :return:
        """
        # 1. 从 Redis 取出所有值（JSON 字符串）
        items = self.__conn.hvals(self.name)
        # 2. 解析成 Python 字典列表
        parsed = [json.loads(item) for item in items]
        # 3. 根据 proxy_type 过滤
        if proxy_type:
            parsed = [p for p in parsed if proxy_type in p.get("proxy_type", [])]
        # 4. 根据 region 过滤
        if region:
            parsed = [p for p in parsed if region in p.get("region", "")]
        # 5. 根据 anonymous 过滤
        if anonymous != -1:
            parsed = [p for p in parsed if p.get("anonymous") == anonymous]
        # 6. 随机返回一个，如果列表空则返回 None
        return choice(parsed) if parsed else None

        # if https:
        #     items = self.__conn.hvals(self.name)
        #     proxies = list(filter(lambda x: json.loads(x).get("https"), items))
        #     if region != '':
        #         proxies = list(filter(lambda x: region in json.loads(x).get("region"), iter(proxies)))
        #     return choice(proxies) if proxies else None
        # elif region != '':
        #     items = self.__conn.hvals(self.name)
        #     proxies = list(filter(lambda x: region in json.loads(x).get("region"), items))
        #     return choice(proxies) if proxies else None
        # else:
        #     proxies = self.__conn.hkeys(self.name)
        #     proxy = choice(proxies) if proxies else None
        #     return self.__conn.hget(self.name, proxy) if proxy else None

    def put(self, proxy_obj):
        """
        将代理放入hash, 使用changeTable指定hash name
        :param proxy_obj: Proxy obj
        :return:
        """
        data = self.__conn.hset(self.name, proxy_obj.proxy, proxy_obj.to_json)
        return data

    def pop(self, proxy_type, region, anonymous):
        """
        弹出一个代理，返回一个 dict（或 None）。
        支持上游返回 JSON 字符串或已经解析好的 dict。
        """
        raw = self.get(proxy_type, region, anonymous)
        if not raw:
            return None
        # 准备一个变量用于存最终的 proxy dict
        proxy_data = None
        # 情况 A：上游返回的是 JSON 文本
        if isinstance(raw, (str, bytes, bytearray)):
            try:
                proxy_data = json.loads(raw)
            except json.JSONDecodeError:
                # 解析失败，就当没拿到
                return None
        # 情况 B：上游已经给了一个 dict
        elif isinstance(raw, dict):
            proxy_data = raw
        else:
            # 其它类型不支持，直接放弃
            return None
        # 到这里，proxy_data 肯定是一个 dict
        proxy_addr = proxy_data.get("proxy", "")
        if proxy_addr:
            # 从 Redis hash 里把这个 proxy key 删除
            self.__conn.hdel(self.name, proxy_addr)
        return proxy_data

    def delete(self, proxy_str):
        """
        移除指定代理, 使用changeTable指定hash name
        :param proxy_str: proxy str
        :return:
        """
        return self.__conn.hdel(self.name, proxy_str)

    def exists(self, proxy_str):
        """
        判断指定代理是否存在, 使用changeTable指定hash name
        :param proxy_str: proxy str
        :return:
        """
        return self.__conn.hexists(self.name, proxy_str)

    def update(self, proxy_obj):
        """
        更新 proxy 属性
        :param proxy_obj:
        :return:
        """
        return self.__conn.hset(self.name, proxy_obj.proxy, proxy_obj.to_json)

    def getAll(self, proxy_type, region, anonymous):
        """
        字典形式返回所有代理, 使用changeTable指定hash name
        :return:
        """
        items = self.__conn.hvals(self.name)
        parsed = [json.loads(item) for item in items]
        # 3. 根据 proxy_type 过滤
        if proxy_type:
            parsed = [p for p in parsed if proxy_type in p.get("proxy_type", [])]
        # 4. 根据 region 过滤
        if region:
            parsed = [p for p in parsed if region in p.get("region", "")]
        # 5. 根据 anonymous 过滤
        if anonymous != -1:
            parsed = [p for p in parsed if p.get("anonymous") == anonymous]
        # 6. 随机返回一个，如果列表空则返回 None
        return parsed

    def clear(self):
        """
        清空所有代理, 使用changeTable指定hash name
        :return:
        """
        return self.__conn.delete(self.name)

    def getCount(self):
        """
        返回代理数量
        :return:
        """
        proxies = self.getAll(proxy_type='', region='', anonymous=-1)
        return {'total': len(proxies)}

    def changeTable(self, name):
        """
        切换操作对象
        :param name:
        :return:
        """
        self.name = name

    def test(self):
        log = LogHandler('redis_client')
        try:
            self.getCount()
        except TimeoutError as e:
            log.error('redis connection time out: %s' % str(e), exc_info=True)
            return e
        except ConnectionError as e:
            log.error('redis connection error: %s' % str(e), exc_info=True)
            return e
        except ResponseError as e:
            log.error('redis connection error: %s' % str(e), exc_info=True)
            return e


