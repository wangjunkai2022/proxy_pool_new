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

import base64
import re
import json
from time import sleep
import quickjs
from handler.configHandler import ConfigHandler
from util.webRequest import WebRequest

conf = ConfigHandler()
ctx = quickjs.Context()


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
            url = 'https://www.zdaye.com/free/{}'.format("" if i == 1 else i)
            html_tree = WebRequest().get(url, verify=False).tree
            for tr in html_tree.xpath("//table//tr"):
                ip = "".join(tr.xpath("./td[1]/text()")).strip()
                port = "".join(tr.xpath("./td[2]/text()")).strip()
                yield "%s:%s" % (ip, port)
            sleep(8)

    @staticmethod
    def freeProxy02():
        """ FreeProxyList http://free-proxy-list.net"""
        url = 'http://free-proxy-list.net'
        html_tree = WebRequest().get(url, proxies=conf.proxies if conf.useProxy else None, verify=False).tree
        proxies = html_tree.xpath("//*[@id='raw']/div/div/div[2]/textarea/text()")
        matches = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', proxies[0])
        for proxy in matches:
            yield proxy

    @staticmethod
    def freeProxy03(page_count=8):
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
            text = WebRequest().get(url).text
            pattern = re.compile(r'fpsList\s*=\s*(\[\s*\{.*?\}\s*\])', re.S)
            match = pattern.search(text)
            if not match:
                continue
            json_str = match.group(1)
            data = json.loads(json_str)
            for proxy in data:
                yield "%s:%s" % (proxy['ip'], proxy['port'])
            sleep(5)  # 必须sleep 不然第二条请求不到数据

    @staticmethod
    def freeProxy04():
        """ 稻壳代理 https://www.docip.net/ """
        r = WebRequest().get("https://www.docip.net/data/free.json", proxies=conf.proxies if conf.useProxy else None,
                             timeout=10)
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
            r = request.get(url, proxies=conf.proxies if conf.useProxy else None, timeout=10)
            proxies = re.findall(r"Proxy\('(.*?)'\)", r.text)
            for proxy in proxies:
                yield base64.b64decode(proxy).decode()
            sleep(2)

    @staticmethod
    def freeProxy06(page_count=3):
        http_pattern = [
            'https://list.proxylistplus.com/Fresh-HTTP-Proxy-List-{}'
        ]
        socks_pattern = [
            'https://list.proxylistplus.com/SSL-List-{}',
            'https://list.proxylistplus.com/Socks-List-{}',
        ]
        url_list = []
        for page_index in range(1, page_count + 1):
            for pattern in http_pattern:
                url_list.append(pattern.format(page_index))
        for page_index in range(1, page_count):
            for pattern in socks_pattern:
                url_list.append(pattern.format(page_index))
        request = WebRequest()
        for url in url_list:
            r = request.get(url, proxies=conf.proxies if conf.useProxy else None, timeout=10)
            proxies = re.findall(r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td>(\d+)</td>', r.text)
            for proxy in proxies:
                yield ':'.join(proxy)
            sleep(2)

    @staticmethod
    def freeProxy07(page_count=3):
        for i in range(1, page_count + 1):
            url = 'https://proxylist.geonode.com/api/proxy-list?limit=100&page={}&sort_by=lastChecked&sort_type=desc'.format(
                i)
            data = WebRequest().get(url, proxies=conf.proxies if conf.useProxy else None, timeout=10).json['data']
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
            sleep(2)

    @staticmethod
    def freeProxy09(page_count=3):
        for i in range(1, page_count + 1):
            url = 'https://freeproxylist.cc/servers/{}.html'.format(i)
            text = WebRequest().get(url, proxies=conf.proxies if conf.useProxy else None, timeout=10).text
            proxies = re.findall(r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td>(\d+)</td>', text)
            for proxy in proxies:
                yield ':'.join(proxy)
            sleep(5)

    @staticmethod
    def freeProxy10(page_count=8):
        for i in range(1, page_count + 1):
            url = 'https://cn.proxy-tools.com/proxy{}'.format("/" if i == 1 else ('?page=' + str(i)))
            html_tree = WebRequest().get(url, proxies=conf.proxies if conf.useProxy else None, timeout=10).tree
            for tr in html_tree.xpath("//table//tr"):
                ip = "".join(tr.xpath("./td[1]/text()")).strip()
                port = 80
                if ip and port:
                    yield "%s:%s" % (ip, port)
            sleep(5)

    @staticmethod
    def freeProxy11():
        """ 小幻HTTP代理 """
        url = 'https://ip.ihuan.me/today.html'
        request = WebRequest(url)
        html_tree = request.Session(url, timeout=10).tree
        href = html_tree.xpath("/html/body//div[2]/div/div/div[1]/a/@href")[0]
        sleep(2)
        href_text = request.Session('https://ip.ihuan.me' + href, timeout=10).text
        matches = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', href_text)
        for proxy in matches:
            yield proxy

    @staticmethod
    def freeProxy12(page_count=5):
        """ 89免费代理 """
        url = 'https://www.89ip.cn/'
        request = WebRequest(url)
        for i in range(1, page_count + 1):
            url = 'https://www.89ip.cn/{}'.format("" if i == 1 else ('index_{}.html'.format(i)))
            html_tree = request.Session(url, timeout=10).tree
            for tr in html_tree.xpath("//table//tr"):
                ip = "".join(tr.xpath("./td[1]/text()")).strip()
                port = "".join(tr.xpath("./td[2]/text()")).strip()
                if ip and port:
                    yield "%s:%s" % (ip, port)
            sleep(3)

    @staticmethod
    def freeProxy13():
        """ 齐云代理 """
        url = 'https://www.qiyunip.com/freeProxy/'
        html_tree = WebRequest().get(url, timeout=10).tree
        for tr in html_tree.xpath("//table//tr"):
            ip = "".join(tr.xpath("./th[1]/text()")).strip()
            port = "".join(tr.xpath("./th[2]/text()")).strip()
            if ip and port:
                yield "%s:%s" % (ip, port)

    @staticmethod
    def freeProxy14():
        """ proxy5 """
        url = 'https://proxy5.net/cn/free-proxy'
        html_tree = WebRequest().get(url, proxies=conf.proxies if conf.useProxy else None, timeout=10).tree
        for tr in html_tree.xpath("//table//tr"):
            ip = "".join(tr.xpath("./td[1]/strong/text()")).strip()
            port = "".join(tr.xpath("./td[2]/text()")).strip()
            if ip and port:
                yield "%s:%s" % (ip, port)

    @staticmethod
    def freeProxy15():
        """ proxynova """
        def extract_expr(s: str) -> str:
            start = s.find('(') + 1
            end = s.rfind(')')
            if start == 0 or end == -1:
                raise ValueError("无法在字符串中找到匹配的括号")
            return s[start:end]

        def decode_atob_in_js(js_code: str) -> str:
            """
            将 js_code 中所有 atob("…") 调用替换为对应的解码后字符串，
            比如 atob("NDcuMjU0LjM=") -> "47.254.3"
            """
            # 匹配 atob("…") 并捕获内部的 base64 文本
            pattern = re.compile(r'atob\("([^"]+)"\)')

            def _repl(m: re.Match) -> str:
                b64_str = m.group(1)
                try:
                    decoded = base64.b64decode(b64_str).decode('utf-8')
                except Exception:
                    return m.group(0)
                return f'"{decoded}"'

            return pattern.sub(_repl, js_code)

        url = 'https://www.proxynova.com/proxy-server-list/'
        html_tree = WebRequest().get(url, proxies=conf.proxies if conf.useProxy else None, timeout=10).tree
        for tr in html_tree.xpath("//*[@id='tbl_proxy_list']/tbody/tr"):
            js_tree = tr.xpath("./td[1]//script/text()")
            js_code = extract_expr(js_tree[0])
            if 'atob(' in js_code:
                js_code = decode_atob_in_js(js_code)
            ip = ctx.eval(js_code)
            port = "".join(tr.xpath("./td[2]/text()")).strip()
            if ip and port:
                yield "%s:%s" % (ip, port)

    @staticmethod
    def freeProxy16(page_count = 2):
        """ proxydb """
        url = 'https://proxydb.net/list'
        for i in range(0, page_count):
            json = {'protocols': [], 'anonlvls': [], 'offset': i * 30}
            resp = WebRequest().post(url, json=json, proxies=conf.proxies if conf.useProxy else None, timeout=10).json
            if "proxies" in resp:
                proxies = resp["proxies"]
                for proxy in proxies:
                    yield "%s:%s" % (proxy['ip'], proxy['port'])

    @staticmethod
    def customProxy01():
        """
        返回格式为 ip:port
        """
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
            'https://api.proxyscrape.com/?request=getproxies&proxytype=socks5&timeout=5000&country=all',
            'https://api.openproxylist.xyz/http.txt',
            'https://api.openproxylist.xyz/socks4.txt',
            'https://api.openproxylist.xyz/socks5.txt'
        ]
        for url in urls:
            text = WebRequest().get(url, proxies=conf.proxies if conf.useProxy else None, timeout=10).text
            matches = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', text)
            for proxy in matches:
                yield proxy
            sleep(2)


if __name__ == '__main__':
    p = ProxyFetcher()
    for _ in p.freeProxy16():
        print(_)
