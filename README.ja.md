<p align="center"><img src="docs/assets/icon.svg" width="64" alt="Digitizer logo"></p>

![Digitizer — Figures in. Evidence out.](docs/assets/banner.svg)

[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md)

[![CI](https://github.com/GISWLH/digitizer/actions/workflows/test.yml/badge.svg)](https://github.com/GISWLH/digitizer/actions) ![Python](https://img.shields.io/badge/Python-3.11%2B-315847) ![Software license](https://img.shields.io/badge/Software-MIT-cdeaac)

# 論文の曲線を、検証できるデータへ。

**Digitizer** は [THU Digitizer](https://github.com/Rimagination/thu-digitizer) を基盤に、科学論文の図を CSV に変換します。凡例の除外、遮蔽部分の欠損保持、検証資料の出力を強化し、CLI とインストール可能なエージェントスキルを提供します。

**[→ 対話型事例ギャラリー](https://giswlh.github.io/digitizer/)** · [Agent skill](SKILL.md) · [Configuration](references/configuration.md)

## 主な機能

- **精密な凡例マスク**：矩形、多角形、系列別の除外領域を、抽出処理と残存点の検査の両方に適用します。
- **見えている情報だけを抽出**：原図は変更せず、補間・生成画像・参照値で隠れた曲線を埋めません。
- **検証資料を一括出力**：CSV、原図、マスク、重ね合わせ図、CSV からの再描画、比較図、不確かさの推定値、SHA-256 による出典記録。
- **複数の図形式に対応**：折れ線、線形・対数軸、塗りつぶし・中空マーカーの散布図、棒グラフ、ヒートマップ。軸の校正と系列の意味は目視で確認します。

## AI 塗り分け抽出：Nano Banana / GPT image 2.5

**凡例と不要要素を除外 → 対象系列だけを赤色化 → 原画像の画素を確認 → THU で抽出 → グリッド CSV。**
統合した [paper-figure-csv-ai スキル](skills/paper-figure-csv-ai/SKILL.md) には実行コマンド、バージョン付きプロンプト、入力・出力のハッシュ、座標確認、オフライン再実行が含まれます。AI は選択領域を示し、最終測定は原画像から行います。隠れたデータは欠損のままです。

![実際の FLUX 図：凡例マスク、AI 着色、原画像確認、グリッド、CSV 再描画](docs/ai/a02/process.png)

2026-10-13 に APIYI で実行：GPT の 2 事例と旧プロンプトの対照 1 回、Nano Banana の 1 事例。下表は**処理全体のスコア**と、同じ対象を直接 THU で抽出した基準値です。各プロンプトの成功生成は 1 回のみで、モデル順位や塗り分けによる精度向上の証明ではありません。

| 事例 | モデルと対象 | AI 補助の結果 | 直接 THU | 過程とデータ |
|---|---|---:|---:|---|
| a01 · 同色の観測点と近似曲線（原稿） | GPT · 青い円の塗り分け | **F1 96.77%**、15/16 点一致 | 96.77% | [過程](docs/ai/a01/process.png) · [CSV](docs/ai/a01/data.csv) |
| a02 · 実論文の塩性湿地 NEE | GPT · 青線、帯、推定曲線を分離 | **未評価**、759 列に数値 | 792 列に数値 | [過程](docs/ai/a02/process.png) · [グリッド CSV](docs/ai/a02/grid.csv) |
| a03 · 実論文の泥炭草地累積 NEE | Nano Banana Pro · Stein の青線 | **97.51%**、391/401 一致 | 97.51% | [過程](docs/ai/a03/process.png) · [CSV](docs/ai/a03/data.csv) |

散布図は一対一対応の F1、a03 は独立 PDF パスに対する y 軸範囲 1% の許容誤差で評価し、欠損も不一致として数えます。a03 は Stein のみが対象で、f04 の 2 曲線の 95.39% とは評価範囲が異なります。a02 には独立した著者数値がなく、見た目や色の対応率を精度とは呼びません。これらは従来の 11 事例のマクロ平均に含めません。

### プロンプトの改善点

旧指示「対象を赤くし、他の曲線や凡例はそのまま残す」では既存の赤い妨害線が残ります。新指示では、**単一系列、幾何形状の固定、凡例・無関係な線・帯・誤差棒の削除、校正目印の保持、隠れたデータの補描禁止**を明示します。散布点は先に原画像で形状を確認し、近似曲線の断片が偽の点になることを防ぎます。

![同じ入力・モデルによる旧・新プロンプトの比較](docs/ai/a02/prompt-ab.png)

同一のマスク済み入力による今回の A/B では、位置合わせ後の赤画素のうち原画像の対象色近傍で支持されない割合が **34.81% → 18.87%** に低下しました。これは除去処理の診断値であり、**精度ではありません**。最終的な数値列も 788 から 759 に減少し、抽出範囲の減少を隠していません。[新プロンプト](docs/ai/a02/prompt.txt) · [旧プロンプト](docs/ai/a02/legacy-prompt.txt) · [全結果](benchmarks/ai/results.json)

<details><summary>Nano Banana の実論文抽出と GPT の観測点塗り分けを表示</summary>

![Nano Banana：実際の FLUX 図の単一曲線抽出](docs/ai/a03/process.png)

![GPT：観測点の塗り分けと原画像形状の確認](docs/ai/a01/process.png)

Nano Banana は出力サイズを変更しました。位置合わせには実測した 4 つの枠の目印を用い、画像サイズだけで自動拡大縮小していません。[座標確認](docs/ai/a03/review.json) · [生の出力](docs/ai/a03/generated.png) · [呼び出し記録](docs/ai/a03/request.json)

</details>

### グリッド抽出：曲線の標本点とヒートマップのセル

曲線は固定 x 位置に最も近い原画像の列を使い、欠損位置を空欄のまま保持します。遮蔽を越えて補間しません。ヒートマップは **32 × 21 = 672** セルの行列ラベル、色校正、飽和区間を保持します。定量ヒートマップの測定には原色を使用し、生成モデルで色値を変更しません。

![実論文ヒートマップ：原図、校正グリッド、セルごとの抽出](docs/ai/grid/process.png)

[672 セルの CSV](docs/ai/grid/grid.csv) · [49 位置の曲線グリッド](docs/ai/a02/grid.csv) · [手法・API 呼び出し・オフライン再実行](references/ai-workflow.md)

```bash
python -m pip install -e '.[ai,dev,pdf]'
# 保存済みの実出力を無料で再実行。API は呼び出しません。
python scripts/validate_ai.py --require-90
digitizer grid --config benchmarks/flux/f05/config.json --columns 49 --out runs/line-grid
digitizer grid --config benchmarks/cases/p01/config.json --out runs/heatmap-grid
# 新しい画像の有料呼び出しは ai-edit で明示的に開始。詳細は手法文書を参照。
```

## 実際の FLUX 論文から 8 パネルを追加

今回、**2 編の論文から 8 パネル・12 本の曲線**を追加しました。デジタイズの実例であり、新規観測地点として登録するものではありません。研究サブプロジェクトの地点別成果表には追加しません。NEE、呼吸、分離推定された光合成量の意味を区別して記録します。

塩性湿地の四季の実測 NEE：青線のみを抽出し、標準偏差の帯と推定曲線は原図の情報として残します。以下は冬季の例です。CSV からの再描画でも欠損を保持します。

![FLUX winter: original and CSV reconstruction](docs/cases/f05/comparison.png)

[Original](docs/cases/f05/original.png) · [Overlay](docs/cases/f05/overlay.png) · [Mask](docs/cases/f05/legend-overlay.png) · [CSV](docs/cases/f05/data.csv)

### 累積 NEE の 2 曲線

![Cumulative NEE: original and CSV reconstruction](docs/cases/f04/comparison.png)

**累積 NEE の 2 曲線：95.39%。** 各曲線の固定 401 点で、画像からの抽出結果を独立した PDF ベクトルパスと比較します。許容誤差は y 軸範囲の 1% とし、欠損は不一致に数えます。これは描かれた図形の再現精度であり、元の観測値の精度ではありません。密な日別系列の 3 パネルは 90% 未満であり、難易度の高い事例として公開しています。

| 事例 | 検証方法 | スコア | ファイル |
|---|---|---:|---|
| f01 · 泥炭草地の日別 NEE | PDF のベクトルパス | 52.24% · 難易度の高い事例 | [CSV](docs/cases/f01/data.csv) · [JSON](docs/cases/f01/metrics.json) |
| f02 · 泥炭草地の生態系呼吸 | PDF のベクトルパス | 63.84% · 難易度の高い事例 | [CSV](docs/cases/f02/data.csv) · [JSON](docs/cases/f02/metrics.json) |
| f03 · 泥炭草地の総生態系光合成 | PDF のベクトルパス | 53.87% · 難易度の高い事例 | [CSV](docs/cases/f03/data.csv) · [JSON](docs/cases/f03/metrics.json) |
| f04 · 泥炭草地の累積炭素交換 | PDF のベクトルパス | 95.39% | [CSV](docs/cases/f04/data.csv) · [JSON](docs/cases/f04/metrics.json) |
| f05 · 塩性湿地の実測 NEE · 冬季 | 独立した参照値なし | 未評価 | [CSV](docs/cases/f05/data.csv) · [JSON](docs/cases/f05/metrics.json) |
| f06 · 塩性湿地の実測 NEE · 春季 | 独立した参照値なし | 未評価 | [CSV](docs/cases/f06/data.csv) · [JSON](docs/cases/f06/metrics.json) |
| f07 · 塩性湿地の実測 NEE · 夏季 | 独立した参照値なし | 未評価 | [CSV](docs/cases/f07/data.csv) · [JSON](docs/cases/f07/metrics.json) |
| f08 · 塩性湿地の実測 NEE · 秋季 | 独立した参照値なし | 未評価 | [CSV](docs/cases/f08/data.csv) · [JSON](docs/cases/f08/metrics.json) |

塩性湿地の四季の図はラスター画像です。著者の元データは依頼による提供のため、精度は報告していません。泥炭草地の日別系列には欠測補完が含まれ、Reco/GEP は分離推定量です。独立して直接測定された観測量とは区別します。

## 回帰テストと独立検証

従来の **11 タスクのマクロ平均は 98.20%、11/11 が 90% 以上**です。内訳は合成図 8 件と書籍原稿の 3 タスクで、校正は目視確認済みです。折れ線は軸範囲 1% の一致率、散布図は正規化座標距離 1% の一対一対応による F1 を使用します。単純な 4 例は主ギャラリーから外し、回帰テスト用に保持しました。このスコアに新しい FLUX パネルは含まれず、任意の論文に対する保証でもありません。

Nature Medicine のヒートマップは別途検証しています。数値セル 578 個、飽和区間 94 個、MAE 0.00329。厳密な元スコアは **84.60%**、参照値の小数第 2 位への丸めを考慮すると **98.79%** です。この事例は個別に報告します。

[評価プロトコル](references/benchmark.md) · [FLUX protocol](references/flux-validation.md) · [機械可読の結果](benchmarks/results.json)

## クイックスタート

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

同梱画像を使うため API キーは不要です。Windows での有効化は `.venv\Scripts\activate` です。

### 自分の図を処理する

```bash
digitizer inspect figure.png --plot-bounds 80,30,950,650 --out figure.json
digitizer extract --config figure.json --out runs/my-figure
```

2 つのコマンドの間に、原図とマスク候補を確認し、軸の基準点・対象系列・除外領域を設定します。`review_note` に確認内容を記録し、`reviewed: true` にします。任意のローカル OCR は `pip install ".[ocr]"` 後に `inspect --ocr` で使用できます。OCR は候補の提示のみを行います。

## エージェントスキルとして使う

リポジトリのルートがスキルパッケージです。`~/.codex/skills/digitizer` にクローンして依存関係をインストールするか、スキルインストーラーでリポジトリのルートを指定します。

> $digitizer でこの論文図を抽出してください。軸、系列、凡例マスクを確認し、CSV と比較図を出力してください。遮蔽部分は欠損のままにし、実測量と推定量を区別してください。独立した参照値がなければ精度を報告しないでください。

## 対応範囲と制約

| 入力・図形式 | 対応状況 |
|---|---|
| PNG / JPEG / PDF のパネル | PDF は画像化した後に校正を確認 |
| 折れ線・散布図 | 可視画素を追跡。完全に重なった点や隠れたデータは復元不可 |
| 棒グラフ・ヒートマップ | THU の処理を継承。棒グラフの除外は全系列共通の矩形のみ、飽和した色端点は区間として保持 |
| 自動化の範囲 | 人またはエージェントによる目視確認が必要 |

`extraction_error` は画素・校正に由来する不確かさの推定であり、測定された精度ではありません。複雑な日別系列には依然として大きな誤差があり、公開事例に記録しています。

## プロジェクトへの参加

密な交差や同色系列の分離を改善するため、実際の論文図と独立した参照値の提供を歓迎します。

[Contributing](CONTRIBUTING.md) · [Roadmap](ROADMAP.md) · [Changelog](CHANGELOG.md) · [Submit a figure](https://github.com/GISWLH/digitizer/issues/new?template=figure.yml)

## ビジュアル素材

ヘッダー画像とロゴは **Excalidraw 0.18.1** の手描きスタイルで作成し、SVG、PNG、編集可能なシーンを提供しています。ヘッダー画像の数値は説明用で、実験結果ではありません。

[Banner source](docs/assets/banner.excalidraw) · [Logo source](docs/assets/icon.excalidraw) · [Design workflow](design/README.md)

## 出典・ライセンス・引用

ソフトウェアは MIT ライセンスで、主要なデジタイズ機能は THU Digitizer に由来します。図のライセンスは別です。Mayen et al. (2024) は CC BY 4.0、Veenendaal et al. (2007) の図とその改変資料は **CC BY-NC-SA 2.5** で、ソフトウェアの MIT は適用されません。利用時はソフトウェアと該当論文の両方を引用してください。

[Figure provenance](benchmarks/SOURCES.md) · [THU attribution](THIRD_PARTY_NOTICES.md) · [CITATION.cff](CITATION.cff)
