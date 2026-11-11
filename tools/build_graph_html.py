# -*- coding: utf-8 -*-
"""
医藏知识图谱 ECharts 力导向图页面生成脚本。
数据从 yizang_graph.json 内联嵌入 HTML (通过 __GRAPH_JSON__ 占位符替换)。

输出: data/ontology/yizang_graph.html
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH = os.path.join(ROOT, "data", "ontology", "yizang_graph.json")
OUT = os.path.join(ROOT, "data", "ontology", "yizang_graph.html")

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>医藏知识图谱 · 中华医藏概念关联力导向图</title>
<style>
  body{margin:0;font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:#0d1117;color:#e6edf3;overflow:hidden}
  #chart{width:100vw;height:100vh}
  .panel{position:fixed;right:20px;top:20px;width:320px;max-height:calc(100vh-120px);overflow:auto;
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
  .title{position:fixed;left:20px;bottom:20px;color:#8b949e;font-size:12px;z-index:20}
  .stats{position:fixed;right:20px;bottom:20px;color:#8b949e;font-size:12px;z-index:20}
</style>
</head>
<body>
<div id="chart"></div>

<div class="legend" id="legend"></div>
<div class="title">医藏知识图谱 · ECharts 力导向图 · 拖拽/缩放/点击节点查看详情</div>
<div class="stats" id="stats"></div>

<div class="panel" id="panel">
  <button class="close" onclick="hidePanel()">×</button>
  <h3 id="pName"></h3>
  <span class="cls" id="pCls"></span>
  <div id="pBody"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js"></script>
<script>
const DATA = __GRAPH_JSON__;

const CLS_COLOR = {
  concept:  '#4ade80',
  wuxing:   '#f59e0b',
  category: '#38bdf8',
  bian:     '#a78bfa',
  book:     '#64748b'
};
const CLS_NAME = {
  concept:  '概念类',
  wuxing:   '五行',
  category: '类目',
  bian:     '四编',
  book:     '典籍'
};
const CLS_SIZE = {
  concept:  42,
  wuxing:   30,
  category: 32,
  bian:     38,
  book:     10
};
const EDGE_COLOR = {
  belongs: '#475569',
  concept: '#4ade80',
  wu:      '#f59e0b',
  cites:   '#38bdf8'
};

const chart = echarts.init(document.getElementById('chart'));

// ---- 力导向图 series ----
const series = [{
  type: 'graph',
  layout: 'force',
  data: DATA.nodes.map(n => {
    const size = CLS_SIZE[n.class] || 10;
    return {
      id: n.id,
      name: n.name,
      category: n.class,
      symbolSize: size,
      itemStyle: { color: CLS_COLOR[n.class] || '#64748b' },
      value: n,
      label: { show: size >= 28, fontSize: 11, color: '#e6edf3' },
      tooltip: { formatter: () => {
        return `<b>${n.name}</b><br/>${CLS_NAME[n.class] || n.class}` +
          (n.bian ? `<br/>编: ${n.bian}` : '') +
          (n.category ? `<br/>类: ${n.category}` : '') +
          (n.count ? `<br/>藏书: ${n.count} 部` : '') +
          (n.chars ? `<br/>字数: ${n.chars}` : '');
      }}
    };
  }),
  links: DATA.links.map(l => ({
    source: l.source,
    target: l.target,
    lineStyle: { color: EDGE_COLOR[l.type] || '#475569', width: l.type==='wu'?2:1, curveness: 0.1, opacity: 0.7 },
    tooltip: { formatter: () => `<b>${l.label || l.type}</b><br/>${l.source} → ${l.target}` }
  })),
  categories: Object.keys(CLS_COLOR).map(k => ({ name: k, itemStyle: { color: CLS_COLOR[k] } })),
  force: { repulsion: 320, edgeLength: [50, 150], gravity: 0.08, friction: 0.6 },
  roam: true,
  draggable: true,
  emphasis: { focus: 'adjacency', lineStyle: { width: 2 } },
  scaleLimit: { min: 0.3, max: 4 }
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
  if (n.bian) body += `<div class="row"><b>编</b>${n.bian}</div>`;
  if (n.category) body += `<div class="row"><b>类</b>${n.category}</div>`;
  if (n.count) body += `<div class="row"><b>藏书</b>${n.count} 部</div>`;
  if (n.chars) body += `<div class="row"><b>字数</b>${n.chars}</div>`;
  if (n.hanzi) body += `<div class="row"><b>汉字</b>${n.hanzi}</div>`;
  if (n.file) body += `<div class="row"><b>文件</b>${n.file}</div>`;
  if (n.root) body += `<div class="row"><b>根类</b>医藏根类节点</div>`;
  if (n.rootOf) body += `<div class="row"><b>属</b>${n.rootOf}</div>`;
  document.getElementById('pBody').innerHTML = body || '<div class="row">概念节点</div>';
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
      .map(n => ({ id: n.id, name: n.name, category: n.class,
        symbolSize: CLS_SIZE[n.class]||10,
        itemStyle: { color: CLS_COLOR[n.class]||'#64748b' },
        value: n,
        label: { show: (CLS_SIZE[n.class]||10)>=28, fontSize: 11, color:'#e6edf3' },
        tooltip: { formatter: () => `<b>${n.name}</b><br/>${CLS_NAME[n.class]||n.class}` }
      })) }] });
  };
  legendEl.appendChild(div);
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
    html = TEMPLATE.replace("__GRAPH_JSON__", json.dumps(graph, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"生成 {OUT}  ({os.path.getsize(OUT)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
