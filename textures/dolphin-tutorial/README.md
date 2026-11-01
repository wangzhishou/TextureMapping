# dolphin-tutorial · 海豚抱海星 彩铅临摹教程

竖屏 9:16（1008×1792）的绘画教程工程骨架：一张黑白线稿 + 一张对齐的彩铅效果图，
后续按 `lineart-svg → lineart-color → svg-motion-video` 的流水线生成逐笔上色视频。

当前状态：**骨架（图已就位，流水线未跑）**。`project.json` 里 `status` 为
`skeleton_inputs_ready`，跑完一段就把它改成实际的阶段名。

## 输入图

原始图不在本目录，统一归档在相邻的图片目录，避免二进制重复入库：

| 用途 | 文件 | 尺寸 |
| --- | --- | --- |
| 线稿 | [`../dolphin-coloring/海豚 线稿.png`](../dolphin-coloring/海豚%20线稿.png) | 1008×1792 |
| 彩铅效果图 | [`../dolphin-coloring/海豚 彩铅画.png`](../dolphin-coloring/海豚%20彩铅画.png) | 1008×1792 |

`project.json` 记录了这两张图的相对路径、字节数和 sha256；图片换版本时先跑
`check_project.py`，按报错把哈希更新掉，别让配置和图悄悄对不上。

## 目录约定

```
dolphin-tutorial/
├── project.json          # 输入图哈希 + 流水线阶段 + 输出清单
├── semantic-config.json  # 上色分组与顺序（regions 待流水线补齐）
├── check_project.py      # 输入/尺寸/哈希/分组校验
└── README.md
```

流水线产物（`vector/`、`color/`、`final/`、`review/`）由各 skill 生成，
形状参考 `../mermaid-tutorial/`，本骨架不预置空目录。

## 校验

```bash
python3 check_project.py          # 人读
python3 check_project.py --json   # 机读，CI 里好用
```

退出码 0 = 通过。`regions` 为空时只报 warning，不算失败。

## 后续步骤

1. `lineart-svg`：线稿 → 独立中心线路径（`vector/strokes.svg` + `manifest.json`）。
2. `lineart-color`：按彩图生成逐区域蒙版、上色顺序与时长（`color/`），
   把分区写回 `semantic-config.json` 的 `regions`。
3. `svg-motion-video`：渲逐笔绘制 + 逐区域上色。
4. `drawing-tutorial-video`：套封面、步骤提示、轻音乐出成片，并回填 `verification.json`。

## 元数据

两张图入库前已跑过 `strip-ai-metadata` 的 scan → strip → verify：
本身不含 C2PA / eXIf / iTXt 等标识，清理前后逐字节一致，像素零损失。
