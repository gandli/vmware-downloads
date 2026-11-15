"""无人值守流水线的数据健康度判定。

背景：``data-update.yml`` 每周自动跑，没有人盯着。Broadcom Portal 偶尔某个
detail 页返回空 ``fileDetails``，archive.org metadata 偶尔返回不完整的文件列表，
都会让本次采集结果**少几条下载链接**。这种静默退化看起来和"正常更新"一样，
提交上去之后 README 的最新版就只剩一行纯文本（2026-11-01 的 26H1u1 Windows
条目、17.6 Linux 条目就是这样消失的）。

本模块只放纯函数，供两处复用：
- ``scripts/check_data_regression.py`` —— 提交前拦截（工作区 vs HEAD）
- ``scripts/fetch_broadcom.py`` —— 元数据落盘前拦截（新抓取 vs 上一次）

判定原则：**只拦"抓取抖动"，不拦"上游真的下架"**。Broadcom 会真的把老版本
从 Portal 撤下（这也是 legacy_merger 存在的理由），那属于正当收缩，必须放行。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

# 顶层产品分组（与 data/vmware_downloads.json 的 key 一致）
PRODUCT_GROUPS = ("workstation_pro", "fusion_pro")

# 分组名 → 展示用的短名（报告里给人看）
_GROUP_SHORT = {"workstation_pro": "workstation", "fusion_pro": "fusion"}


def _short(group: str) -> str:
    return _GROUP_SHORT.get(group, group)


def _url(dl: Mapping[str, Any]) -> str:
    return str(dl.get("url") or "").strip()


def inventory(data: Mapping[str, Any]) -> dict[tuple[str, str, str], Mapping[str, Any]]:
    """拍平成 {(产品, 版本, 平台): 下载条目}。

    用"条目集合"而不是"数量"做对比，才能发现"总数没变但某条链接丢了"
    （26H1u1 Windows 消失、17.6 Linux 消失都属于这种局部丢失）。
    """
    out: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for group in PRODUCT_GROUPS:
        for item in data.get(group) or []:
            version = str(item.get("version", ""))
            downloads = item.get("downloads") or {}
            for platform, dl in downloads.items():
                if isinstance(dl, Mapping):
                    out[(_short(group), version, str(platform))] = dl
    return out


def versions(data: Mapping[str, Any]) -> set[tuple[str, str]]:
    return {(product, ver) for product, ver, _plat in inventory(data)}


def label(key: tuple[str, str, str]) -> str:
    return f"{key[0]}/{key[1]}/{key[2]}"


def compare(
    old: Mapping[str, Any], new: Mapping[str, Any]
) -> dict[str, list[str]]:
    """对比两版下载清单。

    返回 ``lost`` / ``added`` / ``degraded`` 三个字符串列表：
    - lost：上一版有、本次没有的条目
    - added：本次新增的条目
    - degraded：条目还在，但原本可下载的直链变成了"需登录"
    """
    o = inventory(old)
    n = inventory(new)
    lost = sorted(label(k) for k in o.keys() - n.keys())
    added = sorted(label(k) for k in n.keys() - o.keys())
    degraded = sorted(
        label(k) for k in o.keys() & n.keys() if _url(o[k]) and not _url(n[k])
    )
    return {"lost": lost, "added": added, "degraded": degraded}


def regressions(old: Mapping[str, Any], new: Mapping[str, Any]) -> list[str]:
    """返回阻断性回归原因；空列表表示数据健康。

    注意：不比较 ``stats``（它是派生值，与条目对比重复）；
    也不比较 broadcom-only 数量的增加（archive.org 滞后属正常现象）。
    """
    diff = compare(old, new)
    reasons = [
        f"下载条目丢失：{item}（上一版有，本次没有）" for item in diff["lost"]
    ]
    reasons += [
        f"下载链接退化：{item}（原本可直接下载，现在需要登录）"
        for item in diff["degraded"]
    ]
    reasons += [
        f"版本整体消失：{product}/{version}" for product, version in sorted(
            versions(old) - versions(new)
        )
    ]
    return reasons


def metadata_file_counts(meta: Mapping[str, Any]) -> dict[tuple[str, str, str], int]:
    """Broadcom 元数据 → {(产品, release, displayGroup): 文件数}"""
    counts: dict[tuple[str, str, str], int] = {}
    for entry in meta.get("entries") or []:
        if not isinstance(entry, Mapping):
            continue
        key = (
            str(entry.get("product", "")),
            str(entry.get("release", "")),
            str(entry.get("displayGroup", "")),
        )
        counts[key] = counts.get(key, 0) + len(entry.get("files") or [])
    return counts


def metadata_regressions(
    old: Mapping[str, Any],
    new: Mapping[str, Any],
    *,
    missing_ratio: float = 0.3,
) -> list[str]:
    """判断新抓的 Broadcom 元数据是否可信。

    只拦「抓取抖动」，不拦「上游真的下架」：
    1. 某版本上次有 N 个文件、这次同版本只剩 M<N 个 —— detail 页抓空
       （2026-11-01 的事故就是这一种：entry 还在，files 变成空数组）
    2. 一次消失的版本数超过 ``missing_ratio``（且至少 2 个）—— 列表页可能整页
       没抓到。正常的零散下架（Broadcom 退老版本）远低于这个比例。
    """
    old_counts = metadata_file_counts(old)
    new_counts = metadata_file_counts(new)

    reasons = [
        f"版本文件数减少：{'/'.join(key)} "
        f"从 {old_counts[key]} 个降到 {new_counts[key]} 个（detail 页可能抓空）"
        for key in sorted(old_counts.keys() & new_counts.keys())
        if new_counts[key] < old_counts[key]
    ]

    missing = len(old_counts.keys() - new_counts.keys())
    threshold = max(2, int(len(old_counts) * missing_ratio))
    if missing > threshold:
        reasons.append(
            f"大面积版本消失：{len(old_counts)} → {len(new_counts)} 个版本"
            f"（消失 {missing} 个，超过阈值 {threshold}，疑似列表页抓取失败）"
        )
    return reasons
