import argparse
import psutil
import requests
import time
import socket
from ping3 import ping


def get_ip_from_interface(interface_name):
    addrs = psutil.net_if_addrs()
    if interface_name not in addrs:
        raise ValueError(f"Interface {interface_name} tidak ditemukan!")
    for snic in addrs[interface_name]:
        if snic.family == socket.AF_INET:
            return snic.address
    raise ValueError(f"Tidak ada alamat IPv4 untuk interface {interface_name}!")


def measure_rtt_latency(target_ip, count=4):
    rtt_list = []
    for _ in range(count):
        result = ping(target_ip, unit='ms')
        if result is not None:
            rtt_list.append(result)
        time.sleep(0.5)
    if not rtt_list:
        raise Exception("Ping gagal. Cek koneksi ke target.")
    avg_rtt = sum(rtt_list) / len(rtt_list)
    min_rtt = min(rtt_list)
    max_rtt = max(rtt_list)
    return avg_rtt, min_rtt, max_rtt


def measure_throughput(url, duration_sec=10):
    start_time = time.time()
    bytes_received = 0
    session = requests.Session()

    while time.time() - start_time < duration_sec:
        try:
            response = session.get(url, stream=True, timeout=5)
            for chunk in response.iter_content(chunk_size=4096):
                bytes_received += len(chunk)
        except Exception as e:
            print(f"Request error: {e}")
            continue

    elapsed = time.time() - start_time
    throughput_mbps = (bytes_received * 8) / (elapsed * 1e6)
    return throughput_mbps, bytes_received, elapsed


def main():
    parser = argparse.ArgumentParser(description="OAI-Compatible Traffic Generator")
    parser.add_argument('-I', '--interface', required=True, help='Nama interface (misal: uesimtun0)')
    parser.add_argument('-U', '--url', required=True, help='Target URL (misal: http://10.0.0.1/file)')
    parser.add_argument('-p', '--ping-count', type=int, default=4, help='Jumlah ping untuk ukur RTT')
    parser.add_argument('-t', '--throughput-duration', type=int, default=10, help='Durasi test throughput (detik)')

    args = parser.parse_args()

    try:
        print(f"[INFO] Menggunakan interface: {args.interface}")
        local_ip = get_ip_from_interface(args.interface)
        print(f"[INFO] IP Address dari {args.interface}: {local_ip}")
    except ValueError as e:
        print(f"[ERROR] {e}")
        return

    # Resolving target IP dari URL
    try:
        target_host = args.url.split("//")[-1].split("/")[0]
        target_ip = socket.gethostbyname(target_host)
        print(f"[INFO] Target IP: {target_ip}")
    except Exception as e:
        print(f"[ERROR] Tidak bisa resolve URL: {e}")
        return

    print("\n=== Mengukur RTT dan Latency ===")
    try:
        avg_rtt, min_rtt, max_rtt = measure_rtt_latency(target_ip, args.ping_count)
        print(f"RTT Rata-rata: {avg_rtt:.2f} ms")
        print(f"RTT Minimum : {min_rtt:.2f} ms")
        print(f"RTT Maksimum: {max_rtt:.2f} ms")
    except Exception as e:
        print(f"[ERROR] {e}")

    print("\n=== Mengukur Throughput ===")
    try:
        tp, bytes_recv, elapsed = measure_throughput(args.url, args.throughput_duration)
        print(f"Total Data Diterima: {bytes_recv / 1e6:.2f} MB")
        print(f"Durasi: {elapsed:.2f} detik")
        print(f"Throughput: {tp:.2f} Mbps")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
