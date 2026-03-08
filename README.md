# spss_draw

## 名前

`spss_draw` — 単純完全正方形分割 (Simple Perfect Squared Square) の可視化ツール

---

## 書式

```
uv run main.py [オプション]
```

---

## 説明

Duijvestijn (1978) が発見した最小の単純完全正方形分割 (SPSS) を描画する。

**単純完全正方形分割 (SPSS)** とは、1つの正方形をすべて異なる辺長を持つ小正方形のみで隙間なく充填したもの。  
Duijvestijn の解は現在知られている唯一の最小 SPSS であり、辺長 112 の正方形を 21 個の小正方形で分割する (次数 21)。

内部の小正方形の彩色には四色定理に基づくバックトラッキング法を用いており、隣接するタイルが常に異なる色となるよう自動配色される。

引数を与えない場合は画面上にウィンドウを開いて描画結果を表示する。  
`--output` を指定するとウィンドウ表示の代わりに画像ファイルへ保存する。

---

## オプション

| オプション | デフォルト値 | 説明 |
|---|---|---|
| `-o FILE`, `--output FILE` | なし | 描画結果を `FILE` に保存する。省略時はウィンドウに表示する。出力形式はファイル拡張子で自動判定される (`.png`, `.svg`, `.pdf` 等)。 |
| `--dpi DPI` | `150` | ファイル保存時の解像度 (dots per inch)。`--output` 未指定時は無効。 |
| `--edge-color COLOR` | `white` | タイル間の境界線の色。matplotlib が解釈できる色文字列 (色名・16進数など) を指定する。 |
| `--edge-width WIDTH` | `1.5` | タイル間の境界線の太さ (ポイント)。 |
| `--outer-edge-color COLOR` | `black` | 外枠の色。 |
| `--outer-edge-width WIDTH` | `2.5` | 外枠の太さ (ポイント)。 |
| `--palette C1 C2 C3 C4` | 組み込みパレット | タイルの塗り色を 4 色指定する。各色は色名 (`red`)、`#` なし 16 進数 (`4E79A7`)、`#` 付き 16 進数 (`#4E79A7`) のいずれでも指定できる。|
| `--rotate {0,90,180,270}` | `0` | 画像を時計回りに回転する角度。|
| `--flip-h` | 無効 | 左右反転する。|
| `--flip-v` | 無効 | 上下反転する。|
| `-h`, `--help` | — | ヘルプメッセージを表示して終了する。 |

---

## 使用例

画面に表示する (引数なし):
```
uv run main.py
```

PNG ファイルとして保存する:
```
uv run main.py -o spss_o21_s112.png
```

高解像度で保存する:
```
uv run main.py -o spss_o21_s112.png --dpi 300
```

SVG ベクター形式で保存する:
```
uv run main.py -o spss_o21_s112.svg
```

境界線を黒・太めに変更して保存する:
```
uv run main.py -o spss_o21_s112.png --edge-color black --edge-width 2 --outer-edge-width 4
```

配色を 16 進数 (`#` なし) で指定して保存する:
```
uv run main.py -o spss_o21_s112.png --palette 4E79A7 F28E2B 59A14F E15759
```

配色を色名で指定する:
```
uv run main.py --palette steelblue darkorange forestgreen crimson
```

90度時計回りに回転して保存する:
```
uv run main.py -o spss_o21_s112_r90.png --rotate 90
```

左右反転して保存する:
```
uv run main.py -o spss_o21_s112_fh.png --flip-h
```

回転と反転を組み合わせる (270度時計回り + 左右反転):
```
uv run main.py -o spss_o21_s112_r270fh.png --rotate 270 --flip-h
```

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
