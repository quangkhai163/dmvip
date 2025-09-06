import requests
from concurrent.futures import ThreadPoolExecutor
import threading
import os

# Danh sách API proxy
API_SOURCES = [
    "https://api.proxyscrape.com/?request=displayproxies&proxytype=http&timeout=5000",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://proxylist.geonode.com/api/proxy-list?limit=500&sort_by=lastChecked&format=textplain",
    "https://getproxylist.com/api/proxy?protocol=http",  # JSON từng proxy
    "http://rootjazz.com/proxies/proxies.txt",
    "https://openproxylist.xyz/http.txt",
    "https://multiproxy.org/txt_all/proxy.txt",
    "https://proxyspace.pro/http.txt",
]

ALL_OUTPUT = "all.txt"
live_http = 0
live_https = 0
checked = 0
total = 0
lock = threading.Lock()

def fetch_proxies_from_apis():
    all_proxies = set()
    total_api = len(API_SOURCES)

    for i, url in enumerate(API_SOURCES, 1):
        print(f"Đã check {i}/{total_api} API")
        try:
            if "getproxylist.com" in url:
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    json_data = res.json()
                    ip = json_data.get("ip")
                    port = json_data.get("port")
                    if ip and port:
                        all_proxies.add(f"{ip}:{port}")
            else:
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    lines = [line.strip() for line in res.text.splitlines() if ":" in line]
                    all_proxies.update(lines)
        except:
            pass

    print(f"📥 Tổng proxy lấy được: {len(all_proxies)} từ {total_api} API")
    return list(all_proxies)

def save(proxy):
    with open(ALL_OUTPUT, "a") as f:
        f.write(proxy + "\n")

def check(proxy):
    global live_http, live_https, checked
    proxy_url = f"http://{proxy}"
    proxies = {"http": proxy_url, "https": proxy_url}

    is_http = False
    is_https = False

    try:
        r = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=1)
        if r.status_code == 200:
            is_http = True
    except:
        pass

    try:
        r = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=2, verify=False)
        if r.status_code == 200:
            is_https = True
    except:
        pass

    with lock:
        if is_http or is_https:
            save(proxy)
        if is_http:
            live_http += 1
        if is_https:
            live_https += 1
        checked += 1
        percent = (checked / total) * 100
        print(f"✅ Đã check: {checked}/{total} ({percent:.2f}%) | 🟢 HTTP: {live_http} | 🔒 HTTPS: {live_https}", end='\r')

def scan(proxies, max_threads=70):
    if os.path.exists(ALL_OUTPUT):
        os.remove(ALL_OUTPUT)
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        executor.map(check, proxies)

if __name__ == "__main__":
    print("🚀 Đang lấy danh sách proxy từ API...")
    proxy_list = fetch_proxies_from_apis()
    total = len(proxy_list)

    if total == 0:
        print("❌ Không có proxy nào.")
        exit()

    print(f"🔍 Tổng proxy: {total}")
    print("⚙️ Bắt đầu kiểm tra proxy...\n")
    scan(proxy_list)

    print(f"\n\n✅ Kết thúc.")
    print(f"📦 Proxy sống lưu vào: {ALL_OUTPUT}")
    print(f"🟢 HTTP: {live_http} | 🔒 HTTPS: {live_https}")
