# -*- coding: utf-8 -*-
"""
医藏内容层知识元抽取器（全量 788 部）。

抽取对象（知识元节点）:
  - herb (中药):  药名 + 四气五味 + 归经 + 主治
  - formula (方剂): 方名 + 药味组成 + 主治
  - syndrome (证候): 病-脉-证-治条文中的证候名

关系边:
  - formula->herb  方剂组成 (composedOf)
  - syndrome->formula 证候用方 (treatsWith)
  - herb->meridian 药物归经 (hasTropism)
  - unit->book     知识元归属典籍 (inBook)

输出: data/ontology/yizang_kg.json  {nodes:[], links:[]}
"""
import json
import os
import re
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTS = os.path.join(ROOT, "data", "yizang", "texts")
CAT = os.path.join(ROOT, "data", "yizang", "categories.json")
IDX = os.path.join(ROOT, "data", "yizang", "index.json")
OUT = os.path.join(ROOT, "data", "ontology", "yizang_kg.json")

# 常见中药别名 -> 规范名（用于跨书归并）
HERB_ALIAS = {}

# 常见方剂别名 -> 规范名
FORMULA_ALIAS = {}

# 十二经脉 / 归经
MERIDIANS = ["手太阴肺经", "手阳明大肠经", "足阳明胃经", "足太阴脾经",
             "手少阴心经", "手太阳小肠经", "足太阳膀胱经", "足少阴肾经",
             "手厥阴心包经", "手少阳三焦经", "足少阳胆经", "足厥阴肝经"]
MERIDIAN_SHORT = ["肺", "大肠", "胃", "脾", "心", "小肠", "膀胱", "肾",
                  "心包", "三焦", "胆", "肝"]

# 四气五味
QI = ["寒", "热", "温", "凉", "平", "大寒", "大热", "微寒", "微温", "微凉"]
WEI = ["酸", "苦", "甘", "辛", "咸", "淡", "涩"]


def norm_name(name):
    """规范化药名/方名：去空白、括号、数字剂量尾缀、异体字。"""
    s = re.sub(r"[（(].*?[)）]", "", name)
    s = re.sub(r"[0-9一二三四五六七八九十两钱分升合枚片个粒铢]+$", "", s)
    s = re.sub(r"[\s　·、,，。；;]+", "", s)
    return s


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ============ 本草类条目解析 ============
# 神农本草经格式: "药名[PUA]味甘平。主治..."
# 药名后可能跟私人使用区字符 (\uE000-\uF8FF)，需剥离
PUA_RE = re.compile(r"[\ue000-\uf8ff]")
# 条目: 药名 味X性Y。主治 （允许药名后 PUA 字符；性味块仅含四气五味）
HERB_ENTRY_RE = re.compile(
    r"([\u4e00-\u9fff]{2,8}?)[\ue000-\uf8ff]{0,2}"
    r"[味气]([酸苦甘辛咸淡涩]+[寒热温凉平大微]*)[。.]\s*(.*)$"
)


def extract_herbs(text, book_name):
    """从本草类文本抽取药物条目。返回 herbs 字典。"""
    herbs = OrderedDict()
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if len(line) < 6 or len(line) > 160:
            continue
        m = HERB_ENTRY_RE.match(line)
        if not m:
            continue
        name = PUA_RE.sub("", m.group(1))
        wx = m.group(2) or ""
        rest = m.group(3) or ""
        name = norm_name(name)
        if len(name) < 2 or not re.match(r"^[\u4e00-\u9fff]+$", name):
            continue
        # 性味解析
        qi = ""
        for q in QI:
            if q in wx:
                qi = q
                break
        wei = "".join(w for w in WEI if w in wx)
        # 归经
        meridians = []
        for mz in MERIDIAN_SHORT:
            if mz + "经" in rest:
                meridians.append(mz + "经")
        # 主治: 取"主/治"到"生山谷/一名"之间的内容
        zhi = ""
        zm = re.search(r"(?:主治|主|治)[:：]?\s*([^。]{0,60})", rest)
        if zm:
            zhi = zm.group(1)
        if not zhi:
            zhi = rest[:60]
        key = name
        if key not in herbs:
            herbs[key] = {"name": name, "qi": qi, "wei": wei,
                          "meridians": meridians, "zhi": zhi,
                          "books": [book_name]}
        else:
            h = herbs[key]
            if qi and not h["qi"]:
                h["qi"] = qi
            if wei and not h["wei"]:
                h["wei"] = wei
            if meridians and not h["meridians"]:
                h["meridians"] = meridians
            if book_name not in h["books"]:
                h["books"].append(book_name)
    return herbs


# ============ 方剂条目解析 ============
# 伤寒/金匮格式药味行: "桂枝（去皮，三两） 芍药（三两） 甘草（炙，二两）..."
# 药名后跟括号(炮制，剂量)，或多个药名连续
HERB_DOSE_RE = re.compile(
    r"([\u4e00-\u9fff]{1,6}?)[（(][^）)]*?([0-9一二三四五六七八九十百]+)"
    r"(?:两|钱|分|升|合|枚|片|个|粒|铢|斤|斗|勺|盏|字|方寸匕)[）)]"
)
# 汤头歌诀格式药味: "人参、白术、茯苓各二钱，甘草一钱" / "黄芪二两，人参、半夏各一钱"
HERB_NAI_RE = re.compile(
    r"([\u4e00-\u9fff]{1,6}?)(?:各)?([0-9一二三四五六七八九十百]+)"
    r"(?:两|钱|分|升|合|枚|片|个|粒|铢|斤|斗|勺|盏|字|方寸匕)"
)
# 方名在"XX汤主之/宜XX汤"中
FORMULA_MAIN_RE = re.compile(
    r"([\u4e00-\u9fff]{2,10}?(?:汤|散|丸|丹|膏|饮|煎|方|锭|露|酒|茶|粥|饼|栓))主之"
)
# 行首方名: "XX汤/散/丸..." 独立成行（汤头歌诀）
FORMULA_LINE_RE = re.compile(
    r"^([\u4e00-\u9fff]{2,10}?(?:汤|散|丸|丹|膏|饮|煎|方|锭|露|酒|茶|粥|饼|栓))[。．:]?\s*$"
)
# 金匮格式: "XX汤方+药味同行"
FORMULA_INLINE_RE = re.compile(
    r"^([\u4e00-\u9fff]{2,10}?(?:汤|散|丸|丹|膏|饮|煎|方|锭))方\s*"
)


def is_herb_line(line):
    """判断是否药味组成行。"""
    return bool(HERB_DOSE_RE.search(line)) or bool(HERB_NAI_RE.search(line))


def extract_formulas(text, book_name, herbs):
    """从方书/伤寒类文本抽取方剂条目及其药味组成。
    返回 (formulas, comp_links)。
    """
    formulas = OrderedDict()
    comp_links = []
    lines = text.split("\n")

    def add_formula(fname, herb_names):
        fname = norm_name(fname)
        if len(fname) < 2:
            return
        if fname not in formulas:
            formulas[fname] = {"name": fname, "herbs": herb_names,
                               "zhi": "", "books": [book_name]}
        elif book_name not in formulas[fname]["books"]:
            formulas[fname]["books"].append(book_name)
        for hn in herb_names:
            comp_links.append((fname, hn))
            if hn not in herbs:
                herbs[hn] = {"name": hn, "qi": "", "wei": "",
                             "meridians": [], "zhi": "",
                             "books": [book_name]}
            elif book_name not in herbs[hn]["books"]:
                herbs[hn]["books"].append(book_name)

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # 金匮内联格式: "XX汤方+药味"（方名与药味同行）
        im = FORMULA_INLINE_RE.match(line)
        if im:
            fname = im.group(1)
            after = line[im.end():]
            herb_names = parse_herb_line(after) if after else []
            if herb_names:
                add_formula(fname, herb_names)
        # 独立方名行（汤头歌诀）
        elif FORMULA_LINE_RE.match(line):
            fname = FORMULA_LINE_RE.match(line).group(1)
            # 找后续药味行（跳过非药味行最多3行）
            herb_names = []
            for j in range(i + 1, min(i + 5, len(lines))):
                nxt = lines[j].strip()
                if not nxt:
                    continue
                if is_herb_line(nxt):
                    herb_names.extend(parse_herb_line(nxt))
                    break
            if herb_names:
                add_formula(fname, herb_names)
        # 条文内"XX汤主之"
        else:
            for fm in FORMULA_MAIN_RE.finditer(line):
                fname = fm.group(1)
                # 找条文后独立药味行（跳过空行，遇新条文停止）
                herb_names = []
                for j in range(i + 1, min(i + 8, len(lines))):
                    nxt = lines[j].strip()
                    if nxt.startswith("○") or nxt.startswith("●"):
                        break
                    if not nxt:
                        continue
                    if is_herb_line(nxt):
                        herb_names.extend(parse_herb_line(nxt))
                        break
                if herb_names:
                    add_formula(fname, herb_names)
        i += 1
    return formulas, comp_links


def parse_herb_line(line):
    """解析一行药味，返回药名列表（过滤噪声）。"""
    names = []
    # 优先括号剂量模式（伤寒/金匮格式）
    for m in HERB_DOSE_RE.finditer(line):
        nm = norm_name(m.group(1))
        if is_valid_herb(nm):
            names.append(nm)
    if names:
        return names
    # 无括号模式 "药名X两/钱"（药名限长，防截断噪声）
    for m in HERB_NAI_RE.finditer(line):
        nm = norm_name(m.group(1))
        if len(nm) > HERB_NAI_MAXLEN:
            continue
        if is_valid_herb(nm):
            names.append(nm)
    return names


# 煎服法/炮制噪声词（精确匹配整词，避免误伤真药如大枣/生姜）
HERB_NOISE_EXACT = {
    "以水", "以酒", "以醋", "以蜜", "以浆水", "以井花水",
    "水一", "水二", "水三", "水四", "水五", "水六", "水七", "水八", "水九",
    "水半", "水斗", "水升", "水盏", "酒半", "酒一", "酒二", "酒盏",
    "煎至", "煎取", "煎八分", "煎六分", "煎五分", "煎四分",
    "煮取", "煮至", "煮八分", "煮六分", "煮五分", "煮四分", "煮三沸",
    "去滓", "去渣", "温服", "分温", "顿服", "再服", "日三", "日再", "日二",
    "日一", "每服", "饮服", "食前", "食后", "空心", "空腹", "不拘时",
    "研末", "为末", "杵为", "捣为", "细末", "细研", "为散", "为丸",
    "服此", "取肉", "和煮取", "水酒", "好醋", "米醋", "入蜜", "食蜜",
    "白蜜", "清酒", "浆水", "水银", "细茶", "麝香末", "凝水石", "水萍",
    "石蜜", "蜜蜡", "水苏", "水靳", "取如弹丸", "相去如炊", "浆水调下",
    "绵裹", "去节", "去皮", "去心", "去芦", "去尖", "去翅", "去足",
    "酒洗", "酒浸", "酒炒", "醋炒", "盐炒", "土炒", "麸炒", "炒黄", "炒焦",
    "米泔", "汤泡", "水飞", "阴干", "焙干", "曝干", "晒干", "炙",
    "咀", "铡", "锉", "筛", "绢筛", "罗", "为细末",
}
# 单字虚词/计量/炮制（作整词药名出现即为噪声）
HERB_NOISE_SINGLE = {
    "各", "共", "和", "上", "右", "下", "内", "取", "以", "于", "与",
    "加", "减", "去", "名", "方", "汤", "散", "丸", "每", "服", "煎",
    "水", "火", "酒", "醋", "蜜", "盐", "姜", "枣", "葱", "豉",
    "升", "斗", "合", "枚", "片", "粒", "铢", "钱", "分", "两", "寸",
    "尺", "碗", "盏", "匙", "匕", "字", "味", "药", "滓", "淬", "泡",
}
# 无括号模式的药名长度区间（1字多为虚词/计量，≥5字多为方名残串，均拒绝）
HERB_NAI_MINLEN = 2
HERB_NAI_MAXLEN = 4
# 方剂后缀字：药名含此字且非结尾，多为"XX汤+药"残串（如"胃承气汤大黄"）
FORMULA_SUFFIX_CHARS = set("汤散丸丹膏饮煎方锭露酒茶粥饼栓")
# 真药白名单：含煎服/炮制特征字但确实是中药名（避免误伤）
HERB_WHITELIST = {
    "细辛", "升麻", "水蛭", "两头尖", "寒水石", "白蜜", "清酒", "浆水",
    "好醋", "米醋", "水银", "食蜜", "入蜜", "细茶", "麝香末", "雄黄",
    "芒硝", "硝石", "朴硝", "石膏", "滑石", "代赭石", "赤石脂", "白石脂",
    "紫石英", "白石英", "禹余粮", "太一禹余粮", "六畜毛蹄甲",
    "生姜", "干姜", "大枣", "甘草", "桂枝", "白芍", "赤芍", "附子",
    "炮姜", "炮附子", "煨姜", "炙甘草", "酒大黄", "醋香附",
    "阿胶", "鹿胶", "龟胶", "蜂蜜", "竹沥", "童便", "乳汁", "人乳汁",
    # 当归系列（单味/产地变体，保留；"当归X"并写属两味误并，由前缀过滤拦截）
    "当归", "全当归", "土当归", "川当归", "小当归", "大当归", "油当归",
    "黄当归", "白当归", "杜当归", "陇西当归", "当归头", "当归尾",
    "当归身", "当归须", "当归梢",
    # 以虚词开头但确为真药
    "五加皮", "五加根茎", "破故纸", "故纸", "旋复花", "复盆子", "无食子",
    "无名异", "合欢", "合口椒", "合桃肉", "于朮", "于白术", "并南星",
    "并皂荚刺", "即黄鱼胶", "即苏", "即六一散", "即白术", "无灰上酝",
}
# 煎服法/炮制特征字：药名含任一且不在白名单 → 噪声
HERB_NOISE_CHARS = set(
    "服煮煎取滓渣煨焙炙炒淬浸漂洗晒曝阴干炮制熬炼炼滤搅"
    "水酒醋蜜浆滓末碎细研筛罗杵捣"
)
# 虚词/动词前缀：药名以这些字开头且非白名单 → 残句（"加附子""去节桂枝"等）
HERB_NOISE_PREFIX = set(
    "加去以为无有其此即因复更则乃当若故但脉或失作合止窃宗能必可又并却且所于"
)


def is_valid_herb(nm):
    """药名合法性过滤：排除方名残留、煎服法噪声、虚词、过长。"""
    if not (1 <= len(nm) <= 6) or not re.match(r"^[\u4e00-\u9fff]+$", nm):
        return False
    # 无括号模式下仅接受 2-4 字药名（1字虚词/计量、≥5字方名残串均拒绝）
    if not (HERB_NAI_MINLEN <= len(nm) <= HERB_NAI_MAXLEN):
        return False
    # 真药白名单直接放行（优先于黑名单，避免误杀真药）
    if nm in HERB_WHITELIST:
        return True
    # 虚词/动词前缀残句过滤：以"加/去/以/为/无/有/其/此/即/因/复/更/
    # 则/乃/当/若/故/但/脉/或/失/作/合/止/窃/宗/能/必/可/又/并/却/且/
    # 所/于"开头且非白名单 → 残句（如"加附子""去节桂枝""此桂枝加"）
    if nm and nm[0] in HERB_NOISE_PREFIX:
        return False
    # 排除方名残留（含"汤方""方""主之"等）
    if any(t in nm for t in ["汤方", "主之", "之", "各", "每服", "上药", "右药",
                             "右件", "为末", "共为", "等分", "研末", "煎服"]):
        return False
    # 排除煎服法/炮制噪声整词
    if nm in HERB_NOISE_EXACT:
        return False
    # 排除单字虚词/计量
    if nm in HERB_NOISE_SINGLE:
        return False
    # 排除"XX汤/散/丸... + 药名"残串：药名含方剂后缀字且不在末尾
    if any(c in nm[:-1] for c in FORMULA_SUFFIX_CHARS):
        return False
    # 含煎服法/炮制特征字且非白名单 → 噪声
    if any(c in nm for c in HERB_NOISE_CHARS):
        return False
    return True


# ============ 证候条文解析 ============
# 伤寒金匮格式: "○证候描述...XX汤主之。"
SYND_LINE_RE = re.compile(r"^[○●]\s*(.+)$")
# 用方: "XX汤主之" / "XX丸主之" / "宜XX汤"
SYND_FORMULA_RE = re.compile(
    r"([\u4e00-\u9fff]{2,10}?(?:汤|散|丸|丹|膏|饮|煎|方|锭))?(?:主之|主方|治之|宜用|宜)")
# 病名提示词: 病/证结尾的短语
SYND_HEAD_RE = re.compile(
    r"([\u4e00-\u9fff]{2,12}?(?:之为病|病|证候|证|症))")


def extract_syndromes(text, book_name, formulas):
    """从条文类文本抽取证候及其用方。返回 (syndromes, links)。
    syndromes: {证候名: {name, desc, formulas:[], books}}
    links: [(syndrome, formula)]
    """
    syndromes = OrderedDict()
    links = []
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        m = SYND_LINE_RE.match(line)
        if not m:
            continue
        desc = m.group(1)
        if len(desc) < 6 or len(desc) > 200:
            continue
        # 证候名: 取"之为病"或首个顿号前短语
        hm = SYND_HEAD_RE.search(desc)
        sname = hm.group(1) if hm else desc[:10]
        sname = norm_name(sname)
        if len(sname) < 2:
            continue
        # 用方: 直接提取"XX汤主之"，不依赖 formulas 过滤
        used = []
        for fm in FORMULA_MAIN_RE.finditer(desc):
            f = norm_name(fm.group(1))
            if f:
                used.append(f)
        key = sname
        if key not in syndromes:
            syndromes[key] = {"name": sname, "desc": desc[:80],
                              "formulas": used, "books": [book_name]}
        else:
            if book_name not in syndromes[key]["books"]:
                syndromes[key]["books"].append(book_name)
            for f in used:
                if f not in syndromes[key]["formulas"]:
                    syndromes[key]["formulas"].append(f)
        for f in used:
            links.append((key, f))
    return syndromes, links


# ============ 主聚合 ============
# 按类目判定抽取策略
HERB_LEI = {"本草", "方书", "本草纲目"}   # 主要产药物条目
FORMULA_LEI = {"方书", "伤寒金匮", "本草"}  # 主要产方剂条目
SYND_LEI = {"伤寒金匮", "医经", "病因病机", "通论", "内科", "女科", "儿科",
            "外科", "眼科", "喉科", "伤科", "医案医话", "医史"}  # 主要产证候条文


def book_file_map():
    idx = load_json(IDX)
    return {b["name"]: b["file"] for b in idx}


def main():
    cats = load_json(CAT)
    fmap = book_file_map()
    herbs = OrderedDict()
    formulas = OrderedDict()
    syndromes = OrderedDict()
    comp_links = []       # (formula, herb)
    synd_links = []       # (syndrome, formula)

    total = len(cats)
    for n, c in enumerate(cats, 1):
        name = c["name"]
        lei = c["lei"]
        fpath = os.path.join(ROOT, "data", "yizang", fmap.get(name, ""))
        if not os.path.exists(fpath):
            continue
        with open(fpath, encoding="utf-8", errors="ignore") as f:
            text = f.read()
        # 本草类: 抽药物
        if lei in HERB_LEI or "本草" in lei:
            hs = extract_herbs(text, name)
            for k, v in hs.items():
                if k not in herbs:
                    herbs[k] = v
                else:
                    for b in v["books"]:
                        if b not in herbs[k]["books"]:
                            herbs[k]["books"].append(b)
                    if v["qi"] and not herbs[k]["qi"]:
                        herbs[k]["qi"] = v["qi"]
                    if v["wei"] and not herbs[k]["wei"]:
                        herbs[k]["wei"] = v["wei"]
                    if v["meridians"] and not herbs[k]["meridians"]:
                        herbs[k]["meridians"] = v["meridians"]
        # 方书/伤寒: 抽方剂
        if lei in FORMULA_LEI or "方" in lei or "伤寒" in lei or "金匮" in lei:
            fs, cl = extract_formulas(text, name, herbs)
            for k, v in fs.items():
                if k not in formulas:
                    formulas[k] = v
                else:
                    for b in v["books"]:
                        if b not in formulas[k]["books"]:
                            formulas[k]["books"].append(b)
            comp_links.extend(cl)
        # 条文类: 抽证候
        if lei in SYND_LEI:
            ss, sl = extract_syndromes(text, name, formulas)
            for k, v in ss.items():
                if k not in syndromes:
                    syndromes[k] = v
                else:
                    for b in v["books"]:
                        if b not in syndromes[k]["books"]:
                            syndromes[k]["books"].append(b)
                    for fm in v["formulas"]:
                        if fm not in syndromes[k]["formulas"]:
                            syndromes[k]["formulas"].append(fm)
            synd_links.extend(sl)
        if n % 100 == 0:
            print(f"  processed {n}/{total}  herbs={len(herbs)} formulas={len(formulas)} synd={len(syndromes)}",
                  file=sys.stderr)

    # ---- 组装图谱 ----
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

    # 药物节点
    for k, h in herbs.items():
        add_node("herb:" + k, h["name"], "herb",
                 qi=h["qi"], wei=h["wei"], meridians=h["meridians"],
                 zhi=h["zhi"], books=h["books"][:5])
    # 方剂节点
    for k, f in formulas.items():
        add_node("formula:" + k, f["name"], "formula",
                 zhi=f["zhi"], books=f["books"][:5])
    # 证候节点
    for k, s in syndromes.items():
        add_node("syndrome:" + k, s["name"], "syndrome",
                 desc=s["desc"], books=s["books"][:5])
    # 归经边: herb->meridian
    for k, h in herbs.items():
        for mz in h["meridians"]:
            links.append({"source": "herb:" + k, "target": "mer:" + mz,
                          "type": "tropism", "label": "归经"})
    # 归经节点
    for mz in set(m for h in herbs.values() for m in h["meridians"]):
        add_node("mer:" + mz, mz, "meridian")
    # 组成边: formula->herb (去重)
    seen_comp = set()
    for f, h in comp_links:
        key = (f, h)
        if key in seen_comp:
            continue
        seen_comp.add(key)
        links.append({"source": "formula:" + f, "target": "herb:" + h,
                      "type": "compose", "label": "组成"})
    # 证候-方边: syndrome->formula (去重)
    seen_sf = set()
    for s, f in synd_links:
        key = (s, f)
        if key in seen_sf:
            continue
        seen_sf.add(key)
        links.append({"source": "syndrome:" + s, "target": "formula:" + f,
                      "type": "treat", "label": "用方"})

    # 过滤悬空边 (source/target 必须存在于节点 id 集合)
    links = [l for l in links if l["source"] in seen and l["target"] in seen]

    graph = {"nodes": nodes, "links": links}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False)

    from collections import Counter
    nc = Counter(n["class"] for n in nodes)
    lt = Counter(l["type"] for l in links)
    print(f"nodes: {len(nodes)}  {dict(nc)}")
    print(f"links: {len(links)}  {dict(lt)}")
    print(f"herbs={len(herbs)} formulas={len(formulas)} syndromes={len(syndromes)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # 小样本验证: 仅跑几部代表典籍，不写全量
        TEST_BOOKS = ["神农本草经", "伤寒论", "金匮要略方论", "汤头歌诀"]
        cats = load_json(CAT)
        fmap = book_file_map()
        for c in cats:
            if c["name"] in TEST_BOOKS:
                name, lei = c["name"], c["lei"]
                fpath = os.path.join(ROOT, "data", "yizang", fmap[name])
                with open(fpath, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                print(f"\n===== {name} ({lei}) chars={len(text)} =====")
                if lei in HERB_LEI or "本草" in lei:
                    hs = extract_herbs(text, name)
                    print(f"  herbs: {len(hs)}")
                    for k in list(hs)[:6]:
                        h = hs[k]
                        print(f"    {k}: 气={h['qi']} 味={h['wei']} 归经={h['meridians']} 主治={h['zhi'][:20]}")
                if lei in FORMULA_LEI or "方" in lei or "伤寒" in lei or "金匮" in lei:
                    fs, cl = extract_formulas(text, name, {})
                    print(f"  formulas: {len(fs)} comp_links: {len(cl)}")
                    for k in list(fs)[:6]:
                        print(f"    {k}: {fs[k]['herbs'][:6]}")
                if lei in SYND_LEI:
                    ss, sl = extract_syndromes(text, name, {})
                    print(f"  syndromes: {len(ss)} links: {len(sl)}")
                    for k in list(ss)[:6]:
                        print(f"    {k}: {ss[k]['desc'][:30]}")
    else:
        main()
