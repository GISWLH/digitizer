"""Build the public evidence gallery from actual extraction runs and metrics."""
from pathlib import Path
import json
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from digitizer_core.engine import save_json

TITLES={'s01':'清晰彩色折线','s02':'同色交叉线 × 内嵌图例','s03':'阶梯线 × 不可见遮挡','s04':'对数坐标曲线','s05':'稀疏实心散点','s06':'密集重叠散点','s07':'空心标记 × 网格','s08':'低清 JPEG × 压缩伪影','r01':'海洋热输送 × 图例与注释','r02':'多系列曲线 × 置信带','r03':'同色散点 × 拟合曲线','p01':'Nature Medicine · 672 格热图'}


def public_report(value):
    if isinstance(value,dict):return {k:public_report(v) for k,v in value.items()}
    if isinstance(value,list):return [public_report(v) for v in value]
    if isinstance(value,str) and value.startswith(str(ROOT)):return str(Path(value).relative_to(ROOT))
    return value


def main():
    summary=json.loads((ROOT/'runs/benchmark/summary.json').read_text())
    if summary['case_count']!=11:raise ValueError('Build the full 11-case benchmark before publishing.')
    manifest={c['id']:c for c in json.loads((ROOT/'benchmarks/manifest.json').read_text())}
    cases=[]
    for case in summary['cases']+[json.loads((ROOT/'runs/paper/p01/metrics.json').read_text())]:
        cid=case['id'];source=ROOT/('runs/paper/p01' if cid=='p01' else 'runs/benchmark/'+cid);dest=ROOT/'docs/cases'/cid;dest.mkdir(parents=True,exist_ok=True)
        for name in ['source.png','original.png','legend-overlay.png','exclusion-mask.png','overlay.png','recreated.png','comparison.png','data.csv','metrics.json']:
            shutil.copy2(source/name,dest/name)
        save_json(dest/'report.json',public_report(json.loads((source/'report.json').read_text())))
        if cid=='p01':shutil.copy2(source/'source-comparison.csv',dest/'source-comparison.csv')
        cases.append(dict(id=cid,title=TITLES[cid],kind='heatmap' if cid=='p01' else manifest[cid]['kind'],
            source_label='论文' if cid=='p01' else '合成图' if cid.startswith('s') else '书稿',metrics=case))
    order=['r01','s02','r03','s08','s06','p01','r02','s03','s07','s04','s05','s01']
    cases.sort(key=lambda c:order.index(c['id']))
    save_json(ROOT/'docs/cases.json',dict(macro_accuracy_pct=summary['macro_accuracy_pct'],cases=cases))
    save_json(ROOT/'benchmarks/results.json',summary)
    score=summary['macro_accuracy_pct'];minimum=min(c['accuracy_pct'] for c in summary['cases'])
    banner=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="520" viewBox="0 0 1280 520">
<rect width="1280" height="520" rx="28" fill="#142723"/><g fill="none" stroke="#315043" opacity=".5"><path d="M760 72v340h444M760 150h444M760 230h444M760 310h444M860 72v340M960 72v340M1060 72v340M1160 72v340"/></g>
<text x="64" y="65" font-family="Arial,sans-serif" font-size="22" font-weight="bold" fill="#d9f99d">digitizer</text>
<text x="64" y="105" font-family="Arial,sans-serif" font-size="12" letter-spacing="3" fill="#a5bcae">SCIENTIFIC FIGURES → REUSABLE DATA</text>
<text x="60" y="210" font-family="Arial,sans-serif" font-size="79" font-weight="bold" letter-spacing="-3" fill="#fff">FIGURES IN.</text>
<text x="60" y="302" font-family="Arial,sans-serif" font-size="79" font-weight="bold" letter-spacing="-3" fill="#d9f99d">DATA OUT.</text>
<text x="64" y="351" font-family="Arial,sans-serif" font-size="17" fill="#b7cbbd">Precise legend masks. Reproducible CSV. Visible evidence.</text>
<rect x="64" y="395" width="235" height="56" rx="8" fill="#d9f99d"/><text x="83" y="430" font-family="Arial,sans-serif" font-size="24" font-weight="bold" fill="#142723">{score:.2f}%</text><text x="178" y="429" font-family="Arial,sans-serif" font-size="12" fill="#142723">11-case macro</text>
<text x="324" y="416" font-family="Arial,sans-serif" font-size="13" fill="#c8d5cd">Built on THU Digitizer</text><text x="324" y="439" font-family="Arial,sans-serif" font-size="12" fill="#92aa9a">Enhanced by GISWLH · MIT</text>
<path d="M772 350C850 342 815 190 900 180S982 309 1043 270 1115 154 1190 109" stroke="#d9f99d" stroke-width="5" fill="none"/>
<g fill="#fff">{''.join(f'<circle cx="{x}" cy="{y}" r="6"/>' for x,y in [(772,350),(900,180),(1043,270),(1190,109)])}</g>
<rect x="789" y="84" width="171" height="65" rx="5" fill="#f54a8b" fill-opacity=".18" stroke="#f54a8b" stroke-dasharray="6 4"/><text x="804" y="111" font-family="Arial,sans-serif" font-size="11" fill="#fcb7d0">LEGEND EXCLUDED</text><path d="M805 131h42" stroke="#d9f99d" stroke-width="4"/><path d="M860 131h73" stroke="#b0c5b7" stroke-width="3"/>
<text x="803" y="463" font-family="Arial,sans-serif" font-size="10" letter-spacing="2" fill="#8ba692">MASK → TRACE → CSV → VERIFY</text>
<text x="64" y="490" font-family="Arial,sans-serif" font-size="10" fill="#80988a">Assisted regression: 8 synthetic + 3 manuscript tasks. Not an unseen-paper guarantee. Graphic at right is schematic.</text></svg>'''
    (ROOT/'docs/assets/banner.svg').write_text(banner)
    (ROOT/'docs/.nojekyll').touch()
    metrics={c['id']:c for c in summary['cases']}
    table='\n'.join(f"| [{c['id']} · {TITLES[c['id']]}](docs/cases/{c['id']}/comparison.png) | {'折线 ≤1% 量程' if manifest[c['id']]['kind']=='line' else '散点 F1 @1%'} | **{c['accuracy_pct']:.2f}%** | {c.get('coverage_pct',c.get('recall_pct')):.2f}% | [CSV](docs/cases/{c['id']}/data.csv) · [指标](docs/cases/{c['id']}/metrics.json) |" for c in summary['cases'])
    panels=[]
    for cid in ['r01','s02','r03','s08']:
        m=metrics[cid];panels.append(f"### {TITLES[cid]} · {m['accuracy_pct']:.2f}%\n\n| 原图 | 提取覆盖 | CSV 重绘 |\n|---|---|---|\n| ![原图](docs/cases/{cid}/original.png) | ![提取覆盖](docs/cases/{cid}/overlay.png) | ![重绘](docs/cases/{cid}/recreated.png) |\n\n[查看高清并排对比](docs/cases/{cid}/comparison.png) · [下载 CSV](docs/cases/{cid}/data.csv) · [图例遮罩](docs/cases/{cid}/legend-overlay.png)\n")
    readme=f'''<p align="center"><a href="https://giswlh.github.io/digitizer/"><img src="docs/assets/banner.svg" width="100%" alt="Digitizer: figures in, data out. {score:.2f}% macro score on 11 assisted regression cases."></a></p>

<p align="center"><a href="https://giswlh.github.io/digitizer/">交互案例画廊</a> · <a href="#快速开始">快速开始</a> · <a href="SKILL.md">Agent 技能</a> · <a href="references/benchmark.md">测试协议</a> · <a href="README.en.md">English</a></p>
<p align="center"><img alt="MIT software" src="https://img.shields.io/badge/license-MIT-d9f99d?labelColor=142723"> <img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-d9f99d?labelColor=142723"> <img alt="11 of 11 primary cases meet 90 percent" src="https://img.shields.io/badge/primary_cases-11%2F11_%E2%89%A590%25-d9f99d?labelColor=142723"> <a href="https://github.com/GISWLH/digitizer/actions"><img alt="CI" src="https://github.com/GISWLH/digitizer/actions/workflows/test.yml/badge.svg"></a></p>

# 图例退场，数据登场。

**Digitizer** 把科研论文中的可见图表数据数字化为 CSV。它以 [THU Digitizer](https://github.com/Rimagination/thu-digitizer) 为核心，增强复杂图例的精细排除、低清图处理和混合标记识别，并打包为可安装的 Agent 技能。

**原有 11 个案例全部 ≥90%，宏平均分 {score:.2f}%，最低 {minimum:.2f}%。** 这是人工复核校准后的开发回归结果：8 个合成图、3 个书稿面板任务；折线使用误差阈值命中率，散点使用 F1。不是对任意论文或全自动图例识别的保证。

## 为什么关注图例？

图例中的线段和圆点，往往与真实数据同色同形。删除整个角落会误删数据，完全忽略图例又会制造假点。

- **精细排除**：矩形、多边形、按系列生效的遮罩，在主提取和残余点检查中一致生效。
- **忠于可见证据**：保留原图；遮挡区留空；不通过生成式补图、插值或作者数据补齐曲线。
- **THU 核心增强**：连续路径追踪、线性/对数校准、填充散点；新增空心环与独立描边标记路线。
- **完整交付**：CSV、原图、遮罩、提取覆盖、重绘、并排对比和带 SHA-256 的 JSON 报告。

## 看得见的提取结果

粉色区域是被排除的图例/注释，蓝色标记是提取位置。所有重绘均来自本次提取值。点击图片可看大图。

{chr(10).join(panels)}

## 全量测试结果

| 案例 | 指标 | 分数 | 覆盖率 / 召回率 | 证据 |
|---|---|---:|---:|---|
{table}

折线：固定 401 个 x 采样位置，误差 ≤ y 轴量程 1%，漏点计为未命中。散点：归一化坐标距离阈值 1% 的一对一匹配 F1，同时惩罚漏点和误检。阈值、缺失与遮挡规则见[完整协议](references/benchmark.md)，[机器可读结果](benchmarks/results.json)保留每个分母及输入哈希。

### 真实论文：与作者数据独立比较

![Nature Medicine 热图原图与数字化重绘](docs/cases/p01/comparison.png)

Nature Medicine Fig. 4c：**672** 个可见单元，**578** 个数值颜色和 **94** 个饱和区间。对作者两位小数参考值，MAE 为 **0.00329**；考虑 ±0.005 参考舍入区间后的 1% 色标容差命中率 **98.79%**，未经舍入调整的严格分数为 **84.60%**。94 个饱和区间全部与参考相容。此案例单独报告，不进入 11 案例宏平均。

[论文及许可](benchmarks/SOURCES.md) · [独立评分](docs/cases/p01/metrics.json) · [CSV](docs/cases/p01/data.csv) · [逐单元对比](docs/cases/p01/source-comparison.csv)

## 快速开始

```bash
git clone https://github.com/GISWLH/digitizer.git
cd digitizer
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install -e '.[dev,pdf]'

# 立即运行包含图例的真实本地案例
digitizer extract --config benchmarks/cases/r01/config.json --out runs/demo

# 重现全部主测试（每个案例都必须 ≥90%）
python scripts/benchmark.py --ablation --require-90
python scripts/validate_paper.py
```

处理自己的图片：

```bash
digitizer inspect figure.png --plot-bounds 80,30,950,650 --out figure.json
# 由 Agent 查看原图和 overlay，填写坐标锚点、系列和图例遮罩并确认 reviewed。
digitizer extract --config figure.json --out runs/my-figure
```

可选本地 OCR：`python -m pip install '.[ocr]'`，然后使用 `inspect --ocr`。OCR 只提出候选，视觉复核决定遮罩。无需任何远程 API Key。

## 作为独立技能使用

仓库根目录就是技能包，包含 `SKILL.md`、`agents/openai.yaml`、可执行引擎和参考协议。将仓库安装到 Agent 的 skills 目录后，可直接请求：

> 用 $digitizer 提取这张论文图。先核验坐标轴、数据系列和图例遮罩；导出 CSV，展示原图、提取覆盖、重绘与并排对比。被遮挡的数据保持缺失。

Codex 示例：克隆到 `~/.codex/skills/digitizer`，在该目录创建虚拟环境并按上面的命令安装依赖。也可让 Agent 的 skill installer 安装此仓库根目录。

## 边界与来源

坐标轴、面板边界和系列语义需要视觉复核。全遮挡、完全重合、未知非线性投影等情况不能可靠恢复。CSV 的 `extraction_error` 是像素与校准误差估计，不是作者真值误差。热图饱和端点保留区间；未通过残余检查的散点保留未授权状态。

THU 已提供本项目依赖的主要数字化能力，原工作区也已有矩形图例排除。我们的增量与修改文件在 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 中列明。软件沿用 MIT 许可；论文图件与作者数据保留各自许可。感谢 [Rimagination / THU Digitizer](https://github.com/Rimagination/thu-digitizer)。
'''
    (ROOT/'README.md').write_text(readme,encoding='utf-8')
    english=f'''# Digitizer

![Digitizer banner](docs/assets/banner.svg)

[Interactive evidence gallery](https://giswlh.github.io/digitizer/) · [中文](README.md) · [Skill](SKILL.md) · [Evaluation protocol](references/benchmark.md)

Turn visible scientific figure geometry into auditable CSV. Built on **THU Digitizer**, with polygon and series-specific legend masks, JPEG chroma filtering, hollow markers and outlined-marker/curve separation.

**{score:.2f}% macro score; all 11 primary regression cases ≥90%.** This assisted development suite contains eight synthetic fixtures and three manuscript extraction tasks. Lines use a 1% y-axis-range hit rate including missing samples; scatter uses one-to-one F1 at 1% normalized distance. These are not unseen-paper or autonomous legend-detection claims.

![Original and reconstruction](docs/cases/r01/comparison.png)

```bash
git clone https://github.com/GISWLH/digitizer.git
cd digitizer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,pdf]'
digitizer extract --config benchmarks/cases/r01/config.json --out runs/demo
python scripts/benchmark.py --ablation --require-90
```

For your own image, run `digitizer inspect`, visually review the axes, series and mask overlay, then `digitizer extract`. The agent can perform this review. Nothing is inferred beneath opaque legends. Source images stay unchanged. Every run includes CSV, original, legend mask, overlay, recreation, comparison and a hashed report.

Install the repository root as the `$digitizer` agent skill. Read [SKILL.md](SKILL.md) and [configuration](references/configuration.md) for PDF rendering, optional local OCR and supported routes.

An additional real-paper heatmap is validated separately against its author workbook: 578 numeric cells, 94 censored endpoints, MAE 0.00329. The workbook rounds values to 0.01. Raw 1% colour-range accuracy is 84.60%; the explicitly rounding-aware score is 98.79%. It does not enter the primary headline average. [Source and license](benchmarks/SOURCES.md).

Core tracing, calibration, scatter, bars and heatmaps come from [Rimagination/THU Digitizer](https://github.com/Rimagination/thu-digitizer), MIT. [Attribution and exact extensions](THIRD_PARTY_NOTICES.md). Figure/data licenses are separate from the software license.
'''
    (ROOT/'README.en.md').write_text(english,encoding='utf-8')
    print(f'Built {len(cases)} evidence cards and READMEs; macro {score:.2f}%.')


if __name__=='__main__':main()
