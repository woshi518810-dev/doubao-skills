#!/usr/bin/env python3
"""扫描Ozon SKU根目录，输出每个一级子文件夹及其第一张图片的路径。

用法: python scan_sku.py "<根目录绝对路径>"
输出: JSON数组到stdout，每项含 folder, folder_name, image, image_name
"""
import json
import re
import sys
from pathlib import Path

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def natural_sort_key(path: Path):
    """自然排序键，使 01.jpg 排在 2.jpg 之前。"""
    parts = re.split(r"(\d+)", path.name.lower())
    return [int(p) if p.isdigit() else p for p in parts]


def find_first_image(folder: Path):
    """返回文件夹内按自然排序的第一张图片，无则返回None。"""
    images = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMG_EXTS
    ]
    if not images:
        return None
    images.sort(key=natural_sort_key)
    return images[0]


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "缺少根目录参数"}, ensure_ascii=False))
        sys.exit(1)

    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(json.dumps({"error": f"路径不存在或不是目录: {root}"}, ensure_ascii=False))
        sys.exit(1)

    # 获取一级子文件夹
    subfolders = sorted(
        [d for d in root.iterdir() if d.is_dir()],
        key=lambda d: d.name.lower()
    )

    # 如果根目录下没有子文件夹，将根目录本身视为唯一SKU
    if not subfolders:
        subfolders = [root]

    results = []
    for folder in subfolders:
        first_img = find_first_image(folder)
        results.append({
            "folder": str(folder),
            "folder_name": folder.name,
            "image": str(first_img) if first_img else None,
            "image_name": first_img.name if first_img else None,
        })

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
