"""从 archive.org metadata API 收集 VMware 文件索引并与 Broadcom 权威源融合。

**主入口**：
- ``fetch_metadata()`` — 拉 archive.org metadata JSON
- ``build_archive_filename_index()`` — filename → archive URL/hash 索引
- ``merge_broadcom_with_archive()`` — 融合两源，输出 grouped 结构给 renderer

archive.org 侧的版本解析 / 排序辅助函数集中在 ``vmware_lib.archive_common``；
本模块只做「Broadcom 主 + archive 副」的融合逻辑，避免副本函数漂移。
"""

from __future__ import annotations

import json
import logging
import urllib.request

from vmware_lib.archive_common import version_sort_key
from vmware_lib.parser import parse_filename

logger = logging.getLogger(__name__)

ARCHIVE_COLLECTION = "vmwareworkstationarchive"
METADATA_URL = f"https://archive.org/metadata/{ARCHIVE_COLLECTION}"
DOWNLOAD_BASE = f"https://archive.org/download/{ARCHIVE_COLLECTION}"


def build_download_url(path: str) -> str:
    """archive.org 相对路径 → 完整下载 URL"""
    return f"{DOWNLOAD_BASE}/{path}"


def fetch_metadata(url: str = METADATA_URL, timeout: int = 30) -> dict:
    """从 archive.org 拉取 metadata JSON"""
    # audit v5 P1-C: archive.org 域硬编码非用户输入 · path traversal 不适用
    # 白名单断言防未来 URL 变量化时误开 file:// 等危险 scheme
    assert url.startswith(("https://archive.org/", "http://archive.org/")), (
        f"unexpected URL scheme: {url}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "vmware-downloads/2.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
        return json.load(r)


def build_archive_filename_index(metadata: dict) -> dict[str, dict]:
    """从 archive.org metadata 建 filename → 下载信息索引。

    供 Broadcom 融合时按官方 filename 直接查 archive.org 的可下载 URL 使用。
    键统一 lowercase，跨源匹配大小写不敏感。冲突时保留 size 更大的（多为完整包）。
    """
    index: dict[str, dict] = {}
    for file_info in metadata.get("files", []):
        name = file_info.get("name", "")
        if not name:
            continue
        # 只保留 VMware 安装包（parse_filename 已过滤 tools/ossp 等附件）
        f = parse_filename(name)
        if f is None:
            continue
        try:
            size_bytes = int(file_info.get("size", 0))
        except (ValueError, TypeError):
            size_bytes = 0
        base = name.rsplit("/", 1)[-1]
        key = base.lower()
        entry = {
            "url": build_download_url(name),
            "path": name,
            "size_bytes": size_bytes,
            "sha1": file_info.get("sha1", "").lower(),
            "md5_archive": file_info.get("md5", "").lower(),
            "mtime": file_info.get("mtime", ""),
        }
        if key in index:
            prev = index[key]
            if entry["size_bytes"] >= prev["size_bytes"]:
                logger.warning(
                    "archive basename 冲突: %s (取 size=%d 覆盖 size=%d)",
                    base,
                    entry["size_bytes"],
                    prev["size_bytes"],
                )
                index[key] = entry
            else:
                logger.warning(
                    "archive basename 冲突: %s (保留 size=%d 忽略 size=%d)",
                    base,
                    prev["size_bytes"],
                    entry["size_bytes"],
                )
        else:
            index[key] = entry
    return index


def merge_broadcom_with_archive(
    broadcom_entries: dict[str, list[dict]],
    archive_index: dict[str, dict],
) -> dict[str, list[dict]]:
    """融合两个数据源，输出向下兼容 renderer 的 grouped 结构。

    Broadcom 为权威源（提供 SHA256/MD5/精确大小/发布日期）；
    archive.org 通过 filename 匹配补下载 URL。找不到就标 broadcom-only。

    输出格式::

        {"workstation": [
            {
                version: "17.6.4",
                build: "24832109",
                date: "2025-07-15",
                last_updated: "2025-07-09",
                downloads: {
                    "windows": {
                        url, filename, size, sha256, md5, sha1,
                        source: "broadcom+archive" | "broadcom-only",
                        md5_mismatch: "..."  # 仅在 Broadcom / archive.org 双源 MD5 不一致时出现
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
            bucket = result.setdefault(product, {}).setdefault(
                key,
                {
                    "version": version,
                    "build": e.get("build", ""),
                    "date": e.get("release_date", ""),
                    "last_updated": e.get("last_updated", ""),
                    "downloads": {},
                },
            )

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
                # 交叉校验 MD5（供应链投毒检测）
                if (
                    arch["md5_archive"]
                    and e.get("md5")
                    and arch["md5_archive"] != e["md5"]
                ):
                    dl["md5_mismatch"] = arch["md5_archive"]
            else:
                dl["url"] = ""
                dl["sha1"] = ""
                dl["source"] = "broadcom-only"

            bucket["downloads"][e["platform"]] = dl

    # dict → list，按语义/年份混合版本降序
    out: dict[str, list[dict]] = {}
    for product, items in result.items():
        entries_list = list(items.values())
        entries_list.sort(key=lambda x: version_sort_key(x["version"]), reverse=True)
        out[product] = entries_list

    return out
