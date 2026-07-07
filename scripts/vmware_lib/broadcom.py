"""Broadcom Support Portal 官方元数据数据源

从 fetch_broadcom.py 抓到的 broadcom_metadata.json 加载数据，
提供权威 SHA256/MD5/文件大小/发布日期，替代基于 archive.org 的推断。
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# 月份缩写 → 数字
_MONTHS = {
    m: i
    for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1
    )
}


@dataclass
class BroadcomFile:
    """单个可下载文件的官方元数据"""

    filename: str
    size: str
    build: str
    sha256: str
    md5: str
    release_date: str  # 原文，如 "Jul 15, 2025"
    last_updated: str


@dataclass
class BroadcomVersion:
    """一个 Broadcom 版本条目（包含 1~N 个文件；实际 VMware 一般 1 个）"""

    product: str  # "workstation" | "fusion"
    version: str  # "17.6.4" / "26H1" 等
    platform: str  # 从 display_group + filename 推断的 "windows" / "linux" / "macos"
    display_group: str
    service_pk: str
    files: list[BroadcomFile] = field(default_factory=list)


def infer_platform(display_group: str, filename: str) -> str:
    """从 display_group 和文件名推断平台"""
    dg_lower = display_group.lower()
    fn_lower = filename.lower()

    if "for windows" in dg_lower or fn_lower.endswith(".exe"):
        return "windows"
    if "for linux" in dg_lower or fn_lower.endswith(".bundle"):
        return "linux"
    if "fusion" in dg_lower or fn_lower.endswith(".dmg"):
        return "macos"
    return "unknown"


def parse_release_date(raw: str) -> str:
    """把 'Jul 15, 2025' 转成 '2025-07-15'。无法解析返回空串"""
    if not raw:
        return ""
    try:
        # datetime.strptime 兼容 %b (Jul) 但要小心 locale；直接手工解析更稳
        parts = raw.replace(",", "").split()
        if len(parts) != 3:
            return ""
        mon, day, year = parts
        month_num = _MONTHS.get(mon)
        if not month_num:
            return ""
        return f"{int(year):04d}-{month_num:02d}-{int(day):02d}"
    except (ValueError, KeyError):
        return ""


def load_broadcom_metadata(path: Path | str) -> list[BroadcomVersion]:
    """加载 broadcom_metadata.json 并转成结构化对象"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Broadcom metadata not found: {p}")

    data = json.loads(p.read_text(encoding="utf-8"))
    versions: list[BroadcomVersion] = []

    for entry in data.get("entries", []):
        product_raw = entry.get("subFamily", "")
        # 归一化 product
        if "Workstation" in product_raw:
            product = "workstation"
        elif "Fusion" in product_raw:
            product = "fusion"
        else:
            product = entry.get("product", "unknown")

        files = []
        for f in entry.get("files", []):
            files.append(
                BroadcomFile(
                    filename=f.get("filename", ""),
                    size=f.get("size", ""),
                    build=f.get("build", ""),
                    sha256=f.get("sha256", "").lower(),
                    md5=f.get("md5", "").lower(),
                    release_date=f.get("release_date", ""),
                    last_updated=f.get("last_updated", ""),
                )
            )

        # 平台从第一个文件推断（VMware 每版本一般只 1 个文件）
        first_fn = files[0].filename if files else ""
        platform = infer_platform(entry.get("displayGroup", ""), first_fn)

        versions.append(
            BroadcomVersion(
                product=product,
                version=entry.get("release", ""),
                platform=platform,
                display_group=entry.get("displayGroup", ""),
                service_pk=entry.get("servicePk", ""),
                files=files,
            )
        )

    return versions


def build_download_entries(
    versions: Iterable[BroadcomVersion],
    *,
    skip_incomplete: bool = True,
) -> dict[str, list[dict]]:
    """
    把结构化对象平铺成 {product: [entry, ...]}。

    每个 entry 是渲染器/collector 认识的 dict shape：
      {version, platform, build, filename, size,
       sha256, md5, release_date, last_updated}

    skip_incomplete=True 时跳过没有 SHA256 的条目
    （Broadcom 新版发布后几天才补 SHA，这段时间不给假数据）
    """
    result: dict[str, list[dict]] = {"workstation": [], "fusion": []}
    skipped_unknown = 0

    for v in versions:
        for f in v.files:
            if skip_incomplete and not f.sha256:
                continue
            if v.platform == "unknown":
                # 平台推断失败：display_group/文件名都识别不出来，跳过并告警
                # 避免下游 merge_broadcom_with_archive 把它放进 downloads["unknown"]
                # 静默丢失
                skipped_unknown += 1
                continue
            entry = {
                "version": v.version,
                "platform": v.platform,
                "build": f.build,
                "filename": f.filename,
                "size": f.size,
                "sha256": (f.sha256 or "").lower(),
                "md5": (f.md5 or "").lower(),
                "release_date": parse_release_date(f.release_date),
                "last_updated": parse_release_date(f.last_updated),
                "display_group": v.display_group,
                "service_pk": v.service_pk,
            }
            result.setdefault(v.product, []).append(entry)

    if skipped_unknown:
        logger.warning(
            "build_download_entries: 跳过 %d 个平台推断失败(unknown)的条目",
            skipped_unknown,
        )

    return result
