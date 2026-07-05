"""测试 Broadcom 数据源到内部模型的转换"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest
from vmware_lib.broadcom import (
    BroadcomFile,
    BroadcomVersion,
    build_download_entries,
    load_broadcom_metadata,
    parse_release_date,
)

FIXTURE = {
    "collected_at": "2026-07-06T00:59:00+00:00",
    "source": "Broadcom Support Portal (support.broadcom.com)",
    "total_entries": 2,
    "total_files": 2,
    "entries": [
        {
            "product": "workstation",
            "subFamily": "VMware Workstation Pro",
            "displayGroup": "VMware Workstation Pro 17.0 for Windows",
            "release": "17.6.4",
            "servicePk": "533272",
            "path": "/group/ecx/productfiles?...",
            "full_url": "https://support.broadcom.com/group/ecx/productfiles?...",
            "files": [
                {
                    "filename": "VMware-workstation-full-17.6.4-24832109.exe",
                    "size": "405.72 MB",
                    "build": "24832109",
                    "sha256": "10fe3a36f525d88aa133118ab3b5a16b18da88d4aa11b14d74e4164b3fb94ba9",
                    "md5": "b387e0a655798ba356d9a7331d98851a",
                    "release_date": "Jul 15, 2025",
                    "last_updated": "Jul 09, 2025",
                }
            ],
        },
        {
            "product": "fusion",
            "subFamily": "VMware Fusion",
            "displayGroup": "VMware Fusion 13",
            "release": "13.6.4",
            "servicePk": "533271",
            "path": "/group/ecx/productfiles?...",
            "full_url": "https://support.broadcom.com/...",
            "files": [
                {
                    "filename": "VMware-Fusion-13.6.4-24832108_universal.dmg",
                    "size": "530.91 MB",
                    "build": "24832108",
                    "sha256": "a43fd031165896bc0000000000000000000000000000000000000000deadbeef",
                    "md5": "e8c0ede515460000000000000000ffff",
                    "release_date": "Jul 15, 2025",
                    "last_updated": "Jul 09, 2025",
                }
            ],
        },
    ],
}


def _write_fixture(tmp_path: Path) -> Path:
    p = tmp_path / "broadcom_metadata.json"
    p.write_text(json.dumps(FIXTURE), encoding="utf-8")
    return p


# ---------- 加载/结构 ----------


def test_load_returns_two_versions(tmp_path: Path) -> None:
    metadata = load_broadcom_metadata(_write_fixture(tmp_path))
    assert len(metadata) == 2


def test_first_version_is_workstation_17_6_4(tmp_path: Path) -> None:
    metadata = load_broadcom_metadata(_write_fixture(tmp_path))
    v = metadata[0]
    assert isinstance(v, BroadcomVersion)
    assert v.product == "workstation"
    assert v.version == "17.6.4"
    assert v.platform == "windows"
    assert v.display_group == "VMware Workstation Pro 17.0 for Windows"


def test_workstation_file_has_official_sha256(tmp_path: Path) -> None:
    metadata = load_broadcom_metadata(_write_fixture(tmp_path))
    f = metadata[0].files[0]
    assert isinstance(f, BroadcomFile)
    assert f.filename == "VMware-workstation-full-17.6.4-24832109.exe"
    assert f.sha256 == "10fe3a36f525d88aa133118ab3b5a16b18da88d4aa11b14d74e4164b3fb94ba9"
    assert f.md5 == "b387e0a655798ba356d9a7331d98851a"
    assert f.build == "24832109"
    assert f.size == "405.72 MB"


# ---------- 平台推断 ----------


def test_platform_windows_from_display_group() -> None:
    from vmware_lib.broadcom import infer_platform

    assert infer_platform("VMware Workstation Pro 17.0 for Windows", "x.exe") == "windows"


def test_platform_linux_from_display_group() -> None:
    from vmware_lib.broadcom import infer_platform

    assert infer_platform("VMware Workstation Pro 17.0 for Linux", "x.bundle") == "linux"


def test_platform_macos_from_dmg() -> None:
    from vmware_lib.broadcom import infer_platform

    assert infer_platform("VMware Fusion 13", "x.dmg") == "macos"


def test_platform_windows_from_exe_when_group_ambiguous() -> None:
    from vmware_lib.broadcom import infer_platform

    assert infer_platform("VMware Workstation Pro 25H2", "x.exe") == "windows"


def test_platform_linux_from_bundle_when_group_ambiguous() -> None:
    from vmware_lib.broadcom import infer_platform

    assert infer_platform("Some Group", "x.x86_64.bundle") == "linux"


# ---------- 日期解析 ----------


def test_parse_release_date_iso_format() -> None:
    assert parse_release_date("Jul 15, 2025") == "2025-07-15"


def test_parse_release_date_single_digit_day() -> None:
    assert parse_release_date("Jul 9, 2025") == "2025-07-09"


def test_parse_release_date_returns_empty_for_unknown() -> None:
    assert parse_release_date("") == ""
    assert parse_release_date("garbage") == ""


# ---------- 转换到 DownloadEntry ----------


def test_build_download_entries_shape(tmp_path: Path) -> None:
    metadata = load_broadcom_metadata(_write_fixture(tmp_path))
    entries = build_download_entries(metadata)
    assert isinstance(entries, dict)
    assert "workstation" in entries
    assert "fusion" in entries


def test_workstation_entry_has_official_metadata(tmp_path: Path) -> None:
    metadata = load_broadcom_metadata(_write_fixture(tmp_path))
    entries = build_download_entries(metadata)
    ws_entries = entries["workstation"]
    assert len(ws_entries) == 1
    e = ws_entries[0]
    assert e["version"] == "17.6.4"
    assert e["platform"] == "windows"
    assert e["build"] == "24832109"
    assert e["sha256"] == "10fe3a36f525d88aa133118ab3b5a16b18da88d4aa11b14d74e4164b3fb94ba9"
    assert e["md5"] == "b387e0a655798ba356d9a7331d98851a"
    assert e["size"] == "405.72 MB"
    assert e["release_date"] == "2025-07-15"
    assert e["last_updated"] == "2025-07-09"
    assert e["filename"] == "VMware-workstation-full-17.6.4-24832109.exe"


def test_fusion_entry_is_macos(tmp_path: Path) -> None:
    metadata = load_broadcom_metadata(_write_fixture(tmp_path))
    entries = build_download_entries(metadata)
    f = entries["fusion"][0]
    assert f["platform"] == "macos"
    assert f["version"] == "13.6.4"


# ---------- 错误处理 ----------


def test_load_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_broadcom_metadata(tmp_path / "nope.json")


def test_skip_files_without_sha256(tmp_path: Path) -> None:
    """暂无 SHA256（新版刚发布还没补）应该跳过而非报错"""
    fixture = dict(FIXTURE)
    fixture["entries"] = [dict(FIXTURE["entries"][0])]
    fixture["entries"][0]["files"] = [
        {
            "filename": "VMware-Test-9.9.9.exe",
            "size": "",
            "build": "",
            "sha256": "",
            "md5": "",
            "release_date": "",
            "last_updated": "",
        }
    ]
    p = tmp_path / "empty.json"
    p.write_text(json.dumps(fixture), encoding="utf-8")
    metadata = load_broadcom_metadata(p)
    entries = build_download_entries(metadata, skip_incomplete=True)
    assert entries["workstation"] == []


def test_keep_files_without_sha256_when_not_skipping(tmp_path: Path) -> None:
    """skip_incomplete=False 时保留 SHA256 空的条目，结构完整且哈希字段为空串"""
    fixture = dict(FIXTURE)
    fixture["entries"] = [dict(FIXTURE["entries"][0])]
    fixture["entries"][0]["files"] = [
        {
            "filename": "VMware-Test-9.9.9.exe",
            "size": "100 MB",
            "build": "12345",
            "sha256": "",
            "md5": "",
            "release_date": "Jan 1, 2030",
            "last_updated": "",
        }
    ]
    p = tmp_path / "incomplete.json"
    p.write_text(json.dumps(fixture), encoding="utf-8")
    metadata = load_broadcom_metadata(p)
    entries = build_download_entries(metadata, skip_incomplete=False)

    # 条目应被保留
    assert len(entries["workstation"]) == 1
    e = entries["workstation"][0]

    # 哈希字段应为空串（而非 None / 缺 key）
    assert e["sha256"] == ""
    assert e["md5"] == ""

    # 其余元数据仍需正确
    assert e["filename"] == "VMware-Test-9.9.9.exe"
    assert e["size"] == "100 MB"
    assert e["build"] == "12345"
    assert e["release_date"] == "2030-01-01"


def test_skip_unknown_platform_entries(tmp_path: Path) -> None:
    """平台推断失败（unknown）的条目应被静默跳过，避免污染 downloads['unknown']"""
    fixture = {
        "collected_at": "2026-07-06T00:00:00+00:00",
        "entries": [
            {
                "product": "workstation",
                "subFamily": "Mystery Product",
                "displayGroup": "Mystery Group",
                "release": "1.0",
                "servicePk": "999",
                "files": [
                    {
                        "filename": "some-weird-package.tar",  # 非 exe/bundle/dmg
                        "size": "1 MB",
                        "build": "1",
                        "sha256": "a" * 64,  # 有 SHA256 但平台推断不出
                        "md5": "b" * 32,
                        "release_date": "Jan 1, 2026",
                        "last_updated": "Jan 1, 2026",
                    }
                ],
            }
        ],
    }
    p = tmp_path / "unknown.json"
    p.write_text(json.dumps(fixture), encoding="utf-8")
    metadata = load_broadcom_metadata(p)
    entries = build_download_entries(metadata, skip_incomplete=True)

    # 应该被跳过，不会出现在任何产品下
    assert entries.get("workstation") == []
    assert entries.get("fusion") == []
    assert "unknown" not in entries  # 也不该单开 unknown key


def test_hashes_normalized_to_lowercase(tmp_path: Path) -> None:
    """跨源对比需要哈希小写归一化，避免大小写不同触发误报 md5_mismatch"""
    fixture = dict(FIXTURE)
    fixture["entries"] = [dict(FIXTURE["entries"][0])]
    fixture["entries"][0]["files"] = [
        {
            "filename": "VMware-Uppercase.exe",
            "size": "1 MB",
            "build": "1",
            "sha256": "ABCDEF" + "0" * 58,  # 大写 SHA256
            "md5": "AABBCC" + "0" * 26,      # 大写 MD5
            "release_date": "Jan 1, 2026",
            "last_updated": "",
        }
    ]
    p = tmp_path / "upper.json"
    p.write_text(json.dumps(fixture), encoding="utf-8")
    metadata = load_broadcom_metadata(p)
    entries = build_download_entries(metadata, skip_incomplete=True)

    assert len(entries["workstation"]) == 1
    e = entries["workstation"][0]
    assert e["sha256"] == "abcdef" + "0" * 58  # 全小写
    assert e["md5"] == "aabbcc" + "0" * 26
