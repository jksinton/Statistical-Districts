#!/usr/bin/env python

# This file is part of Statistical Districts.
# 
# Copyright (c) 2017, James Sinton
# All rights reserved.
# 
# Released under the BSD 3-Clause License
# See https://github.com/jksinton/Statistical-Districts/blob/master/LICENSE

import os

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.gen

WEB_SERVER_ADDRESS = ('0.0.0.0', 8000)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


def main():
    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
    }
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
         ], **settings
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(WEB_SERVER_ADDRESS[1], WEB_SERVER_ADDRESS[0])
    print "Listening on port:", WEB_SERVER_ADDRESS[1]
 
    main_loop = tornado.ioloop.IOLoop.instance()
    main_loop.start()

if __name__ == "__main__":
    main()
