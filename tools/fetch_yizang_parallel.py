# -*- coding: utf-8 -*-
"""
殆知阁「医藏」文本并行下载脚本
使用 ThreadPoolExecutor 并行下载，支持断点续传（已存在的 .txt 跳过）。
用法：python tools/fetch_yizang_parallel.py [线程数]
默认 8 线程。
"""
import json
import os
import re
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

BASE = "https://daizhige.org"
YIZANG_URL = BASE + "/%E5%8C%BB%E8%97%8F/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "yizang", "raw")
TXT_DIR = os.path.join(ROOT, "data", "yizang", "txt")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(TXT_DIR, exist_ok=True)

_log_lock = threading.Lock()
_index_lock = threading.Lock()
_index = []
_ok = _fail = 0


def log(msg):
    with _log_lock:
        with open(os.path.join(ROOT, "data", "yizang", "download.log"), "a", encoding="utf-8") as f:
            f.write(msg + "\n")
        print(msg, flush=True)


def fetch_catalog():
    r = requests.get(YIZANG_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")
    items, seen = [], set()
    for a in soup.select("div.files-grid a.file-item"):
        name = a.get_text(strip=True)
        href = a.get("href", "")
        if not name or not href or name in seen:
            continue
        seen.add(name)
        url = BASE + href if href.startswith("/") else (href if href.startswith("http") else BASE + "/" + href)
        items.append({"name": name, "url": url})
    return items


def clean_text(html):
    soup = BeautifulSoup(html, "html.parser")
    content = soup.select_one(".markdown-content") or soup.select_one(".text-content")
    if not content:
        return ""
    for disc in content.select(".medical-disclaimer"):
        disc.decompose()
    for br in content.find_all("br"):
        br.replace_with("\n")
    for p in content.find_all("p"):
        p.append("\n")
    text = content.get_text()
    lines = [ln.strip() for ln in text.split("\n")]
    cleaned, blank = [], 0
    for ln in lines:
        if not ln:
            blank += 1
            if blank <= 1:
                cleaned.append("")
        else:
            blank = 0
            cleaned.append(ln)
    return "\n".join(cleaned).strip()


def download_one(item):
    global _ok, _fail
    name, url = item["name"], item["url"]
    safe_name = re.sub(r'[\\/:*?"<>|]', "_", name)
    txt_path = os.path.join(TXT_DIR, safe_name + ".txt")
    raw_path = os.path.join(RAW_DIR, safe_name + ".html")
    if os.path.exists(txt_path) and os.path.getsize(txt_path) > 0:
        with _index_lock:
            _index.append({"name": name, "url": url, "file": txt_path, "size": os.path.getsize(txt_path)})
            _ok += 1
        return ("skip", name)
    for i in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            r.encoding = "utf-8"
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(r.text)
            text = clean_text(r.text)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            size = len(text.encode("utf-8"))
            with _index_lock:
                _index.append({"name": name, "url": url, "file": txt_path, "size": size})
                _ok += 1
            return ("ok", name, size)
        except Exception as e:
            if i == 2:
                with _index_lock:
                    _index.append({"name": name, "url": url, "file": txt_path, "size": 0, "error": "download_failed"})
                    _fail += 1
                return ("fail", name, str(e))
            time.sleep(1.5 * (i + 1))


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    items = fetch_catalog()
    log(f"共获取医书 {len(items)} 部，使用 {workers} 线程")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(download_one, it): it for it in items}
        for fut in as_completed(futures):
            res = fut.result()
            if res[0] == "ok":
                log(f"[OK] {res[1]} ({res[2]} 字节)")
            elif res[0] == "fail":
                log(f"[FAIL] {res[1]} {res[2]}")
    with open(os.path.join(ROOT, "data", "yizang", "index.json"), "w", encoding="utf-8") as f:
        json.dump(_index, f, ensure_ascii=False, indent=2)
    log(f"全部完成：成功 {_ok}，失败 {_fail}，共 {len(items)}")


if __name__ == "__main__":
    main()
