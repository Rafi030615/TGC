import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import socket

class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_address, **kwargs):
        self.source_address = source_address
        super(SourceIPAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['source_address'] = (self.source_address, 0)
        return super(SourceIPAdapter, self).init_poolmanager(*args, **kwargs)

session = requests.Session()
session.mount('http://', SourceIPAdapter('10.60.0.1'))
session.mount('https://', SourceIPAdapter('10.60.0.1'))

# 🔥 Request dipaksa lewat uesimtun0
response = session.get('http://testasp.vulnweb.com/')
print(f"Status Code: {response.status_code}")
print(f"Content: {response.text[:500]}")  # Cetak 500 karakter pertama
