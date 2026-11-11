# -*- coding: utf-8 -*-
"""
按《中华医藏》四编二十八类，把 788 部医书原文归类到 texts/<编>_<类>/ 目录，
并同步更新 index.json / categories.json 的 file 引用。原文移动（不复制）节省磁盘。

与佛学仓库对齐：原文单本小文件入库（最大 19.97MB，远低于 GitHub 100MB 限制），
分类通过目录树 + categories.json 元数据双轨呈现。

用法: python tools/organize_repo.py
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "yizang")
TXT_DIR = os.path.join(DATA, "txt")
CAT = os.path.join(DATA, "categories.json")
IDX = os.path.join(DATA, "index.json")
TEXTS = os.path.join(DATA, "texts")


def main():
    with open(CAT, encoding="utf-8") as f:
        cats = json.load(f)
    with open(IDX, encoding="utf-8") as f:
        idx = json.load(f)

    # name -> index 条目
    idx_by_name = {b["name"]: b for b in idx}

    moved = 0
    missing = []
    stat = {}
    for c in cats:
        name = c["name"]
        bian = c["bian"]
        lei = c["lei"]
        folder = f"{bian}_{lei}"
        dest_dir = os.path.join(TEXTS, folder)
        src = os.path.join(TXT_DIR, name + ".txt")
        if not os.path.exists(src):
            missing.append(name)
            continue
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, name + ".txt")
        shutil.move(src, dest)
        moved += 1
        stat[folder] = stat.get(folder, 0) + 1
        # 同步 file 引用
        new_file = f"texts/{folder}/{name}.txt"
        c["file"] = new_file
        if name in idx_by_name:
            idx_by_name[name]["file"] = new_file

    # 删除空 txt 目录
    if os.path.isdir(TXT_DIR) and not os.listdir(TXT_DIR):
        os.rmdir(TXT_DIR)

    with open(CAT, "w", encoding="utf-8") as f:
        json.dump(cats, f, ensure_ascii=False, indent=2)
    with open(IDX, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)

    print(f"已归类移动 {moved} 部，缺失 {len(missing)} 部")
    if missing:
        print("缺失:", missing)
    print(f"\n共 {len(stat)} 个类目目录:")
    for folder in sorted(stat):
        print(f"  {folder}: {stat[folder]}")


if __name__ == "__main__":
    main()
