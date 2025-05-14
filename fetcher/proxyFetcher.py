# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     proxyFetcher
   Description :
   Author :        JHao
   date：          2016/11/25
-------------------------------------------------
   Change Activity:
                   2016/11/25: proxyFetcher
-------------------------------------------------
"""
__author__ = 'JHao'

import re
import json
from time import sleep

from handler.configHandler import ConfigHandler
from util.webRequest import WebRequest

conf = ConfigHandler()

class ProxyFetcher(object):
    """
    proxy getter
    """

    @staticmethod
    def freeProxy01():
        """
        站大爷 https://www.zdaye.com/dayProxy.html
        """
        for i in range(1, 5):
            url = 'https://www.zdaye.com/free/{}'.format(i)
            html_tree = WebRequest().get(url, proxies = conf.proxies if conf.useProxy else None, verify=False).tree
            for tr in html_tree.xpath("//table//tr"):
                ip = "".join(tr.xpath("./td[1]/text()")).strip()
                port = "".join(tr.xpath("./td[2]/text()")).strip()
                yield "%s:%s" % (ip, port)
            sleep(8)

    @staticmethod
    def freeProxy02():
        """ FreeProxyList http://free-proxy-list.net"""
        url = 'http://free-proxy-list.net'
        html_tree = WebRequest().get(url, proxies = conf.proxies if conf.useProxy else None, verify=False).tree
        proxies = html_tree.xpath("//*[@id='raw']/div/div/div[2]/textarea/text()")
        matches = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', proxies[0])
        for proxy in matches:
            yield proxy

    @staticmethod
    def freeProxy03(page_count=5):
        """ 快代理 https://www.kuaidaili.com """
        url_pattern = [
            'https://www.kuaidaili.com/free/inha/{}/',
            'https://www.kuaidaili.com/free/intr/{}/',
            'https://www.kuaidaili.com/free/fps/{}/'
        ]
        url_list = []
        for page_index in range(1, page_count + 1):
            for pattern in url_pattern:
                url_list.append(pattern.format(page_index))

        for url in url_list:
            tree = WebRequest().get(url, proxies = conf.proxies if conf.useProxy else None).tree
            proxy_list = tree.xpath('.//table//tr')
            sleep(2)  # 必须sleep 不然第二条请求不到数据
            for tr in proxy_list[1:]:
                yield ':'.join(tr.xpath('./td/text()')[0:2])

    @staticmethod
    def freeProxy04():
        """ 稻壳代理 https://www.docip.net/ """
        r = WebRequest().get("https://www.docip.net/data/free.json", proxies = conf.proxies if conf.useProxy else None, timeout=10)
        try:
            for each in r.json['data']:
                yield each['ip']
        except Exception as e:
            print(e)

    @staticmethod
    def freeProxy05():
        """
        https://proxy-list.org/english/index.php
        :return:
        """
        urls = ['https://proxy-list.org/english/index.php?p=%s' % n for n in range(1, 10)]
        request = WebRequest()
        import base64
        for url in urls:
            r = request.get(url, proxies = conf.proxies if conf.useProxy else None, timeout=10)
            proxies = re.findall(r"Proxy\('(.*?)'\)", r.text)
            for proxy in proxies:
                yield base64.b64decode(proxy).decode()

    @staticmethod
    def freeProxy06():
        urls = ['https://list.proxylistplus.com/Fresh-HTTP-Proxy-List-1']
        request = WebRequest()
        for url in urls:
            r = request.get(url, proxies = conf.proxies if conf.useProxy else None, timeout=10)
            proxies = re.findall(r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td>(\d+)</td>', r.text)
            for proxy in proxies:
                yield ':'.join(proxy)

    @staticmethod
    def freeProxy07(page_count=3):
        for i in range(1, page_count + 1):
            url = 'https://proxylist.geonode.com/api/proxy-list?limit=100&page={}&sort_by=lastChecked&sort_type=desc'.format(
                i)
            data = WebRequest().get(url, proxies = conf.proxies if conf.useProxy else None, timeout=10).json['data']
            for each in data:
                yield "%s:%s" % (each['ip'], each['port'])
            sleep(5)

    @staticmethod
    def freeProxy08(page_count=5):
        for i in range(1, page_count + 1):
            url = 'https://www.freeproxy.world/?type=&anonymity=&country=&speed=&port=&page={}'.format(i)
            html_tree = WebRequest().get(url, proxies=conf.proxies if conf.useProxy else None, timeout=10).tree
            for tr in html_tree.xpath("//table//tr"):
                ip = "".join(tr.xpath("./td[1]/text()")).strip()
                port = "".join(tr.xpath("./td[2]/a/text()")).strip()
                if ip and port:
                    yield "%s:%s" % (ip, port)

    @staticmethod
    def freeProxy09(page_count = 3):
        for i in range(1, page_count + 1):
            url = 'https://freeproxylist.cc/servers/{}.html'.format(i)
            text = WebRequest().get(url, proxies = conf.proxies if conf.useProxy else None, timeout=10).text
            proxies = re.findall(r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td>(\d+)</td>', text)
            for proxy in proxies:
                yield ':'.join(proxy)
            sleep(5)

    @staticmethod
    def freeProxy10(page_count = 5):
        for i in range(1, page_count + 1):
            url = 'https://cn.proxy-tools.com/proxy/http?page={}'.format(i)
            html_tree = WebRequest().get(url, proxies = conf.proxies if conf.useProxy else None, timeout=10).tree
            for tr in html_tree.xpath("//table//tr"):
                ip = "".join(tr.xpath("./td[1]/text()")).strip()
                port = 80
                if ip and port:
                    yield "%s:%s" % (ip, port)
            sleep(5)

    @staticmethod
    def customProxy01():
        urls = [
            'https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/http.txt',
            'https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/https.txt',
            'https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/socks4.txt',
            'https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/socks5.txt',
            'https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/http/data.txt',
            'https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/socks4/data.txt',
            'https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/socks5/data.txt',
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://www.proxy-list.download/api/v1/get?type=socks4',
            'https://www.proxy-list.download/api/v1/get?type=socks5',
            'https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=5000&country=all&ssl=all&anonymity=all',
            'https://api.proxyscrape.com/?request=getproxies&proxytype=socks4&timeout=5000&country=all',
            'https://api.proxyscrape.com/?request=getproxies&proxytype=socks5&timeout=5000&country=all'
        ]
        for url in urls:
            text = WebRequest().get(url, proxies = conf.proxies if conf.useProxy else None, timeout=10).text
            matches = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', text)
            for proxy in matches:
                yield proxy


if __name__ == '__main__':
    p = ProxyFetcher()
    for _ in p.freeProxy10():
        print(_)
