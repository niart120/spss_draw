# Infill 3D Mode — 浮き彫り (Relief) / 掘り込み (Engraved)

## 概要

スケルトンモデル（壁のみ）の代わりに、タイル内部を実体として残す
インフィルモードを追加する。ベースプレートの **上下両面** に対称的に
パターンを形成する。高さ・深さはタイルサイズによらず **一定** 。

SPSSパターンは溝 (groove) / リッジの位置と囲まれる面積で認識される。

```
   Top relief/carve
   ─────────────────
  ┌─┐ ┌───┐ ┌─────┐     ← groove_width で区切り
  │ │ │   │ │     │     ← 一定高さ (relief) / 一定深さ (engraved)
══╧═╧═╧═══╧═╧═════╧══   ← base plate 上面
║                     ║   ← base_thickness
══╤═╤═╤═══╤═╤═════╤══   ← base plate 下面
  │ │ │   │ │     │     ← 下面も同じパターン（鏡像）
  └─┘ └───┘ └─────┘
   Bottom (mirrored)
```

## 1. 浮き彫り (Relief)

ベースプレートの上下両面から各タイルを **同一高さのソリッドブロック**
として突起させる。

### 構築手順

1. ベースプレート生成: 全体サイズ × `base_thickness`、Z中心 = 0
   - Z範囲: `[-base_thickness/2, +base_thickness/2]`
2. 各タイルのブロックサイズ算出:
   - 内部辺のマージン: `groove_width / 2`
   - **外周辺のマージン: `groove_width`** （外壁を内部リッジと同じ幅に統一）
   - ブロックは非正方形になりうる（辺ごとにマージンが異なるため）
3. 各ブロックを上下面から `relief_depth` 突起
4. `fillet_radius > 0` の場合、各ブロックを個別に fillet してから
   Compound で合成（OCCT の boolean fillet 不安定性を回避）

### パラメータ

| パラメータ       | デフォルト | 説明                        |
|------------------|:----------:|-----------------------------|
| `base_thickness` |    0.6     | ベースプレート厚 (mm)       |
| `relief_depth`   |    0.3     | 片面あたりの突起高さ (mm)   |
| `groove_width`   |    0.3     | タイル間の溝幅 (mm)         |
| `fillet_radius`  |    0.0     | ブロック角の丸め半径 (mm)。0で無効 |
| `scale`          |    0.5     | mm/tile-unit                |

## 2. 掘り込み (Engraved)

ベースプレートの上下両面から各タイル内部を **一定深さ** で彫り込む。
タイル境界のリッジが残ることでパターンが浮かび上がる。

### 構築手順

1. ソリッドスラブ生成: 全体サイズ × `base_thickness`
   - `fillet_radius > 0` の場合、`RectangleRounded` + `extrude` で
     スラブ4隅を角丸化（半径 = `groove_width / 2`）
2. 各タイルのカーブ領域算出:
   - 内部辺のマージン: `groove_width / 2`
   - **外周辺のマージン: `groove_width`** （外壁を内部リッジと同じ幅に統一）
   - カーブ領域は非正方形になりうる
3. 上面・下面から `carve_depth` だけ減算
4. `fillet_radius > 0` の場合、リッジ頂上に
   半径 `groove_width / 2` の水平シリンダー＋球を配置して角を丸める
   - 内部セグメント＋外周セグメントの全リッジに配置
   - 境界座標は `groove_width / 2` だけ内側にオフセット

### 貫通防止制約

$$\texttt{carve\_depth} \le 0.45 \times \texttt{base\_thickness}$$

片面最大 45%、両面合計最大 90% → 中央に最低 **10%** の肉が残る。
CLIで指定値が超過した場合は **自動クランプ + warning** を表示する。

### パラメータ

| パラメータ       | デフォルト | 説明                                            |
|------------------|:----------:|-------------------------------------------------|
| `base_thickness` |    1.5     | ベースプレート厚 (mm)                           |
| `carve_depth`    |    0.5     | 片面あたりの彫り込み深さ (mm)。45%制約でクランプ |
| `groove_width`   |    0.5     | リッジ幅 (mm)                                   |
| `fillet_radius`  |    0.0     | リッジ頂上の丸め半径 (mm)。0で無効               |
| `scale`          |    0.5     | mm/tile-unit                                    |

## CLI インターフェース

```bash
# 浮き彫り（デフォルト値で実行）
uv run main_3d.py --infill relief -o spss_relief.stl

# 浮き彫り（フィレット付き）
uv run main_3d.py --infill relief -o spss_relief.stl --fillet-radius 0.2

# 掘り込み（フィレット付き）
uv run main_3d.py --infill engraved -o spss_engraved.stl --fillet-radius 0.2

# パラメータ全指定
uv run main_3d.py --infill engraved -o spss_engraved.stl \
    --base-thickness 1.5 --carve-depth 0.5 --groove-width 0.5 \
    --fillet-radius 0.2
```

`--infill {relief,engraved}` は `--round` / `--dual` と **排他的** 。

`--groove-width` 未指定時のデフォルトはモード別:
- relief: **0.3 mm**
- engraved: **0.5 mm**

## フィレット実装詳細

### Relief モード

各タイルブロックを個別に `Box` → `fillet(top 4 edges)` → `Compound` で
組み立てる。BuildPart による全体 fillet は OCCT が不安定なため回避。

### Engraved モード

BuildPart の `fillet()` は複雑なブーリアン結果に使えないため、
**加算的アプローチ** を採用:

1. シャープなカーブ（fillet なし）を BuildPart で完成
2. リッジ頂上に水平シリンダー + 接合点に球を Compound で追加
3. シリンダー/球の半径は常に `groove_width / 2`（溝幅の半分）
4. 外周の座標は `groove_width / 2` だけ内側へオフセット

### 外壁の角丸

`fillet_radius > 0` 時、engraved のスラブは `RectangleRounded` +
`extrude` で生成され、4隅が `groove_width / 2` の角丸になる。

## 既存パラメータとの関係

| パラメータ               | Infill モードでの動作                  |
|--------------------------|----------------------------------------|
| `--scale`                | そのまま使用                           |
| `--base-thickness`       | ベースプレート厚 (モード別デフォルト)  |
| `--height`               | 無視                                   |
| `--height-multiplier`    | 無視                                   |
| `--wall-thickness`       | 無視 (`groove-width` で代替)           |
| `--outer-wall-thickness` | 無視                                   |
| `--rotate / --flip-*`    | そのまま使用                           |

## 実装

- `draw_3d.py` に `build_infill_relief()` / `build_infill_engraved()` 追加
- `cli.py` の `main_3d()` に `--infill` 分岐追加、排他チェック
