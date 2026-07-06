"""测试 legacy_merger 模块

注：is_installer / detect_platform / human_size / parse_ws_version /
parse_fusion_version 等公共辅助函数的测试见 test_archive_common.py。
这里只测 legacy_merger 自身的解析和合并逻辑。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# 从 archive_common 导入公共辅助（用于本文件里少量的兼容性测试）
from vmware_lib.archive_common import (
    detect_platform,
    human_size,
    is_installer,
    parse_fusion_version,
    parse_ws_version,
)
from vmware_lib.legacy_merger import (
    fetch_and_merge,
    merge_with_broadcom,
    parse_archive_files,
    sort_by_build_desc,
)


# =========================================================
# is_installer
# =========================================================

def test_installer_recognizes_exe_bundle_dmg():
    assert is_installer("VMware-workstation-full-17.5.1-23298084.exe")
    assert is_installer("VMware-Workstation-Full-17.5.2-23775571.x86_64.bundle")
    assert is_installer("VMware-Fusion-13.5.0-22583790_universal.dmg")


def test_installer_rejects_tools_and_ossp():
    assert not is_installer("VMware-tools-11.0.5-15389592.exe")
    assert not is_installer("VMware-OSSP-17.5.2-source.zip")
    assert not is_installer("guest-tools.iso")
    assert not is_installer("README.txt")


def test_installer_rejects_non_installer_extensions():
    assert not is_installer("VMware-workstation-17.txt")
    assert not is_installer("VMware-workstation-17.zip")


# =========================================================
# parse_ws_version / parse_fusion_version
# =========================================================

def test_parse_ws_version_semver():
    assert parse_ws_version("17.x/VMware-workstation-full-17.5.1-23298084.exe") == ("17.5.1", "23298084")


def test_parse_ws_version_channel_style():
    assert parse_ws_version("25H2/VMware-Workstation-Full-25H2u1-25219725.exe") == ("25H2u1", "25219725")
    assert parse_ws_version("26H1/VMware-Workstation-Full-26H1-25388281.exe") == ("26H1", "25388281")


def test_parse_ws_version_rejects_fusion_names():
    assert parse_ws_version("Fusion/13.x/VMware-Fusion-13.5.1-23298085_universal.dmg") is None


def test_parse_fusion_version_universal():
    assert parse_fusion_version("Fusion/13.x/VMware-Fusion-13.5.1-23298085_universal.dmg") == ("13.5.1", "23298085")


def test_parse_fusion_version_channel_style():
    assert parse_fusion_version("Fusion/26H1/VMware-Fusion-26H1-25388279_universal.dmg") == ("26H1", "25388279")


# =========================================================
# detect_platform
# =========================================================

def test_detect_platform_all_types():
    assert detect_platform("foo.exe") == "windows"
    assert detect_platform("foo.bundle") == "linux"
    assert detect_platform("foo.dmg") == "macos"
    assert detect_platform("foo.txt") == "unknown"


# =========================================================
# human_size
# =========================================================

def test_human_size_gb_mb_kb():
    assert human_size(2_147_483_648) == "2.00 GB"
    assert human_size(500 * 1024 * 1024) == "500.00 MB"
    assert human_size(500) == "500 B"
    assert human_size(0) == "0 B"  # 0 也是合法字节数（虽然实际不会出现）
    assert human_size(None) == ""  # 但 None 应保持空字符串
    assert human_size("bad") == ""


# =========================================================
# parse_archive_files
# =========================================================

def test_parse_archive_files_typical_structure():
    """典型 archive.org files 数组 → ws/fu 双字典"""
    fake_files = [
        {
            "name": "17.x/VMware-workstation-full-17.5.1-23298084.exe",
            "size": "623158248",
            "md5": "5151f645be318233abc",
            "sha1": "aaaaa" * 8,
        },
        {
            "name": "Fusion/13.x/VMware-Fusion-13.5.1-23298085_universal.dmg",
            "size": "725975073",
            "md5": "fusionmd5",
            "sha1": "fusionsha1",
        },
        {
            "name": "Not-a-vmware-file.zip",  # 应被过滤
            "size": "100",
        },
    ]
    ws, fu = parse_archive_files(fake_files)
    assert "17.5.1" in ws
    assert ws["17.5.1"]["build"] == "23298084"
    assert ws["17.5.1"]["downloads"]["windows"]["md5"] == "5151f645be318233abc"
    assert ws["17.5.1"]["downloads"]["windows"]["sha256"] == ""
    assert ws["17.5.1"]["downloads"]["windows"]["sha256_verified"] is False
    assert ws["17.5.1"]["source"] == "archive.org"

    assert "13.5.1" in fu
    assert fu["13.5.1"]["downloads"]["macos"]["md5"] == "fusionmd5"


def test_parse_archive_files_size_human_formatted():
    fake = [{"name": "17.x/VMware-workstation-full-17.5.1-23298084.exe", "size": str(500 * 1024 * 1024)}]
    ws, _ = parse_archive_files(fake)
    assert ws["17.5.1"]["downloads"]["windows"]["size"] == "500.00 MB"
    assert ws["17.5.1"]["downloads"]["windows"]["size_bytes"] == 500 * 1024 * 1024


def test_parse_archive_files_multiple_platforms_same_version():
    fake = [
        {"name": "17.x/VMware-workstation-full-17.5.2-23775571.exe", "size": "1000"},
        {"name": "Linux/17.x/VMware-Workstation-Full-17.5.2-23775571.x86_64.bundle", "size": "2000"},
    ]
    ws, _ = parse_archive_files(fake)
    assert "windows" in ws["17.5.2"]["downloads"]
    assert "linux" in ws["17.5.2"]["downloads"]
    assert ws["17.5.2"]["build"] == "23775571"


# =========================================================
# sort_by_build_desc
# =========================================================

def test_sort_by_build_desc():
    versions = {
        "17.0.0": {"build": "20800274"},
        "26H1": {"build": "25388281"},
        "17.5.1": {"build": "23298084"},
    }
    sorted_list = sort_by_build_desc(versions)
    assert sorted_list[0]["build"] == "25388281"  # 26H1
    assert sorted_list[1]["build"] == "23298084"  # 17.5.1
    assert sorted_list[2]["build"] == "20800274"  # 17.0.0


def test_sort_handles_non_numeric_build_safely():
    versions = {
        "a": {"build": "unknown"},
        "b": {"build": "100"},
    }
    r = sort_by_build_desc(versions)
    # 数字 build 排前，非数字回退到 0
    assert r[0]["build"] == "100"


# =========================================================
# merge_with_broadcom - 核心合并逻辑
# =========================================================

def test_merge_broadcom_takes_priority():
    """Broadcom 已有 build 号的版本，不会被 archive.org 版本覆盖"""
    broadcom = [
        {"version": "17.5.2", "build": "23775571", "downloads": {"windows": {"sha256": "abc"}}, "source": "broadcom"}
    ]
    archive = [
        {"version": "17.5.2", "build": "23775571", "downloads": {"windows": {"md5": "def"}}, "source": "archive.org"}
    ]
    r = merge_with_broadcom(broadcom, archive, top_n=15)
    # Broadcom 版本保留
    assert len(r) == 1
    assert r[0]["source"] == "broadcom"
    assert r[0]["downloads"]["windows"]["sha256"] == "abc"


def test_merge_appends_new_archive_versions():
    broadcom = [
        {"version": "26H1", "build": "25388281", "downloads": {"windows": {}}, "source": "broadcom"},
    ]
    archive = [
        {"version": "17.5.1", "build": "23298084", "downloads": {"windows": {}}, "source": "archive.org"},
        {"version": "17.5.0", "build": "22583795", "downloads": {"windows": {}}, "source": "archive.org"},
    ]
    r = merge_with_broadcom(broadcom, archive, top_n=15)
    assert len(r) == 3
    builds = [v["build"] for v in r]
    # 应按 build 降序
    assert builds == ["25388281", "23298084", "22583795"]


def test_merge_respects_top_n_cap():
    """top_n=3 时，最多返回 3 版"""
    broadcom = [{"version": f"v{i}", "build": str(30000 + i), "downloads": {}} for i in range(2)]
    archive = [{"version": f"a{i}", "build": str(10000 + i), "downloads": {}} for i in range(10)]
    r = merge_with_broadcom(broadcom, archive, top_n=3)
    assert len(r) == 3


def test_merge_preserves_broadcom_sha256_over_archive_md5():
    """核心保证：Broadcom 官方 SHA256 不会被 archive.org 只有 MD5 的版本覆盖"""
    broadcom = [
        {
            "version": "17.5.2",
            "build": "23775571",
            "downloads": {"windows": {"sha256": "OFFICIAL_SHA256", "md5": ""}},
            "source": "broadcom",
        }
    ]
    archive = [
        {
            "version": "17.5.2",
            "build": "23775571",
            "downloads": {"windows": {"sha256": "", "md5": "archive_md5", "sha256_verified": False}},
        }
    ]
    r = merge_with_broadcom(broadcom, archive)
    assert r[0]["downloads"]["windows"]["sha256"] == "OFFICIAL_SHA256"


# =========================================================
# fetch_and_merge - 顶层集成
# =========================================================

def test_fetch_and_merge_with_mock_meta():
    """用 mock 的 archive_meta 完整跑 fetch_and_merge"""
    broadcom = {
        "workstation_pro": [
            {"version": "26H1", "build": "25388281", "downloads": {"windows": {"sha256": "abc"}}, "source": "broadcom"}
        ],
        "fusion_pro": [
            {"version": "26H1", "build": "25388279", "downloads": {"macos": {"sha256": "def"}}, "source": "broadcom"}
        ],
    }
    mock_archive = {
        "files": [
            {"name": "17.x/VMware-workstation-full-17.5.1-23298084.exe", "size": "1000", "md5": "m1"},
            {"name": "17.x/VMware-workstation-full-17.5.0-22583795.exe", "size": "1000", "md5": "m2"},
            {"name": "Fusion/13.x/VMware-Fusion-13.5.1-23298085_universal.dmg", "size": "1000", "md5": "m3"},
        ]
    }
    r = fetch_and_merge(broadcom, top_n=15, archive_meta=mock_archive)
    # Workstation: 26H1 (broadcom) + 17.5.1 + 17.5.0
    assert len(r["workstation_pro"]) == 3
    assert r["workstation_pro"][0]["version"] == "26H1"
    assert r["workstation_pro"][0]["source"] == "broadcom"
    assert r["workstation_pro"][1]["version"] == "17.5.1"
    assert r["workstation_pro"][1]["source"] == "archive.org"
    # Fusion: 26H1 + 13.5.1
    assert len(r["fusion_pro"]) == 2
    assert r["fusion_pro"][0]["version"] == "26H1"


def test_fetch_and_merge_top_n_cap_respected():
    """top_n 限制生效"""
    broadcom = {"workstation_pro": [], "fusion_pro": []}
    mock_archive = {
        "files": [
            {"name": f"17.x/VMware-workstation-full-17.5.{i}-2329808{i}.exe", "size": "1000"}
            for i in range(20)
        ]
    }
    r = fetch_and_merge(broadcom, top_n=5, archive_meta=mock_archive)
    assert len(r["workstation_pro"]) == 5
