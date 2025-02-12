import requests
import numpy as np
from datetime import datetime
import pandas as pd
import argparse
import time
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from joblib import load

def zipf_mandelbrot(N, q, s):
    ranks = np.arange(1, N + 1)
    weights = (ranks + q) ** -s
    probabilities = weights / weights.sum()
    return probabilities

def log_to_log(data, filename='request_log_http.log'):
    with open(filename, mode='a') as file:
        file.write('\t'.join(map(str, data)) + '\n')

def fetch_content_size(url):
    content_size = 0
    try:
        response = requests.get(url)
        content_size += len(response.content)
        
        links = extract_links(response.text, url)
        for link in links:
            try:
                content_response = requests.get(link)
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
        if link.startswith(("http", "//")):
            links.append(link if link.startswith("http") else "http:" + link)
        else:
            links.append(urljoin(base_url, link))
        start = end_quote + 1
    return links

def make_request(url, results):
    start_time = datetime.now()
    try:
        content_size = fetch_content_size(url)
        end_time = datetime.now()
        rtt = (end_time - start_time).total_seconds() * 1000
        
        if rtt < 1:
            rtt = 1
        
        throughput = content_size / rtt
        
        log_data = [url, start_time, end_time, rtt, 200, content_size, throughput]
        results.append(log_data)
        print(f"Request to {url} completed with status code: 200, RTT: {rtt:.6f} ms, Content size: {content_size} bytes, Throughput: {throughput:.2f} bytes/ms")
    except requests.exceptions.RequestException as e:
        end_time = datetime.now()
        rtt = (end_time - start_time).total_seconds() * 1000
        if rtt < 1:
            rtt = 1
        log_data = [url, start_time, end_time, rtt, f"Failed: {e}", 0, 0]
        results.append(log_data)
        print(f"Request to {url} failed: {e}, RTT: {rtt:.6f} ms")
    
    log_to_log(log_data)

def generate_traffic(urls, num_requests, requests_per_second, zipf_params):
    probabilities = zipf_mandelbrot(len(urls), *zipf_params)
    results = []
    executor = ThreadPoolExecutor(max_workers=100)
    
    total_requests = 0
    while total_requests < num_requests:
        requests_in_this_batch = min(num_requests - total_requests, int(requests_per_second * 100))
        for _ in range(requests_in_this_batch):
            url = np.random.choice(urls, p=probabilities)
            executor.submit(make_request, url, results)
            total_requests += 1
        
        time.sleep(100)
    
    executor.shutdown(wait=True)
    return results

def calculate_totals_and_averages(results):
    if not results:
        print("No results to calculate totals and averages.")
        return ["Total", "", "", 0, "", "", 0], ["Average", "", "", 0, "", "", 0]
    
    total_rtt = sum(result[3] for result in results)
    total_throughput = sum(result[6] for result in results)
    average_rtt = total_rtt / len(results)
    average_throughput = total_throughput / len(results)
    
    total_data = ["Total", "", "", total_rtt, "", "", total_throughput]
    average_data = ["Average", "", "", average_rtt, "", "", average_throughput]
    
    return total_data, average_data

def load_model_and_forecast(pickle_file, forecast_data_file, feature_columns):
    model = load(pickle_file)
    df = pd.read_csv(forecast_data_file)
    dfor = df[feature_columns]
    forecast = model.predict(dfor)
    return forecast[0]

def main():
    print("############ Tunggu Sebentar ############")
    
    parser = argparse.ArgumentParser(description='Generate traffic for URLs with Zipf distribution.')
    parser.add_argument('-url', type=int, required=True, help='Number of URLs')
    parser.add_argument('-req', type=int, required=True, help='Number of requests')
    parser.add_argument('-rps', required=True, help='Requests per second or "rf" for Random Forest forecast')
    parser.add_argument('-zipf', type=float, nargs=2, required=True, help='Zipf parameters: q and s')

    args = parser.parse_args()

    number_of_requests = args.req
    if args.rps.lower() == 'rf':
        feature_columns = ['x1', 'x2', 'x3']
        requests_per_second = load_model_and_forecast('rf_model.pkl', 'data_forecast.csv', feature_columns)
    else:
        try:
            requests_per_second = float(args.rps)
        except ValueError:
            print(f"Invalid value for requests per second: {args.rps}")
            return

    zipf_params = tuple(args.zipf)

    df = pd.read_csv('url_bineca_http.csv')
    urls = df['URL'].tolist()

    with open('request_log_http.log', mode='w') as file:
        file.write("URL\tStart Time\tEnd Time\tRTT (ms)\tStatus Code\tContent Size (bytes)\tThroughput (bytes/ms)\n")

    results = generate_traffic(urls, number_of_requests, requests_per_second, zipf_params)
    
    total_data, average_data = calculate_totals_and_averages(results)
    
    with open('request_log_http.log', mode='a') as file:
        file.write('\t'.join(map(str, total_data)) + '\n')
        file.write('\t'.join(map(str, average_data)) + '\n')
    
    print(f"Total RTT: {total_data[3]:.2f} ms, Total Throughput: {total_data[6]:.2f} bytes/ms")
    print(f"Average RTT: {average_data[3]:.2f} ms, Average Throughput: {average_data[6]:.2f} bytes/ms")

if __name__ == "__main__":
    main()
