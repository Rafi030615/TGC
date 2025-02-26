import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import socket
import time
import re
from urllib.parse import urljoin

class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_address, **kwargs):
        self.source_address = source_address
        super(SourceIPAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['source_address'] = (self.source_address, 0)
        return super(SourceIPAdapter, self).init_poolmanager(*args, **kwargs)

def extract_links(html, base_url):
    """🔗 Cari semua link resource dari HTML pake regex (tanpa BeautifulSoup)"""
    src_links = re.findall(r'src=["\'](.*?)["\']', html, re.IGNORECASE)
    href_links = re.findall(r'href=["\'](.*?)["\']', html, re.IGNORECASE)
    full_links = [urljoin(base_url, link) for link in src_links + href_links]
    return full_links

def fetch_content_size(session, url):
    """📦 Fetch semua content dan hitung size total"""
    total_size = 0
    try:
        response = session.get(url)
        total_size += len(response.content)
        links = extract_links(response.text, url)
        for link in links:
            try:
                res = session.get(link)
                total_size += len(res.content)
            except requests.exceptions.RequestException:
                pass
    except requests.exceptions.RequestException as e:
        print(f"💥 Error di {url}: {e}")
    return total_size

def measure_rtt_throughput(session, url):
    """🕒 Ukur RTT, Latency, Throughput"""
    start_time = time.time()
    total_size_bytes = fetch_content_size(session, url)
    end_time = time.time()

    total_size_kb = total_size_bytes / 1024
    total_size_mb = total_size_kb / 1024
    total_time_sec = end_time - start_time
    rtt = total_time_sec * 1000
    latency = rtt / 2
    throughput_kbps = (total_size_kb * 8) / total_time_sec
    throughput_mbps = throughput_kbps / 1024

    print(f"⚡ URL: {url}")
    print(f"🕒 RTT: {rtt:.2f} ms")
    print(f"⏳ Latency: {latency:.2f} ms")
    print(f"📦 Total Size: {total_size_bytes} bytes ({total_size_kb:.2f} KB / {total_size_mb:.2f} MB)")
    print(f"🚀 Throughput: {throughput_kbps:.2f} Kbps ({throughput_mbps:.2f} Mbps)")

# 🚀 Session dengan source IP dipaksa lewat uesimtun0
session = requests.Session()
session.mount('http://', SourceIPAdapter('10.60.0.2'))
session.mount('https://', SourceIPAdapter('10.60.0.2'))

# 🌐 Coba jalanin
url = 'https://aljazeera.com/'
measure_rtt_throughput(session, url)
