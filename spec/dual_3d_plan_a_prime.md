# 方針 A': Cube-based Ball-and-Stick 3D 双対グラフ

## 概要

方針 A の拡張。各タイルを **辺長に比例した高さを持つ立方体 (キューブ)** と見なし、
そのキューブの **重心 (3D 中心)** にノードを配置する。
大きなタイルほどノードが高い位置に来るため、立体的な配置となる。

## 幾何モデル

### 座標系

- XY 平面にタイルパターンを配置。原点 = 外枠中心。
- Z 軸方向にタイル辺長に比例した高さを持つ。

### 概念キューブ

各タイル `(x, y, s)` に対し、概念上のキューブを定義する:

- XY 範囲: `(x*scale, y*scale)` → `((x+s)*scale, (y+s)*scale)`  (原点補正あり)
- Z 範囲: `0` → `s * scale * height_multiplier`

このキューブ自体はモデルに出力されない (ノード位置の決定にのみ使用)。

### ノード

- 形状: **球 (Sphere)**。
- 位置: キューブの重心。ただし Z は `node_radius` 以上にクランプされる。
  `cz = max(node_radius, s * scale * height_multiplier / 2)`
- 半径: `node_radius` (mm)。デフォルト `1.0`。

### エッジ

- 形状: **円柱 (Cylinder)**。
- 隣接ノードの 3D 位置間を直線で接続。
- 半径: `edge_radius` (mm)。デフォルト `0.5`。

### height_multiplier

ノードの Z 座標を制御する係数:

$$z_{\text{node}} = \max\!\left(\texttt{node\_radius},\; \frac{s \times \texttt{scale} \times \texttt{height\_multiplier}}{2}\right)$$

| 値 | 効果 |
|---|---|
| `1.0` | 各タイルが正立方体であるかのように扱う (辺長 = 高さ) |
| `0.5` | 高さは辺長の半分 → 控えめな高低差 |
| `0.0` | すべて Z = `node_radius` → 方針 A と同等 (フラット) |
| `2.0` | 高さを強調 → 極端な地形表現 |

### 底面

- 底面カットは行わない。
- ノードの Z 座標は `node_radius` 以上にクランプされるため、球が Z < 0 にはみ出すことはない。

## パラメータ

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `scale` | `0.5` | mm/タイル単位。 |
| `node_radius` | `1.0` | ノード球の半径 (mm)。 |
| `edge_radius` | `0.5` | エッジ円柱の半径 (mm)。 |
| `height_multiplier` | `1.0` | キューブ高さ係数。`0` でフラット (方針 A 相当)。 |

## STL テッセレーション

STL 出力時のメッシュ粒度はデフォルトで 3D プリント向けに調整済み:

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `tolerance` | `0.01` | 線形偏差 (mm)。小さいほど高精度。 |
| `angular_tolerance` | `5.0` | 角度偏差 (度)。小さいほど高精度。 |

## ビルド手順

1. 全ノードの 3D 座標を算出:
   - `cx = (x + s/2) * scale - half_S`
   - `cy = (y + s/2) * scale - half_S`
   - `cz = max(node_radius, s * scale * height_multiplier / 2)`
2. 隣接リスト (`build_adjacency`) からエッジペアを列挙。
3. `BuildPart` 内で:
   a. 各ノード位置に `Sphere(node_radius)` を ADD。
   b. 各エッジに対し、2 つの 3D 点間を結ぶ `Cylinder` を ADD。
      - 向き: 2 点間ベクトルの方向に回転。

## CLI

```
# フラット (方針 A 相当)
uv run main_3d.py --dual -o dual_flat.step --height-multiplier 0

# 正立方体ベース (デフォルト height-multiplier=1)
uv run main_3d.py --dual -o dual_cube.step --height-multiplier 1.0

# 高低差を強調
uv run main_3d.py --dual -o dual_terrain.step --height-multiplier 2.0

# ノード・エッジサイズ調整
uv run main_3d.py --dual -o dual.stl --node-radius 1.5 --edge-radius 0.6

# STL 精度の調整
uv run main_3d.py --dual -o dual.stl --stl-tolerance 0.005 --stl-angular-tolerance 3
```

## 方針 A との関係

- `height_multiplier = 0` → 方針 A と完全に一致 (全ノード同一平面)。
- したがって A' の実装 1 本で方針 A もカバーできる。
