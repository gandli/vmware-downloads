"""探测 archive.org 上 VMware Workstation / Fusion 的完整历史版本清单

用于：
1. 决定要从 archive.org 补哪些历史版本（补齐到 15 版）
2. 生成 legacy_versions.json 数据（archive.org md5/sha1 + 无 SHA256）
"""

from __future__ import annotations

import json
import re
import urllib.request
from collections import defaultdict


ARCHIVE_META_URL = "https://archive.org/metadata/vmwareworkstationarchive"
ARCHIVE_DL_BASE = "https://archive.org/download/vmwareworkstationarchive/"


def fetch_archive_metadata() -> dict:
    with urllib.request.urlopen(ARCHIVE_META_URL, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def is_installer(name: str) -> bool:
    """判断是否是安装包（排除 tools/ossp 等附件）"""
    lower = name.lower()
    if not (lower.endswith(".exe") or lower.endswith(".bundle") or lower.endswith(".dmg")):
        return False
    if any(x in lower for x in ["tools", "ossp", "source", "guest"]):
        return False
    return True


def parse_ws_version(name: str) -> tuple[str, str] | None:
    """从 Workstation 文件名提取 (version, build)"""
    if "fusion" in name.lower():
        return None
    # 匹配 17.6.4 或 25H2u1 或 26H1 等
    m = re.search(r"[Ww]orkstation.*?(\d+\.\d+\.\d+|\d+[Hh]\d+(?:u\d+)?)-(\d+)", name)
    return (m.group(1), m.group(2)) if m else None


def parse_fusion_version(name: str) -> tuple[str, str] | None:
    m = re.search(r"Fusion-(\d+\.\d+\.\d+|\d+[Hh]\d+(?:u\d+)?)-(\d+)", name)
    return (m.group(1), m.group(2)) if m else None


def detect_platform(name: str) -> str:
    if name.endswith(".exe"):
        return "windows"
    if name.endswith(".bundle"):
        return "linux"
    if name.endswith(".dmg"):
        return "macos"
    return "unknown"


def _human_size(n) -> str:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return ""
    if n >= 1024 ** 3:
        return f"{n / 1024 ** 3:.2f} GB"
    if n >= 1024 ** 2:
        return f"{n / 1024 ** 2:.2f} MB"
    if n >= 1024:
        return f"{n / 1024:.2f} KB"
    return f"{n} B"


def collect_all_versions(files: list[dict]) -> tuple[dict, dict]:
    """
    输入 archive.org files 列表，返回 (ws_versions, fusion_versions)
    结构：{version: {"build": "...", "downloads": {platform: {...}}, "files": [...]}}
    """
    ws = defaultdict(lambda: {"build": "", "downloads": {}, "files": []})
    fu = defaultdict(lambda: {"build": "", "downloads": {}, "files": []})

    for f in files:
        name = f.get("name", "")
        if not is_installer(name):
            continue

        size_bytes = int(f.get("size", 0)) if f.get("size") else 0
        entry_data = {
            "filename": name.rsplit("/", 1)[-1],
            "url": ARCHIVE_DL_BASE + name,
            "size": _human_size(size_bytes),
            "size_bytes": size_bytes,
            "md5": f.get("md5", ""),
            "sha1": f.get("sha1", ""),
            "sha256": "",  # archive.org 只给 md5+sha1
            "sha256_verified": False,
        }
        platform = detect_platform(name)

        r = parse_ws_version(name)
        if r:
            ver, build = r
            ws[ver]["build"] = build
            ws[ver]["downloads"][platform] = entry_data
            ws[ver]["files"].append(name)
            continue

        r = parse_fusion_version(name)
        if r:
            ver, build = r
            fu[ver]["build"] = build
            fu[ver]["downloads"][platform] = entry_data
            fu[ver]["files"].append(name)

    return dict(ws), dict(fu)


def sort_by_build_desc(versions: dict) -> list[tuple[str, dict]]:
    """按 build 号降序（最新在前）"""
    def key(item):
        b = item[1]["build"]
        return int(b) if b.isdigit() else 0
    return sorted(versions.items(), key=key, reverse=True)


def main():
    print("📥 拉取 archive.org 元数据...")
    meta = fetch_archive_metadata()
    files = meta.get("files", [])
    print(f"   共 {len(files)} 个文件")

    ws, fu = collect_all_versions(files)
    print(f"   Workstation 独立版本: {len(ws)}")
    print(f"   Fusion 独立版本:      {len(fu)}")

    print()
    print("=" * 70)
    print("📊 Workstation Pro 前 20 版（按 build 降序）")
    print("=" * 70)
    for i, (v, info) in enumerate(sort_by_build_desc(ws)[:20], 1):
        plats = ",".join(sorted(info["downloads"].keys()))
        print(f"  {i:2d}. {v:12s} build={info['build']:>10} [{plats:15s}] files={len(info['files'])}")

    print()
    print("=" * 70)
    print("📊 Fusion Pro 前 20 版（按 build 降序）")
    print("=" * 70)
    for i, (v, info) in enumerate(sort_by_build_desc(fu)[:20], 1):
        plats = ",".join(sorted(info["downloads"].keys()))
        print(f"  {i:2d}. {v:12s} build={info['build']:>10} [{plats:15s}] files={len(info['files'])}")


if __name__ == "__main__":
    main()
