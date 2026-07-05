"""测试 Broadcom + archive.org 融合逻辑"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vmware_lib.collector import (
    build_archive_filename_index,
    merge_broadcom_with_archive,
)


# archive.org fixture：两个 Workstation Windows 版本
ARCHIVE_METADATA = {
    "files": [
        {
            "name": "workstation/17.6.4/VMware-workstation-full-17.6.4-24832109.exe",
            "size": "425506000",
            "sha1": "aaaaaaaa1111111111111111111111111111aaaa",
            "md5": "b387e0a655798ba356d9a7331d98851a",  # 与 Broadcom 一致
        },
        {
            "name": "workstation/17.6.3/VMware-workstation-full-17.6.3-24583834.exe",
            "size": "420000000",
            "sha1": "bbbbbbbb2222222222222222222222222222bbbb",
            "md5": "ffffffffffffffffffffffffffffffff",  # 故意与 Broadcom 不一致
        },
        # 26H1 archive.org 没有（模拟太新未镜像）
    ]
}

# Broadcom fixture：3 条 Windows Workstation
BROADCOM_ENTRIES = {
    "workstation": [
        {
            "version": "26H1",
            "platform": "windows",
            "build": "25388281",
            "filename": "VMware-Workstation-Full-26H1-25388281.exe",
            "size": "274.34 MB",
            "sha256": "a" * 64,
            "md5": "a" * 32,
            "release_date": "2025-10-15",
            "last_updated": "2025-10-15",
        },
        {
            "version": "17.6.4",
            "platform": "windows",
            "build": "24832109",
            "filename": "VMware-workstation-full-17.6.4-24832109.exe",
            "size": "405.72 MB",
            "sha256": "10fe3a36f525d88aa133118ab3b5a16b18da88d4aa11b14d74e4164b3fb94ba9",
            "md5": "b387e0a655798ba356d9a7331d98851a",
            "release_date": "2025-07-15",
            "last_updated": "2025-07-09",
        },
        {
            "version": "17.6.3",
            "platform": "windows",
            "build": "24583834",
            "filename": "VMware-workstation-full-17.6.3-24583834.exe",
            "size": "401.43 MB",
            "sha256": "d7c04b4dd1e6bf5500000000000000000000000000000000000000deadbeef00",
            "md5": "de592b18a3950000000000000000ffff",
            "release_date": "2025-04-01",
            "last_updated": "2025-04-01",
        },
    ],
    "fusion": [],
}


# ---------- archive.org 索引 ----------


def test_index_has_two_files() -> None:
    idx = build_archive_filename_index(ARCHIVE_METADATA)
    assert len(idx) == 2


def test_index_lookup_case_insensitive() -> None:
    idx = build_archive_filename_index(ARCHIVE_METADATA)
    # 用不同大小写查
    assert "vmware-workstation-full-17.6.4-24832109.exe" in idx
    e = idx["vmware-workstation-full-17.6.4-24832109.exe"]
    assert e["url"].endswith(
        "VMware-workstation-full-17.6.4-24832109.exe"
    )
    assert e["sha1"] == "aaaaaaaa1111111111111111111111111111aaaa"


# ---------- 融合结果 ----------


def test_merge_gives_three_workstation_entries() -> None:
    idx = build_archive_filename_index(ARCHIVE_METADATA)
    merged = merge_broadcom_with_archive(BROADCOM_ENTRIES, idx)
    assert len(merged["workstation"]) == 3
    assert merged["fusion"] == []


def test_merge_sort_newest_first() -> None:
    idx = build_archive_filename_index(ARCHIVE_METADATA)
    merged = merge_broadcom_with_archive(BROADCOM_ENTRIES, idx)
    versions = [e["version"] for e in merged["workstation"]]
    assert versions == ["26H1", "17.6.4", "17.6.3"]


def test_26h1_is_broadcom_only() -> None:
    """26H1 archive.org 没镜像 → source=broadcom-only、url 为空"""
    idx = build_archive_filename_index(ARCHIVE_METADATA)
    merged = merge_broadcom_with_archive(BROADCOM_ENTRIES, idx)
    e26 = next(e for e in merged["workstation"] if e["version"] == "26H1")
    dl = e26["downloads"]["windows"]
    assert dl["source"] == "broadcom-only"
    assert dl["url"] == ""
    # SHA256 仍来自 Broadcom
    assert dl["sha256"] == "a" * 64


def test_17_6_4_is_dual_source() -> None:
    idx = build_archive_filename_index(ARCHIVE_METADATA)
    merged = merge_broadcom_with_archive(BROADCOM_ENTRIES, idx)
    e = next(x for x in merged["workstation"] if x["version"] == "17.6.4")
    dl = e["downloads"]["windows"]
    assert dl["source"] == "broadcom+archive"
    assert "archive.org/download" in dl["url"]
    assert dl["sha1"] == "aaaaaaaa1111111111111111111111111111aaaa"
    assert dl["sha256"] == "10fe3a36f525d88aa133118ab3b5a16b18da88d4aa11b14d74e4164b3fb94ba9"
    # MD5 一致 → 无 mismatch 字段
    assert "md5_mismatch" not in dl


def test_17_6_3_detects_md5_mismatch() -> None:
    """跨源校验：archive.org 的 MD5 与 Broadcom 不一致 → 标记 mismatch"""
    idx = build_archive_filename_index(ARCHIVE_METADATA)
    merged = merge_broadcom_with_archive(BROADCOM_ENTRIES, idx)
    e = next(x for x in merged["workstation"] if x["version"] == "17.6.3")
    dl = e["downloads"]["windows"]
    assert dl["source"] == "broadcom+archive"
    assert dl["md5"] == "de592b18a3950000000000000000ffff"
    assert dl["md5_mismatch"] == "ffffffffffffffffffffffffffffffff"


def test_release_date_carried_over() -> None:
    idx = build_archive_filename_index(ARCHIVE_METADATA)
    merged = merge_broadcom_with_archive(BROADCOM_ENTRIES, idx)
    e = next(x for x in merged["workstation"] if x["version"] == "17.6.4")
    assert e["date"] == "2025-07-15"
    assert e["last_updated"] == "2025-07-09"
    assert e["build"] == "24832109"


def test_empty_broadcom_gives_empty_result() -> None:
    idx = build_archive_filename_index(ARCHIVE_METADATA)
    merged = merge_broadcom_with_archive({"workstation": [], "fusion": []}, idx)
    assert merged == {"workstation": [], "fusion": []}
