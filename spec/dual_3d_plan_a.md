# 方針 A: Ball-and-Stick 3D 双対グラフ (フラット)

## 概要

SPSS の各タイル中心を **球 (ノード)**、隣接タイル間を **円柱 (エッジ)** で接続した
ボール＆スティック型の 3D モデルを生成する。
すべてのノードは同一平面上に配置される。

方針 A' (`height_multiplier > 0`) の特殊ケース (`height_multiplier = 0`) として
統一実装されている。

## 幾何モデル

### 座標系

- XY 平面にタイルパターンを配置 (既存スケルトンと同様)。
- 原点 = 外枠中心。タイル座標 `(x, y, s)` → XY 中心 `((x+s/2)*scale - half_S, (y+s/2)*scale - half_S)`。
- ノード (球) の中心 Z = `node_radius` (球底面が Z = 0 に接する)。

### ノード

- 形状: **球 (Sphere)**。
- 半径: `node_radius` (mm)。デフォルト `1.0`。

### エッジ

- 形状: **円柱 (Cylinder)**。
- 隣接タイル中心間を直線で接続。
- 半径: `edge_radius` (mm)。デフォルト `0.5`。
- 円柱の軸 = 2 ノード中心を結ぶベクトル、長さ = ノード間距離。

### 底面

- 底面カットは行わない。
- ノードの Z 座標は `node_radius` 以上に保証されるため、球が Z < 0 にはみ出すことはない。

## パラメータ

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `scale` | `0.5` | mm/タイル単位。 |
| `node_radius` | `1.0` | ノード球の半径 (mm)。 |
| `edge_radius` | `0.5` | エッジ円柱の半径 (mm)。 |

## ビルド手順

1. 全ノード (21 個) の XY 座標を算出。Z = `node_radius`。
2. 隣接リスト (`build_adjacency`) からエッジペアを列挙。
3. `BuildPart` 内で:
   a. 各ノード位置に `Sphere(node_radius)` を ADD。
   b. 各エッジに対し、2 点間を結ぶ `Cylinder` を ADD。
      - 向き: 2 点間のベクトル方向に回転。

## CLI

```
uv run main_3d.py --dual -o dual.step --height-multiplier 0
uv run main_3d.py --dual -o dual.stl --height-multiplier 0 --node-radius 1.5 --edge-radius 0.6
```

`--dual --height-multiplier 0` で方針 A (フラット) となる。
