# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     WebRequest
   Description :   Network Requests Class
   Author :        J_hao
   date：          2017/7/31
-------------------------------------------------
   Change Activity:
                   2017/7/31:
-------------------------------------------------
"""
__author__ = 'J_hao'

from requests.models import Response
from lxml import etree
import requests
import random
import time

from handler.logHandler import LogHandler

requests.packages.urllib3.disable_warnings()


class WebRequest(object):
    name = "web_request"

    def __init__(self, *args, **kwargs):
        self.log = LogHandler(self.name, file=False)
        self.response = Response()

    @property
    def user_agent(self):
        """
        return an User-Agent at random
        :return:
        """
        ua_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/90.0.4472.114 Safari/537.3',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
            'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.10.289 Version/12.02',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
            'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'
        ]
        return random.choice(ua_list)

    @property
    def header(self):
        """
        basic header
        :return:
        """
        return {'User-Agent': self.user_agent,
                'Accept': '*/*',
                'Connection': 'keep-alive',
                'Accept-Language': 'zh-CN,zh;q=0.8'}

    def get(self, url, header=None, retry_time=3, retry_interval=5, timeout=5, *args, **kwargs):
        """
        get method
        :param url: target url
        :param header: headers
        :param retry_time: retry time
        :param retry_interval: retry interval
        :param timeout: network timeout
        :return:
        """
        headers = self.header
        if header and isinstance(header, dict):
            headers.update(header)
        while True:
            try:
                self.response = requests.get(url, headers=headers, timeout=timeout, *args, **kwargs)
                return self
            except Exception as e:
                self.log.error("requests: %s error: %s" % (url, str(e)))
                retry_time -= 1
                if retry_time <= 0:
                    resp = Response()
                    resp.status_code = 200
                    return self
                self.log.info("retry %s second after" % retry_interval)
                time.sleep(retry_interval)

    @property
    def tree(self):
        return etree.HTML(self.response.content)

    @property
    def text(self):
        return self.response.text

    @property
    def json(self):
        try:
            return self.response.json()
        except Exception as e:
            self.log.error(str(e))
            return {}

