# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     proxyScheduler
   Description :
   Author :        JHao
   date：          2019/8/5
-------------------------------------------------
   Change Activity:
                   2019/08/05: proxyScheduler
                   2021/02/23: runProxyCheck时,剩余代理少于POOL_SIZE_MIN时执行抓取
-------------------------------------------------
"""
__author__ = 'JHao'

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ProcessPoolExecutor

from util.six import Queue
from helper.fetch import Fetcher
from helper.check import Checker
from handler.logHandler import LogHandler
from handler.proxyHandler import ProxyHandler
from handler.configHandler import ConfigHandler


def __runProxyFetch():
    proxy_queue = Queue()
    proxy_fetcher = Fetcher()

    for proxy in proxy_fetcher.run():
        proxy_queue.put(proxy)

    Checker("raw", proxy_queue)


def __runProxyCheck():
    proxy_handler = ProxyHandler()
    proxy_queue = Queue()
    if proxy_handler.db.getCount().get("total", 0) < proxy_handler.conf.poolSizeMin:
        __runProxyFetch()
    for proxy in proxy_handler.getAll():
        proxy_queue.put(proxy)
    Checker("use", proxy_queue)


def runScheduler():
    __runProxyFetch()

    scheduler_log = LogHandler("scheduler")
    scheduler = BlockingScheduler(
        executors={
            'fetch_pool': {'type': 'threadpool', 'max_workers': 5},
            'check_pool': {'type': 'threadpool', 'max_workers': 20},
            'processpool': ProcessPoolExecutor(max_workers=5)
        },
        job_defaults={
            'coalesce': False,
            'max_instances': 10
        },
        timezone=ConfigHandler().timezone,
        logger=scheduler_log
    )

    scheduler.add_job(__runProxyFetch, 'interval', minutes=ConfigHandler().fetchInterval, executor='fetch_pool', id="proxy_fetch", name="proxy采集")
    scheduler.add_job(__runProxyCheck, 'interval', minutes=5, misfire_grace_time=0, executor='check_pool', id="proxy_check", name="proxy检查")

    scheduler.start()


if __name__ == '__main__':
    runScheduler()
