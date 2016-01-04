import tornado
import ssl
import struct
import json
import socket
import itertools

from tornado.gen import coroutine, with_timeout
from tornado.tcpclient import TCPClient
from tornado.ioloop import IOLoop


class APNS(object):
    def __init__(self, debug=True, certfile=None):
        self.gateway_url = "gateway.sandbox.push.apple.com"
        if not debug:
            self.gateway_url = "gateway.push.apple.com"
        self.gateway_port = 2195
        self.ssl_opts = {
            "certfile": certfile,
            "ssl_version": ssl.PROTOCOL_TLSv1
        }

    @coroutine
    def send_notifications(self, data):
        tcp_client = TCPClient()
        self.stream = yield tcp_client.connect(self.gateway_url,
                                               self.gateway_port,
                                               ssl_options=self.ssl_opts)

        for (item, device_tokens) in data:
            for token in device_tokens:
                msg = json.dumps(item, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                frame_length = 1 + 2 + 32 + 1 + 2 + len(msg) + 1 + 2 + 1
                message = struct.pack("!BIBH32sBH%dsBHB" % len(msg), 2, frame_length,
                                      1, 32, token.decode("hex"),
                                      2, len(msg), msg,
                                      5, 1, 10)
                self.stream.write(message)


class APNSFeedback(object):
    def __init__(self, debug=True, certfile=None):
        self.gateway_url = "feedback.sandbox.push.apple.com"
        if not debug:
            self.gateway_url = "feedback.push.apple.com"
        self.gateway_port = 2196
        self.ssl_opts = {
            "certfile": certfile,
            "ssl_version": ssl.PROTOCOL_TLSv1
        }

    def fetch(self, datetime=None):
        sock = socket.socket()
        sock.setblocking(True)
        sock = ssl.wrap_socket(sock, **self.ssl_opts)
        sock.connect((self.gateway_url, self.gateway_port))
        buff = bytearray(4096)
        sock.recv_into(buff)
        sock.close()
        response = ()
        if len(buff) >= 38:
            response = struct.unpack_from("!IH32s", buff)
        device_tokens = []
        response_tuples = itertools.izip_longest(*([iter(response)] * 3))
        for row in response_tuples:
            if row[0] < datetime.strftime("%s"):
                continue
            device_tokens.append(row[2].encode("hex"))
        return device_tokens
