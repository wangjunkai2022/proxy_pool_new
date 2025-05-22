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
__author__ = 'jinting'

import asyncio

from apscheduler.schedulers.blocking import BlockingScheduler

from helper.fetch import Fetcher
from helper.check import Checker
from handler.logHandler import LogHandler
from handler.proxyHandler import ProxyHandler
from handler.configHandler import ConfigHandler
import time
from datetime import datetime, timedelta

# proxy采集 最小时间间隔
FETCH_INTERVAL = int(ConfigHandler().fetchInterval) * 60
# proxy检查 最小时间间隔
CHECK_INTERVAL = 120 * 60

async def __runProxyFetch():
    proxy_queue = asyncio.Queue()
    proxy_fetcher = Fetcher()

    for proxy in proxy_fetcher.run():
        await proxy_queue.put(proxy)

    await Checker("raw", proxy_queue)


async def __runProxyCheck():
    proxy_handler = ProxyHandler()
    proxy_queue = asyncio.Queue()
    if proxy_handler.db.getCount().get("total", 0) < proxy_handler.conf.poolSizeMin:
        await __runProxyFetch()
    for proxy in proxy_handler.getAll():
        await proxy_queue.put(proxy)
    await Checker("use", proxy_queue)


def schedule_fetch_job(scheduler, scheduler_log):
    def fetch_job():
        start_time = time.time()
        scheduler_log.info("[{}] Starting proxy fetch...".format(datetime.now()))

        asyncio.run(__runProxyFetch())

        duration = time.time() - start_time
        scheduler_log.info("[{}] Proxy fetch finished in {:.2f} minutes".format(datetime.now(), duration/60 if duration > 60 else 1))

        if duration < FETCH_INTERVAL:
            next_run = FETCH_INTERVAL - duration
        else:
            next_run = 1

        scheduler_log.info("[{}] Scheduling next fetch in {:.2f} minutes".format(datetime.now(), next_run/60 if next_run > 60 else 1))
        scheduler.add_job(fetch_job, 'date', run_date=datetime.now() + timedelta(seconds=next_run), executor='fetch_pool', id="proxy_fetch", name="proxy采集", replace_existing=True)

    scheduler.add_job(fetch_job, 'date', run_date=datetime.now() + timedelta(seconds=1), executor='fetch_pool', id="proxy_fetch", name="proxy采集", replace_existing=True)
    scheduler_log.info("[{}] Proxy fetch scheduled to run in 1 seconds".format(datetime.now()))

def schedule_check_job(scheduler, scheduler_log):
    def check_job():
        start_time = time.time()
        scheduler_log.info("[{}] Starting proxy check...".format(datetime.now()))

        asyncio.run(__runProxyCheck())

        duration = time.time() - start_time
        scheduler_log.info("[{}] Proxy check finished in {:.2f} minutes".format(datetime.now(), duration/60 if duration > 60 else 1))

        if duration < CHECK_INTERVAL:
            next_run = CHECK_INTERVAL - duration
        else:
            next_run = 1

        scheduler_log.info("[{}] Scheduling next check in {:.2f} minutes".format(datetime.now(), next_run/60 if next_run > 60 else 1))
        scheduler.add_job(check_job, 'date', run_date=datetime.now() + timedelta(seconds=next_run), executor='check_pool', id="proxy_check", name="proxy检查", replace_existing=True)

    # 延迟30分钟启动第一次任务
    scheduler.add_job(check_job, 'date', run_date=datetime.now() + timedelta(minutes=30), executor='check_pool', id="proxy_check", name="proxy检查", replace_existing=True)
    scheduler_log.info("[{}] Proxy check scheduled to run in 30 minutes".format(datetime.now()))

def runScheduler():
    scheduler_log = LogHandler("scheduler")
    scheduler = BlockingScheduler(
        executors={
            'fetch_pool': {'type': 'threadpool', 'max_workers': 20},
            'check_pool': {'type': 'threadpool', 'max_workers': 10}
        },
        job_defaults={
            'coalesce': False,
            'max_instances': 10
        },
        timezone=ConfigHandler().timezone,
        logger=scheduler_log
    )

    # 启动调度器任务
    schedule_fetch_job(scheduler, scheduler_log)
    schedule_check_job(scheduler, scheduler_log)

    scheduler.start()

if __name__ == '__main__':
    runScheduler()
