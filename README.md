# spss_draw

**単純完全正方形分割 (Simple Perfect Squared Square) の 2D 可視化 & 3D CAD モデル生成ツール**

---

## 概要

Duijvestijn (1978) が発見した最小の単純完全正方形分割 (SPSS) を描画・立体化する。

**単純完全正方形分割 (SPSS)** とは、1 つの正方形をすべて異なる辺長を持つ小正方形のみで隙間なく充填したもの。  
Duijvestijn の解は現在知られている唯一の最小 SPSS であり、辺長 112 の正方形を 21 個の小正方形で分割する (次数 21)。

本ツールでは以下の 2 つの出力モードを提供する。

| モード | エントリポイント | 出力形式 |
|---|---|---|
| **2D 描画** | `main.py` | PNG / SVG / PDF 等 (matplotlib) |
| **3D CAD モデル** | `main_3d.py` | STEP / STL (build123d) |

---

## プロジェクト構成

```
spss_draw/           ← ライブラリ本体
  __init__.py            公開 API
  data.py                Duijvestijn SPSS の定数 (Bouwkamp code)
  bouwkamp.py            Bouwkamp code → タイル座標 + バリデーション
  coloring.py            隣接グラフ構築 + 四色彩色
  transforms.py          回転・反転
  draw_2d.py             matplotlib 2D 描画
  draw_3d.py             build123d 3D スケルトンモデル生成
  cli.py                 CLI パーサ (main_2d / main_3d)
main.py              ← 2D エントリポイント
main_3d.py           ← 3D エントリポイント
```

---

## セットアップ

```
uv sync
```

build123d (3D モデル生成) は `uv sync` で一括インストールされる。  
2D 描画のみを使う場合も同様。

---

## 2D 描画

### 書式

```
uv run main.py [オプション]
```

引数を与えない場合はウィンドウに描画結果を表示する。  
`-o` を指定するとファイルへ保存する (拡張子で形式を自動判定)。

内部の小正方形の彩色には四色定理に基づくバックトラッキング法を用いており、隣接するタイルが常に異なる色となるよう自動配色される。

### オプション

| オプション | デフォルト | 説明 |
|---|---|---|
| `-o FILE`, `--output FILE` | なし | 描画結果を `FILE` に保存する。省略時はウィンドウに表示する。 |
| `--dpi DPI` | `150` | ファイル保存時の解像度 (dots per inch)。 |
| `--edge-color COLOR` | `white` | タイル間の境界線の色。 |
| `--edge-width WIDTH` | `1.5` | タイル間の境界線の太さ (ポイント)。 |
| `--outer-edge-color COLOR` | `black` | 外枠の色。 |
| `--outer-edge-width WIDTH` | `2.5` | 外枠の太さ (ポイント)。 |
| `--palette C1 C2 C3 C4` | 組み込みパレット | タイルの塗り色を 4 色指定する。色名 (`red`)、`#` なし hex (`4E79A7`)、`#` 付き hex (`#4E79A7`) のいずれも可。 |
| `--rotate {0,90,180,270}` | `0` | 時計回りの回転角度。 |
| `--flip-h` | 無効 | 左右反転。 |
| `--flip-v` | 無効 | 上下反転。 |

### 使用例

```bash
# 画面に表示
uv run main.py

# PNG 保存
uv run main.py -o spss.png

# 高解像度 SVG
uv run main.py -o spss.svg --dpi 300

# 配色変更 + 境界線カスタマイズ
uv run main.py -o spss.png --palette 4E79A7 F28E2B 59A14F E15759 \
  --edge-color black --edge-width 2

# Matrix 風テーマ
uv run main.py -o matrix.svg \
  --palette 001400 001400 001400 001400 \
  --edge-color 00FF41 --edge-width 1.5 \
  --outer-edge-color 00FF41 --outer-edge-width 3.5 --flip-v

# 回転 + 反転
uv run main.py -o rotated.png --rotate 270 --flip-h
```

---

## 3D CAD モデル生成

### 概要

SPSS のタイル境界 (内辺) のみを壁として残し、各タイル内部をくり抜いた **スケルトン (骨格) フレーム** を生成する。  
アクセサリやフィギュア、3D プリント用途を想定した設計。

**生成アルゴリズム:**

1. 各タイルに `(辺長 × scale + wall_thickness)` の立体ブロックを加算 → 隣接タイル同士で `wall_thickness / 2` ずつ重なり壁を形成
2. 各タイル内部 `(辺長 × scale − wall_thickness)` をくり抜き
3. 共有壁は隣接タイルのうち背の高い方の高さが自動的に採用される (boolean union)

### 書式

```
uv run main_3d.py [オプション]
```

### オプション

| オプション | デフォルト | 説明 |
|---|---|---|
| `-o FILE`, `--output FILE` | `spss_skeleton.step` | 出力パス。`.step` / `.stp` で STEP 形式、`.stl` で STL 形式。 |
| `--scale SCALE` | `0.5` | mm/タイル単位。`0.5` → 全体 56 mm。`1.0` → 112 mm。 |
| `--wall-thickness WT` | `1.0` | 壁の厚み (mm)。 |
| `--height HEIGHT` | `1.0` | 壁の押し出し高さ (mm)。`--height-multiplier` 使用時は最小高さとなる。 |
| `--height-multiplier MULT` | `0.0` | 可変高さ係数。各タイルの壁高さ = `height + side × scale × MULT`。`0` で均一高さ。 |
| `--base-thickness BT` | `0.0` | 底板の厚み (mm)。`0` で底板なし (貫通スケルトン)。 |
| `--rotate {0,90,180,270}` | `0` | 時計回りの回転角度。 |
| `--flip-h` | 無効 | 左右反転。 |
| `--flip-v` | 無効 | 上下反転。 |

### 可変高さ (`--height-multiplier`)

壁の高さを各タイルの辺長に比例させることで、大きなタイルほど壁が高くなる地形的な立体表現が得られる。

$$h_{tile} = \texttt{height} + s \times \texttt{scale} \times \texttt{height\text{-}multiplier}$$

| 値 | 効果 |
|---|---|
| `0.0` | 全タイル均一高さ |
| `0.05` | 控えめなレリーフ |
| `0.3` | 明確な高低差 |
| `1.0` | 極端な地形表現 |

### 使用例

```bash
# 均一高さのスケルトン (STEP) — デフォルト設定そのまま
uv run main_3d.py -o skeleton.step

# 底板付き (3D プリント向け STL)
uv run main_3d.py -o skeleton.stl --wall-thickness 1.2 --height 4.0 \
  --base-thickness 0.8

# 可変高さ — 中程度の高低差
uv run main_3d.py -o terrain.step --wall-thickness 1.0 --height 1.0 \
  --height-multiplier 0.3

# 可変高さ — 極端な地形
uv run main_3d.py -o extreme.step --wall-thickness 1.0 --height 0.5 \
  --height-multiplier 1.0

# 大きめサイズ (112 mm)
uv run main_3d.py -o large.step --scale 1.0 --wall-thickness 1.5 --height 3.0

# 反転 + 回転
uv run main_3d.py -o rotated.step --flip-v --rotate 90
```

### 出力ファイルについて

- **STEP** — Fusion 360 / FreeCAD / SolidWorks 等の CAD で直接開ける。後加工・フィレット追加などに最適。
- **STL** — スライサー (Bambu Studio / PrusaSlicer 等) に直接投入して 3D プリント可能。

生成モデルは **Z 軸 = 押し出し方向** (XY 平面にタイルパターン)。スライサーでそのまま読み込めば積層方向が正しい向きとなる。  
STEP / STL には積層方向のメタ情報は含まれない (スライサー側で配置を決定する)。

---

## 色指定について

2D 描画の `--palette` / `--edge-color` / `--outer-edge-color` には以下の形式が使える:

- 色名: `red`, `steelblue`, `forestgreen`
- `#` なし hex: `4E79A7`
- `#` 付き hex: `#4E79A7`

---

## ライブラリとしての利用

`spss_draw` パッケージは単体でも `import` して利用できる。

```python
from spss_draw import (
    DUIJVESTIJN_BOUWKAMP,
    DUIJVESTIJN_SIZE,
    bouwkamp_to_tiles,
    four_color,
    transform_tiles,
    validate,
)

tiles = bouwkamp_to_tiles(DUIJVESTIJN_SIZE, DUIJVESTIJN_BOUWKAMP)
validate(DUIJVESTIJN_SIZE, tiles)
colors = four_color(tiles)
```

---

## 参考文献

- A. J. W. Duijvestijn, "Simple perfect squared square of lowest order", *Journal of Combinatorial Theory, Series B*, Vol. 25, Issue 2, 1978, pp. 240–243.

---

## 設定定数

コマンドライン引数では変更できない設定はソースコード内の定数で管理されている。

| 定数 | 説明 |
|---|---|
| `PALETTE` | タイルに使用する 4 色のリスト (matplotlib 色文字列)。 |
| `COLOR_INDICES` | タイルごとの色インデックス。空リストのとき自動配色される。 |

---

## 依存関係

| パッケージ | 用途 |
|---|---|
| `matplotlib >= 3.10` | 描画・ファイル出力 |
| `numpy` | 検証処理 (重複・隙間チェック用グリッド演算) |

---

## 参考文献

- A. J. W. Duijvestijn, "Simple perfect squared square of lowest order", *Journal of Combinatorial Theory, Series B*, 25(2), 240–243, 1978.
