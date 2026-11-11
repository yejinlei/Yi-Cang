# -*- coding: utf-8 -*-
"""
构建医藏本体七层嵌套金字塔 D3.js 交互原型。
产出 data/ontology/yizang_tree.html —— 自包含单文件，内联数据，浏览器直接打开。

布局：左侧七层金字塔（L1-L7 嵌套），右侧详情面板。
交互：点击节点下钻/聚焦，悬浮显示数量，面包屑导航返回上级。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "yizang")
OUT_DIR = os.path.join(ROOT, "data", "ontology")
TREE_FILE = os.path.join(OUT_DIR, "yizang_tree.json")
OUT = os.path.join(OUT_DIR, "yizang_tree.html")

tree = json.load(open(TREE_FILE, encoding="utf-8"))

# 嵌入数据
tree_json = json.dumps(tree, ensure_ascii=False)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>医藏本体论 · 七层嵌套金字塔</title>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<style>
:root{
  --bg:#0f1419; --panel:#1a2230; --panel2:#222c3d; --line:#33415a;
  --txt:#e6edf3; --muted:#8b98ad; --brand:#3fa96c; --brand2:#5ecb8a;
  --accent:#4a9eff; --warn:#e6b350; --red:#e06c6c;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:"Microsoft YaHei","PingFang SC",sans-serif;height:100vh;display:flex;flex-direction:column;overflow:hidden}
header{padding:14px 22px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:16px;flex-shrink:0}
header h1{font-size:19px;font-weight:600;letter-spacing:1px}
header .sub{font-size:12px;color:var(--muted)}
header .badge{font-size:11px;background:var(--brand);color:#06231a;padding:3px 9px;border-radius:20px;font-weight:600}
header .badge.alt{background:var(--accent);color:#05131f}
.breadcrumb{font-size:13px;color:var(--muted);padding:10px 22px;border-bottom:1px solid var(--line);flex-shrink:0;display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.breadcrumb a{color:var(--brand2);cursor:pointer;text-decoration:none}
.breadcrumb a:hover{text-decoration:underline}
.breadcrumb .sep{color:#4a5a75}
main{flex:1;display:flex;overflow:hidden}
#chart{flex:1;position:relative;overflow:hidden}
#panel{width:340px;border-left:1px solid var(--line);overflow-y:auto;padding:18px;flex-shrink:0;background:var(--panel)}
#panel h2{font-size:15px;margin-bottom:6px;color:var(--brand2)}
#panel .meta{font-size:12px;color:var(--muted);margin-bottom:12px;line-height:1.8}
#panel .props{background:var(--panel2);border-radius:8px;padding:10px 12px;font-size:12.5px;line-height:1.9}
#panel .props b{color:var(--accent);font-weight:600}
#panel .count{font-size:22px;font-weight:700;color:var(--brand);margin:8px 0}
#panel .count small{font-size:12px;color:var(--muted);font-weight:400;margin-left:6px}
#panel .child-list{margin-top:12px}
#panel .child-item{padding:7px 10px;border:1px solid var(--line);border-radius:6px;margin-bottom:6px;font-size:12.5px;cursor:pointer;transition:.15s}
#panel .child-item:hover{border-color:var(--brand);background:var(--panel2)}
#panel .child-item .n{float:right;color:var(--muted);font-size:11px}
.legend{position:absolute;top:12px;left:12px;background:rgba(26,34,48,.9);border:1px solid var(--line);border-radius:8px;padding:10px 12px;font-size:11px;color:var(--muted);z-index:5;max-width:220px}
.legend b{color:var(--txt)}
.legend .row{display:flex;align-items:center;gap:6px;margin-top:4px}
.legend .dot{width:10px;height:10px;border-radius:2px;display:inline-block}
.zoom-ctrl{position:absolute;bottom:16px;right:16px;display:flex;flex-direction:column;gap:6px;z-index:6}
.zoom-ctrl button{width:34px;height:34px;background:var(--panel);border:1px solid var(--line);color:var(--txt);border-radius:6px;cursor:pointer;font-size:16px}
.zoom-ctrl button:hover{border-color:var(--brand);color:var(--brand2)}
.node{cursor:pointer}
.node circle{stroke:var(--line);stroke-width:1.5px;transition:r .2s}
.node text{font-size:11px;fill:var(--txt);pointer-events:none}
.node .sub{font-size:9px;fill:var(--muted)}
.link{fill:none;stroke:var(--line);stroke-opacity:.7;stroke-width:1.2px}
.tooltip{position:absolute;background:var(--panel2);border:1px solid var(--brand);color:var(--txt);padding:6px 10px;border-radius:6px;font-size:12px;pointer-events:none;opacity:0;transition:opacity .15s;z-index:10;max-width:260px}
.empty{position:absolute;top:45%;width:100%;text-align:center;color:var(--muted);font-size:14px}
</style>
</head>
<body>
<header>
  <h1>医藏本体论 · 七层嵌套金字塔</h1>
  <span class="badge">《中华医藏》四编二十八类</span>
  <span class="badge alt">W3C OWL 2 DL</span>
  <span class="sub" id="total"></span>
</header>
<div class="breadcrumb" id="crumb"></div>
<main>
  <div id="chart">
    <div class="legend">
      <b>图例</b>
      <div class="row"><span class="dot" style="background:#3fa96c"></span>L1 顶层(BFO)</div>
      <div class="row"><span class="dot" style="background:#4a9eff"></span>L2 四大根类</div>
      <div class="row"><span class="dot" style="background:#e6b350"></span>L3 四编二十八类</div>
      <div class="row"><span class="dot" style="background:#8b98ad"></span>L4 单本典籍(788)</div>
      <div class="row"><span class="dot" style="background:#5ecb8a"></span>L5-L7 篇章/知识元/条文</div>
    </div>
    <div class="zoom-ctrl">
      <button id="zin" title="放大">+</button>
      <button id="zout" title="缩小">−</button>
      <button id="zreset" title="重置">⟲</button>
    </div>
    <div class="tooltip" id="tip"></div>
  </div>
  <div id="panel">
    <h2>—</h2>
    <div class="meta" id="pmeta"></div>
    <div class="count" id="pcount"></div>
    <div class="props" id="pprops" style="display:none"></div>
    <div class="child-list" id="pchildren"></div>
  </div>
</main>

<script>
const RAW = __TREE_JSON__;
const LCOLOR = {1:"#3fa96c",2:"#4a9eff",3:"#e6b350",4:"#8b98ad",5:"#5ecb8a",6:"#5ecb8a",7:"#5ecb8a"};
const LNAME = {0:"根",1:"L1 顶层",2:"L2 根类",3:"L3 类目",4:"L4 典籍",5:"L5 篇章",6:"L6 知识元",7:"L7 条文"};

let svg, root, g, zoom, tooltip;
let focusNode = null;
const W=window.innerWidth, H=window.innerHeight;

function init(){
  const chart=d3.select("#chart");
  svg=chart.append("svg").attr("width","100%").attr("height","100%");
  g=svg.append("g").attr("transform","translate(0,30)");
  tooltip=d3.select("#tip");
  zoom=d3.zoom().scaleExtent([0.3,4]).on("zoom",e=>g.attr("transform",e.transform));
  svg.call(zoom);
  root=d3.hierarchy(RAW, d=>d.children);
  document.getElementById("total").textContent="L4 典籍 "+root.data.count+" 部 · 28 类";
  draw(RAW);
  d3.select("#zin").on("click",()=>svg.transition().call(zoom.scaleBy,1.3));
  d3.select("#zout").on("click",()=>svg.transition().call(zoom.scaleBy,0.75));
  d3.select("#zreset").on("click",()=>svg.transition().call(zoom.transform,d3.zoomIdentity));
  window.addEventListener("resize",()=>{ if(focusNode) draw(focusNode); else draw(RAW); });
}

function crumbChain(node){
  const chain=[]; let cur=node;
  while(cur){chain.unshift(cur); cur=cur.parent;}
  return chain;
}

function draw(node){
  focusNode=node;
  // 面包屑
  const chain=crumbChain(node);
  const crumb=d3.select("#crumb");
  crumb.html("");
  chain.forEach((n,i)=>{
    if(i>0){crumb.append("span").attr("class","sep").text("›");}
    crumb.append("a").text(n.data.label).on("click",()=>{ if(n!==node) draw(n); });
  });

  // 收集可展示节点（取 node 及其子树，若子树过大则聚合）
  const treeRoot=d3.hierarchy(node, d=>d.children);
  const all=treeRoot.descendants();
  g.selectAll("*").remove();
  const width=Math.max(700, chartWidth());
  const height=Math.max(420, chartHeight());

  const nodes=all;
  const depthSet=new Set(nodes.map(n=>n.depth));
  const maxDepth=Math.max(...depthSet);

  // 布局：按深度分列
  const xPad=120, xGap=(width-2*xPad)/Math.max(1,(maxDepth+1));
  const yScale=d3.scaleBand().domain(nodes.map(n=>n.data.label)).range([20,height-20]).padding(.15);

  // 计算每深度数量以分层
  const depthCount={};
  nodes.forEach(n=>{depthCount[n.depth]=(depthCount[n.depth]||0)+1;});
  const maxCount=Math.max(1,...Object.values(depthCount));

  nodes.forEach(n=>{
    const depth=n.depth;
    const x=xPad+depth*xGap;
    const colNodes=nodes.filter(m=>m.depth===depth);
    const idx=colNodes.indexOf(n);
    const y=20+(height-40)*(maxCount>1?idx/(colNodes.length):0.5);
    n.x=x; n.y=y;
  });

  // 连线
  g.selectAll(".link").data(treeRoot.links()).enter().append("path")
    .attr("class","link")
    .attr("d",d=>{ const dx=d.target.x-d.source.x, dy=d.target.y-d.source.y;
      return "M"+d.source.x+","+d.source.y+"C"+(d.source.x+dx/2)+","+d.source.y+" "+(d.source.x+dx/2)+","+d.target.y+" "+d.target.x+","+d.target.y; });

  // 节点
  const nodeSel=g.selectAll(".node").data(nodes).enter().append("g")
    .attr("class","node")
    .attr("transform",d=>"translate("+d.x+","+d.y+")")
    .on("click",(e,d)=>draw(d))
    .on("mouseover",(e,d)=>showTip(e,d))
    .on("mousemove",(e,d)=>moveTip(e))
    .on("mouseout",hideTip);

  nodeSel.append("circle")
    .attr("r",d=> rFor(d))
    .attr("fill",d=>LCOLOR[d.data.level]||"#8b98ad")
    .attr("stroke-width",d=> d===treeRoot?3:1.5);

  nodeSel.append("text")
    .attr("x",d=>rFor(d)+8)
    .attr("y",2)
    .text(d=>trunc(d.data.label,14));
  nodeSel.append("text")
    .attr("class","sub")
    .attr("x",d=>rFor(d)+8)
    .attr("y",14)
    .text(d=>d.data.count?("共"+d.data.count+" 部"):LNAME[d.data.level]||"");

  // 详情面板
  showPanel(node);
}

function rFor(d){ return Math.min(18, 8+ (d.children?Math.sqrt(d.children.length)*1.6:0)); }

function chartWidth(){ return Math.max(700, document.getElementById("chart").clientWidth-20); }
function chartHeight(){ return Math.max(420, document.getElementById("chart").clientHeight-60); }

function trunc(s,n){ if(!s)return""; return s.length>n?s.slice(0,n)+"…":s; }

function showTip(e,d){
  const parts=["<b>"+d.data.label+"</b>","层："+LNAME[d.data.level]];
  if(d.data.count)parts.push("含 "+d.data.count+" 部典籍");
  tooltip.html(parts.join("<br>")).style("opacity",1);
  moveTip(e);
}
function moveTip(e){ const c=document.getElementById("chart").getBoundingClientRect();
  tooltip.style("left",(e.clientX-c.left+14)+"px").style("top",(e.clientY-c.top+10)+"px"); }
function hideTip(){ tooltip.style("opacity",0); }

function showPanel(n){
  const d=n.data;
  document.getElementById("panel").querySelector("h2").textContent=d.label;
  const meta=[];
  meta.push("层级："+LNAME[d.level]);
  if(d.level===3){meta.push("类型：分类类目");}
  if(d.level===4&&d.type==="book"){meta.push("来源：殆知阁医藏"); meta.push("文件："+(d.file||"—"));}
  if(d.demo)meta.push("状态：原型演示节点");
  document.getElementById("pmeta").innerHTML=meta.map(m=>m.replace(/&/g,"&amp;")).join("<br>");

  const pc=document.getElementById("pcount");
  if(d.count){pc.innerHTML=d.count+"<small>部典籍</small>";pc.style.display="block";}
  else{pc.style.display="none";}

  const pp=document.getElementById("pprops");
  if(d.props){pp.style.display="block";pp.innerHTML=Object.entries(d.props).map(([k,v])=>`<b>${k}</b>：${v}`).join("<br>");}
  else{pp.style.display="none";}

  const cl=document.getElementById("pchildren");
  cl.innerHTML="";
  const kids=(d.children||[]);
  if(kids.length){
    cl.innerHTML='<div style="font-size:12px;color:var(--muted);margin-bottom:8px">子节点 ('+kids.length+')</div>';
    kids.slice(0,40).forEach(k=>{
      const item=document.createElement("div");item.className="child-item";
      const n=(k.count||k.children&&k.children.length||0);
      item.innerHTML=(k.label||k.id)+(n?'<span class="n">'+n+'</span>':'');
      item.onclick=()=>{ // 找到对应层级节点
        const t=findIn(n,k); if(t)draw(t); };
      cl.appendChild(item);
    });
  }
}

function findIn(parent,k){
  // 在原始树中按 id 查找
  function walk(node){ if(node.id===k.id)return node;
    for(const c of (node.children||[])){const r=walk(c);if(r)return r;} return null;}
  return walk(parent);
}

init();
</script>
</body>
</html>
"""

html = HTML_TEMPLATE.replace("__TREE_JSON__", tree_json)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print(f"已生成 {OUT}  ({os.path.getsize(OUT)/1024:.0f} KB)")
