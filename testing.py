import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import socket
import time

class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_address, **kwargs):
        self.source_address = source_address
        super(SourceIPAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['source_address'] = (self.source_address, 0)
        return super(SourceIPAdapter, self).init_poolmanager(*args, **kwargs)

session = requests.Session()
session.mount('http://', SourceIPAdapter('10.60.0.2'))
session.mount('https://', SourceIPAdapter('10.60.0.2'))

# 🚀 Mulai hitung RTT
url = 'http://testasp.vulnweb.com/'
start_time = time.time()  # ⏱️ Waktu sebelum request
try:
    response = session.get(url)
    end_time = time.time()  # ⏱️ Waktu setelah request

    rtt = (end_time - start_time) * 1000  # RTT dalam ms
    content_size_bytes = len(response.content)  # Ukuran konten dalam byte
    content_size_kb = content_size_bytes / 1024  # Konversi ke KB

    print(f"⚡ Status Code: {response.status_code}")
    print(f"🕒 RTT: {rtt:.2f} ms")  # RTT dengan 2 desimal
    print(f"📦 Content Size: {content_size_bytes} bytes ({content_size_kb:.2f} KB)")
    print(f"📄 Content: {response.text[:500]}")  # Cetak 500 karakter pertama
except requests.exceptions.RequestException as e:
    print(f"💥 Error: {e}")
