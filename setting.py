# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     setting.py
   Description :   配置文件
   Author :        JHao
   date：          2019/2/15
-------------------------------------------------
   Change Activity:
                   2025/5/14:
-------------------------------------------------
"""

BANNER = r"""
****************************************************************
*** ______  ********************* ______ *********** _  ********
*** | ___ \_ ******************** | ___ \ ********* | | ********
*** | |_/ / \__ __   __  _ __   _ | |_/ /___ * ___  | | ********
*** |  __/|  _// _ \ \ \/ /| | | ||  __// _ \ / _ \ | | ********
*** | |   | | | (_) | >  < \ |_| || |  | (_) | (_) || |___  ****
*** \_|   |_|  \___/ /_/\_\ \__  |\_|   \___/ \___/ \_____/ ****
****                       __ / /                          *****
************************* /___ / *******************************
*************************       ********************************
****************************************************************
"""

VERSION = "2.5.0"

# ############### server config ###############
HOST = "0.0.0.0"

PORT = 5010

# ############### database config ###################
# db connection uri
# example:
#      Redis: redis://:password@ip:port/db
#      Ssdb:  ssdb://:password@ip:port
DB_CONN = 'redis://:pwd@127.0.0.1:6379/0'

# proxy table name
TABLE_NAME = 'use_proxy'

# ############# proxy validator #################
# 代理验证目标网站
HTTP_URL = "http://httpbin.org/ip"

HTTPS_URL = "https://httpbin.org/ip"

# 抓取代理时使用的代理是否使用代理
USE_PROXY = True
# 抓取代理时使用的代理
PROXIES = {'http': "http://127.0.0.1:7897", 'https': "http://127.0.0.1:7897"}

# 代理验证时的工作协程数量
WORKERS_NUMBER = 100

# 代理验证时超时时间
VERIFY_TIMEOUT = 10

# 代理抓取最小时间间隔（分钟）
FETCH_INTERVAL = 480

# 近PROXY_CHECK_COUNT次校验中允许的最大失败次数,超过则剔除代理
MAX_FAIL_COUNT = 3

# proxyCheck时代理数量少于POOL_SIZE_MIN触发抓取
POOL_SIZE_MIN = 100

# ############# proxy attributes #################
# 是否启用代理地域属性
PROXY_REGION = True

# ############# scheduler config #################

# Set the timezone for the scheduler forcely (optional)
# If it is running on a VM, and
#   "ValueError: Timezone offset does not match system offset"
#   was raised during scheduling.
# Please uncomment the following line and set a timezone for the scheduler.
# Otherwise it will detect the timezone from the system automatically.

TIMEZONE = "Asia/Shanghai"

# ############# log config #################
# 是否将日志输出到文件
INPUT_LOG_FILE = True
# 日志文件保存日期
LOG_FILE_SAVE_DATE = 1