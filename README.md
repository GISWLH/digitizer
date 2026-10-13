<p align="center"><img src="docs/assets/icon.svg" width="64" alt="Digitizer logo"></p>

![Digitizer — Figures in. Evidence out.](docs/assets/banner.svg)

[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md)

[![CI](https://github.com/GISWLH/digitizer/actions/workflows/test.yml/badge.svg)](https://github.com/GISWLH/digitizer/actions) ![Python](https://img.shields.io/badge/Python-3.11%2B-315847) ![Software license](https://img.shields.io/badge/Software-MIT-cdeaac)

# 让论文中的曲线，成为可复核的数据。

**Digitizer** 基于 [THU Digitizer](https://github.com/Rimagination/thu-digitizer)，将科研图表数字化为 CSV。重点增强图例排除、遮挡留空和证据交付，提供 CLI 与可安装的 Agent 技能。

**[→ 交互案例画廊](https://giswlh.github.io/digitizer/)** · [Agent skill](SKILL.md) · [Configuration](references/configuration.md)

## 核心能力

- **精细图例遮罩**：矩形、多边形和按系列生效的排除区域；同时约束主提取与残余点检查。
- **保留真实缺口**：不修改原图，不用插值、生成式补图或参考值填补被遮挡的曲线。
- **完整证据包**：CSV、原图、遮罩、覆盖图、CSV 重绘、并排对比、误差估计和 SHA-256 来源记录。
- **多种图形**：连续折线、线性/对数坐标、实心/空心散点、柱图、热图；校准和系列含义需要视觉复核。

## AI 填色提取：Nano Banana / GPT image 2.5

**先清理图例与干扰 → 单一目标填红 → 原图像素复核 → THU 提取 → 网格 CSV。**
新接入的 [paper-figure-csv-ai 技能](skills/paper-figure-csv-ai/SKILL.md) 包含可运行命令、版本化 prompt、原图与返回图双哈希、坐标复核和离线回放。AI 提供选区，最终测量仍来自原图；隐藏数据保持为空。

![真实 FLUX：图例遮罩、AI 填色、原图复核、网格与 CSV 重绘](docs/ai/a02/process.png)

2026-10-13 实际调用 APIYI：GPT 两个案例及一个旧 prompt 对照、Nano Banana 一个案例。以下是**完整流程的分数**，并同时展示相同目标的直接 THU 基线。每个 prompt 仅一次成功生成，不构成模型排名，也不证明填色必然提高准确率。

| 案例 | 模型与目标 | AI 辅助结果 | 直接 THU | 过程与数据 |
|---|---|---:|---:|---|
| a01 · 同色散点与拟合线（书稿） | GPT · 蓝色圆点填色 | **96.77% F1**，15/16 匹配 | 96.77% | [过程](docs/ai/a01/process.png) · [CSV](docs/ai/a01/data.csv) |
| a02 · 真实盐沼 NEE | GPT · 蓝线、色带与估算线分离 | **未评分**；759 列数值 | 792 列数值 | [过程](docs/ai/a02/process.png) · [网格 CSV](docs/ai/a02/grid.csv) |
| a03 · 真实泥炭草地累积 NEE | Nano Banana Pro · Stein 蓝线 | **97.51%**，391/401 命中 | 97.51% | [过程](docs/ai/a03/process.png) · [CSV](docs/ai/a03/data.csv) |

散点使用一对一 F1；a03 按独立 PDF 矢量路径、y 轴量程 1% 容差评分，漏点计错。a03 只测 Stein 单曲线，与上文/下文 f04 双曲线 95.39% 的范围不同。a02 没有独立作者数值，不用外观或颜色覆盖率冒充准确率。这些案例不计入原有 11 例宏平均。

### Prompt 的具体改进

旧写法“把目标改成红色，其余曲线和图例保持不变”会留下原有红色干扰。新 prompt 明确约束：**一个系列、原位几何、清除图例和无关曲线/色带/误差棒、保留校准标记、禁止补画缺失**。散点先在原图中验证形状，避免 AI 把拟合线片段截成假圆点。

![相同输入和模型的旧、新 prompt 对照](docs/ai/a02/prompt-ab.png)

在这次相同遮罩输入的 A/B 中，配准后红色像素中“原图目标色邻域不支持”的比例从 **34.81% → 18.87%**；这是清理诊断，**不是准确率**。最终有效列也从 788 降为 759，完整保留覆盖率代价。[新 prompt](docs/ai/a02/prompt.txt) · [旧 prompt](docs/ai/a02/legacy-prompt.txt) · [全部结果](benchmarks/ai/results.json)

<details><summary>展开 Nano Banana 真实论文过程与 GPT 散点填色过程</summary>

![Nano Banana：真实 FLUX 单曲线提取](docs/ai/a03/process.png)

![GPT：同色散点填色与原图形状复核](docs/ai/a01/process.png)

Nano Banana 返回图尺寸发生变化；四个实测边框锚点用于配准，未按图片尺寸比例盲目缩放。[坐标复核](docs/ai/a03/review.json) · [原始返回图](docs/ai/a03/generated.png) · [调用记录](docs/ai/a03/request.json)

</details>

### 网格化提取：曲线采样与热图单元

曲线按固定 x 网格取最近原图列，缺失位置留空，不插值跨越遮挡。热图按 **32 × 21 = 672** 个单元保留行列标签、色标和饱和区间；定量热图直接读取原色，不能先用生成模型改变色值。

![真实论文热图：原图、网格与逐单元提取](docs/ai/grid/process.png)

[672 单元 CSV](docs/ai/grid/grid.csv) · [49 位置曲线网格](docs/ai/a02/grid.csv) · [详细方法、调用与离线回放](references/ai-workflow.md)

```bash
python -m pip install -e '.[ai,dev,pdf]'
# 免费离线回放已保存的真实模型返回图；不调用 API。
python scripts/validate_ai.py --require-90
digitizer grid --config benchmarks/flux/f05/config.json --columns 49 --out runs/line-grid
digitizer grid --config benchmarks/cases/p01/config.json --out runs/heatmap-grid
# 新图的付费调用由 ai-edit 显式触发，详见方法文档。
```

## 来自 FLUX 真实论文的 8 个面板

本次新增来自 **2 篇论文的 8 个面板、12 条曲线**。这些是数字化示范，不计为新站点，不写入研究子项目的站点成果表。NEE、呼吸和光合分解量的语义分别记录。

盐沼四季实测 NEE：只提取蓝线，保留标准差带与估算曲线作为原图背景。下图为冬季；所有缺口在 CSV 重绘中保留。

![FLUX winter: original and CSV reconstruction](docs/cases/f05/comparison.png)

[Original](docs/cases/f05/original.png) · [Overlay](docs/cases/f05/overlay.png) · [Mask](docs/cases/f05/legend-overlay.png) · [CSV](docs/cases/f05/data.csv)

### 累积 NEE 双曲线

![Cumulative NEE: original and CSV reconstruction](docs/cases/f04/comparison.png)

**累积 NEE 双曲线：95.39%。** 评分在每条曲线固定 401 个位置，将像素提取结果与 PDF 独立矢量路径比较；误差 ≤ y 轴量程 1%，缺失计未命中。它衡量图形还原精度，不等于原始观测精度。三张密集日序列尚未达到 90%，完整保留在困难案例区。

| 案例 | 验证方式 | 分数 | 文件 |
|---|---|---:|---|
| f01 · 泥炭草地 · 日 NEE | PDF 矢量路径 | 52.24% · 困难案例 | [CSV](docs/cases/f01/data.csv) · [JSON](docs/cases/f01/metrics.json) |
| f02 · 泥炭草地 · 生态系统呼吸 | PDF 矢量路径 | 63.84% · 困难案例 | [CSV](docs/cases/f02/data.csv) · [JSON](docs/cases/f02/metrics.json) |
| f03 · 泥炭草地 · 总生态系统光合 | PDF 矢量路径 | 53.87% · 困难案例 | [CSV](docs/cases/f03/data.csv) · [JSON](docs/cases/f03/metrics.json) |
| f04 · 泥炭草地 · 累积碳交换 | PDF 矢量路径 | 95.39% | [CSV](docs/cases/f04/data.csv) · [JSON](docs/cases/f04/metrics.json) |
| f05 · 盐沼实测 NEE · 冬季 | 无独立参考 | 未评分 | [CSV](docs/cases/f05/data.csv) · [JSON](docs/cases/f05/metrics.json) |
| f06 · 盐沼实测 NEE · 春季 | 无独立参考 | 未评分 | [CSV](docs/cases/f06/data.csv) · [JSON](docs/cases/f06/metrics.json) |
| f07 · 盐沼实测 NEE · 夏季 | 无独立参考 | 未评分 | [CSV](docs/cases/f07/data.csv) · [JSON](docs/cases/f07/metrics.json) |
| f08 · 盐沼实测 NEE · 秋季 | 无独立参考 | 未评分 | [CSV](docs/cases/f08/data.csv) · [JSON](docs/cases/f08/metrics.json) |

四季盐沼图只有位图，作者原始数据需另行索取，因此不标注准确率。泥炭草地日序列含缺测填补，Reco/GEP 为分解估算量；它们不会被标成独立直接实测。

## 回归测试与独立验证

原有 **11 个回归任务宏平均 98.20%，11/11 ≥90%**：8 个合成图与 3 个书稿任务，人工复核校准。折线用 1% 量程命中率，散点用归一化坐标距离 1% 的一对一 F1。4 个简单示例已从主画廊撤下，仍保留为回归夹具。此分数不包含新增 FLUX 面板，不是对任意论文的保证。

独立 Nature Medicine 热图验证：578 个数值单元、94 个饱和区间；MAE 0.00329，原始严格分数 **84.60%**，考虑参考值两位小数舍入后的分数 **98.79%**。此案例单列报告。

[测试协议](references/benchmark.md) · [FLUX protocol](references/flux-validation.md) · [机器可读结果](benchmarks/results.json)

## 快速开始

```bash
git clone https://github.com/GISWLH/digitizer.git
cd digitizer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,pdf]'
digitizer extract --config benchmarks/flux/f05/config.json --out runs/demo
python scripts/validate_flux.py
python scripts/benchmark.py --ablation --require-90
python scripts/validate_paper.py
```

示例使用仓库自带图片，无需 API Key。Windows 激活命令为 `.venv\Scripts\activate`。

### 处理自己的图片

```bash
digitizer inspect figure.png --plot-bounds 80,30,950,650 --out figure.json
digitizer extract --config figure.json --out runs/my-figure
```

在两条命令之间，查看原图和候选遮罩，填写坐标锚点、目标系列和排除区域，记录 `review_note` 并设为 `reviewed: true`。可选本地 OCR：`pip install ".[ocr]"`，然后使用 `inspect --ocr`；OCR 只提出候选。

## 作为 Agent 技能

仓库根目录就是技能包。可克隆到 `~/.codex/skills/digitizer` 并安装依赖，或用技能安装器安装仓库根目录。

> 用 $digitizer 提取这张论文图。核验坐标轴、系列与图例遮罩，导出 CSV 和对比图。被遮挡的数据留空，区分实测量和估算量；没有独立参考就不报告准确率。

## 支持范围与边界

| 输入 / 图形 | 支持情况 |
|---|---|
| PNG / JPEG / PDF 面板 | PDF 先渲染，再复核校准 |
| 折线 / 散点 | 可见像素追踪；不能恢复完全重合或被遮挡的数据 |
| 柱图 / 热图 | THU 继承路线；柱图仅支持全局矩形排除，热图饱和端点保留区间 |
| 自动化程度 | 人工或 Agent 视觉复核；不是零复核自动提取 |

`extraction_error` 为像素与校准不确定度估计，不是实测准确率。真实复杂日序列仍存在明显误差，见公开困难案例。

## 参与项目

欢迎提交真实论文图和独立参考值，帮助完善密集交叉曲线与同色系列分离。

[Contributing](CONTRIBUTING.md) · [Roadmap](ROADMAP.md) · [Changelog](CHANGELOG.md) · [Submit a figure](https://github.com/GISWLH/digitizer/issues/new?template=figure.yml)

## 视觉资产

头图和 logo 使用 **Excalidraw 0.18.1** 手绘风格绘制，提供 SVG、PNG 和可编辑场景。头图中的数值为流程示意，不是实验结果。

[Banner source](docs/assets/banner.excalidraw) · [Logo source](docs/assets/icon.excalidraw) · [Design workflow](design/README.md)

## 来源、许可与引用

软件采用 MIT；核心数字化能力来自 THU Digitizer。图件许可独立：Mayen et al. (2024) 为 CC BY 4.0；Veenendaal et al. (2007) 图件及改编证据为 **CC BY-NC-SA 2.5**，不适用软件的 MIT 许可。请同时引用软件及实际使用的论文。

[Figure provenance](benchmarks/SOURCES.md) · [THU attribution](THIRD_PARTY_NOTICES.md) · [CITATION.cff](CITATION.cff)
