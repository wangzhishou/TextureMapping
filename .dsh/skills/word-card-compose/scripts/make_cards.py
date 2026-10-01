#!/usr/bin/env python3
"""把现成的动物插画合成为「单词启蒙卡片」。

给一批**没有文字的插画**,加上「上英文 / 中插画 / 下中文」的卡片版式,
输出 1536x2048 PNG,与 textures/word-flashcards/ 既有卡片同规格。

用法:
  python3 make_cards.py                          # 用默认词表(珍稀动物 12 种)
  python3 make_cards.py --words my.json          # 自定义词表
  python3 make_cards.py --sample 3               # 只出前 3 张
  python3 make_cards.py --src <插画目录> --out <输出目录>
  python3 make_cards.py --list                   # 打印当前词表

词表格式(JSON 数组):
  [{"src": "东北虎", "cn": "老虎", "en": "tiger", "ipa": "/ˈtaɪɡə(r)/"}, ...]
  src  = 插画文件名去掉 <后缀> 的部分,即 <src><后缀>.png
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)

# ---------------- 版式(与既有卡片对齐,改动前先看 SKILL.md 的说明) ----------------
W, H = 1536, 2048
WHITE = (255, 255, 255)
WORD_BASE = 474                      # 英文单词基线
ART_BOX = (56, 530, 1480, 1800)      # 插画可用区(等比缩放居中,不裁切)
CN_BASE = 1985                       # 中文基线
WORD_SIZE = 336                      # 英文基准字号(长词自动缩)
MAX_WORD_W = 1352                    # 英文最大宽度
CN_SIZE = 150                        # 中文字号

LETTER_COLORS = ["#E8352B", "#F39200", "#8CC63E", "#22A7D8", "#3F51B5",
                 "#9B59B6", "#EC4E9C", "#00A88E"]

# ---------------- 字体 ----------------
F_WORD = "/System/Library/Fonts/Supplemental/ChalkboardSE.ttc"   # 圆润手写,认读性好
WORD_IDX = 1                                                     # Bold
F_CN = os.path.join(SKILL_DIR, "fonts", "ZCOOLKuaiLe-Regular.ttf")  # 站酷快乐体,简体全覆盖
CN_IDX = 0


def find_project_root(start):
    cur = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return os.path.abspath(start)
        cur = parent


PROJECT = find_project_root(HERE)
DEF_SRC = os.path.join(PROJECT, "textures", "endangered-animals")
DEF_OUT = os.path.join(PROJECT, "textures", "word-flashcards")
DEF_WORDS = os.path.join(SKILL_DIR, "words.json")


def hexa(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def make_font(size):
    return ImageFont.truetype(F_WORD, size, index=WORD_IDX)


def letter_tile(ch, size, color):
    """单字母图块。

    图块高度对所有字母**统一**为 ascent+descent+16,字形画在升部线上,
    这样每个图块的基线都落在同一 y —— 带降部的 p/y 不会被顶高。
    (按图块底边对齐是错的:降部字母图块更高,会被整体抬起来。)
    """
    f = make_font(size)
    d = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    asc, desc = f.getmetrics()
    bb = d.textbbox((0, 0), ch, font=f)
    tile = Image.new("RGBA", (bb[2] - bb[0] + 16, asc + desc + 16), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((8 - bb[0], 8), ch, font=f, fill=hexa(color))
    return tile


def draw_word(img, word, size=WORD_SIZE):
    """整词一行排开,逐字母上色。不旋转不抖动 —— 学习者要一眼看清。"""
    while size > 90:
        f = make_font(size)
        w = sum((f.getbbox(c)[2] - f.getbbox(c)[0]) if c != " " else int(size * 0.30)
                for c in word) + int(size * 0.06) * (len(word) - 1)
        if w <= MAX_WORD_W:
            break
        size -= 4

    tiles, widths = [], []
    for i, ch in enumerate(word):
        if ch == " ":
            tiles.append(None); widths.append(int(size * 0.30)); continue
        t = letter_tile(ch, size, LETTER_COLORS[i % len(LETTER_COLORS)])
        tiles.append(t); widths.append(t.width - 16)
    sp = int(size * 0.06)
    asc = make_font(size).getmetrics()[0]
    top = int(WORD_BASE - asc - 8)          # 图块内基线在 8+asc 处,据此反推贴图 y
    x = (W - (sum(widths) + sp * (len(word) - 1))) // 2
    for i, t in enumerate(tiles):
        if t is None:
            x += widths[i] + sp; continue
        img.paste(t, (int(x - 8), top), t)  # 图块同高,基线自然对齐
        x += widths[i] + sp


def draw_cn(img, text, size=CN_SIZE):
    f = ImageFont.truetype(F_CN, size, index=CN_IDX)
    d = ImageDraw.Draw(img)
    bb = d.textbbox((0, 0), text, font=f)
    d.text(((W - (bb[2] - bb[0])) // 2 - bb[0], CN_BASE - bb[3]), text, font=f,
           fill=(94, 78, 66))


def paste_art(img, path, box=ART_BOX):
    """插画等比缩放居中,不裁切"""
    art = Image.open(path).convert("RGB")
    x0, y0, x1, y1 = box
    sc = min((x1 - x0) / art.width, (y1 - y0) / art.height)
    nw, nh = int(art.width * sc), int(art.height * sc)
    art = art.resize((nw, nh), Image.LANCZOS)
    img.paste(art, (x0 + ((x1 - x0) - nw) // 2, y0 + ((y1 - y0) - nh) // 2))
    return nw, nh


def build(word, cn, src_path, out_path):
    img = Image.new("RGB", (W, H), WHITE)
    nw, nh = paste_art(img, src_path)
    draw_word(img, word)
    draw_cn(img, cn)
    img.save(out_path, format="PNG")
    return nw, nh


def main():
    ap = argparse.ArgumentParser(description="把插画合成单词启蒙卡片")
    ap.add_argument("--words", default=DEF_WORDS, help="词表 JSON")
    ap.add_argument("--src", default=DEF_SRC, help="插画目录")
    ap.add_argument("--out", default=DEF_OUT, help="输出目录")
    ap.add_argument("--src-suffix", default="-彩色完成图", help="插画文件名后缀(不含 .png)")
    ap.add_argument("--name", default="{en} 单词启蒙卡片（彩色）.png", help="输出文件名模板")
    ap.add_argument("--sample", type=int, default=0, help="只出前 N 张")
    ap.add_argument("--list", action="store_true", help="只打印词表")
    a = ap.parse_args()

    words = json.load(open(a.words, encoding="utf-8"))
    if a.list:
        for i, w in enumerate(words, 1):
            print(f"{i:>2}. {w['src']:<14} {w['cn']:<8} {w['en']:<12} {w.get('ipa','')}")
        print(f"\n共 {len(words)} 条 · 词表 {a.words}")
        return
    if a.sample:
        words = words[:a.sample]

    os.makedirs(a.out, exist_ok=True)
    missing = []
    for w in words:
        src = os.path.join(a.src, w["src"] + a.src_suffix + ".png")
        if not os.path.exists(src):
            missing.append(src); continue
        out = os.path.join(a.out, a.name.format(**w))
        nw, nh = build(w["en"], w["cn"], src, out)
        print(f"  {w['src']:<14} {w['cn']:<8} {w['en']:<12} → {os.path.basename(out)}  插画 {nw}x{nh}")
    print(f"\n共 {len(words) - len(missing)} 张 → {a.out}")
    if missing:
        print("以下源图没找到:")
        for m in missing:
            print("  ", m)
        sys.exit(1)


if __name__ == "__main__":
    main()
