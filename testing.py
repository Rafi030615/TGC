import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import socket

class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_ip, **kwargs):
        self.source_ip = source_ip
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['socket_options'] = [(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(self.source_ip))]
        kwargs['source_address'] = (self.source_ip, 0)
        super().init_poolmanager(*args, **kwargs)

# 🔥 Bikin session yang maksa lewat uesimtun0 (IP 10.60.0.1)
session = requests.Session()
session.mount('http://', SourceIPAdapter('10.60.0.1'))
session.mount('https://', SourceIPAdapter('10.60.0.1'))

# 💀 Di fungsi lo tinggal ganti requests.get jadi session.get

def fetch_content_size(url):
    response = session.get(url)
    return len(response.content)

def make_request(url):
    response = session.get(url)
    return response.status_code

# 🚀 Contoh pemakaian
def main():
    url = "http://testasp.vulnweb.com/"  # Ganti URL sesuai kebutuhan
    print("Content size:", fetch_content_size(url))
    print("Status code:", make_request(url))

if __name__ == "__main__":
    main()
