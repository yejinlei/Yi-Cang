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
  body{margin:0;font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:#0d1117;color:#e6edf3;overflow:hidden}
  #chart{width:100vw;height:100vh}
  .panel{position:fixed;right:20px;top:20px;width:340px;max-height:calc(100vh-120px);overflow:auto;
         background:#161b22;border:1px solid #30363d;border-radius:12px;padding:18px;display:none;z-index:20}
  .panel h3{margin:0 0 6px;color:#4ade80;font-size:18px}
  .panel .cls{display:inline-block;font-size:12px;padding:2px 10px;border-radius:12px;margin-bottom:10px}
  .panel .row{margin:6px 0;font-size:13px;color:#c9d1d9;line-height:1.6}
  .panel .row b{color:#8b949e;font-weight:400;margin-right:6px}
  .panel .close{position:absolute;right:12px;top:12px;cursor:pointer;color:#8b949e;font-size:18px;background:none;border:none}
  .legend{position:fixed;left:20px;top:20px;background:#161b22;border:1px solid #30363d;border-radius:12px;padding:12px 16px;z-index:20;font-size:13px}
  .legend .item{display:flex;align-items:center;margin:6px 0;cursor:pointer}
  .legend .sw{width:14px;height:14px;border-radius:4px;margin-right:8px;display:inline-block}
  .legend .off{opacity:.3;text-decoration:line-through}
  .search{position:fixed;left:20px;top:170px;background:#161b22;border:1px solid #30363d;border-radius:12px;padding:12px;z-index:20;font-size:13px;width:220px}
  .search input{width:100%;box-sizing:border-box;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#e6edf3;padding:6px 8px;font-size:13px;outline:none}
  .search .hint{color:#8b949e;font-size:11px;margin-top:6px}
  .title{position:fixed;left:20px;bottom:20px;color:#8b949e;font-size:12px;z-index:20}
  .stats{position:fixed;right:20px;bottom:20px;color:#8b949e;font-size:12px;z-index:20}
</style>
</head>
<body>
<div id="chart"></div>

<div class="legend" id="legend"></div>
<div class="search">
  <input id="search" placeholder="搜索药名/方名/证候..." />
  <div class="hint">输入名称，回车定位高亮</div>
</div>
<div class="title">医藏知识图谱 · 内容层知识元（药-方-证候）力导向图 · 拖拽/缩放/点击查看详情</div>
<div class="stats" id="stats"></div>

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
  herb:     '#4ade80',
  formula:  '#38bdf8',
  syndrome: '#f59e0b',
  meridian: '#a78bfa'
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
  compose: '#38bdf8',
  treat:   '#f59e0b',
  tropism: '#a78bfa'
};

const chart = echarts.init(document.getElementById('chart'));

function nodeToData(n) {
  const size = CLS_SIZE[n.class] || 10;
  return {
    id: n.id, name: n.name, category: n.class,
    symbolSize: size,
    itemStyle: { color: CLS_COLOR[n.class] || '#64748b' },
    value: n,
    label: { show: size >= 14, fontSize: 10, color: '#e6edf3' },
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
    lineStyle: { color: EDGE_COLOR[l.type] || '#475569', width: 1, curveness: 0.1, opacity: 0.6 },
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
  tooltip: { show: true, backgroundColor: '#161b22', borderColor: '#30363d', textStyle: { color: '#e6edf3' } },
  series: series
});

// ---- 点击详情 ----
chart.on('click', function(params) {
  if (params.dataType !== 'node') return;
  const n = params.data.value;
  const el = document.getElementById('panel');
  document.getElementById('pName').textContent = n.name;
  const cls = document.getElementById('pCls');
  cls.textContent = CLS_NAME[n.class] || n.class;
  cls.style.color = CLS_COLOR[n.class] || '#64748b';
  cls.style.border = '1px solid ' + (CLS_COLOR[n.class] || '#64748b');
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

// ---- 图例筛选 ----
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
  const hit = DATA.nodes.find(n => n.name.includes(q) || (n.id.indexOf(q) > -1));
  if (hit) {
    chart.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex:
      DATA.nodes.findIndex(n => n.id === hit.id) });
    chart.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex:
      DATA.nodes.findIndex(n => n.id === hit.id) });
  }
});

document.getElementById('stats').textContent =
  `节点 ${DATA.nodes.length} · 边 ${DATA.links.length}`;

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
