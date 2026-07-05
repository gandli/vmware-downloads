"""从 archive.org metadata API 收集所有 VMware 文件并分组"""

from __future__ import annotations

import json
import re
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from vmware_lib.parser import VMwareFile, parse_filename

ARCHIVE_COLLECTION = "vmwareworkstationarchive"
METADATA_URL = f"https://archive.org/metadata/{ARCHIVE_COLLECTION}"
DOWNLOAD_BASE = f"https://archive.org/download/{ARCHIVE_COLLECTION}"

# 只关注 Workstation 15+ 和 Fusion 12+（更早的 VMware 早已停维护）
MIN_WORKSTATION_MAJOR = 15
MIN_FUSION_MAJOR = 12


def build_download_url(path: str) -> str:
    """archive.org 相对路径 → 完整下载 URL"""
    return f"{DOWNLOAD_BASE}/{path}"


def _human_size(n: int) -> str:
    if n <= 0:
        return "N/A"
    return f"{n / 1024 / 1024:.1f} MB"


def _version_sort_key(v: str) -> tuple:
    """把版本号变成可比较的 tuple，越大越新"""
    # YYHN[uN] 格式：如 26H1, 25H2u1
    m = re.match(r"^(\d{2})H(\d)(?:u(\d))?$", v)
    if m:
        year, half, update = m.group(1), m.group(2), m.group(3) or "0"
        # 加个高偏移量保证 YYHN 在语义版本之上
        return (1, int(year), int(half), int(update))
    # 语义化版本
    parts = v.split(".")
    try:
        nums = tuple(int(x) for x in parts)
    except ValueError:
        nums = (0,)
    return (0,) + nums


def sort_versions(versions: list[str]) -> list[str]:
    """按新旧排序，最新在前"""
    return sorted(set(versions), key=_version_sort_key, reverse=True)


def group_files_by_version(files: list[VMwareFile]) -> dict[str, list[dict]]:
    """把扁平文件列表按 (product, version) 分组"""
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    build_map: dict[tuple[str, str], str] = {}
    date_map: dict[tuple[str, str], str] = {}

    for f in files:
        key = (f.product, f.version)
        if key not in buckets:
            buckets[key] = {}
            build_map[key] = f.build
        # 记录/更新 mtime → 日期（取最早的 mtime 作为发布日期）
        if f.mtime:
            try:
                ts = int(f.mtime)
                d = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
                if key not in date_map or d < date_map[key]:
                    date_map[key] = d
            except (ValueError, OSError):
                pass

        buckets[key][f.platform] = {
            "url": build_download_url(f.path),
            "filename": f.filename,
            "size": _human_size(f.size_bytes),
            "size_bytes": f.size_bytes,
            "sha1": f.sha1,
            "md5": f.md5,
        }

    # 按产品汇总
    grouped: dict[str, list[dict]] = defaultdict(list)
    for (product, version), downloads in buckets.items():
        grouped[product].append(
            {
                "version": version,
                "build": build_map[(product, version)],
                "date": date_map.get((product, version), ""),
                "downloads": downloads,
            }
        )

    # 每个产品内部按版本排序
    for _product, items in grouped.items():
        items.sort(key=lambda x: _version_sort_key(x["version"]), reverse=True)

    return grouped


def _passes_min_version(product: str, version: str) -> bool:
    """过滤掉太老的版本"""
    if re.match(r"^\d{2}H\d", version):
        return True  # 新命名规则都保留
    try:
        major = int(version.split(".")[0])
    except (ValueError, IndexError):
        return False
    if product == "workstation":
        return major >= MIN_WORKSTATION_MAJOR
    if product == "fusion":
        return major >= MIN_FUSION_MAJOR
    return False


def load_sha256_cache(path) -> dict[str, str]:
    """加载 SHA256 缓存：filename -> hash"""
    from pathlib import Path

    p = Path(path)
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_sha256_cache(path, cache: dict[str, str]) -> None:
    from pathlib import Path

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, sort_keys=True)


def merge_sha256(grouped: dict[str, list[dict]], cache: dict[str, str]) -> None:
    """把缓存的 SHA256 写入到分组结果中"""
    for _product, items in grouped.items():
        for item in items:
            for _plat, dl in item["downloads"].items():
                fn = dl["filename"]
                if fn in cache:
                    dl["sha256"] = cache[fn]


def fetch_metadata(url: str = METADATA_URL, timeout: int = 30) -> dict:
    """从 archive.org 拉取 metadata JSON"""
    req = urllib.request.Request(url, headers={"User-Agent": "vmware-downloads/2.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def collect_from_metadata(metadata: dict) -> dict[str, list[dict]]:
    """从 archive.org metadata 字典 → 分组后的下载信息"""
    parsed_files: list[VMwareFile] = []
    for file_info in metadata.get("files", []):
        name = file_info.get("name", "")
        f = parse_filename(name)
        if f is None:
            continue
        if not _passes_min_version(f.product, f.version):
            continue
        try:
            f.size_bytes = int(file_info.get("size", 0))
        except (ValueError, TypeError):
            f.size_bytes = 0
        f.sha1 = file_info.get("sha1", "")
        f.md5 = file_info.get("md5", "")
        f.mtime = file_info.get("mtime", "")
        parsed_files.append(f)
    return group_files_by_version(parsed_files)


def build_archive_filename_index(metadata: dict) -> dict[str, dict]:
    """
    从 archive.org metadata 建 filename → 下载信息索引，供 Broadcom
    融合时按官方 filename 直接查 archive.org 的可下载 URL。

    大小写不敏感的键便于跨源匹配（Broadcom 用 lowercase 'workstation'
    但 archive.org 用 'Workstation' 混写）。
    """
    index: dict[str, dict] = {}
    for file_info in metadata.get("files", []):
        name = file_info.get("name", "")
        if not name:
            continue
        # 只保留 VMware 安装包
        f = parse_filename(name)
        if f is None:
            continue
        try:
            size_bytes = int(file_info.get("size", 0))
        except (ValueError, TypeError):
            size_bytes = 0
        base = name.rsplit("/", 1)[-1]  # 去目录，只留 basename
        entry = {
            "url": build_download_url(name),
            "path": name,
            "size_bytes": size_bytes,
            "sha1": file_info.get("sha1", ""),
            "md5_archive": file_info.get("md5", ""),
            "mtime": file_info.get("mtime", ""),
        }
        index[base.lower()] = entry
    return index


def merge_broadcom_with_archive(
    broadcom_entries: dict[str, list[dict]],
    archive_index: dict[str, dict],
) -> dict[str, list[dict]]:
    """
    融合两个数据源，输出向下兼容 renderer 的 grouped 结构。

    Broadcom 为权威源，提供 SHA256/MD5/精确大小/发布日期；
    archive.org 通过 filename 匹配补下载 URL。找不到就标 broadcom-only。

    输出格式：
        {"workstation": [
            {
                version: "17.6.4",
                build: "24832109",
                date: "2025-07-15",         # Broadcom release_date
                last_updated: "2025-07-09",
                downloads: {
                    "windows": {
                        url: "https://archive.org/download/...", # 空则 broadcom-only
                        filename, size, sha256, md5, sha1,
                        source: "broadcom+archive" | "broadcom-only",
                    },
                    ...
                },
            }, ...
        ]}
    """
    result: dict[str, dict[tuple[str, str], dict]] = {"workstation": {}, "fusion": {}}

    for product, entries in broadcom_entries.items():
        for e in entries:
            version = e["version"]
            key = (product, version)
            bucket = result.setdefault(product, {}).setdefault(key, {
                "version": version,
                "build": e.get("build", ""),
                "date": e.get("release_date", ""),
                "last_updated": e.get("last_updated", ""),
                "downloads": {},
            })

            fname = e.get("filename", "")
            arch = archive_index.get(fname.lower())
            dl = {
                "filename": fname,
                "size": e.get("size", ""),
                "sha256": e.get("sha256", ""),
                "md5": e.get("md5", ""),
            }
            if arch:
                dl["url"] = arch["url"]
                dl["sha1"] = arch["sha1"]
                dl["source"] = "broadcom+archive"
                # 交叉校验 MD5（Broadcom 与 archive.org 都提供）
                if arch["md5_archive"] and e.get("md5") and arch["md5_archive"] != e["md5"]:
                    dl["md5_mismatch"] = arch["md5_archive"]
            else:
                dl["url"] = ""
                dl["sha1"] = ""
                dl["source"] = "broadcom-only"

            bucket["downloads"][e["platform"]] = dl

    # dict → list，并排序（最新在前）
    out: dict[str, list[dict]] = {}
    for product, items in result.items():
        entries_list = list(items.values())
        entries_list.sort(key=lambda x: _version_sort_key(x["version"]), reverse=True)
        out[product] = entries_list

    return out
