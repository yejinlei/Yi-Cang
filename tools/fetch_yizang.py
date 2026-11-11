# -*- coding: utf-8 -*-
"""
殆知阁「医藏」文本下载脚本
从 https://daizhige.org/医藏/ 抓取全部医书文本并保存到本地。
输出结构：
  data/yizang/
    raw/<书名>.html        原始页面
    txt/<书名>.txt         提取的纯文本（含免责声明）
    index.json             医书索引（书名、URL、字数）
    download.log           下载日志
"""
import json
import os
import re
import sys
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup

BASE = "https://daizhige.org"
YIZANG_URL = BASE + "/%E5%8C%BB%E8%97%8F/"  # https://daizhige.org/医藏/
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


def log(msg):
    print(msg, flush=True)
    with open(os.path.join(ROOT, "data", "yizang", "download.log"), "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def get(url, retries=3, timeout=30):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            # 页面声明 UTF-8，强制按 UTF-8 解码，避免中文乱码导致 URL 双重编码
            r.encoding = "utf-8"
            return r
        except Exception as e:
            log(f"  [retry {i+1}] {url} -> {e}")
            time.sleep(2 * (i + 1))
    return None


def fetch_catalog():
    """抓取医藏目录页，解析出所有医书的 (书名, 链接)。"""
    r = get(YIZANG_URL)
    if not r:
        sys.exit("无法获取医藏目录")
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    seen = set()
    for a in soup.select("div.files-grid a.file-item"):
        name = a.get_text(strip=True)
        href = a.get("href", "")
        if not name or not href:
            continue
        if name in seen:
            continue
        seen.add(name)
        # href 形如 /医藏/八十一难经.html，服务器返回的是 UTF-8 百分号编码，
        # 但 BeautifulSoup 已解码。直接拼接原始路径，避免 requests 二次编码。
        if href.startswith("/"):
            url = BASE + href
        elif href.startswith("http"):
            url = href
        else:
            url = urllib.parse.urljoin(BASE, href)
        items.append({"name": name, "url": url})
    return items


def clean_text(html):
    """从原始 HTML 的 .markdown-content 中提取纯文本。"""
    soup = BeautifulSoup(html, "html.parser")
    content = soup.select_one(".markdown-content")
    if not content:
        content = soup.select_one(".text-content")
    if not content:
        return ""
    # 移除免责声明块
    for disc in content.select(".medical-disclaimer"):
        disc.decompose()
    # 把 <p>、<br> 等转成换行
    for br in content.find_all("br"):
        br.replace_with("\n")
    for p in content.find_all("p"):
        p.append("\n")
    text = content.get_text()
    # 归一化：全角空格段落缩进保留，去掉多余空行
    text = text.replace("\u3000", "　")
    lines = [ln.rstrip() for ln in text.split("\n")]
    cleaned = []
    blank = 0
    for ln in lines:
        if not ln.strip():
            blank += 1
            if blank <= 1:
                cleaned.append("")
        else:
            blank = 0
            cleaned.append(ln.strip())
    return "\n".join(cleaned).strip()


def main():
    items = fetch_catalog()
    log(f"共获取医书 {len(items)} 部")
    index = []
    ok = fail = 0
    for i, item in enumerate(items, 1):
        name = item["name"]
        url = item["url"]
        safe_name = re.sub(r'[\\/:*?"<>|]', "_", name)
        raw_path = os.path.join(RAW_DIR, safe_name + ".html")
        txt_path = os.path.join(TXT_DIR, safe_name + ".txt")
        # 已存在则跳过
        if os.path.exists(txt_path) and os.path.getsize(txt_path) > 0:
            log(f"[{i}/{len(items)}] 已存在，跳过: {name}")
            index.append({"name": name, "url": url, "file": txt_path, "size": os.path.getsize(txt_path)})
            ok += 1
            continue
        r = get(url)
        if not r:
            log(f"[{i}/{len(items)}] 失败: {name}")
            fail += 1
            index.append({"name": name, "url": url, "file": txt_path, "size": 0, "error": "download_failed"})
            continue
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(r.text)
        text = clean_text(r.text)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        size = len(text.encode("utf-8"))
        log(f"[{i}/{len(items)}] 完成: {name} ({size} 字节)")
        index.append({"name": name, "url": url, "file": txt_path, "size": size})
        ok += 1
        time.sleep(0.3)
    with open(os.path.join(ROOT, "data", "yizang", "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    log(f"全部完成：成功 {ok}，失败 {fail}，共 {len(items)}")


if __name__ == "__main__":
    main()
