#!/usr/bin/env python3
"""校验 dolphin-tutorial 工程骨架：输入图、尺寸、哈希、分组配置。

用法:
    python3 check_project.py            # 校验并打印状态
    python3 check_project.py --json     # 机器可读输出

只依赖标准库：PNG 尺寸直接从 IHDR 读，不经过 Pillow。
"""

import argparse
import hashlib
import json
import os
import struct
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_JSON = os.path.join(PROJECT_DIR, "project.json")
SEMANTIC_JSON = os.path.join(PROJECT_DIR, "semantic-config.json")

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def png_size(path):
    """返回 PNG 的 (宽, 高)；不是 PNG 或已损坏返回 None。"""
    with open(path, "rb") as f:
        head = f.read(24)
    if len(head) < 24 or head[:8] != PNG_SIG or head[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check():
    errors = []
    warnings = []
    report = {}

    with open(PROJECT_JSON, encoding="utf-8") as f:
        project = json.load(f)

    canvas = project.get("canvas", {})
    cw, ch = canvas.get("width"), canvas.get("height")
    sizes = {}

    for role, meta in project.get("inputs", {}).items():
        path = os.path.normpath(os.path.join(PROJECT_DIR, meta["path"]))
        if not os.path.isfile(path):
            errors.append(f"{role}: 输入图不存在 → {meta['path']}")
            continue
        size = os.path.getsize(path)
        digest = sha256(path)
        dims = png_size(path)
        if dims is None:
            errors.append(f"{role}: 不是合法 PNG → {meta['path']}")
        sizes[role] = dims
        if size != meta.get("bytes"):
            errors.append(f"{role}: 字节数不符 {size} != {meta.get('bytes')}")
        if digest != meta.get("sha256"):
            errors.append(f"{role}: sha256 不符 {digest[:12]}… != {meta.get('sha256')[:12]}…")
        if dims and (dims[0] != cw or dims[1] != ch):
            errors.append(f"{role}: 尺寸 {dims[0]}x{dims[1]} 与画布 {cw}x{ch} 不一致")
        report[role] = {"path": meta["path"], "bytes": size, "dims": dims, "sha256": digest[:12]}

    if len(sizes) == 2 and None not in sizes.values() and sizes["lineart"] != sizes["color"]:
        warnings.append(f"线稿与彩图尺寸不一致: {sizes['lineart']} vs {sizes['color']}（上色蒙版会对不齐）")

    with open(SEMANTIC_JSON, encoding="utf-8") as f:
        semantic = json.load(f)
    groups = semantic.get("groups", {})
    orders = [g.get("order") for g in groups.values()]
    if len(orders) != len(set(orders)):
        errors.append("semantic-config.json: groups 的 order 有重复")
    regions = semantic.get("regions", [])
    if not regions:
        warnings.append("semantic-config.json: regions 还是空的（等 lineart-svg / lineart-color 跑完再补）")
    for idx, region in enumerate(regions):
        if region.get("group") not in groups:
            errors.append(f"regions[{idx}]: group {region.get('group')!r} 未在 groups 中定义")
        rect = region.get("rect")
        if not (isinstance(rect, list) and len(rect) == 4):
            errors.append(f"regions[{idx}]: rect 需要 [x1, y1, x2, y2]")

    report["groups"] = len(groups)
    report["regions"] = len(regions)
    report["status"] = "ok" if not errors else "failed"
    return {"ok": not errors, "errors": errors, "warnings": warnings, "report": report}


def main():
    parser = argparse.ArgumentParser(description="校验 dolphin-tutorial 工程骨架")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    result = check()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for role, info in result["report"].items():
            if not isinstance(info, dict):
                continue
            dims = info["dims"] or ("?", "?")
            print(f"  ✓ {role:8s} {dims[0]}x{dims[1]}  {info['bytes']:>8} B  sha256:{info['sha256']}…")
        print(f"  分组 {result['report'].get('groups')} 个 · 区域 {result['report'].get('regions')} 个")
        for warning in result["warnings"]:
            print(f"  ! {warning}")
        for error in result["errors"]:
            print(f"  ✗ {error}")
        print("  → " + ("通过" if result["ok"] else f"失败 {len(result['errors'])} 项"))

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
