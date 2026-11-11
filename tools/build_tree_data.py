# -*- coding: utf-8 -*-
"""
生成七层嵌套金字塔原型用的层级树数据 yizang_tree.json。

L1 BFO / L2 四大根类       -> 元类定义（静态）
L3 四编二十八类            -> categories.json 聚合
L4 单本医书(788部)         -> categories.json 真实数据
L5 篇章卷次 / L6 知识元 / L7 条文 -> 《黄帝内经素问》示例拆解（原型演示）

输出: data/ontology/yizang_tree.json
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "yizang")
OUT_DIR = os.path.join(ROOT, "data", "ontology")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "yizang_tree.json")

CATS = json.load(open(os.path.join(DATA, "categories.json"), encoding="utf-8"))

# 元类定义（与 build_meta_ontology.py 保持一致）
L1_L2 = [
    {"id": "Continuant", "label": "持续实体", "level": 1,
     "children": [
         {"id": "MedicalCanon", "label": "医藏典籍类", "level": 2, "type": "root"},
         {"id": "TCMConcept", "label": "理论概念类", "level": 2, "type": "root"},
         {"id": "DiagnosisTreatment", "label": "诊疗过程类", "level": 2, "type": "root"},
         {"id": "ResourceEntity", "label": "实体资源类", "level": 2, "type": "root"},
     ]},
    {"id": "Occurrent", "label": "瞬时实体", "level": 1, "children": []},
]

# 28 类体系（含编）
BIAN_ORDER = ["第一编", "第二编", "第三编", "第四编"]
BIAN_LABEL = {"第一编": "基础核心", "第二编": "理论细分", "第三编": "临床实践", "第四编": "民族医药"}


def by_lei():
    m = {}
    for c in CATS:
        m.setdefault(c["lei"], []).append(c)
    return m


def build():
    by = by_lei()
    # 统计 28 类分布
    lei_stats = {}
    for c in CATS:
        lei_stats[c["lei"]] = lei_stats.get(c["lei"], 0) + 1

    # L3 分类类目：按编分组
    bian_groups = {}
    for c in CATS:
        bian_groups.setdefault(c["bian"], {}).setdefault(c["lei"], []).append(c)

    # 构造 L3 树（每编 -> 每类 -> 每书）
    l3_children = []
    for bian in BIAN_ORDER:
        if bian not in bian_groups:
            continue
        lei_map = bian_groups[bian]
        bian_node = {
            "id": bian, "label": f"{bian} · {BIAN_LABEL[bian]}", "level": 3,
            "type": "bian", "count": sum(len(v) for v in lei_map.values()),
            "children": []
        }
        for lei, books in sorted(lei_map.items(), key=lambda x: -len(x[1])):
            lei_node = {
                "id": lei, "label": lei, "level": 3, "type": "lei",
                "count": len(books),
                "children": [
                    {"id": b["name"], "label": b["name"], "level": 4,
                     "type": "book", "file": b["file"], "size": b.get("file", ""),
                     "children": []}
                    for b in sorted(books, key=lambda x: x["name"])
                ]
            }
            bian_node["children"].append(lei_node)
        l3_children.append(bian_node)

    # 医藏典籍根类 -> L3
    medical_canon = {
        "id": "MedicalCanon", "label": "医藏典籍类", "level": 2, "type": "root",
        "count": len(CATS),
        "children": l3_children
    }

    # 演示：《黄帝内经素问》拆解 L5-L7
    suwen = {
        "id": "黄帝内经素问", "label": "《黄帝内经素问》", "level": 4,
        "type": "book_demo", "demo": True,
        "children": [
            {"id": "上古天真论", "label": "《上古天真论》", "level": 5, "type": "chapter",
             "children": [
                 {"id": "kn1", "label": "病证元·肾气虚", "level": 6, "type": "kn",
                  "children": [
                      {"id": "t1", "label": "条文：肾者主水，受五脏六腑之精而藏之", "level": 7,
                       "type": "text", "props": {"注音": "藏 zàng", "异体": "藏→臟", "白话": "肾脏主水，接受五脏六腑的精气而贮藏之"}},
                  ]},
                 {"id": "kn2", "label": "治法元·调阴阳", "level": 6, "type": "kn",
                  "children": [
                      {"id": "t2", "label": "条文：法于阴阳，和于术数", "level": 7, "type": "text",
                       "props": {"白话": "取法阴阳，调和术数"}},
                  ]},
             ]},
            {"id": "四气调神大论", "label": "《四气调神大论》", "level": 5, "type": "chapter",
             "children": [
                 {"id": "kn3", "label": "概念元·四时", "level": 6, "type": "kn",
                  "children": [
                      {"id": "t3", "label": "条文：春三月，此谓发陈", "level": 7, "type": "text",
                       "props": {"白话": "春季三个月，叫做发陈"}},
                  ]},
             ]},
            {"id": "阴阳应象大论", "label": "《阴阳应象大论》", "level": 5, "type": "chapter",
             "children": [
                 {"id": "kn4", "label": "概念元·阴阳", "level": 6, "type": "kn",
                  "children": [
                      {"id": "t4", "label": "条文：阴阳者，天地之道也", "level": 7, "type": "text",
                       "props": {"注音": "道 dào", "白话": "阴阳是天地间的普遍规律"}},
                  ]},
             ]},
        ]
    }

    # 挂到医经类
    for bian in medical_canon["children"]:
        if bian["id"] == "第一编":
            for lei in bian["children"]:
                if lei["id"] == "医经":
                    # 在医经类下加《黄帝内经素问》演示节点
                    lei["children"].append(suwen)

    root = {
        "id": "YizangOntology", "label": "医藏本体", "level": 0, "type": "root",
        "count": len(CATS),
        "children": [
            {"id": "Continuant", "label": "持续实体", "level": 1, "type": "bfo",
             "children": [medical_canon,
                          {"id": "TCMConcept", "label": "理论概念类", "level": 2, "type": "root",
                           "count": 0, "children": [
                               {"id": "YinYang", "label": "阴阳类", "level": 2, "type": "concept"},
                               {"id": "WuXing", "label": "五行类", "level": 2, "type": "concept"},
                               {"id": "ZangXiang", "label": "藏象类", "level": 2, "type": "concept"},
                               {"id": "JingLuo", "label": "经络类", "level": 2, "type": "concept"},
                               {"id": "QiXueJinYe", "label": "气血津液类", "level": 2, "type": "concept"},
                               {"id": "YunQi", "label": "运气类", "level": 2, "type": "concept"},
                           ]},
                          {"id": "DiagnosisTreatment", "label": "诊疗过程类", "level": 2, "type": "root",
                           "count": 0, "children": [
                               {"id": "Disease", "label": "病证类", "level": 2, "type": "concept"},
                               {"id": "Symptom", "label": "症状类", "level": 2, "type": "concept"},
                               {"id": "SyndromePattern", "label": "证候类", "level": 2, "type": "concept"},
                               {"id": "TreatmentMethod", "label": "治法类", "level": 2, "type": "concept"},
                               {"id": "Formula", "label": "方剂类", "level": 2, "type": "concept"},
                               {"id": "Herb", "label": "中药类", "level": 2, "type": "concept"},
                           ]},
                          {"id": "ResourceEntity", "label": "实体资源类", "level": 2, "type": "root",
                           "count": 0, "children": [
                               {"id": "Physician", "label": "医家类", "level": 2, "type": "concept"},
                               {"id": "Edition", "label": "版本类", "level": 2, "type": "concept"},
                               {"id": "CollectionInstitution", "label": "馆藏机构类", "level": 2, "type": "concept"},
                           ]},
             ]},
            {"id": "Occurrent", "label": "瞬时实体", "level": 1, "type": "bfo", "children": []},
        ]
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(root, f, ensure_ascii=False, indent=2)

    # 统计
    def count_leaves(n):
        if not n.get("children"):
            return 1 if n.get("type") == "book" else 0
        return sum(count_leaves(c) for c in n["children"])

    print(f"已生成 {OUT}")
    print(f"L4 典籍总数: {count_leaves(root)}")
    print(f"28类分布: {lei_stats}")


if __name__ == "__main__":
    build()
