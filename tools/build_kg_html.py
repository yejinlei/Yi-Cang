# -*- coding: utf-8 -*-
"""
医藏内容层知识图谱 ECharts 力导向图页面生成脚本。
数据从 yizang_kg.json 内联嵌入 HTML (通过 __KG_JSON__ 占位符替换)。

输出: data/ontology/yizang_kg.html
节点类型: herb(中药) / formula(方剂) / syndrome(证候) / meridian(归经)
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH = os.path.join(ROOT, "data", "ontology", "yizang_kg.json")
OUT = os.path.join(ROOT, "data", "ontology", "yizang_kg.html")

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>医藏知识图谱 · 内容层知识元（病-证-方-药）力导向图</title>
<style>
  /* ===== 设计系统：深空蓝 + 星象金（参照《易经》本体论 · The Book of Changes）===== */
  :root{
    --gutter:40px;
    --space:#060f1f; --space-2:#0a1628; --space-3:#0f1f3a;
    --space-card:rgba(18,34,64,.78); --space-card-solid:#132544; --space-deep:#050b18;
    --line:rgba(180,200,230,.18); --line-strong:rgba(200,215,240,.35); --line-soft:rgba(150,175,210,.1);
    --shadow:0 4px 24px rgba(0,0,0,.45); --shadow-lg:0 12px 48px rgba(0,0,0,.6);
    --ink:#e8edf5; --ink-2:#c8d3e5; --ink-3:#8a97ae; --ink-dim:#6a778e;
    --zhu:#d94a4a; --zhu-deep:#b53232; --zhu-soft:#e87b72;
    --gold:#d4b079; --gold-bright:#efd5a4; --gold-deep:#a88648;
    --silver:#c8d0dd; --jade:#7bbfa6; --ice:#7aa8d4; --violet:#a888c8; --amber:#e0a060;
    --radius:6px; --radius-lg:10px;
    --font-serif:'Songti SC','STSong','SimSun','Noto Serif CJK SC','Source Han Serif SC','Noto Serif SC',serif;
    --font-sans:'PingFang SC','Microsoft YaHei','Hiragino Sans GB','Noto Sans CJK SC',sans-serif;
    --font-kai:'STKaiti','KaiTi','Kaiti SC',serif;
  }
  *{margin:0;padding:0;box-sizing:border-box;}
  html,body{height:100%;}
  body{
    font-family:var(--font-serif);
    background:var(--space-2); color:var(--ink);
    line-height:1.9; font-size:16px; -webkit-font-smoothing:antialiased;
    color-scheme:dark; position:relative; overflow-x:hidden;
  }
  /* 星空罗盘背景 */
  body::before{
    content:"";position:fixed;inset:0;z-index:-2;pointer-events:none;
    background:
      radial-gradient(ellipse 1200px 800px at 75% 35%, rgba(60,90,150,.35) 0%, transparent 55%),
      radial-gradient(ellipse 900px 700px at 20% 75%, rgba(120,60,100,.18) 0%, transparent 55%),
      radial-gradient(circle at 50% 50%, #0a1628 0%, #060f1f 100%);
  }
  body::after{
    content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;
    background-image:
      radial-gradient(1px 1px at 13% 22%, rgba(255,255,255,.8), transparent 50%),
      radial-gradient(1px 1px at 28% 56%, rgba(255,255,255,.6), transparent 50%),
      radial-gradient(1.5px 1.5px at 44% 18%, rgba(230,210,170,.9), transparent 50%),
      radial-gradient(1px 1px at 60% 72%, rgba(255,255,255,.7), transparent 50%),
      radial-gradient(1px 1px at 72% 36%, rgba(255,255,255,.5), transparent 50%),
      radial-gradient(1.5px 1.5px at 85% 62%, rgba(220,200,160,.85), transparent 50%),
      radial-gradient(1px 1px at 92% 14%, rgba(255,255,255,.6), transparent 50%),
      radial-gradient(1px 1px at 8% 82%, rgba(255,255,255,.55), transparent 50%),
      radial-gradient(2px 2px at 52% 28%, rgba(255,230,180,.95), transparent 50%),
      radial-gradient(1px 1px at 35% 88%, rgba(255,255,255,.5), transparent 50%);
    background-size:100% 100%;
    animation:starTwinkle 8s ease-in-out infinite alternate;
  }
  @keyframes starTwinkle{0%{opacity:.75;}100%{opacity:1;}}
  a{color:var(--gold);text-decoration:none;transition:color .2s,text-shadow .2s;}
  a:hover{color:var(--gold-bright);text-shadow:0 0 8px rgba(212,176,121,.5);}
  h1,h2,h3,h4{font-family:var(--font-serif);font-weight:700;color:var(--ink);letter-spacing:1px;}
  h2{font-size:26px;letter-spacing:4px;margin-bottom:20px;color:var(--gold-bright);}
  ::selection{background:var(--zhu);color:#fff;}
  ::-webkit-scrollbar{width:8px;height:8px;}
  ::-webkit-scrollbar-track{background:var(--space-deep);}
  ::-webkit-scrollbar-thumb{background:rgba(212,176,121,.25);border-radius:4px;}
  ::-webkit-scrollbar-thumb:hover{background:rgba(212,176,121,.45);}

  /* ===== 顶部导航 ===== */
  .topbar{
    position:sticky;top:0;z-index:1000;height:64px;
    background:linear-gradient(180deg, rgba(10,22,40,.95) 0%, rgba(10,22,40,.82) 100%);
    border-bottom:1px solid var(--line); box-shadow:0 2px 20px rgba(0,0,0,.5);
    display:flex;align-items:center;justify-content:space-between;
    padding:0 28px; backdrop-filter:blur(12px);
  }
  .logo{display:flex;align-items:center;gap:12px;color:var(--ink);font-weight:700;font-size:20px;letter-spacing:6px;}
  .logo .taiji{font-size:26px;line-height:1;color:var(--gold);text-shadow:0 0 12px rgba(212,176,121,.6);}
  .logo .en{font-size:10px;color:var(--ink-3);font-weight:400;letter-spacing:2px;margin-left:6px;font-family:var(--font-sans);}
  .nav-links{display:flex;gap:2px;align-items:center;flex-wrap:wrap;}
  .nav-links a{color:var(--ink-2);font-size:14px;padding:6px 12px;border-radius:4px;letter-spacing:1px;transition:all .2s;white-space:nowrap;}
  .nav-links a:hover{background:rgba(212,176,121,.12);color:var(--gold-bright);text-shadow:0 0 8px rgba(212,176,121,.4);}
  .nav-links a.active{color:var(--gold-bright);background:rgba(212,176,121,.14);font-weight:600;position:relative;}
  .nav-links a.active::after{content:"";position:absolute;left:12px;right:12px;bottom:2px;height:2px;background:linear-gradient(90deg,transparent,var(--gold),transparent);}

  /* ===== 布局：侧边栏 + 内容 ===== */
  .layout{display:flex;min-height:calc(100vh - 64px);}
  .sidebar{
    width:240px;flex-shrink:0;
    background:linear-gradient(180deg, rgba(10,22,40,.92) 0%, rgba(8,16,30,.96) 100%);
    border-right:1px solid var(--line); padding:24px 14px;
    position:sticky;top:64px;height:calc(100vh - 64px);overflow-y:auto;
  }
  .sidebar-section{margin-bottom:20px;}
  .sidebar-title{font-size:11px;color:var(--gold);letter-spacing:4px;padding:0 8px 8px;border-bottom:1px solid var(--line);margin-bottom:8px;font-family:var(--font-sans);text-transform:uppercase;}
  .sidebar a{display:block;padding:7px 10px;color:var(--ink-2);font-size:14px;border-radius:3px;border-left:2px solid transparent;transition:all .15s;}
  .sidebar a:hover{background:rgba(212,176,121,.08);color:var(--gold-bright);border-left-color:var(--gold);}
  .sidebar a.on{color:var(--gold-bright);border-left-color:var(--zhu);background:rgba(217,74,74,.1);font-weight:600;}
  .content{flex:1;min-width:0;padding:32px var(--gutter) 60px;max-width:100%;}

  /* ===== Hero 区 ===== */
  .hero{
    position:relative;overflow:hidden;z-index:1;text-align:center;
    padding:60px 20px 40px;margin-bottom:24px;
    background:
      radial-gradient(ellipse 800px 400px at 50% 40%, rgba(40,70,130,.25) 0%, transparent 70%),
      linear-gradient(180deg, rgba(8,16,32,.4) 0%, transparent 100%);
    border-bottom:1px solid var(--line);
  }
  .hero-taiji{font-size:64px;color:var(--zhu);margin-bottom:8px;display:inline-block;animation:spin 60s linear infinite;text-shadow:0 0 24px rgba(217,74,74,.4);}
  @keyframes spin{to{transform:rotate(360deg);}}
  .hero h1{margin:0 0 6px;font-size:36px;letter-spacing:8px;}
  .hero .subtitle{margin-bottom:14px;color:var(--ink-3);font-size:15px;letter-spacing:3px;}
  .quote{
    background:linear-gradient(135deg, rgba(217,74,74,.08), rgba(212,176,121,.05));
    border-left:3px solid var(--zhu); border-right:1px solid var(--line);
    border-top:1px solid var(--line); border-bottom:1px solid var(--line);
    padding:14px 22px;margin:0 auto 20px;max-width:760px;
    border-radius:0 var(--radius) var(--radius) 0;
    font-family:var(--font-kai); font-size:17px;color:var(--ink);
  }
  .stats-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;max-width:1100px;width:100%;margin:0 auto;}
  .stat-card{
    background:rgba(255,255,255,.04);border:1px solid rgba(212,176,121,.18);
    border-radius:var(--radius-lg);padding:18px 10px;text-align:center;
    backdrop-filter:blur(4px);transition:all .3s;
  }
  .stat-card:hover{background:rgba(212,176,121,.12);border-color:var(--gold);transform:translateY(-3px);}
  .stat-card .stat-num{font-size:30px;color:var(--gold-bright);font-weight:700;letter-spacing:2px;font-family:var(--font-serif);text-shadow:0 0 16px rgba(212,176,121,.3);}
  .stat-card .stat-label{color:var(--ink);font-size:14px;letter-spacing:3px;margin-top:6px;font-weight:600;}
  .stat-card .stat-sub{color:var(--ink-3);font-size:11px;letter-spacing:2px;margin-top:2px;}

  /* ===== 区块卡片 ===== */
  .section{
    background:var(--space-card);border:1px solid var(--line);
    border-radius:var(--radius-lg);padding:28px 32px;margin-bottom:24px;
    backdrop-filter:blur(6px); box-shadow:var(--shadow);
  }
  .section-title{
    font-size:22px;color:var(--gold-bright);letter-spacing:4px;
    margin-bottom:18px;padding-bottom:10px;border-bottom:1px solid var(--line);
    display:flex;align-items:center;gap:10px;
  }
  .section-title .icon{color:var(--zhu);font-size:20px;}

  /* ===== 图谱工具栏 ===== */
  .graph-toolbar{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px;}
  .legend{display:flex;gap:10px;flex-wrap:wrap;align-items:center;}
  .legend .item{display:inline-flex;align-items:center;gap:7px;padding:5px 13px;border-radius:16px;border:1px solid var(--line-strong);cursor:pointer;font-size:13px;letter-spacing:1px;color:var(--ink-2);background:rgba(255,255,255,.02);transition:all .2s;font-family:var(--font-sans);}
  .legend .item:hover{border-color:var(--gold);color:var(--gold-bright);background:rgba(212,176,121,.08);}
  .legend .sw{width:12px;height:12px;border-radius:3px;display:inline-block;}
  .legend .item.off{opacity:.35;text-decoration:line-through;}
  .graph-ctrl{display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
  .search{display:flex;align-items:center;gap:6px;}
  .search input{background:var(--space);border:1px solid var(--line-strong);border-radius:var(--radius);color:var(--ink);padding:7px 10px;font-size:13px;outline:none;width:220px;font-family:var(--font-sans);transition:border-color .2s;}
  .search input:focus{border-color:var(--gold);}
  .btn{display:inline-block;padding:8px 16px;border-radius:4px;font-size:13px;letter-spacing:2px;cursor:pointer;border:1px solid var(--line-strong);background:transparent;color:var(--gold);transition:all .2s;font-family:var(--font-serif);}
  .btn:hover{background:rgba(212,176,121,.12);color:var(--gold-bright);border-color:var(--gold);text-shadow:0 0 8px rgba(212,176,121,.4);}

  /* ===== 图谱容器 ===== */
  #graphBox{width:100%;height:min(72vh,760px);background:var(--space-card-solid);border:1px solid var(--line-soft);border-radius:var(--radius-lg);overflow:hidden;}
  #graphBox.expanded{position:fixed;inset:76px 24px 24px;height:auto;z-index:600;background:var(--space-2);}
  .graph-hint{margin-top:12px;color:var(--ink-3);font-size:12px;letter-spacing:1px;text-align:center;font-family:var(--font-sans);}

  /* ===== 详情面板 ===== */
  .panel{
    position:fixed;right:24px;top:88px;width:340px;max-height:calc(100vh - 140px);overflow:auto;
    background:var(--space-card-solid);border:1px solid rgba(212,176,121,.28);
    border-radius:var(--radius-lg);padding:18px 20px;display:none;z-index:700;
    box-shadow:var(--shadow-lg);backdrop-filter:blur(8px);
  }
  .panel h3{margin:0 0 8px;color:var(--gold-bright);font-size:18px;letter-spacing:2px;}
  .panel .cls{display:inline-block;font-size:12px;padding:2px 12px;border-radius:12px;margin-bottom:10px;font-family:var(--font-sans);letter-spacing:1px;}
  .panel .row{margin:6px 0;font-size:13px;color:var(--ink-2);line-height:1.7;font-family:var(--font-sans);}
  .panel .row b{color:var(--gold);font-weight:400;margin-right:6px;}
  .panel .close{position:absolute;right:12px;top:12px;cursor:pointer;color:var(--ink-3);font-size:18px;background:none;border:none;line-height:1;}
  .panel .close:hover{color:var(--zhu);}

  /* ===== 页脚 ===== */
  .footer{border-top:1px solid var(--line);padding:20px 40px;text-align:center;color:var(--ink-3);font-size:12px;letter-spacing:2px;font-family:var(--font-sans);}

  /* ===== 响应式 ===== */
  @media (max-width:900px){
    .sidebar{display:none;}
    .stats-grid{grid-template-columns:repeat(3,1fr);}
    .hero{padding:40px 14px 30px;}
  }
  @media (max-width:640px){
    body{font-size:15px;}
    .stats-grid{grid-template-columns:repeat(2,1fr);gap:8px;}
    .stat-card{padding:12px 6px;}
    .stat-card .stat-num{font-size:22px;}
    .logo .en{display:none;}
    .content{padding:20px 16px 48px;}
    .section{padding:20px 18px;}
    #graphBox{height:min(64vh,480px);}
    .search input{width:150px;}
  }
</style>
</head>
<body>

<header class="topbar">
  <a class="logo" href="../../index.html"><span class="taiji">☯</span>医藏本体论<span class="en">YI-CANG ONTOLOGY</span></a>
  <nav class="nav-links">
    <a href="../../index.html">首页</a>
    <a class="active" href="yizang_kg.html">知识元图谱</a>
    <a href="yizang_graph.html">结构图谱</a>
    <a href="yizang_tree.html">七层原型</a>
    <a href="../../docs/ontology_spec.md">规范</a>
  </nav>
</header>

<div class="layout">
  <aside class="sidebar">
    <div class="sidebar-section">
      <div class="sidebar-title">图谱导航</div>
      <a class="on" href="yizang_kg.html">知识元图谱</a>
      <a href="yizang_graph.html">概念结构图谱</a>
      <a href="yizang_tree.html">七层嵌套原型</a>
    </div>
    <div class="sidebar-section">
      <div class="sidebar-title">说明</div>
      <p style="font-size:12px;color:var(--ink-3);padding:0 8px;line-height:1.8;font-family:var(--font-sans);">
        内容层知识元：中药 · 方剂 · 证候，含组成（方-药）与治疗（证-方）两类关系。拖拽、缩放、点击节点查看详情，支持图例筛选与搜索定位。
      </p>
    </div>
  </aside>

  <main class="content">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-taiji">☯</div>
      <h1>医藏知识图谱</h1>
      <div class="subtitle">THE MEDICAL CANON ONTOLOGY · 内容层知识元（病-证-方-药）力导向图</div>
      <div class="quote">"方随证立，药随方出 · 理法方药，一以贯之"</div>
      <div class="stats-grid" id="statsGrid"></div>
    </section>

    <!-- 图谱 -->
    <section class="section">
      <div class="section-title"><span class="icon">✦</span>知识元关系图谱</div>
      <div class="graph-toolbar">
        <div class="legend" id="legend"></div>
        <div class="graph-ctrl">
          <div class="search">
            <input id="search" placeholder="搜索药名/方名/证候..." />
          </div>
          <button class="btn" id="fullBtn">全屏</button>
        </div>
      </div>
      <div id="graphBox"></div>
      <div class="graph-hint">拖拽节点 · 滚轮缩放 · 点击节点查看详情 · 回车搜索定位高亮</div>
    </section>

    <div class="footer">医藏本体论 · 参照《易经》本体论范式 · 殆知阁医藏文本 · 力导向图谱</div>
  </main>
</div>

<div class="panel" id="panel">
  <button class="close" onclick="hidePanel()">×</button>
  <h3 id="pName"></h3>
  <span class="cls" id="pCls"></span>
  <div id="pBody"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js"></script>
<script>
const DATA = __KG_JSON__;

const CLS_COLOR = {
  herb:     '#7bbfa6',   /* 玉青 */
  formula:  '#7aa8d4',   /* 冰蓝 */
  syndrome: '#e0a060',   /* 琥珀 */
  meridian: '#a888c8'    /* 紫 */
};
const CLS_NAME = {
  herb:     '中药',
  formula:  '方剂',
  syndrome: '证候',
  meridian: '归经'
};
const CLS_SIZE = {
  herb:     10,
  formula:  14,
  syndrome: 12,
  meridian: 18
};
const EDGE_COLOR = {
  compose: '#7aa8d4',   /* 冰蓝 */
  treat:   '#d94a4a',   /* 朱红 */
  tropism: '#a888c8'    /* 紫 */
};

const graphBox = document.getElementById('graphBox');
const chart = echarts.init(graphBox);

function nodeToData(n) {
  const size = CLS_SIZE[n.class] || 10;
  return {
    id: n.id, name: n.name, category: n.class,
    symbolSize: size,
    itemStyle: { color: CLS_COLOR[n.class] || '#8a97ae' },
    value: n,
    label: { show: size >= 14, fontSize: 10, color: '#e8edf5' },
    tooltip: { formatter: () => {
      let t = `<b>${n.name}</b><br/>${CLS_NAME[n.class] || n.class}`;
      if (n.qi) t += `<br/>性: ${n.qi}`;
      if (n.wei) t += `<br/>味: ${n.wei}`;
      if (n.meridians && n.meridians.length) t += `<br/>归经: ${n.meridians.join('、')}`;
      if (n.books && n.books.length) t += `<br/>出处: ${n.books.join('、')}`;
      return t;
    }}
  };
}

const series = [{
  type: 'graph',
  layout: 'force',
  data: DATA.nodes.map(nodeToData),
  links: DATA.links.map(l => ({
    source: l.source, target: l.target,
    lineStyle: { color: EDGE_COLOR[l.type] || '#6a778e', width: 1, curveness: 0.1, opacity: 0.6 },
    tooltip: { formatter: () => `<b>${l.label || l.type}</b>` }
  })),
  categories: Object.keys(CLS_COLOR).map(k => ({ name: k, itemStyle: { color: CLS_COLOR[k] } })),
  force: { repulsion: 260, edgeLength: [40, 130], gravity: 0.1, friction: 0.6 },
  roam: true,
  draggable: true,
  emphasis: { focus: 'adjacency', lineStyle: { width: 2 } },
  scaleLimit: { min: 0.2, max: 5 }
}];

chart.setOption({
  tooltip: {
    show: true,
    backgroundColor: '#132544', borderColor: 'rgba(200,215,240,.35)',
    textStyle: { color: '#e8edf5' }
  },
  series: series
});

// ---- 统计卡 ----
(function() {
  const counts = {};
  DATA.nodes.forEach(n => counts[n.class] = (counts[n.class] || 0) + 1);
  const edgeCounts = {};
  DATA.links.forEach(l => edgeCounts[l.type] = (edgeCounts[l.type] || 0) + 1);
  const items = [
    { num: DATA.nodes.length, label: '节点总数', sub: '知识元' },
    { num: counts.herb || 0, label: '中药', sub: 'herb' },
    { num: counts.formula || 0, label: '方剂', sub: 'formula' },
    { num: counts.syndrome || 0, label: '证候', sub: 'syndrome' },
    { num: DATA.links.length, label: '关系边', sub: 'links' },
    { num: edgeCounts.compose || 0, label: '组成边', sub: '方-药' }
  ];
  const grid = document.getElementById('statsGrid');
  grid.innerHTML = items.map(it =>
    `<div class="stat-card"><div class="stat-num">${it.num.toLocaleString()}</div>` +
    `<div class="stat-label">${it.label}</div><div class="stat-sub">${it.sub}</div></div>`
  ).join('');
})();

// ---- 图例筛选（徽章）----
const legendEl = document.getElementById('legend');
const toggles = {};
Object.keys(CLS_COLOR).forEach(k => {
  toggles[k] = true;
  const div = document.createElement('div');
  div.className = 'item';
  div.innerHTML = `<span class="sw" style="background:${CLS_COLOR[k]}"></span>${CLS_NAME[k]}`;
  div.onclick = () => {
    toggles[k] = !toggles[k];
    div.classList.toggle('off', !toggles[k]);
    chart.setOption({ series: [{ data: DATA.nodes
      .filter(n => toggles[n.class] !== false)
      .map(nodeToData) }] });
  };
  legendEl.appendChild(div);
});

// ---- 搜索定位 ----
document.getElementById('search').addEventListener('keydown', function(e) {
  if (e.key !== 'Enter') return;
  const q = this.value.trim();
  if (!q) return;
  const idx = DATA.nodes.findIndex(n => n.name.includes(q) || (n.id.indexOf(q) > -1));
  if (idx >= 0) {
    chart.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex: idx });
    chart.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: idx });
  }
});

// ---- 全屏切换 ----
document.getElementById('fullBtn').addEventListener('click', function() {
  const exp = graphBox.classList.toggle('expanded');
  this.textContent = exp ? '还原' : '全屏';
  setTimeout(() => chart.resize(), 30);
});

// ---- 点击详情 ----
chart.on('click', function(params) {
  if (params.dataType !== 'node') return;
  const n = params.data.value;
  const el = document.getElementById('panel');
  document.getElementById('pName').textContent = n.name;
  const cls = document.getElementById('pCls');
  cls.textContent = CLS_NAME[n.class] || n.class;
  cls.style.color = CLS_COLOR[n.class] || '#8a97ae';
  cls.style.border = '1px solid ' + (CLS_COLOR[n.class] || '#8a97ae');
  cls.style.background = 'rgba(255,255,255,.03)';
  let body = '';
  if (n.qi) body += `<div class="row"><b>性</b>${n.qi}</div>`;
  if (n.wei) body += `<div class="row"><b>味</b>${n.wei}</div>`;
  if (n.meridians && n.meridians.length) body += `<div class="row"><b>归经</b>${n.meridians.join('、')}</div>`;
  if (n.zhi) body += `<div class="row"><b>主治</b>${n.zhi}</div>`;
  if (n.desc) body += `<div class="row"><b>条文</b>${n.desc}</div>`;
  if (n.books && n.books.length) body += `<div class="row"><b>出处</b>${n.books.join('、')}</div>`;
  document.getElementById('pBody').innerHTML = body || '<div class="row">知识元节点</div>';
  el.style.display = 'block';
});

function hidePanel() { document.getElementById('panel').style.display = 'none'; }

window.addEventListener('resize', () => chart.resize());
</script>
</body>
</html>
"""


def main():
    with open(GRAPH, encoding="utf-8") as f:
        graph = json.load(f)
    html = TEMPLATE.replace("__KG_JSON__", json.dumps(graph, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"生成 {OUT}  ({os.path.getsize(OUT)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
