"""探测 archive.org 上 VMware Workstation / Fusion 的完整历史版本清单

用于调研目的：查看 archive.org 上有哪些历史版本可以补齐。
生产合并逻辑在 vmware_lib/legacy_merger.py，与本脚本共享 archive_common 辅助函数。

**audit v4 P1-A 豁免说明**：本脚本是纯调研 CLI 报告（人交互查看），
所有 print 均为格式化 report 输出（含表头、分隔线），不迁 stdlib logging。
详见 audit v4 报告 P1-A。
"""

from __future__ import annotations

import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

# 添加 scripts/ 到 sys.path 以便直接运行
sys.path.insert(0, str(Path(__file__).resolve().parent))

from vmware_lib.archive_common import (
    ARCHIVE_DL_BASE,
    ARCHIVE_META_TIMEOUT,
    ARCHIVE_META_URL,
    build_sort_key,
    detect_platform,
    human_size,
    is_installer,
    parse_fusion_version,
    parse_ws_version,
    safe_size_int,
)


def fetch_archive_metadata() -> dict:
    # audit v5 P1-C: archive.org 域硬编码 · nosec 显式豁免 Bandit B310
    with urllib.request.urlopen(  # nosec B310
        ARCHIVE_META_URL, timeout=ARCHIVE_META_TIMEOUT
    ) as resp:
        return json.loads(resp.read().decode("utf-8"))


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

        size_bytes = safe_size_int(f.get("size"))
        entry_data = {
            "filename": name.rsplit("/", 1)[-1],
            "url": ARCHIVE_DL_BASE + name,
            "size": human_size(size_bytes) if size_bytes else "",
            "size_bytes": size_bytes,
            "md5": f.get("md5", ""),
            "sha1": f.get("sha1", ""),
            "sha256": "",  # archive.org 只给 md5+sha1
            "sha256_verified": False,
        }
        platform = detect_platform(name)
        # unknown 平台跳过（防止未预期的 dict 键）
        if platform == "unknown":
            continue

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
    """按 build 号降序（最新在前），使用统一的 build_sort_key 处理各种类型"""
    return sorted(
        versions.items(),
        key=lambda item: build_sort_key(item[1].get("build", "")),
        reverse=True,
    )


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
