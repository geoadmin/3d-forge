# -*- coding: utf-8 -*-


import sys
import SimpleHTTPServer
import SocketServer


if len(sys.argv) > 1:
    if not sys.argv[1].isdigit():
        sys.exit(1)
    PORT = int(sys.argv[1])


if __name__ == '__main__':
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", PORT), Handler)
    print 'Serving at port: %s' % PORT
    httpd.serve_forever()
