#!/usr/bin/env python3
"""扫描图片目录，导出可复现资产清单。纯标准库，无第三方依赖。

ComfyUI 的 SaveImage 会把完整生成参数写进 PNG 的文本块（prompt / workflow）。
本脚本只读元数据、不解码像素，因此几乎没有时间成本，适合一次扫描上万张历史图。

用法:
    python inventory.py <图片目录> [-o inventory.csv]

输出列:
    path, file, dir, ext, width, height, has_workflow, has_api, meta_level,
    ckpt, seed, steps, cfg, sampler_name, scheduler, denoise, loras, prompts

meta_level:
    A = 有完整生成参数，可当基线参数
    B = 无参数，只能当风格参考图
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import struct
import sys
from collections import Counter

IMAGE_EXT = {".png", ".jpg", ".jpeg"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SAMPLER_KEYS = ("seed", "noise_seed", "steps", "cfg", "sampler_name", "scheduler", "denoise")
JPEG_SIZE_MARKERS = {
    0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
    0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
}
OUTPUT_FIELDS = (
    "path", "file", "dir", "ext", "width", "height",
    "has_workflow", "has_api", "meta_level",
    "ckpt", "seed", "steps", "cfg", "sampler_name", "scheduler", "denoise",
    "loras", "prompts",
)


def png_meta(path: str):
    """读取 PNG 的尺寸与文本块。"""
    width = height = 0
    texts = {}
    with open(path, "rb") as handle:
        if handle.read(8) != PNG_SIGNATURE:
            return 0, 0, texts
        while True:
            head = handle.read(8)
            if len(head) < 8:
                break
            length = struct.unpack(">I", head[:4])[0]
            chunk_type = head[4:8]
            data = handle.read(length)
            handle.read(4)  # CRC
            if chunk_type == b"IHDR" and len(data) >= 8:
                width, height = struct.unpack(">II", data[:8])
            elif chunk_type == b"tEXt":
                key, _, value = data.partition(b"\x00")
                texts[key.decode("latin-1")] = value.decode("utf-8", "ignore")
            elif chunk_type == b"iTXt":
                key, _, rest = data.partition(b"\x00")
                if len(rest) >= 2:
                    rest = rest[2:]  # 跳过压缩标志与压缩方法
                    _, _, rest = rest.partition(b"\x00")  # 语言标签
                    _, _, rest = rest.partition(b"\x00")  # 译名
                    texts.setdefault(key.decode("latin-1"), rest.decode("utf-8", "ignore"))
            elif chunk_type == b"IEND":
                break
    return width, height, texts


def jpeg_size(path: str):
    """从 JPEG 的 SOF 段读取尺寸。"""
    with open(path, "rb") as handle:
        if handle.read(2) != b"\xff\xd8":
            return 0, 0
        while True:
            byte = handle.read(1)
            if not byte:
                return 0, 0
            if byte != b"\xff":
                continue
            marker = handle.read(1)
            while marker == b"\xff":
                marker = handle.read(1)
            if not marker:
                return 0, 0
            if marker == b"\xd8" or b"\xd0" <= marker <= b"\xd7":
                continue
            segment = handle.read(2)
            if len(segment) < 2:
                return 0, 0
            segment_length = struct.unpack(">H", segment)[0]
            if marker[0] in JPEG_SIZE_MARKERS:
                payload = handle.read(5)
                if len(payload) < 5:
                    return 0, 0
                height, width = struct.unpack(">HH", payload[1:5])
                return width, height
            handle.seek(segment_length - 2, 1)


def params_from_comfy(api_text: str) -> dict:
    """从 ComfyUI 的 API 格式 prompt 中抽取采样参数。"""
    try:
        graph = json.loads(api_text)
    except (TypeError, ValueError):
        return {}
    if not isinstance(graph, dict):
        return {}

    out = {}
    texts = []
    loras = []
    for node in graph.values():
        if not isinstance(node, dict):
            continue
        class_type = node.get("class_type", "")
        inputs = node.get("inputs") or {}
        if class_type in ("KSampler", "KSamplerAdvanced"):
            for key in SAMPLER_KEYS:
                if key in inputs:
                    out["seed" if key == "noise_seed" else key] = inputs[key]
        elif class_type in ("CheckpointLoaderSimple", "CheckpointLoader"):
            out["ckpt"] = inputs.get("ckpt_name", "")
        elif class_type in ("UNETLoader", "UnetLoaderGGUF"):
            out["ckpt"] = inputs.get("unet_name", "")
        elif class_type == "LoraLoader":
            name = inputs.get("lora_name", "")
            weight = inputs.get("strength_model", "")
            loras.append("{}@{}".format(name, weight))
        elif class_type == "CLIPTextEncode":
            texts.append(str(inputs.get("text", ""))[:200])
    out["loras"] = ";".join(loras)
    out["prompts"] = " || ".join(texts)
    return out


def build_row(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()
    width = height = 0
    texts = {}
    if ext == ".png":
        try:
            width, height, texts = png_meta(path)
        except OSError:
            pass
    else:
        try:
            width, height = jpeg_size(path)
        except OSError:
            pass

    has_api = "prompt" in texts
    params = params_from_comfy(texts.get("prompt", "")) if has_api else {}
    row = {
        "path": path,
        "file": os.path.basename(path),
        "dir": os.path.dirname(path),
        "ext": ext.lstrip("."),
        "width": width,
        "height": height,
        "has_workflow": int("workflow" in texts),
        "has_api": int(has_api),
        "meta_level": "A" if has_api else "B",
    }
    for key in ("ckpt", "seed", "steps", "cfg", "sampler_name", "scheduler", "denoise", "loras", "prompts"):
        row[key] = params.get(key, "")
    return row


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="扫描图片目录并导出元数据清单")
    parser.add_argument("root", help="图片根目录")
    parser.add_argument("-o", "--output", default="inventory.csv", help="输出 CSV 路径")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.root):
        print("目录不存在: {}".format(args.root), file=sys.stderr)
        return 2

    rows = []
    for dirpath, _, filenames in os.walk(args.root):
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() not in IMAGE_EXT:
                continue
            rows.append(build_row(os.path.join(dirpath, filename)))

    with open(args.output, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    level_a = sum(1 for row in rows if row["meta_level"] == "A")
    checkpoints = Counter(row["ckpt"] for row in rows if row["ckpt"])
    print("图片总数: {}".format(len(rows)))
    print("A 级(有参数): {}  B 级(仅参考): {}".format(level_a, len(rows) - level_a))
    for name, count in checkpoints.most_common(5):
        print("  {} x{}".format(name, count))
    print("输出: {}".format(os.path.abspath(args.output)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
