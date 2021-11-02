""" Snapd bash commands recreated for Python using the Core REST API """

# Built on example shared by SO user david-k-hess:
# https://stackoverflow.com/a/59594889

import logging
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

    # def close(self):
    #     self.sock.close()

class SnapdConnectionPool(HTTPConnectionPool):
    def __init__(self):
        super().__init__("localhost")

    def _new_conn(self):
        return SnapdConnection()

class SnapdAdapter(HTTPAdapter):
    def __init__(self):
        super().__init__()

    def get_connection(self, url, proxies=None):
        return SnapdConnectionPool()

class Snap():
    def __init__(self):
        self.session = requests.Session()
        self.fake_http = 'http://snapd'
        self.session.mount(self.fake_http, SnapdAdapter())

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def get(self, node, child=None):
        """
        Some calls require elevated privileges.
        """
        typical = [
            'connections',
            'find?select=refresh',
            'snaps',
            'system-info',
        ]
        path = f"{self.fake_http}/"
        if node in typical:
            path = f"{path}v2/{node}"
            if node == 'snaps' and child:
                path = f"{path}/{child}"
        elif node == 'system':
            path = f"{path}v2/snaps/{node}/conf"
        if path == self.fake_http:
            return None

        return self.session.get(path).json()

    def list(self):
        return self.get('snaps').get('result')

    def info(self, snap):
        return self.get('snaps', snap).get('result')

    def get_refresh_list(self):
        result = self.get('find?select=refresh').get('result')
        refresh_list = None
        if isinstance(result, list):
            refresh_list = result
        return refresh_list

    def system_info(self):
        payload = '/v2/system-info'
        result = self.session.get(self.fake_http + payload).json()['result']
        return result
