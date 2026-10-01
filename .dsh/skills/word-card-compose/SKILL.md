---
name: word-card-compose
description: 把**现成的插画**合成为「单词启蒙卡片」(上英文 / 中插画 / 下中文,1536x2048),输出到 textures/word-flashcards/。当用户说"把这些图做成单词卡片""给这批动物配单词""给插画加上英文和中文""批量出单词卡",或拿来一批没有文字的插画/贴图要转成教学卡片时使用。不用于从零生成插画(那走 .kimi-code/skills/word-flashcards 的文生图流程)。
whenToUse: 手上已有插画文件(彩铅动物、贴图、涂色稿的彩色版),要加上英文单词和中文释义做成单词卡时
---

# 插画 → 单词启蒙卡片

给一批**没有文字的插画**,套上「上英文 / 中插画 / 下中文」的卡片版式,
输出 1536×2048 PNG,与 `textures/word-flashcards/` 里既有卡片同规格。

## 什么时候用

- 用户给了一个插画目录(或项目里新增了一批贴图),要转成单词卡
- 用户说"把这些动物做成单词卡片""给这批图配单词"
- **不适用**:要从零画出插画 —— 那用 `.kimi-code/skills/word-flashcards`(千问文生图),
  本 skill 只做**排版合成**,不改动插画本身

## 快速用法

```bash
SK=<本项目>/.dsh/skills/word-card-compose

python3 $SK/scripts/make_cards.py --list                 # 看当前词表
python3 $SK/scripts/make_cards.py --sample 3             # 先出 3 张样张验收
python3 $SK/scripts/make_cards.py                        # 全量出片
python3 $SK/scripts/make_cards.py --words my.json --src <插画目录> --out <输出目录>
```

默认:`--src textures/endangered-animals`、`--out textures/word-flashcards`、
`--words <skill>/words.json`。项目根由脚本自己向上找 `.git` 定位。

## 词表

`words.json`,一个数组:

```json
[{"src": "东北虎", "cn": "老虎", "en": "tiger", "ipa": "/ˈtaɪɡə(r)/"}]
```

- `src` —— 插画文件名去掉后缀的部分,即 `<src><后缀>.png`(后缀默认 `-彩色完成图`)
- `cn` —— 卡面中文。**用孩子能懂的通名**(老虎/大象/熊猫),
  物种全名留在 `src` 里不丢
- `en` —— 英文单词,支持带空格的词组(`red panda`)
- `ipa` —— 仅记录用,当前版式不渲染音标(视频里才用)

新增一种动物:往 `words.json` 加一条,插画按 `<src>-彩色完成图.png` 放好,重跑即可。

## 版式(改动前先读)

| 元素 | 位置 | 字体 |
|---|---|---|
| 英文单词 | 基线 y=474,逐字母一个蜡笔色 | Chalkboard SE Bold(系统字体) |
| 插画 | 可用区 (56,530)-(1480,1800),等比缩放居中,**不裁切** | — |
| 中文 | 基线 y=1985 | 站酷快乐体(随 skill 带) |

- 英文字号 336 起,超过 1352px 宽就整体缩小(长词如 `elephant` 会自动降到 ~262)
- 去掉蜡笔颗粒/旋转/抖动 —— 学习者是来看清字的,**清楚优先于质感**

## 两个必须知道的坑

### 1. 字母要按**基线**对齐,不能按图块底边

`letter_tile()` 给所有字母生成**等高等宽规则**的图块(高度统一 `ascent+descent+16`,
字形画在升部线上)。若按图块底边对齐,**带降部的 p/y 会整体被抬高** ——
`elePhant`、`Panda` 就是这么来的。改这块务必保持"图块等高 + 按 `8+asc` 反推贴图 y"。

### 2. 中文字体必须验**简体覆盖**,不能用日文字体凑

`ヒラギノ丸ゴ`(圆体)气质最贴,但它是日文字体,
缺 **东/顶/鹤/亚/马/獭/驴/牦/丝** 等简体字,会渲染成 ⊠ 豆腐块。

而且 **`getmask()` 的长度检测测不出豆腐块**(豆腐本身也有字形)。
要验覆盖,得拿私用区码位当"豆腐指纹"比对:

```python
tofu = bytes(np.asarray(f.getmask("\ue000")))
missing = [c for c in text if bytes(np.asarray(f.getmask(c))) == tofu]
```

本 skill 带的 **站酷快乐体** 已验过简体全覆盖。

## 出片后必须做的三件事

1. **抽看样张**:先 `--sample 3` 肉眼核对单词拼写、中文释义、插画有没有被压到
2. **扫元数据**:`strip-ai-metadata` 的 `scan`,确认卡片 CLEAN
   (脚本用 PIL 合成,本身不携带元数据,但**必须实测而不是假定**)
3. **入库走 LFS**:`textures/**` 是 LFS 路径,`git add` 后确认是 3 行指针,
   并核对 LFS 对象真在本地 —— 否则远端会变成打不开的 131 字节假图

```bash
python3 ~/.dsh/skills/strip-ai-metadata/scripts/ai_meta.py scan <输出目录>
git show :"<新卡片路径>" | head -3          # 应是 version https://git-lfs...
```

## 参考实现

`textures/word-flashcards/` 里 12 张珍稀动物卡(2026-10 入库)就是本 skill 的产物:
`tiger / crane / elephant / marmot / panda / red panda / fox / antelope / donkey / yak / monkey / leopard`。
