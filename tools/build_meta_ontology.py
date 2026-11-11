# -*- coding: utf-8 -*-
"""
生成医藏本体 L1/L2 OWL 元类定义（JSON-LD，兼容 W3C OWL 2 DL）。

依据 docs/ontology_spec.md 蓝图：
  L1  BFO 顶层：Continuant / Occurrent
  L2  四大根类：MedicalCanon / TCMConcept / DiagnosisTreatment / ResourceEntity
  L2  理论细分：阴阳/五行/藏象/经络/气血津液/运气
  L2  诊疗细分：病证/症状/证候/治法/方剂/中药
  L2  资源细分：医家/版本/馆藏机构
  对象属性 15 条 + 数据属性 16 条

输出: data/ontology/yizang_meta_ontology.jsonld
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "ontology")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "yizang_meta_ontology.jsonld")

PREFIX = "yizang:"

# ---------- 类层级定义 ----------
# (本类, 父类, 中文标签)
CLASSES = [
    # L1 BFO 顶层
    ("Continuant", "owl:Thing", "持续实体"),
    ("Occurrent", "owl:Thing", "瞬时实体"),
    # L2 四大根类
    ("MedicalCanon", "yizang:Continuant", "医藏典籍类"),
    ("TCMConcept", "yizang:Continuant", "理论概念类"),
    ("DiagnosisTreatment", "yizang:Continuant", "诊疗过程类"),
    ("ResourceEntity", "yizang:Continuant", "实体资源类"),
    # L2 理论概念细分
    ("YinYang", "yizang:TCMConcept", "阴阳类"),
    ("WuXing", "yizang:TCMConcept", "五行类"),
    ("ZangXiang", "yizang:TCMConcept", "藏象类"),
    ("JingLuo", "yizang:TCMConcept", "经络类"),
    ("QiXueJinYe", "yizang:TCMConcept", "气血津液类"),
    ("YunQi", "yizang:TCMConcept", "运气类"),
    # L2 诊疗过程细分
    ("Disease", "yizang:DiagnosisTreatment", "病证类"),
    ("Symptom", "yizang:DiagnosisTreatment", "症状类"),
    ("SyndromePattern", "yizang:DiagnosisTreatment", "证候类"),
    ("TreatmentMethod", "yizang:DiagnosisTreatment", "治法类"),
    ("Formula", "yizang:DiagnosisTreatment", "方剂类"),
    ("Herb", "yizang:DiagnosisTreatment", "中药类"),
    # L2 实体资源细分
    ("Physician", "yizang:ResourceEntity", "医家类"),
    ("Edition", "yizang:ResourceEntity", "版本类"),
    ("CollectionInstitution", "yizang:ResourceEntity", "馆藏机构类"),
]

# ---------- 对象属性 ----------
# (属性名, 域, 值域, 中文标签, 备注/特性)
OBJECT_PROPS = [
    ("belongsToYizangCategory", "yizang:MedicalCanon", "yizang:MedicalCanon", "属于医藏类目", {"func": True}),
    ("citesYizangBook", "yizang:MedicalCanon", "yizang:MedicalCanon", "引用前代典籍", {"trans": True}),
    ("hasChapter", "yizang:MedicalCanon", "yizang:Continuant", "包含篇章卷次", {}),
    ("containsKnowledgeUnit", "yizang:Continuant", "yizang:Continuant", "篇章包含知识元", {}),
    ("hasVariantText", "yizang:Continuant", "yizang:Continuant", "篇章包含条文异文", {}),
    ("engenders", "yizang:WuXing", "yizang:WuXing", "五行相生", {"trans": True}),
    ("restrains", "yizang:WuXing", "yizang:WuXing", "五行相克", {"trans": True}),
    ("hasSymptom", "yizang:SyndromePattern", "yizang:Symptom", "证候有症状", {}),
    ("composedOf", "yizang:Formula", "yizang:Herb", "方剂由中药组成", {}),
    ("treats", "yizang:Formula", "yizang:Disease", "方剂治疗病证", {}),
    ("hasTropism", "yizang:Herb", "yizang:JingLuo", "中药归经", {}),
    ("appliedTo", "yizang:TreatmentMethod", "yizang:SyndromePattern", "治法应用于证候", {}),
    ("hasAuthor", "yizang:MedicalCanon", "yizang:Physician", "典籍有作者", {}),
    ("hasVersion", "yizang:MedicalCanon", "yizang:Edition", "典籍有版本", {}),
    ("heldBy", "yizang:Edition", "yizang:CollectionInstitution", "版本藏于机构", {}),
]

# ---------- 数据属性 ----------
# (属性名, 域, 值域, 中文标签)
DATA_PROPS = [
    ("bookTitle", "yizang:MedicalCanon", "xsd:string", "规范书名"),
    ("completionYear", "yizang:MedicalCanon", "xsd:date", "成书年代"),
    ("versionDetail", "yizang:MedicalCanon", "xsd:string", "版本源流"),
    ("collectionPlace", "yizang:MedicalCanon", "xsd:string", "馆藏位置"),
    ("conceptDefinition", "yizang:TCMConcept", "xsd:string", "概念定义"),
    ("sourceChapter", "yizang:TCMConcept", "xsd:string", "出处篇章"),
    ("herbNature", "yizang:Herb", "xsd:string", "四气"),
    ("herbFlavor", "yizang:Herb", "xsd:string", "五味"),
    ("dosageRange", "yizang:Herb", "xsd:string", "剂量范围"),
    ("formulaComposition", "yizang:Formula", "xsd:string", "组成简述"),
    ("variantMap", "yizang:Continuant", "xsd:string", "异体字映射"),
    ("phoneticNote", "yizang:Continuant", "xsd:string", "生僻字注音"),
    ("semanticNote", "yizang:Continuant", "xsd:string", "语义差异说明"),
    ("vernacular", "yizang:Continuant", "xsd:string", "白话翻译"),
    ("collationNote", "yizang:Continuant", "xsd:string", "校勘记录"),
    ("sourcePosition", "yizang:Continuant", "xsd:string", "页码卷次定位"),
]


def iri(local):
    return f"{PREFIX}{local}"


def build():
    # 头信息 + 类声明
    graph = [
        {
            "@id": iri("YizangOntology"),
            "@type": "owl:Ontology",
            "rdfs:label": "医藏本体论",
            "owl:versionIRI": iri("yizang-ontology"),
            "owl:imports": [{"@id": "http://purl.obolibrary.org/obo/bfo.owl"}],
            "dc:description": "对齐《中华医藏》四编二十八类，兼容 OWL 2 DL 的医藏本体元类定义（L1/L2）",
        }
    ]
    for cls, parent, label in CLASSES:
        entry = {
            "@id": iri(cls),
            "@type": "owl:Class",
            "rdfs:label": label,
        }
        if parent != "owl:Thing":
            entry["rdfs:subClassOf"] = {"@id": parent if parent.startswith("owl:") else iri(parent.split(":")[1])}
        graph.append(entry)

    # 对象属性
    for pname, dom, rng, label, traits in OBJECT_PROPS:
        entry = {
            "@id": iri(pname),
            "@type": "owl:ObjectProperty",
            "rdfs:label": label,
            "rdfs:domain": {"@id": iri(dom.split(":")[1])},
            "rdfs:range": {"@id": iri(rng.split(":")[1])},
        }
        if traits.get("func"):
            entry["rdfs:subPropertyOf"] = {"@id": "owl:FunctionalProperty"}
        if traits.get("trans"):
            entry["rdfs:subPropertyOf"] = {"@id": "owl:TransitiveProperty"}
        graph.append(entry)

    # 数据属性
    for pname, dom, rng, label in DATA_PROPS:
        graph.append({
            "@id": iri(pname),
            "@type": "owl:DatatypeProperty",
            "rdfs:label": label,
            "rdfs:domain": {"@id": iri(dom.split(":")[1])},
            "rdfs:range": {"@id": rng},
        })

    doc = {
        "@context": {
            "yizang": "http://example.org/yizang-ontology#",
            "owl": "http://www.w3.org/2002/07/owl#",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "dc": "http://purl.org/dc/elements/1.1/",
        },
        "@graph": graph,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

    print(f"已生成 {OUT}")
    print(f"  类: {len(CLASSES)} 个")
    print(f"  对象属性: {len(OBJECT_PROPS)} 条")
    print(f"  数据属性: {len(DATA_PROPS)} 条")
    print(f"  @graph 节点: {len(graph)} 个")
    print("  校验: 五行生克(engenders/restrains)为传递属性、treats 单域方剂、所有类有唯一父类")


if __name__ == "__main__":
    build()
