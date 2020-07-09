""" Snapd bash commands recreated for Python using the Core REST API """

# Built on example shared by SO user david-k-hess:
# https://stackoverflow.com/a/59594889

import requests
import socket

from urllib3.connection import HTTPConnection
from urllib3.connectionpool import HTTPConnectionPool
from requests.adapters import HTTPAdapter


class SnapdConnection(HTTPConnection):
    def __init__(self):
        super().__init__("localhost")

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect("/run/snapd.socket")

class SnapdConnectionPool(HTTPConnectionPool):
    def __init__(self):
        super().__init__("localhost")

    def _new_conn(self):
        return SnapdConnection()

class SnapdAdapter(HTTPAdapter):
    def get_connection(self, url, proxies=None):
        return SnapdConnectionPool()

class Snap():
    def __init__(self):
        self.session = requests.Session()
        self.fake_http = 'http://snapd/'
        self.session.mount(self.fake_http, SnapdAdapter())

    def list(self):
        payload = '/v2/snaps'
        result = self.session.get(self.fake_http + payload).json()['result']
        return result

    def info(self, snap):
        payload = '/v2/snaps/' + snap
        result = self.session.get(self.fake_http + payload).json()['result']
        return result

    def refresh_list(self):
        payload = '/v2/find?select=refresh'
        result = self.session.get(self.fake_http + payload).json()['result']
        if type(result) is dict:
            print(result['message'])
            result = []
        return result

    def system_info(self):
        payload = '/v2/system-info'
        result = self.session.get(self.fake_http + payload).json()['result']
        return result


snap = Snap()
