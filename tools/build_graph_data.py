# -*- coding: utf-8 -*-
"""
医藏知识图谱数据构建脚本。

节点来源:
  - 概念类(L2, class=concept): 从 yizang_meta_ontology.jsonld 读取 rdfs:label 的
    四大根类 + 理论/诊疗/资源细分, 五行类下挂五子(木火土金水)演示节点
  - 类目(L3, class=category): categories.json 的 bian+lei 聚合, 28 个
  - 典籍(L4, class=book): categories.json 的 788 部, 每部归入其 lei 类目

边来源:
  - belongsToYizangCategory (belongs): 书 -> lei 类目 (788)
  - belongsToBian (belongs): 类目 -> bian 编 (28)
  - conceptLink (concept): 细分概念 -> 所属四大根类 (14)
  - engenders/restrains (wu): 五行五子相生相克 (10)
  - citesYizangBook (cites): 代表典籍学术传承引用 (演示)

输出: data/ontology/yizang_graph.json  {nodes:[], links:[]}
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "yizang")
ONT = os.path.join(ROOT, "data", "ontology")
CAT = os.path.join(DATA, "categories.json")
IDX = os.path.join(DATA, "index.json")
OWL = os.path.join(ONT, "yizang_meta_ontology.jsonld")
OUT = os.path.join(ONT, "yizang_graph.json")

# 四大根类 id (IRI 尾段) -> 中文名
ROOT_IDS = {
    "MedicalCanon": "医藏典籍类",
    "TCMConcept": "理论概念类",
    "DiagnosisTreatment": "诊疗过程类",
    "ResourceEntity": "实体资源类",
}
# 细分概念类 id -> 所属根类 id
SUB_ROOT = {
    "YinYang": "TCMConcept", "WuXing": "TCMConcept", "ZangXiang": "TCMConcept",
    "JingLuo": "TCMConcept", "QiXueJinYe": "TCMConcept", "YunQi": "TCMConcept",
    "Disease": "DiagnosisTreatment", "Symptom": "DiagnosisTreatment",
    "SyndromePattern": "DiagnosisTreatment", "TreatmentMethod": "DiagnosisTreatment",
    "Formula": "DiagnosisTreatment", "Herb": "DiagnosisTreatment",
    "Physician": "ResourceEntity", "Edition": "ResourceEntity",
    "CollectionInstitution": "ResourceEntity",
}

# 五行五子相生/相克
WUXING = ["木", "火", "土", "金", "水"]
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 代表典籍学术传承引用 (演示): (book_name, cites_name, label)
CITES = [
    ("黄帝内经素问", "黄帝内经素问", "内经"),
    ("黄帝内经灵枢", "黄帝内经素问", "灵承素"),
    ("难经", "黄帝内经素问", "承内经"),
    ("伤寒论", "黄帝内经素问", "承内经"),
    ("金匮要略", "伤寒论", "承伤寒"),
    ("本草纲目", "神农本草经", "承本经"),
    ("神农本草经", "黄帝内经素问", "本草溯源"),
    ("脉经", "黄帝内经素问", "承内经"),
    ("针灸甲乙经", "黄帝内经灵枢", "承灵枢"),
]


def iri_tail(uri):
    return uri.rsplit(":", 1)[-1] if ":" in uri else uri


def main():
    with open(CAT, encoding="utf-8") as f:
        cats = json.load(f)
    with open(IDX, encoding="utf-8") as f:
        idx = json.load(f)
    with open(OWL, encoding="utf-8") as f:
        owl = json.load(f)

    idx_by_name = {b["name"]: b for b in idx}
    # 读取概念类标签: 遍历 @graph 找 owl:Class
    label_map = {}
    for node in owl["@graph"]:
        if node.get("@type") == "owl:Class":
            lid = iri_tail(node["@id"])
            label_map[lid] = node.get("rdfs:label", lid)

    nodes = []
    links = []
    seen = set()

    def add_node(nid, name, cls, **kw):
        if nid in seen:
            return
        seen.add(nid)
        node = {"id": nid, "name": name, "class": cls}
        node.update(kw)
        nodes.append(node)

    # ---- 概念类节点: 四大根类 + 细分 + 五行五子 ----
    for rid, rname in ROOT_IDS.items():
        add_node("concept:" + rid, rname, "concept", root=True)
    for sid, root in SUB_ROOT.items():
        add_node("concept:" + sid, label_map.get(sid, sid), "concept",
                 rootOf=root)
        links.append({"source": "concept:" + sid, "target": "concept:" + root,
                      "type": "concept", "label": "属于"})
    # 五行五子 (挂在五行类下, 演示生克)
    for w in WUXING:
        add_node("wx:" + w, w + "行", "wuxing", rootOf="concept:WuXing")
        links.append({"source": "wx:" + w, "target": "concept:WuXing",
                      "type": "concept", "label": "五行属"})
    for a in WUXING:
        b = SHENG[a]
        links.append({"source": "wx:" + a, "target": "wx:" + b,
                      "type": "wu", "label": "相生"})
        c = KE[a]
        links.append({"source": "wx:" + a, "target": "wx:" + c,
                      "type": "wu", "label": "相克"})

    # ---- 类目节点: 从 categories 聚合 bian+lei ----
    lei_stat = {}
    for c in cats:
        key = c["lei"]
        lei_stat.setdefault(key, {"bian": c["bian"], "count": 0})
        lei_stat[key]["count"] += 1
    for lei, st in lei_stat.items():
        add_node("cat:" + lei, lei, "category", bian=st["bian"], count=st["count"])
        links.append({"source": "cat:" + lei, "target": "bian:" + st["bian"],
                      "type": "belongs", "label": "属编"})
    # 四编节点 (bian, class=bian)
    BIAN = ["第一编", "第二编", "第三编", "第四编"]
    for b in BIAN:
        add_node("bian:" + b, b, "bian")

    # ---- 典籍节点: 788 部 ----
    for c in cats:
        name = c["name"]
        info = idx_by_name.get(name, {})
        add_node("book:" + name, name, "book", category=c["lei"],
                 bian=c["bian"], file=c["file"],
                 chars=info.get("chars"), hanzi=info.get("hanzi"))
        links.append({"source": "book:" + name, "target": "cat:" + c["lei"],
                      "type": "belongs", "label": "归类"})

    # ---- 学术传承引用边 ----
    for book, cites, label in CITES:
        s = "book:" + book
        t = "book:" + cites
        if s in seen and t in seen:
            links.append({"source": s, "target": t, "type": "cites", "label": label})

    graph = {"nodes": nodes, "links": links}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=1)

    n_class = {}
    for n in nodes:
        n_class[n["class"]] = n_class.get(n["class"], 0) + 1
    print(f"nodes: {len(nodes)}  {n_class}")
    l_type = {}
    for l in links:
        l_type[l["type"]] = l_type.get(l["type"], 0) + 1
    print(f"links: {len(links)}  {l_type}")


if __name__ == "__main__":
    main()
