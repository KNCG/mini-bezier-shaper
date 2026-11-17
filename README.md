# Mini Bezier Shaper

A free Blender add-on for shaping mesh hair strands with a live Bezier curve, plus one-click tools to clean up cross-sections and uneven twist.

免費的 Blender 附加元件：用一條可以拖的貝茲曲線即時塑形網格髮束，再一鍵修好歪掉的截面和不平均的扭轉。

> [!NOTE]
> This add-on is young and has had limited testing. Please [open an issue](../../issues) if something breaks, and include the error message and your Blender version.
>
> 這個插件還很新，測試不多。遇到問題請開 issue，附上錯誤訊息和 Blender 版本。

## Features / 功能

| Tool | 工具 | What it does |
|---|---|---|
| Create Shaper Curve | 建立塑形曲線 | Puts a Bezier curve on the selection. Drag its points and handles and the mesh follows live. Works on a whole strand or on a single row of vertices. |
| Follow Rings | 沿截面找中心線 | Option for strands that are already bent: the curve follows the strand through each cross-section ring. |
| Tidy Strand | 整理髮束 | Makes every cross-section round and evenly spaced, smooths the path and the taper, and removes twist. |
| Smooth Twist | 平順扭轉 | Spreads the twist evenly from root to tip without changing any cross-section's shape or position. Made for flat ribbon strands. |

## Install / 安裝

Download the zip from [Releases](../../releases). 到 Releases 下載 zip。

| Blender version | File | How |
|---|---|---|
| 4.2 and later | `mini_bezier_shaper_4.2+.zip` | Edit → Preferences → Add-ons → ⌄ menu (top right) → Install from Disk |
| 3.0 – 4.1 | `mini_bezier_shaper_legacy.zip` | Edit → Preferences → Add-ons → Install → pick the zip → tick to enable |

Remove the old version before installing a new one. 安裝新版前先移除舊版。

The panel is in the 3D Viewport sidebar: press **N** → **Edit** tab → **Mini Bezier Shaper**.
面板在 3D 視窗側邊欄：按 **N** → **Edit** 分頁。
## Usage / 用法

### Strand layout / 髮束結構

The strand tools work best on a strand built like this: an **open root ring** (or a root ring you leave unselected), **clean rings of vertices** along the length (e.g. a square or 8-vertex section extruded with **E**), and a tip that can close into a single point. Add enough rings (**Ctrl+R**) so bends stay smooth.

髮束最好是這樣的結構：根部開口（或根部那圈不選）、中間每一圈都是整齊的點（例如 8 個點的截面用 E 擠出），髮尖可以收成一點。多用 Ctrl+R 切幾圈，彎起來才順。

Select a whole strand by hovering over it and pressing **L**. 滑鼠指著髮束按 L 就能整撮選起來。

### Bend a strand / 彎髮束

1. In mesh Edit Mode, select the strand. Choose **Whole Strand** mode (or **Single Row** for one row of vertices).
2. Set **Control Points** (3–5 is usually enough). For an already-bent strand, tick **Follow Rings**.
3. Click **Create Shaper Curve**. Move the curve points with **G** and drag the handles; the mesh updates live.
4. Click **Finish Shaping** to keep the shape, or **Cancel Shaping** to restore it.

1. 編輯模式選整撮，模式選「整撮髮束」（只選一排點就用「單排點」）。
2. 設定控制點數（通常 3 到 5 個）。髮束已經彎過就勾「沿截面找中心線」。
3. 按「建立塑形曲線」，用 G 拖控制點和把手，網格即時跟著變。
4. 按「完成塑形」保留，或「取消塑形」還原。

### Clean up a strand / 修髮束

**Tidy Strand** — after the click, open the operator panel at the bottom left of the viewport:

- **Roundness**: 1 = perfect circle; 0.3–0.6 rounds off corners; 0 = keep the section shape (use for flat ribbons).
- **Smooth**: higher = smoother path and taper. Very high values flatten the taper into a straight line.
- **Untwist**: lines each ring up with the one before it, fixing twist from rotating with **R** from several angles.

**Smooth Twist** — for flat ribbons whose twist is uneven (looks pinched or folded). Each ring keeps its shape and position and only turns around the strand. The root ring and the last ring stay put. Lower **Strength** for a lighter touch.

「整理髮束」：按完後打開左下角面板調「圓度」「平順」「解開扭轉」。
「平順扭轉」：扁髮片扭得不平均時用。截面形狀和位置都不變，只把扭轉平均分配，根部和最後一圈不動。

## Limitations / 限制

- One strand at a time for Tidy Strand and Smooth Twist.
- Whole Strand mode without Follow Rings expects a roughly straight strand; U-shaped strands are best done in parts.
- Large selections (thousands of vertices) can feel slow while dragging the curve.
- Not a replacement for full commercial tools such as Bezier Mesh Shaper.

## Build from source / 自行打包

```sh
python scripts/build.py
```

Creates both install zips in `dist/`.

## License

[GPL-3.0-or-later](LICENSE), like Blender itself.
