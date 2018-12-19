# coding: utf-8
#

from __future__ import print_function

import os
import argparse

import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
from tornado.log import enable_pretty_logging

enable_pretty_logging()


class MainHandler(tornado.web.RequestHandler):
    async def get(self):
        yield gen.sleep(.5)
        self.write("Hello, world")
        # save index.html into templates/
        # self.render("index.html")


class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")
    
    def on_message(self, message):
        print("receive message:", message)
        self.ping("OK")
        self.write_message("You said: " + message)
    
    def on_pong(self, message):
        print("on pong", message)
        # self.ws_connection._write_frame(True, 0x9, message) # send pong
        
    def on_close(self):
        print("WebSocket closed")


class ProxyTesterhomeHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        body = yield self.get_testerhome()
        self.write(body)

    @gen.coroutine
    def get_testerhome(self):
        http_client = AsyncHTTPClient()
        response = yield http_client.fetch("https://testerhome.com/")
        raise gen.Return(response.body)


def make_app(**settings):
    settings['template_path'] = 'templates'
    settings['static_path'] = 'static'
    settings['cookie_secret'] = os.environ.get("SECRET", "SECRET:_")
    settings['login_url'] = '/login'
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/testerhome", ProxyTesterhomeHandler),
        (r"/ws/echo", EchoWebSocket),
    ], **settings)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--debug', action='store_true', help='hot reload')
    parser.add_argument('--port', type=int, default=7000, help='listen port')
    args = parser.parse_args()

    app = make_app(debug=args.debug)
    app.listen(args.port)
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        # only works in unix system
        # If you are using mac, consider using https://github.com/codeskyblue/kexec/tree/master/cmds/kexec
        tornado.ioloop.IOLoop.instance().stop()