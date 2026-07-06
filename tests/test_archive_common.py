"""测试 archive_common — 公共辅助函数"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vmware_lib.archive_common import (
    build_sort_key,
    version_sort_key,
    detect_platform,
    human_size,
    is_installer,
    parse_fusion_version,
    parse_ws_version,
    safe_size_int,
)


# ==============================================================
# is_installer
# ==============================================================


def test_installer_recognizes_all_extensions():
    assert is_installer("VMware-workstation-full-17.5.1-23298084.exe")
    assert is_installer("VMware-Fusion-13.5.1-23298085_universal.dmg")
    assert is_installer("VMware-Workstation-Full-25H2-24995812.x86_64.bundle")


def test_installer_case_insensitive():
    """大写后缀也应被识别（.EXE / .DMG）"""
    assert is_installer("VMware-workstation-full-17.5.1-23298084.EXE")
    assert is_installer("VMware-Fusion-13.5.1-23298085.DMG")
    assert is_installer("VMware-workstation-full-25H2-24995812.x86_64.BUNDLE")


def test_installer_rejects_tools_and_ossp():
    assert not is_installer("VMware-tools-linux-11.3.5-18557794.iso")
    assert not is_installer("VMware-workstation-ossp-17.5.1.tar.gz")


# ==============================================================
# detect_platform — 大小写不敏感（review 建议）
# ==============================================================


def test_detect_platform_lowercase():
    assert detect_platform("x.exe") == "windows"
    assert detect_platform("y.bundle") == "linux"
    assert detect_platform("z.dmg") == "macos"


def test_detect_platform_uppercase():
    """大写后缀也要正确识别（防 .EXE / .DMG 漏识别）"""
    assert detect_platform("x.EXE") == "windows"
    assert detect_platform("y.BUNDLE") == "linux"
    assert detect_platform("z.DMG") == "macos"
    # 混合大小写
    assert detect_platform("VMware-Fusion.Dmg") == "macos"


def test_detect_platform_unknown():
    assert detect_platform("x.tar.gz") == "unknown"
    assert detect_platform("readme.txt") == "unknown"


# ==============================================================
# parse_ws_version / parse_fusion_version
# ==============================================================


def test_parse_ws_semver():
    assert parse_ws_version("VMware-workstation-full-17.5.1-23298084.exe") == (
        "17.5.1",
        "23298084",
    )


def test_parse_ws_channel_style():
    assert parse_ws_version("VMware-Workstation-Full-25H2u1-25219725.exe") == (
        "25H2u1",
        "25219725",
    )


def test_parse_ws_rejects_fusion():
    assert parse_ws_version("VMware-Fusion-13.5.1-23298085.dmg") is None


def test_parse_fusion_universal():
    assert parse_fusion_version(
        "VMware-Fusion-13.5.1-23298085_universal.dmg"
    ) == ("13.5.1", "23298085")


# ==============================================================
# human_size
# ==============================================================


def test_human_size_normal():
    assert human_size(2_147_483_648) == "2.00 GB"
    assert human_size(500 * 1024 * 1024) == "500.00 MB"
    assert human_size(500) == "500 B"


def test_human_size_zero():
    """0 是合法字节数，应显示 "0 B"（非空）"""
    assert human_size(0) == "0 B"


def test_human_size_invalid():
    """None 或非数字应返回空字符串"""
    assert human_size(None) == ""
    assert human_size("not-a-number") == ""


# ==============================================================
# build_sort_key — 处理 int/str/None 混杂（review 建议）
# ==============================================================


def test_build_sort_key_int():
    """int 类型 build 号直接返回"""
    assert build_sort_key(24832109) == 24832109


def test_build_sort_key_str_digit():
    """字符串数字 → int"""
    assert build_sort_key("24832109") == 24832109


def test_build_sort_key_non_digit_string():
    """非数字字符串 → 0（不 crash）"""
    assert build_sort_key("abc") == 0
    assert build_sort_key("") == 0


def test_build_sort_key_none():
    """None → 0（不 crash）"""
    assert build_sort_key(None) == 0


def test_build_sort_key_sort_stability():
    """混杂 int/str/None 排序应正常工作，不抛异常"""
    items = [
        {"build": 100},
        {"build": "200"},
        {"build": None},
        {"build": "abc"},
        {"build": 50},
    ]
    sorted_items = sorted(
        items, key=lambda v: build_sort_key(v.get("build", "")), reverse=True
    )
    builds = [v["build"] for v in sorted_items]
    assert builds[0] == "200"  # 最大在前
    assert builds[1] == 100


# ==============================================================
# safe_size_int — 处理 archive.org size 字段异常（review 建议）
# ==============================================================


def test_safe_size_int_normal():
    assert safe_size_int(1024) == 1024
    assert safe_size_int("1024") == 1024


def test_safe_size_int_edge_cases():
    """None / 空串 / 非数字 → 0（不 crash）"""
    assert safe_size_int(None) == 0
    assert safe_size_int("") == 0
    assert safe_size_int("not-a-number") == 0
    assert safe_size_int({}) == 0


# ==============================================================
# version_sort_key — 修复 v14/v15/v12 交错混排（本 PR 新增）
# ==============================================================


def test_version_sort_key_semver():
    """基础语义版本：17.6.4 > 17.6.0 > 17.5.2 > 15.5.7"""
    assert version_sort_key("17.6.4") == (17, 6, 4, 0)
    assert version_sort_key("17.6.0") == (17, 6, 0, 0)
    assert version_sort_key("15.5.7") == (15, 5, 7, 0)
    assert version_sort_key("3.0.0") == (3, 0, 0, 0)


def test_version_sort_key_two_segments():
    """两段语义版本（Broadcom 官方偶尔用）：17.6 → (17, 6, 0, 0)"""
    assert version_sort_key("17.6") == (17, 6, 0, 0)
    assert version_sort_key("13.6") == (13, 6, 0, 0)


def test_version_sort_key_year_naming():
    """年份命名（Broadcom 2025+ 新规则）：26H1 / 25H2u1 / 25H2

    年份视为 100+ 主版号 → 保证比任何 v17/v18/... 都新
    """
    assert version_sort_key("26H1") == (126, 1, 0, 0)
    assert version_sort_key("25H2") == (125, 2, 0, 0)
    assert version_sort_key("25H2u1") == (125, 2, 0, 1)
    # 大小写兼容
    assert version_sort_key("26h1") == (126, 1, 0, 0)


def test_version_sort_key_unknown_format():
    """未知格式 → (0,0,0,0),排到最后不 crash"""
    assert version_sort_key("weird-string") == (0, 0, 0, 0)
    assert version_sort_key("") == (0, 0, 0, 0)
    assert version_sort_key(None) == (0, 0, 0, 0)


def test_version_sort_key_desc_ordering():
    """整体降序排序：年份版 > v17 > v16 > ... > v3

    关键 bug 复现：老版本 build 号混乱不再影响顺序
    """
    versions = [
        "3.0.0",
        "14.1.8",  # build 号大于 15.5.0
        "15.0.0",
        "15.5.0",
        "15.5.7",
        "16.0.0",
        "16.1.0",
        "17.6.4",
        "25H2",
        "26H1",
    ]
    sorted_desc = sorted(versions, key=version_sort_key, reverse=True)
    assert sorted_desc == [
        "26H1",
        "25H2",
        "17.6.4",
        "16.1.0",
        "16.0.0",
        "15.5.7",
        "15.5.0",
        "15.0.0",
        "14.1.8",
        "3.0.0",
    ]
