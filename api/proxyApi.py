# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File Name：     ProxyApi.py
   Description :   WebApi
   Author :       JHao
   date：          2016/12/4
-------------------------------------------------
   Change Activity:
                   2016/12/04: WebApi
                   2019/08/14: 集成Gunicorn启动方式
                   2020/06/23: 新增pop接口
                   2022/07/21: 更新count接口
                   2025/05/14: 更新所有接口，支持socks4/5
-------------------------------------------------
"""
__author__ = 'JHao'

import platform
from typing import Counter

from werkzeug.wrappers import Response
from flask import Flask, jsonify, request

from util.six import iteritems
from helper.proxy import Proxy
from handler.proxyHandler import ProxyHandler
from handler.configHandler import ConfigHandler

app = Flask(__name__)
conf = ConfigHandler()
proxy_handler = ProxyHandler()


class JsonResponse(Response):
    @classmethod
    def force_type(cls, response, environ=None):
        if isinstance(response, (dict, list)):
            response = jsonify(response)

        return super(JsonResponse, cls).force_type(response, environ)


app.response_class = JsonResponse

api_list = [
    {"url": "/get", "params": "type: 'http|https|socks4|socks5 单选', region: '代理地区, 中文 e.g. 香港', anonymous: '0，1，2'", "desc": "get a proxy"},
    {"url": "/gettxt", "params": "type: 'http|https|socks4|socks5 单选', region: '代理地区, 中文 e.g. 香港', anonymous: '0，1，2'", "desc": "get a proxy by txt"},
    {"url": "/pop", "params": "type: 'http|https|socks4|socks5 单选', region: '代理地区, 中文 e.g. 香港', anonymous: '0，1，2'", "desc": "get and delete a proxy"},
    {"url": "/poptxt", "params": "type: 'http|https|socks4|socks5 单选', region: '代理地区, 中文 e.g. 香港', anonymous: '0，1，2'", "desc": "get and delete a proxy by txt"},
    {"url": "/delete", "params": "proxy: 'e.g. 127.0.0.1:8080'", "desc": "delete an unable proxy"},
    {"url": "/all", "params": "type: 'http|https|socks4|socks5 单选', region: '代理地区, 中文 e.g. 香港', anonymous: '0，1，2'", "desc": "get all proxy from proxy pool"},
    {"url": "/alltxt", "params": "type: 'http|https|socks4|socks5 单选', region: '代理地区, 中文 e.g. 香港', anonymous: '0，1，2'", "desc": "get all proxy from proxy pool by txt"},
    {"url": "/count", "params": "", "desc": "return proxy count"}
    # 'refresh': 'refresh proxy pool',
]


@app.route('/')
def index():
    return {'url': api_list}


@app.route('/get/')
def get():
    proxy_type = request.args.get("type", "").lower()
    region = request.args.get("region", "").lower()
    try:
        anonymous = int(request.args.get("anonymous", '').lower())
    except:
        anonymous = -1
    proxy = proxy_handler.get(proxy_type, region, anonymous)
    return proxy.to_dict if proxy else {"code": 0, "src": "no proxy"}

@app.route('/gettxt/')
def gettxt():
    proxy_type = request.args.get("type", "").lower()
    region = request.args.get("region", "").lower()
    try:
        anonymous = int(request.args.get("anonymous", '').lower())
    except:
        anonymous = -1
    proxy = proxy_handler.get(proxy_type, region, anonymous)
    return proxy._proxy if proxy else {"code": 0, "src": "no proxy"}


@app.route('/pop/')
def pop():
    proxy_type = request.args.get("type", "").lower()
    region = request.args.get("region", "").lower()
    try:
        anonymous = int(request.args.get("anonymous", '').lower())
    except:
        anonymous = -1
    proxy = proxy_handler.pop(proxy_type, region, anonymous)
    return proxy.to_dict if proxy else {"code": 0, "src": "no proxy"}

@app.route('/poptxt/')
def poptxt():
    proxy_type = request.args.get("type", "").lower()
    region = request.args.get("region", "").lower()
    try:
        anonymous = int(request.args.get("anonymous", '').lower())
    except:
        anonymous = -1
    proxy = proxy_handler.pop(proxy_type, region, anonymous)
    return proxy._proxy if proxy else {"code": 0, "src": "no proxy"}

@app.route('/refresh/')
def refresh():
    # TODO refresh会有守护程序定时执行，由api直接调用性能较差，暂不使用
    return 'success'


@app.route('/all/')
def getAll():
    proxy_type = request.args.get("type", "").lower()
    region = request.args.get("region", "").lower()
    try:
        anonymous = int(request.args.get("anonymous", '').lower())
    except:
        anonymous = -1
    proxies = proxy_handler.getAll(proxy_type, region, anonymous)
    return jsonify([_.to_dict for _ in proxies])

@app.route('/alltxt/')
def getAllTxt():
    proxy_type = request.args.get("type", "").lower()
    region = request.args.get("region", "").lower()
    try:
        anonymous = int(request.args.get("anonymous", '').lower())
    except:
        anonymous = -1
    proxies = proxy_handler.getAll(proxy_type, region, anonymous)
    return '\n'.join([str(_.proxy) for _ in proxies])


@app.route('/delete/', methods=['GET'])
def delete():
    proxy = request.args.get('proxy')
    status = proxy_handler.delete(Proxy(proxy))
    return {"code": 0, "src": status}

@app.route('/cleardb/', methods=['GET'])
def cleardb():
    status = proxy_handler.cleardb()
    return {"code": 0, "src": status}

@app.route('/count/')
def getCount():
    proxies = proxy_handler.getAll()
    proxy_type_counter = Counter()
    source_counter = Counter()
    for proxy in proxies:
        # 直接访问属性 proxy.proxy_type
        for ptype in getattr(proxy, "proxy_type", []):
            proxy_type_counter[ptype] += 1
        # 直接访问 proxy.source
        for src in getattr(proxy, "source", "").split("/"):
            if src:
                source_counter[src] += 1
    return {
        "proxy_type": dict(proxy_type_counter),
        "source": dict(source_counter),
        "count": len(proxies)
    }


def runFlask():
    if platform.system() == "Windows":
        app.run(host=conf.serverHost, port=conf.serverPort)
    else:
        import gunicorn.app.base

        class StandaloneApplication(gunicorn.app.base.BaseApplication):

            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super(StandaloneApplication, self).__init__()

            def load_config(self):
                _config = dict([(key, value) for key, value in iteritems(self.options)
                                if key in self.cfg.settings and value is not None])
                for key, value in iteritems(_config):
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        _options = {
            'bind': '%s:%s' % (conf.serverHost, conf.serverPort),
            'workers': 4,
            'accesslog': '-',  # log to stdout
            'access_log_format': '%(h)s %(l)s %(t)s "%(r)s" %(s)s "%(a)s"'
        }
        StandaloneApplication(app, _options).run()


if __name__ == '__main__':
    runFlask()
