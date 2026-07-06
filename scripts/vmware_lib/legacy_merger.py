"""archive.org 历史版本合并器

从 archive.org 抓取历史 VMware 安装包元数据，与 Broadcom 官方数据合并，
生成扩展后的 vmware_downloads.json（含更多历史版本）。

设计原则：
- Broadcom 官方版本优先（有 SHA256 + GA 日期）
- archive.org 补齐 Broadcom 未覆盖的老版本
- 老版本只有 MD5/SHA1，明确标记 sha256_verified=False
- 支持按目标版本数（TOP_N）截断

公共辅助函数在 vmware_lib.archive_common 中，与 probe_archive_org.py 共享。
"""

from __future__ import annotations

import json
import urllib.request
from collections import defaultdict
from typing import Any

from vmware_lib.archive_common import (
    ARCHIVE_DL_BASE,
    ARCHIVE_META_URL,
    build_sort_key,
    version_sort_key,
    detect_platform,
    human_size,
    is_installer,
    parse_fusion_version,
    parse_ws_version,
    safe_size_int,
)


def parse_archive_files(files: list[dict]) -> tuple[dict, dict]:
    """将 archive.org files 数组解析为 {version: entry} 字典

    entry 结构与 vmware_downloads.json 兼容：
      {
        "version": "17.5.1",
        "build": "23298084",
        "downloads": {"windows": {..., "sha256_verified": False}, ...},
        "source": "archive.org",
      }

    注意：sha256_verified 位于每个平台的 downloads.* 条目内部，
    不在顶层版本对象上。
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

        size_bytes = safe_size_int(f.get("size"))
        entry = {
            "filename": name.rsplit("/", 1)[-1],
            "url": ARCHIVE_DL_BASE + name,
            "size": human_size(size_bytes) if size_bytes else "",
            "size_bytes": size_bytes,
            "md5": f.get("md5", ""),
            "sha1": f.get("sha1", ""),
            "sha256": "",
            "sha256_verified": False,
        }
        platform = detect_platform(name)
        # 跳过 unknown 平台（防止未预期的 dict 键）
        if platform == "unknown":
            continue

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


def _composite_sort_key(v: dict) -> tuple:
    """复合排序键：(语义版本, build 号) —— 降序时先按版本降,同版内按 build 降

    修复 v14 补丁 build 号大于 v15 早期版导致的交错混排问题
    """
    return (version_sort_key(v.get("version", "")), build_sort_key(v.get("build", "")))


def sort_by_build_desc(versions: dict) -> list[dict]:
    """按版本号降序（复合键：先语义版本，同版内按 build 号）

    v1.1 起：修复老版本 build 号交错混排 —— 用 (version, build) 复合键
    """
    return [
        info
        for _, info in sorted(
            versions.items(),
            key=lambda item: _composite_sort_key(item[1]),
            reverse=True,
        )
    ]


def merge_with_broadcom(
    broadcom_list: list[dict],
    archive_list: list[dict],
    top_n: int | None = 15,
) -> list[dict]:
    """把 Broadcom 官方版本与 archive.org 历史版本合并

    规则（review 修复后）：
    1. **Broadcom 版本全量保留**（有 SHA256 权威）
    2. archive.org 独有的版本（按 build 号去重）追加，直到达到 top_n
    3. 版本按 **(语义版本, build)** 复合键降序排列（最新在前）
    4. 若 Broadcom 版本数已 >= top_n，archive 一条也不追加，但 Broadcom 仍完整保留
    5. **top_n=None 表示无上限**：Broadcom 全保留 + archive 全并入
    """
    # 用 build 号去重 —— 已存在于 Broadcom 的版本不重复添加
    # 统一转字符串比较，防止 int 和 str build 号混杂时去重失败
    known_builds = {str(v["build"]) for v in broadcom_list if v.get("build")}

    # 计算 archive 追加名额
    if top_n is None:
        archive_slots = len(archive_list)  # 全量
    else:
        archive_slots = max(0, top_n - len(broadcom_list))

    # 过滤 archive_list：去重 + 排序（复合键降序），取前 archive_slots 个
    unique_archive = [
        v
        for v in archive_list
        if v.get("build") is not None and str(v["build"]) not in known_builds
    ]
    unique_archive.sort(key=_composite_sort_key, reverse=True)
    archive_picks = unique_archive[:archive_slots]

    # 合并：Broadcom 全量 + archive 追加，最后统一按 (version, build) 降序
    merged = list(broadcom_list) + archive_picks
    merged.sort(key=_composite_sort_key, reverse=True)
    return merged


def fetch_and_merge(
    broadcom_data: dict,
    top_n: int | None = 15,
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
