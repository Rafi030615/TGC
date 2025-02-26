import requests
import re
import time
from urllib.parse import urljoin

def extract_links(html, base_url):
    """🔗 Cari semua link resource dari HTML pake regex (tanpa BeautifulSoup)"""
    # Ambil semua src (gambar, script) & href (CSS)
    src_links = re.findall(r'src=["\'](.*?)["\']', html, re.IGNORECASE)
    href_links = re.findall(r'href=["\'](.*?)["\']', html, re.IGNORECASE)
    all_links = src_links + href_links
    # Gabungkan dengan base_url
    full_links = [urljoin(base_url, link) for link in all_links]
    return full_links

def fetch_content_size(url):
    """📦 Fetch semua content dan hitung size total"""
    total_size = 0
    try:
        response = requests.get(url)
        total_size += len(response.content)
        links = extract_links(response.text, url)
        for link in links:
            try:
                res = requests.get(link)
                total_size += len(res.content)
            except requests.exceptions.RequestException:
                pass
    except requests.exceptions.RequestException as e:
        print(f"💥 Error di {url}: {e}")
    return total_size

def measure_rtt_throughput(url):
    """🕒 Ukur RTT, Latency, Throughput"""
    start_time = time.time()
    total_size_bytes = fetch_content_size(url)
    end_time = time.time()

    # 💾 Konversi ukuran
    total_size_kb = total_size_bytes / 1024
    total_size_mb = total_size_kb / 1024

    # ⏱️ Hitung RTT & Latency
    total_time_sec = end_time - start_time
    rtt = total_time_sec * 1000
    latency = rtt / 2

    # ⚡ Hitung Throughput
    throughput_kbps = (total_size_kb * 8) / total_time_sec
    throughput_mbps = throughput_kbps / 1024

    # 📝 Output hasil
    print(f"⚡ URL: {url}")
    print(f"🕒 RTT: {rtt:.2f} ms")
    print(f"⏳ Latency: {latency:.2f} ms")
    print(f"📦 Total Size: {total_size_bytes} bytes ({total_size_kb:.2f} KB / {total_size_mb:.2f} MB)")
    print(f"🚀 Throughput: {throughput_kbps:.2f} Kbps ({throughput_mbps:.2f} Mbps)")

# 🌐 Coba jalanin
url = 'https://aljazeera.com/'
measure_rtt_throughput(url)
