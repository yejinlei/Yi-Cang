# -*- coding: utf-8 -*-
"""
单独下载《普济方四库》——服务器渲染该页面极慢（可能20-40MB），
使用流式读取 + 长超时 + 多次重试，直到成功或达到最大尝试次数。
用法：python tools/fetch_daishu.py
"""
import os
import re
import sys
import time
import requests

BASE = "https://daizhige.org"
URL = BASE + "/%E5%8C%BB%E8%97%8F/%E6%99%AE%E6%B5%8E%E6%96%B9%E5%9B%9B%E5%BA%93.html"  # /医藏/普济方四库.html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "yizang", "raw", "普济方四库.html")
TXT = os.path.join(ROOT, "data", "yizang", "txt", "普济方四库.txt")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def stream_download(url, dest, timeout=550, min_size=1_000_000):
    """流式下载到 dest，服务器渲染慢故用长超时。返回是否完成。"""
    t0 = time.time()
    try:
        with requests.get(url, headers=HEADERS, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            r.encoding = "utf-8"
            total = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=256 * 1024):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
            return total > min_size
    except Exception as e:
        print(f"  流式失败(已耗时{int(time.time()-t0)}s): {type(e).__name__} {str(e)[:100]}", flush=True)
        return False


def main():
    # 已存在且非空则跳过
    if os.path.exists(TXT) and os.path.getsize(TXT) > 0:
        print("《普济方四库》已存在，跳过", flush=True)
        return
    print(f"开始下载《普济方四库》 -> {URL}", flush=True)
    for attempt in range(1, 9):
        print(f"--- 尝试 {attempt} ---", flush=True)
        ok = stream_download(URL, RAW)
        if ok and os.path.exists(RAW) and os.path.getsize(RAW) > 1_000_000:
            # 解析提取文本
            from bs4 import BeautifulSoup
            with open(RAW, "r", encoding="utf-8", errors="replace") as f:
                html = f.read()
            soup = BeautifulSoup(html, "html.parser")
            content = soup.select_one(".markdown-content") or soup.select_one(".text-content")
            if not content:
                print("  未找到正文容器，重试", flush=True)
                time.sleep(5)
                continue
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
            final = "\n".join(cleaned).strip()
            with open(TXT, "w", encoding="utf-8") as f:
                f.write(final)
            print(f"  成功! 原文 {len(html)} 字节, 文本 {len(final)} 字符", flush=True)
            return
        time.sleep(10)
    print("多次尝试后仍未成功", flush=True)


if __name__ == "__main__":
    main()
