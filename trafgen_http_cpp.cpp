#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <thread>
#include <chrono>
#include <random>
#include <curl/curl.h>
#include <mutex>
#include <atomic>
#include <cmath>
#include <algorithm>
#include <iterator>
#include <unistd.h>

std::mutex mtx;
std::atomic<int> request_counter(0);

size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

struct LogData {
    std::string url;
    std::string start_time;
    std::string end_time;
    double rtt;
    std::string status_code;
    size_t content_size;
    double throughput;
};

class LogWriter {
public:
    LogWriter(const std::string& filename) : filename(filename) {
        file.open(filename, std::ios::out | std::ios::app);
    }
    
    ~LogWriter() {
        file.close();
    }
    
    void write(const std::vector<std::string>& data) {
        std::lock_guard<std::mutex> lock(mtx);
        for (const auto& field : data) {
            file << field << " ";
        }
        file << "\n";
    }

private:
    std::string filename;
    std::ofstream file;
};

double zipf_mandelbrot(size_t N, double q, double s, std::vector<double>& probabilities) {
    std::vector<double> ranks(N);
    for (size_t i = 0; i < N; ++i) {
        ranks[i] = i + 1;
    }
    std::vector<double> weights(N);
    for (size_t i = 0; i < N; ++i) {
        weights[i] = pow(ranks[i] + q, -s);
    }
    double sum = std::accumulate(weights.begin(), weights.end(), 0.0);
    for (size_t i = 0; i < N; ++i) {
        probabilities[i] = weights[i] / sum;
    }
}

std::vector<std::string> split(const std::string& str, char delimiter) {
    std::vector<std::string> tokens;
    std::string token;
    std::istringstream tokenStream(str);
    while (std::getline(tokenStream, token, delimiter)) {
        tokens.push_back(token);
    }
    return tokens;
}

void make_request(const std::string& url, std::vector<LogData>& results, LogWriter& log_writer) {
    try {
        auto start_time = std::chrono::system_clock::now();
        CURL* curl;
        CURLcode res;
        std::string readBuffer;
        long response_code = 0;

        curl = curl_easy_init();
        if(curl) {
            curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
            res = curl_easy_perform(curl);
            if(res == CURLE_OK) {
                curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
            }
            curl_easy_cleanup(curl);
        }

        auto end_time = std::chrono::system_clock::now();
        std::chrono::duration<double> elapsed_seconds = end_time - start_time;
        double rtt = elapsed_seconds.count() * 1000; // Convert to milliseconds
        size_t content_size = readBuffer.size();
        double throughput = content_size / rtt; // Throughput in bytes per millisecond

        LogData log_data = {url, std::to_string(std::chrono::duration_cast<std::chrono::milliseconds>(start_time.time_since_epoch()).count()), 
                            std::to_string(std::chrono::duration_cast<std::chrono::milliseconds>(end_time.time_since_epoch()).count()), 
                            rtt, std::to_string(response_code), content_size, throughput};
        results.push_back(log_data);
        
        std::vector<std::string> log_data_vector = {url, log_data.start_time, log_data.end_time, std::to_string(rtt), 
                                                    std::to_string(response_code), std::to_string(content_size), std::to_string(throughput)};
        log_writer.write(log_data_vector);

        std::cout << "Request to " << url << " completed with status code: " << response_code 
                  << ", RTT: " << rtt << " ms, Total content size: " << content_size 
                  << " bytes, Throughput: " << throughput << " bytes/ms" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Request to " << url << " failed: " << e.what() << std::endl;
    }
}

void generate_traffic(const std::vector<std::string>& urls, int num_requests, double requests_per_second, const std::vector<double>& zipf_params) {
    size_t N = urls.size();
    std::vector<double> probabilities(N);
    zipf_mandelbrot(N, zipf_params[0], zipf_params[1], probabilities);

    std::vector<std::thread> threads;
    std::vector<LogData> results;
    LogWriter log_writer("request_log_http.log");

    double interval = 1.0 / requests_per_second;

    for (int i = 0; i < num_requests; ++i) {
        size_t index = std::distance(probabilities.begin(), std::max_element(probabilities.begin(), probabilities.end()));
        std::string url = urls[index];
        probabilities[index] = 0; // Remove the used probability to avoid reuse
        std::thread t(make_request, url, std::ref(results), std::ref(log_writer));
        threads.push_back(std::move(t));
        std::this_thread::sleep_for(std::chrono::milliseconds(static_cast<int>(interval * 1000)));
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "Traffic generation completed." << std::endl;
}

void calculate_totals_and_averages(const std::vector<LogData>& results) {
    double total_rtt = 0;
    double total_throughput = 0;
    for (const auto& result : results) {
        total_rtt += result.rtt;
        total_throughput += result.throughput;
    }
    double average_rtt = total_rtt / results.size();
    double average_throughput = total_throughput / results.size();

    std::cout << "Total RTT: " << total_rtt << " ms, Total Throughput: " << total_throughput << " bytes/ms" << std::endl;
    std::cout << "Average RTT: " << average_rtt << " ms, Average Throughput: " << average_throughput << " bytes/ms" << std::endl;
}

int main(int argc, char* argv[]) {
    int number_of_urls = 0;
    int number_of_requests = 0;
    double requests_per_second = 0;
    std::vector<double> zipf_params;

    int opt;
    while ((opt = getopt(argc, argv, "url:req:rps:zipf:")) != -1) {
        switch (opt) {
            case 'u':
                number_of_urls = std::stoi(optarg);
                break;
            case 'r':
                number_of_requests = std::stoi(optarg);
                break;
            case 'p':
                requests_per_second = std::stod(optarg);
                break;
            case 'z': {
                std::istringstream iss(optarg);
                std::string token;
                while (std::getline(iss, token, ',')) {
                    zipf_params.push_back(std::stod(token));
                }
                break;
            }
            default:
                std::cerr << "Usage: " << argv[0] << " -url <number_of_urls> -req <number_of_requests> -rps <requests_per_second> -zipf <zipf_q,zipf_s>" << std::endl;
                return 1;
        }
    }

    if (zipf_params.size() != 2) {
        std::cerr << "Usage: " << argv[0] << " -url <number_of_urls> -req <number_of_requests> -rps <requests_per_second> -zipf <zipf_q,zipf_s>" << std::endl;
        return 1;
    }

    // Load URLs from CSV
    std::ifstream infile("url_bineca_http.csv");
    std::string line;
    std::vector<std::string> urls;
    while (std::getline(infile, line)) {
        urls.push_back(line);
    }

    generate_traffic(urls, number_of_requests, requests_per_second, zipf_params);
    
    std::vector<LogData> results;
    calculate_totals_and_averages(results);

    return 0;
}
