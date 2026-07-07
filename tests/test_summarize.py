"""测试 summarize_changes.py 的 versions_map + sha256 对比 + 兜底逻辑"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from summarize_changes import format_changed, versions_map

# ============================================================
# versions_map: 现在返回 (build, sha256) tuple
# ============================================================

def test_versions_map_includes_sha256():
    """versions_map 应包含 sha256 用于对比"""
    data = {
        "workstation_pro": [
            {"version": "17.6.4", "build": "24832109", "sha256": "abc123"},
        ]
    }
    result = versions_map(data, "workstation_pro")
    assert result == {"17.6.4": ("24832109", "abc123")}


def test_versions_map_normalizes_sha256_to_lowercase():
    """sha256 归一化为小写，避免大小写误报"""
    data = {
        "workstation_pro": [
            {"version": "17.6.4", "build": "24832109", "sha256": "ABC123DEF"},
        ]
    }
    result = versions_map(data, "workstation_pro")
    assert result["17.6.4"][1] == "abc123def"


def test_versions_map_handles_missing_sha256():
    """sha256 缺失时返回空字符串，不 crash"""
    data = {
        "workstation_pro": [
            {"version": "17.6.4", "build": "24832109"},  # 无 sha256
        ]
    }
    result = versions_map(data, "workstation_pro")
    assert result["17.6.4"] == ("24832109", "")


def test_versions_map_fallback_to_downloads_dict_sha256():
    """downloads 是 {windows: {...}, linux: {...}} 时也能取到 sha256"""
    data = {
        "workstation_pro": [
            {
                "version": "17.6.4",
                "build": "24832109",
                "downloads": {
                    "windows": {"sha256": "deadbeef" * 8},
                    "linux": {"sha256": "cafebabe" * 8},
                },
            }
        ]
    }
    result = versions_map(data, "workstation_pro")
    # 取字典 values 迭代到的第一个非空 sha256（受 Python dict 顺序影响）
    assert result["17.6.4"][1] in ("deadbeef" * 8, "cafebabe" * 8)


def test_versions_map_fallback_to_downloads_sha256():
    """顶层无 sha256，去 downloads[].sha256 里找"""
    data = {
        "workstation_pro": [
            {
                "version": "17.6.4",
                "build": "24832109",
                "downloads": [{"sha256": "deadbeef" * 8}],
            }
        ]
    }
    result = versions_map(data, "workstation_pro")
    assert result["17.6.4"][1] == "deadbeef" * 8


def test_versions_map_returns_empty_for_missing_key():
    """产品线不存在时返回空 dict"""
    assert versions_map({}, "workstation_pro") == {}


# ============================================================
# sha256 变化必须被识别为 changed（供应链安全信号）
# ============================================================

def test_sha256_change_alone_triggers_changed():
    """build 不变但 sha256 变，必须归入 changed（安装包被替换的告警）"""
    old_data = {
        "workstation_pro": [
            {"version": "17.6.4", "build": "24832109", "sha256": "aaaa" * 16},
        ]
    }
    new_data = {
        "workstation_pro": [
            {"version": "17.6.4", "build": "24832109", "sha256": "bbbb" * 16},
        ]
    }
    old = versions_map(old_data, "workstation_pro")
    new = versions_map(new_data, "workstation_pro")

    changed = {v for v in old.keys() & new.keys() if old[v] != new[v]}
    assert "17.6.4" in changed, "sha256 变化应触发 changed 集合"


def test_build_change_also_triggers_changed():
    """build 变化的经典场景也要触发"""
    old_data = {
        "workstation_pro": [
            {"version": "17.6.4", "build": "24832109", "sha256": "aaaa"},
        ]
    }
    new_data = {
        "workstation_pro": [
            {"version": "17.6.4", "build": "24999999", "sha256": "aaaa"},
        ]
    }
    old = versions_map(old_data, "workstation_pro")
    new = versions_map(new_data, "workstation_pro")

    changed = {v for v in old.keys() & new.keys() if old[v] != new[v]}
    assert "17.6.4" in changed


def test_no_change_when_build_and_sha256_same():
    """完全一样时 changed 为空"""
    data = {
        "workstation_pro": [
            {"version": "17.6.4", "build": "24832109", "sha256": "aaaa" * 16},
        ]
    }
    old = versions_map(data, "workstation_pro")
    new = versions_map(data, "workstation_pro")

    changed = {v for v in old.keys() & new.keys() if old[v] != new[v]}
    assert changed == set()


# ============================================================
# format_changed: 展示逻辑同时体现 build/sha256
# ============================================================

def test_format_changed_shows_build_diff():
    line = format_changed("17.6.4", ("24832109", "aaaa"), ("24999999", "aaaa"))
    assert "24832109 → 24999999" in line
    assert "sha256" not in line  # sha 未变时不展示


def test_format_changed_shows_sha256_warning_only():
    """sha256 变化必须显示 ⚠️ 警告"""
    line = format_changed(
        "17.6.4",
        ("24832109", "a" * 64),
        ("24832109", "b" * 64),
    )
    assert "⚠️" in line
    assert "sha256" in line
    assert "aaaaaaaa" in line  # old prefix
    assert "bbbbbbbb" in line  # new prefix


def test_format_changed_shows_both():
    """build 和 sha256 都变时要同时展示"""
    line = format_changed(
        "17.6.4",
        ("24832109", "a" * 64),
        ("24999999", "b" * 64),
    )
    assert "24832109 → 24999999" in line
    assert "⚠️" in line
