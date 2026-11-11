# 医藏本体论 Yizang Ontology
> 对齐《中华医藏》四编二十八类 · 兼容 W3C OWL 2 DL · 七层嵌套金字塔知识本体

参照[佛学本体论](https://yejinlei.github.io/Buddhist/)与[易经本体论](https://yejinlei.github.io/yejing/)范式构建的医藏典籍知识本体站。

## 项目特点
- 🏛️ **四编二十八类体系**：第一编（医经/伤寒金匮/本草/养生/医史）、第二编（藏象/运气/病因病机/针灸推拿/经络骨度/诊法/方书）、第三编（通论/内外妇儿等临证各科/医案医话/丛书）、第四编（藏医/蒙医/维医/傣医/彝医）
- 📚 **788 部殆知阁医书原文**：全部按类目归类入库，单本小文件（最大 19.97MB），原文入库不压缩不改字
- 🧬 **七层嵌套金字塔**：BFO 顶层 → 四大根类 → 四编二十八类 → 单本医书 → 篇章卷次 → 知识元（病-脉-证-治-方-药）→ 条文异文
- 🕸️ **15 条对象属性 + 16 条数据属性**：五行生克传递、学术传承引用、方剂组成、归经、馆藏等
- ⚙️ **OWL 2 DL / JSON-LD** 元类定义，兼容推理机自动校验
- 🖥️ **D3.js 交互原型**：分层树点击下钻、面包屑导航、右侧详情面板

## 目录结构
```
├── data/
│   ├── yizang/
│   │   ├── texts/         # 788 部医书原文，按 第一编_类目/ 归类
│   │   ├── categories.json  # 28 类分类标注（L3）
│   │   └── index.json     # 788 部完整索引（L4）
│   └── ontology/          # 元类定义 + 七层树数据 + D3 原型
├── docs/
│   └── ontology_spec.md   # 最终实现蓝图
└── tools/                 # 构建脚本（抓取/分类/本体/原型）
```

## 快速部署到 GitHub Pages
1. 在 GitHub 新建名为 `Yi-Cang` 的空公开仓库
2. 推送 main 分支
3. 仓库 Settings → Pages → Source 选择 `main` 分支根目录 `/`
4. 等待 1-2 分钟访问 `https://yejinlei.github.io/Yi-Cang/`

## 本地预览
```bash
python -m http.server 8000
# 打开 http://localhost:8000/data/ontology/yizang_tree.html
```
