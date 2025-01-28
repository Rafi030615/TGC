import subprocess
import time
from datetime import datetime

def ping_with_interface(url, interface="uesimtun0", timeout=60):
    """Ping URL with specified network interface."""
    try:
        start_time = datetime.now()
        command = f"ping -I {interface} {url}"
        print(f"Running command: {command}")

        # Jalankan ping dengan timeout yang lebih lama
        process = subprocess.run(
            command, 
            shell=True,  # Jalankan di shell agar bisa pakai interface
            capture_output=True, 
            text=True, 
            timeout=timeout  # Timeout bisa disesuaikan
        )

        end_time = datetime.now()
        rtt = (end_time - start_time).total_seconds() * 1000  # RTT dalam ms

        if process.returncode == 0:
            output = process.stdout
            content_size = len(output.encode('utf-8'))  # Ukuran konten (bytes)
            throughput = content_size / rtt if rtt > 0 else 0  # Throughput per ms
            print(f"Ping Success: RTT = {rtt:.2f} ms, Content Size = {content_size} bytes, Throughput = {throughput:.2f} bytes/ms")
            return 200, content_size, rtt, throughput
        else:
            print(f"Ping Failed: {process.stderr}")
            return process.returncode, 0, rtt, 0

    except subprocess.TimeoutExpired:
        print(f"Timeout expired for {url} after {timeout} seconds.")
        return "Timeout", 0, 30000, 0  # Timeout error, bisa diatur sesuai kebutuhan

def main():
    # URL yang ingin diuji
    url = "testhtml5.vulnweb.com"  # Ganti dengan URL yang ingin kamu ping
    interface = "uesimtun0"  # Interface jaringan yang digunakan
    timeout = 60  # Timeout dalam detik

    # Panggil fungsi untuk ping
    status_code, content_size, rtt, throughput = ping_with_interface(url, interface, timeout)

    # Cek hasilnya
    if status_code == 200:
        print(f"Ping to {url} successful! RTT: {rtt:.2f} ms, Throughput: {throughput:.2f} bytes/ms")
    else:
        print(f"Ping to {url} failed with status: {status_code}.")

if __name__ == "__main__":
    main()
