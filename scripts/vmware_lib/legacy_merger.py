"""archive.org 历史版本合并器

从 archive.org 抓取历史 VMware 安装包元数据，与 Broadcom 官方数据合并，
生成 legacy_versions.json（保留在 data/ 用于渲染）。

设计原则：
- Broadcom 官方版本优先（有 SHA256 + GA 日期）
- archive.org 补齐 Broadcom 未覆盖的老版本
- 老版本只有 MD5/SHA1，明确标记 sha256_verified=False
- 支持按目标版本数（TOP_N）截断
"""

from __future__ import annotations

import json
import re
import urllib.request
from collections import defaultdict
from typing import Any


ARCHIVE_META_URL = "https://archive.org/metadata/vmwareworkstationarchive"
ARCHIVE_DL_BASE = "https://archive.org/download/vmwareworkstationarchive/"


def is_installer(name: str) -> bool:
    """判断是否为 VMware 主安装包（排除 tools/ossp 等附件）"""
    lower = name.lower()
    if not (lower.endswith(".exe") or lower.endswith(".bundle") or lower.endswith(".dmg")):
        return False
    return not any(x in lower for x in ["tools", "ossp", "source", "guest"])


def parse_ws_version(name: str) -> tuple[str, str] | None:
    if "fusion" in name.lower():
        return None
    m = re.search(
        r"[Ww]orkstation.*?(\d+\.\d+\.\d+|\d+[Hh]\d+(?:u\d+)?)-(\d+)", name
    )
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


def human_size(n) -> str:
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


def parse_archive_files(files: list[dict]) -> tuple[dict, dict]:
    """将 archive.org files 数组解析为 {version: entry} 字典

    entry 结构与 vmware_downloads.json 兼容：
      {
        "version": "17.5.1",
        "build": "23298084",
        "downloads": {"windows": {...}, "linux": {...}},
        "source": "archive.org",
        "sha256_verified": False,
      }
    """
    ws: dict[str, dict] = defaultdict(
        lambda: {"downloads": {}, "source": "archive.org"}
    )
    fu: dict[str, dict] = defaultdict(
        lambda: {"downloads": {}, "source": "archive.org"}
    )

    for f in files:
        name = f.get("name", "")
        if not is_installer(name):
            continue

        size_bytes = int(f.get("size") or 0)
        entry = {
            "filename": name.rsplit("/", 1)[-1],
            "url": ARCHIVE_DL_BASE + name,
            "size": human_size(size_bytes),
            "size_bytes": size_bytes,
            "md5": f.get("md5", ""),
            "sha1": f.get("sha1", ""),
            "sha256": "",
            "sha256_verified": False,
        }
        platform = detect_platform(name)

        parsed_ws = parse_ws_version(name)
        if parsed_ws:
            ver, build = parsed_ws
            ws[ver]["version"] = ver
            ws[ver]["build"] = build
            ws[ver]["downloads"][platform] = entry
            continue

        parsed_fu = parse_fusion_version(name)
        if parsed_fu:
            ver, build = parsed_fu
            fu[ver]["version"] = ver
            fu[ver]["build"] = build
            fu[ver]["downloads"][platform] = entry

    return dict(ws), dict(fu)


def sort_by_build_desc(versions: dict) -> list[dict]:
    """按 build 号降序，转成 list"""
    def key(item: tuple[str, dict]):
        b = item[1].get("build", "")
        return int(b) if b.isdigit() else 0

    return [info for _, info in sorted(versions.items(), key=key, reverse=True)]


def merge_with_broadcom(
    broadcom_list: list[dict],
    archive_list: list[dict],
    top_n: int = 15,
) -> list[dict]:
    """把 Broadcom 官方版本与 archive.org 历史版本合并

    规则：
    1. Broadcom 版本优先（已在 broadcom_list），保留原始字段
    2. archive.org 独有的版本（按 build 号判定）追加到列表末尾
    3. 结果按 build 号降序排列
    4. 截断到 top_n
    """
    known_builds = {v.get("build", "") for v in broadcom_list if v.get("build")}

    merged = list(broadcom_list)  # 复制 Broadcom
    for arc_ver in archive_list:
        if arc_ver.get("build", "") not in known_builds:
            merged.append(arc_ver)

    # 按 build 降序（新在前）
    def sort_key(v):
        b = v.get("build", "")
        return int(b) if b.isdigit() else 0

    merged.sort(key=sort_key, reverse=True)
    return merged[:top_n]


def fetch_and_merge(
    broadcom_data: dict,
    top_n: int = 15,
    archive_meta: dict | None = None,
) -> dict:
    """把 archive.org 历史版本合并到 Broadcom 数据结构里

    输入：broadcom_data 结构（vmware_downloads.json 加载后）
    输出：新的合并后 dict，含更多历史版本

    可选传入 archive_meta 用于测试（避免真实网络）
    """
    if archive_meta is None:
        with urllib.request.urlopen(ARCHIVE_META_URL, timeout=30) as resp:
            archive_meta = json.loads(resp.read().decode("utf-8"))

    ws_arc, fu_arc = parse_archive_files(archive_meta.get("files", []))
    ws_arc_list = sort_by_build_desc(ws_arc)
    fu_arc_list = sort_by_build_desc(fu_arc)

    result = dict(broadcom_data)
    result["workstation_pro"] = merge_with_broadcom(
        broadcom_data.get("workstation_pro", []), ws_arc_list, top_n
    )
    result["fusion_pro"] = merge_with_broadcom(
        broadcom_data.get("fusion_pro", []), fu_arc_list, top_n
    )
    return result
