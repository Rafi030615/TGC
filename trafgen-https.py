import requests
import threading
import numpy as np
from datetime import datetime
import csv
import pandas as pd
import argparse
import time
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

def zipf_mandelbrot(N, q, s):
    ranks = np.arange(1, N + 1)
    weights = (ranks + q) ** -s
    probabilities = weights / weights.sum()
    return probabilities

def log_to_csv(data, writer):
    writer.writerow(data)

def fetch_content_size(url, base_url, executor):
    content_size = 0
    try:
        response = requests.get(url)
        content_size += len(response.content)
        
        # Extract and fetch linked resources asynchronously
        links = extract_links(response.text, base_url)
        futures = [executor.submit(requests.get, link) for link in links]
        for future in as_completed(futures):
            try:
                content_response = future.result()
                content_size += len(content_response.content)
            except requests.exceptions.RequestException:
                pass
    except requests.exceptions.RequestException:
        pass
    return content_size

def extract_links(html, base_url):
    links = []
    start = 0
    while True:
        start_link = html.find("src=\"", start)
        if start_link == -1:
            start_link = html.find("href=\"", start)
        if start_link == -1:
            break
        start_quote = html.find("\"", start_link + 1)
        end_quote = html.find("\"", start_quote + 1)
        link = html[start_quote + 1: end_quote]
        if link.startswith(("https", "//")):
            links.append(link if link.startswith("https") else "https:" + link)
        else:
            links.append(urljoin(base_url, link))
        start = end_quote + 1
    return links

def make_request(url, results, writer):
    try:
        start_time = datetime.now()
        with ThreadPoolExecutor(max_workers=10) as executor:
            total_content_size = fetch_content_size(url, url, executor)
        end_time = datetime.now()
        
        rtt = (end_time - start_time).total_seconds() * 1000  # Convert to milliseconds
        throughput = total_content_size / rtt  # Throughput in bytes per millisecond
        
        log_data = [url, start_time, end_time, rtt, 200, total_content_size, throughput]
        results.append(log_data)
        log_to_csv(log_data, writer)
        print(f"Request to {url} completed with status code: 200, RTT: {rtt:.6f} ms, Total content size: {total_content_size} bytes, Throughput: {throughput:.2f} bytes/ms")
    except requests.exceptions.RequestException as e:
        end_time = datetime.now()
        rtt = (end_time - start_time).total_seconds() * 1000  # Convert to milliseconds
        log_data = [url, start_time, end_time, rtt, f"Failed: {e}", 0, 0]
        results.append(log_data)
        log_to_csv(log_data, writer)
        print(f"Request to {url} failed: {e}, RTT: {rtt:.6f} ms")
    
def generate_traffic(urls, num_requests, requests_per_second, zipf_params):
    probabilities = zipf_mandelbrot(len(urls), *zipf_params)
    threads = []
    interval = 1 / requests_per_second
    results = []
    
    with open('request_log_https.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        
        for _ in range(num_requests):
            url = np.random.choice(urls, p=probabilities)
            thread = threading.Thread(target=make_request, args=(url, results, writer))
            thread.start()
            threads.append(thread)
            time.sleep(interval)
        
        for thread in threads:
            thread.join()
    
    print("Traffic generation completed.")
    return results

def calculate_totals_and_averages(results):
    total_rtt = sum(result[3] for result in results)
    total_throughput = sum(result[6] for result in results)
    average_rtt = total_rtt / len(results)
    average_throughput = total_throughput / len(results)
    
    total_data = ["Total", "", "", total_rtt, "", "", total_throughput]
    average_data = ["Average", "", "", average_rtt, "", "", average_throughput]
    
    return total_data, average_data

def main():
    parser = argparse.ArgumentParser(description='Generate traffic for URLs with Zipf distribution.')
    parser.add_argument('-url', type=int, required=True, help='Number of URLs')
    parser.add_argument('-req', type=int, required=True, help='Number of requests')
    parser.add_argument('-rps', type=float, required=True, help='Requests per second')
    parser.add_argument('-zipf', type=float, nargs=2, required=True, help='Zipf parameters: q and s')

    args = parser.parse_args()

    number_of_requests = args.req
    requests_per_second = args.rps
    zipf_params = tuple(args.zipf)

    # Load URLs from CSV
    df = pd.read_csv('url_bineca_https.csv')
    urls = df['URL'].tolist()

    # Initialize the CSV file
    with open('request_log_https.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["URL", "Start Time", "End Time", "RTT (ms)", "Status Code", "Content Size (bytes)", "Throughput (bytes/ms)"])

    results = generate_traffic(urls, number_of_requests, requests_per_second, zipf_params)
    
    total_data, average_data = calculate_totals_and_averages(results)
    
    with open('request_log_https.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(total_data)
        writer.writerow(average_data)
    
    print(f"Total RTT: {total_data[3]:.2f} ms, Total Throughput: {total_data[6]:.2f} bytes/ms")
    print(f"Average RTT: {average_data[3]:.2f} ms, Average Throughput: {average_data[6]:.2f} bytes/ms")

if __name__ == "__main__":
    main()
