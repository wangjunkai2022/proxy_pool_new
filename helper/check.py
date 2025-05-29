# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     check
   Description :   执行代理校验 异步优化
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
                   2025/5/16  添加socks代理效验https网站
                   2025/5/18  修改代理检测方法
                   2025/5/20  异步重构提升性能
-------------------------------------------------
"""
__author__ = 'jinting'

import json
from datetime import datetime
from handler.logHandler import LogHandler
from helper.validator import ProxyValidator
from handler.proxyHandler import ProxyHandler
from handler.configHandler import ConfigHandler
import asyncio
import aiohttp


class DoValidator(object):
    """ 执行校验 """

    conf = ConfigHandler()

    @classmethod
    async def validator(cls, proxy, work_type):
        """
        校验入口  异步并行
        Args:
            proxy: Proxy Object
            work_type: raw/use
        Returns:
            Proxy Object
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 并行执行基础校验
        results = {
            "http": asyncio.create_task(cls.httpValidator(proxy)),
            "https": asyncio.create_task(cls.httpsValidator(proxy)),
            "socks4": asyncio.create_task(cls.socks4Validator(proxy)),
            "socks5": asyncio.create_task(cls.socks5Validator(proxy))
        }

        # 等待基础校验完成
        results = {k: await v for k, v in results.items()}

        # 条件依赖校验
        results["httptohttps"] = False
        # httptohttps 仅在 http 成功的前提下检查
        if results["http"]:
            results["httptohttps"] = await cls.httptohttpsValidator(proxy)

        results["socks4tohttps"] = False
        # socks4tohttps 仅在 socks4 成功的前提下检查
        if results["socks4"]:
            results["socks4tohttps"] = await cls.socks4tohttpsValidator(proxy)

        results["socks5tohttps"] = False
        # socks5tohttps 仅在 socks5 成功的前提下检查
        if results["socks5"]:
            results["socks5tohttps"] = await cls.socks5tohttpsValidator(proxy)

        # 初始化属性
        proxy.check_count += 1
        proxy.last_time = now
        proxy.last_status = any(results.values())

        # 成功或失败计数更新
        if proxy.last_status:
            proxy.proxy_type = [ptype for ptype, valid in results.items() if valid]
            proxy.fail_count = max(proxy.fail_count - 1, 0)
            # 匿名性检测
            if results["http"] or results["https"]:
                proxy.anonymous = await cls.anonymousValidator(proxy.proxy, results["https"])
            if work_type == "raw" and cls.conf.proxyRegion:
                proxy.region = await cls.region_get(proxy.proxy)
        else:
            proxy.fail_count += 1
        return proxy

    @classmethod
    async def httpValidator(cls, proxy):
        tasks = [func(proxy.proxy) for func in ProxyValidator.http_validator]
        results = await asyncio.gather(*tasks)
        return all(results)

    @classmethod
    async def httptohttpsValidator(cls, proxy):
        tasks = [func(proxy.proxy) for func in ProxyValidator.httptohttps_validator]
        results = await asyncio.gather(*tasks)
        return all(results)

    @classmethod
    async def httpsValidator(cls, proxy):
        tasks = [func(proxy.proxy) for func in ProxyValidator.https_validator]
        results = await asyncio.gather(*tasks)
        return all(results)

    @classmethod
    async def socks4Validator(cls, proxy):
        tasks = [func(proxy.proxy) for func in ProxyValidator.socks4_validator]
        results = await asyncio.gather(*tasks)
        return all(results)

    @classmethod
    async def socks4tohttpsValidator(cls, proxy):
        tasks = [func(proxy.proxy) for func in ProxyValidator.socks4tohttps_validator]
        results = await asyncio.gather(*tasks)
        return all(results)

    @classmethod
    async def socks5Validator(cls, proxy):
        tasks = [func(proxy.proxy) for func in ProxyValidator.socks5_validator]
        results = await asyncio.gather(*tasks)
        return all(results)

    @classmethod
    async def socks5tohttpsValidator(cls, proxy):
        tasks = [func(proxy.proxy) for func in ProxyValidator.socks5tohttps_validator]
        results = await asyncio.gather(*tasks)
        return all(results)

    @classmethod
    def preValidator(cls, proxy):
        for func in ProxyValidator.pre_validator:
            if not func(proxy):
                return False
        return True

    @classmethod
    @DeprecationWarning
    async def regionGetter(cls, proxy):
        try:
            # 地址已失效
            async with aiohttp.ClientSession() as session:
                url = f'https://searchplugin.csdn.net/api/v1/ip/get?ip={proxy.proxy.split(":")[0]}'
                async with session.get(url, timeout=2) as resp:
                    data = await resp.json()
                    return data['data']['address']
        except:
            return 'error'

    @classmethod
    async def region_get(cls, proxy):
        try:
            async with aiohttp.ClientSession() as session:
                ip = proxy.split(':')[0]
                url = f'https://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true'
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        try:
                            data = json.loads(text.strip())
                            return data.get('addr', '未知或请求失败')
                        except json.JSONDecodeError:
                            print(f"响应不是有效的 JSON: {text}")
                            return '未知或请求失败'
                    else:
                        print(f"请求失败，状态码：{resp.status}")
                        return '未知或请求失败'
        except Exception as e:
            print(f"region_get: {str(e)}")
            return '未知或请求失败'

    # 0 透明代理
    # 1 普通匿名代理
    # 2 高匿代理
    @classmethod
    async def anonymousValidator(cls, proxy_addr: str, https: bool, timeout: float = 5.0) -> int:
        """
        判断代理的匿名等级：
        0 = Transparent（透明代理）
        1 = Anonymous（匿名代理）
        2 = Elite（高匿代理）
       -1 = Error（检测失败）
        """
        scheme = 'https' if https else 'http'
        url = f'{scheme}://httpbin.org/ip'
        proxy = f'{scheme}://{proxy_addr}'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, proxy=proxy, timeout=timeout) as resp:
                    if not resp.status == 200:
                        return -1
                    data = await resp.json()
                    origin = data.get('origin', '')
                    headers = dict((k.lower(), v) for k, v in resp.headers.items())
                    # 判断真实IP是否泄露
                    if ',' in origin:
                        return 0  # 透明代理
                    # 判断是否存在代理标识头
                    proxy_headers = ['via', 'proxy-connection', 'x-forwarded-for', 'forwarded']
                    if any(h in headers for h in proxy_headers):
                        return 1  # 匿名代理

                    return 2  # 高匿代理
        except Exception as e:
            print(f"anonymousValidator Error: {str(e)}")
            return -1


async def worker(name: str, work_type: str, queue: asyncio.Queue):
    """
    异步工作协程
    :param name: 工作者名称
    :param work_type: raw/use
    :param queue: 任务队列
    """
    log = LogHandler("checker")
    proxy_handler = ProxyHandler()
    conf = ConfigHandler()

    log.info(f"{work_type.title()}ProxyCheck - {name}: start")

    while True:
        try:
            proxy = queue.get_nowait()
        except asyncio.QueueEmpty:
            log.info(f"{work_type.title()}ProxyCheck - {name}: All Proxy Check Complete")
            break

        try:
            # 执行异步校验
            proxy = await DoValidator.validator(proxy, work_type)

            # 处理校验结果
            if work_type == "raw":
                if proxy.last_status:
                    if proxy_handler.exists(proxy):
                        log.info(f'RawProxyCheck - {name}: {proxy.proxy.ljust(23)} {proxy.proxy_type} exist')
                    else:
                        log.info(f'RawProxyCheck - {name}: {proxy.proxy.ljust(23)} {proxy.proxy_type} pass')
                        proxy_handler.put(proxy)
                else:
                    log.info(f'RawProxyCheck - {name}: {proxy.proxy.ljust(23)} fail')
            else:
                if proxy.last_status:
                    log.info(f'UseProxyCheck - {name}: {proxy.proxy.ljust(23)} {proxy.proxy_type} pass')
                    proxy_handler.put(proxy)
                else:
                    if proxy.fail_count > conf.maxFailCount:
                        log.info(
                            f'UseProxyCheck - {name}: {proxy.proxy.ljust(23)} fail, count {proxy.fail_count} delete')
                        proxy_handler.delete(proxy)
                    else:
                        log.info(f'UseProxyCheck - {name}: {proxy.proxy.ljust(23)} fail, count {proxy.fail_count} keep')
                        proxy_handler.put(proxy)

            queue.task_done()

        except Exception as e:
            log.error(f"Worker {name} error: {str(e)}")


async def Checker(tp: str, queue: asyncio.Queue):
    """
    异步代理检查器
    :param tp: raw/use
    :param queue: 代理队列
    """
    max_workers = 100

    log = LogHandler("checker")
    log.info(f"Starting {max_workers} async workers for {tp} proxy check")

    # 创建工作者任务
    workers = [
        asyncio.create_task(worker(f"worker_{i:03d}", tp, queue))
        for i in range(max_workers)
    ]

    # 等待队列处理完成
    await queue.join()

    # 取消所有工作者任务
    for w in workers:
        w.cancel()

    # 等待任务取消完成
    await asyncio.gather(*workers, return_exceptions=True)

    log.info(f"All {tp} proxy checks completed")