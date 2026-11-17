# Mini Bezier Shaper

**用可以拖的貝茲曲線塑形髮束的免費 Blender 插件**<br>
**A free Blender add-on for shaping hair strands with a live Bezier curve**

[中文](#中文) · [English](#english) · [下載 Download](../../releases/latest)

> [!NOTE]
> 這個插件還很新，測試不多。遇到問題請 [開 issue](../../issues)，附上錯誤訊息和 Blender 版本。
>
> This add-on is new and lightly tested. Please [open an issue](../../issues) with the error message and your Blender version if something breaks.

---

## 中文

### 為什麼做這個

做動漫風頭髮的時候，我常常心裡知道要什麼弧度，手卻拉不出來：手一抖曲線就歪，在透視視角下拉點、從好幾個角度用 R 轉方向，截面就被壓扁、扭歪，看起來像折到一樣。市面上能做到的插件大多是付費的，所以我自己做了一個免費的。

老實說，我才用 Blender 五天左右，這個工具可能根本沒什麼用，或者早就有更好的做法，我也不確定。但總之先做出來分享，如果剛好對你有幫助就太好了。

### 功能

| 工具 | 做什麼 |
|---|---|
| **建立塑形曲線** | 在選取的部分長出一條貝茲曲線，拖控制點和把手，網格即時跟著彎。可以處理整撮髮束，也可以只處理一排點。 |
| **沿截面找中心線** | 給已經彎過的髮束用的選項，曲線會沿著每一圈截面長出來。 |
| **整理髮束** | 截面修圓、點平均分佈、走向和粗細變平順、解開扭轉。 |
| **平順扭轉** | 扁髮片扭得不平均時用。截面的形狀和位置都不變，只把扭轉從根部到髮尖平均分配。 |

### 安裝

到 [Releases](../../releases/latest) 下載對應版本的 zip：

| Blender 版本 | 檔案 | 安裝方式 |
|---|---|---|
| 4.2 以上 | `mini_bezier_shaper_4.2+.zip` | 編輯 → 偏好設定 → 附加元件 → 右上角下拉選單 → 從磁碟安裝 |
| 3.0 – 4.1 | `mini_bezier_shaper_4.1below.zip` | 編輯 → 偏好設定 → 附加元件 → 安裝 → 選 zip → 勾選啟用 |

- 安裝新版前，先移除舊版。
- 面板位置：3D 視窗按 **N** → **Edit** 分頁 → **Mini Bezier Shaper**。

### 髮束要怎麼做

工具最適合這種結構的髮束：

- **根部開口**，或者根部那圈不要選
- **中間每一圈都是整齊的點**，例如 8 個點的截面用 **E** 擠出來
- **髮尖**可以收成一個點
- 多用 **Ctrl+R** 切幾圈，彎起來才順

選取時，滑鼠指著髮束按 **L**，就能整撮選起來。

### 用法

**彎髮束**

1. 在編輯模式選整撮，模式選「整撮髮束」。只選一排點的話，用「單排點」。
2. 設定控制點數，通常 3 到 5 個就夠。髮束已經彎過的話，勾選「沿截面找中心線」。
3. 按「建立塑形曲線」，用 **G** 拖控制點和把手，網格會即時跟著變。
4. 按「完成塑形」保留形狀，或「取消塑形」還原。

**整理髮束**：按完後，打開畫面左下角的面板調整：

- **圓度**：1 是正圓，0.3 到 0.6 是把方角修圓，0 是保留截面形狀（扁髮片用）
- **平順**：數字越大，走向和粗細越平順；太高的話，粗細會變成直線收細
- **解開扭轉**：修掉從好幾個角度用 R 旋轉造成的扭轉

**平順扭轉**：扁髮片扭得不平均、看起來像折到時用。根部和最後一圈不會動。覺得改太多，就把「強度」調低。

### 限制

- 「整理髮束」和「平順扭轉」一次只能處理一撮。
- 沒勾「沿截面找中心線」時，髮束最好大致是直的。彎成 U 字的髮束，建議分段處理。
- 選的點很多（上千個）時，拖曲線可能會卡。
- 功能沒有付費插件（例如 Bezier Mesh Shaper）完整。

---

## English

### Why

When modeling anime-style hair, I often knew exactly the curve I wanted but couldn't get it by hand. Shaky hands made the curves wobble, and dragging points in perspective or rotating with R from several angles left the cross-sections squashed and twisted, as if the strand had been folded. The tools that solve this are mostly paid, so I made a free one.

Honestly, I've only been using Blender for about five days, so this might not even be useful, or there may already be a better way to do it. I'm not sure. But I made it anyway, and if it helps you, that's great.

### Features

| Tool | What it does |
|---|---|
| **Create Shaper Curve** | Puts a Bezier curve on the selection. Drag its points and handles and the mesh follows live. Works on a whole strand or a single row of vertices. |
| **Follow Rings** | Option for strands that are already bent: the curve follows the strand through each cross-section ring. |
| **Tidy Strand** | Makes cross-sections round and evenly spaced, smooths the path and taper, and removes twist. |
| **Smooth Twist** | For flat ribbons with uneven twist. Keeps each cross-section's shape and position and spreads the twist evenly from root to tip. |

### Install

Download the zip for your Blender version from [Releases](../../releases/latest):

| Blender version | File | How |
|---|---|---|
| 4.2 and later | `mini_bezier_shaper_4.2+.zip` | Edit → Preferences → Add-ons → ⌄ menu (top right) → Install from Disk |
| 3.0 – 4.1 | `mini_bezier_shaper_4.1below.zip` | Edit → Preferences → Add-ons → Install → pick the zip → tick to enable |

- Remove the old version before installing a new one.
- The panel is in the 3D Viewport sidebar: press **N** → **Edit** tab → **Mini Bezier Shaper**.

### Strand layout

The tools work best on strands built like this:

- An **open root**, or a root ring you leave unselected
- **Clean rings of vertices** along the length, e.g. an 8-vertex section extruded with **E**
- A **tip** that can close into a single point
- Enough rings (**Ctrl+R**) so bends stay smooth

To select a whole strand, hover over it and press **L**.

### Usage

**Bend a strand**

1. In Edit Mode, select the strand and choose **Whole Strand** mode, or **Single Row** for one row of vertices.
2. Set **Control Points** (3–5 is usually enough). For an already-bent strand, tick **Follow Rings**.
3. Click **Create Shaper Curve**, then move the points with **G** and drag the handles. The mesh updates live.
4. Click **Finish Shaping** to keep the shape, or **Cancel Shaping** to restore it.

**Tidy Strand**: after clicking, open the panel at the bottom left of the viewport:

- **Roundness**: 1 = perfect circle, 0.3–0.6 rounds off corners, 0 = keep the section shape (for flat ribbons)
- **Smooth**: higher = smoother path and taper. Very high values flatten the taper into a straight line.
- **Untwist**: fixes twist from rotating with R from several angles

**Smooth Twist**: for flat ribbons whose twist is uneven and looks pinched. The root ring and the last ring stay put. Lower **Strength** for a lighter touch.

### Limitations

- Tidy Strand and Smooth Twist work on one strand at a time.
- Without Follow Rings, Whole Strand mode expects a roughly straight strand. U-shaped strands are best done in parts.
- Large selections (thousands of vertices) can feel slow while dragging the curve.
- Not as complete as paid tools such as Bezier Mesh Shaper.

---

## Build from source / 自行打包

```sh
python scripts/build.py
```

Creates both install zips in `dist/`. 會在 `dist/` 產生兩個安裝用的 zip。

## Credits

Made by KNCG, with code written together with Claude (Anthropic).<br>
由 KNCG 製作，程式碼與 Claude (Anthropic) 協作完成。

## License

[GPL-3.0-or-later](LICENSE), the same license as Blender.
