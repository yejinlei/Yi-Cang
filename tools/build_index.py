# -*- coding: utf-8 -*-
"""
生成医藏索引 index.json 并做质量校验。
统计每部医书的文件名、原始HTML、txt大小、字数，以及空文件/过小文件等异常。
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "yizang")
TXT_DIR = os.path.join(DATA, "txt")
RAW_DIR = os.path.join(DATA, "raw")


def main():
    index = []
    for txt in sorted(os.listdir(TXT_DIR)):
        if not txt.endswith(".txt"):
            continue
        base = txt[:-4]
        txt_path = os.path.join(TXT_DIR, txt)
        raw_path = os.path.join(RAW_DIR, base + ".html")
        size = os.path.getsize(txt_path)
        raw_size = os.path.getsize(raw_path) if os.path.exists(raw_path) else 0
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
            chars = len(content)
        except Exception:
            content, chars = "", 0
        # 统计汉字数（粗略）
        hanzi = len(re.findall(r"[\u4e00-\u9fff]", content))
        index.append({
            "name": base,
            "file": "txt/" + txt,
            "raw_file": "raw/" + base + ".html" if raw_size else "",
            "size_bytes": size,
            "raw_size": raw_size,
            "chars": chars,
            "hanzi": hanzi,
        })
    with open(os.path.join(DATA, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    # 汇总
    total_size = sum(i["size_bytes"] for i in index)
    total_chars = sum(i["chars"] for i in index)
    total_hanzi = sum(i["hanzi"] for i in index)
    empty = [i["name"] for i in index if i["chars"] < 50]
    small = [i["name"] for i in index if 50 <= i["chars"] < 500]
    print(f"医书总数: {len(index)}")
    print(f"txt总字节: {total_size:,} ({total_size/1024/1024:.1f} MB)")
    print(f"总字符数: {total_chars:,}")
    print(f"总汉字数: {total_hanzi:,}")
    print(f"空/异常小(<50字): {len(empty)} -> {empty[:20]}")
    print(f"偏小(50-500字): {len(small)} -> {small[:20]}")
    print(f"无raw文件: {sum(1 for i in index if not i['raw_file'])}")
    print(f"最大10部:")
    for i in sorted(index, key=lambda x: -x["size_bytes"])[:10]:
        print(f"  {i['name']}: {i['size_bytes']/1024/1024:.2f} MB, 汉字{i['hanzi']:,}")


if __name__ == "__main__":
    main()
