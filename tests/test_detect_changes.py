"""测试 detect_data_changes.py 剔除时间戳字段的对比逻辑"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from detect_data_changes import strip_noise


def test_strip_removes_collected_at():
    """collected_at 是纯时间戳，必须剔除"""
    d = {"collected_at": "2026-07-05T18:15:30", "total_entries": 27}
    assert strip_noise(d) == {"total_entries": 27}


def test_strip_removes_elapsed_sec():
    """elapsed_sec 每次运行都变，必须剔除"""
    d = {"elapsed_sec": 62.3, "total_entries": 27}
    assert strip_noise(d) == {"total_entries": 27}


def test_strip_removes_nested_noise():
    """嵌套结构中的时间戳也要剔除"""
    d = {
        "collected_at": "2026-07-05T18:15:30",
        "entries": [
            {"version": "17.6.4", "collected_at": "should-be-removed", "sha256": "abc"},
        ],
    }
    result = strip_noise(d)
    assert "collected_at" not in result
    assert "collected_at" not in result["entries"][0]
    assert result["entries"][0]["version"] == "17.6.4"
    assert result["entries"][0]["sha256"] == "abc"


def test_strip_keeps_real_data():
    """真实数据字段应保留"""
    d = {
        "collected_at": "2026-07-05",
        "elapsed_sec": 62.3,
        "total_entries": 27,
        "workstation_pro": [
            {"version": "17.6.4", "build": "24832109", "sha256": "abc123"},
        ],
    }
    result = strip_noise(d)
    assert result == {
        "total_entries": 27,
        "workstation_pro": [
            {"version": "17.6.4", "build": "24832109", "sha256": "abc123"},
        ],
    }


def test_only_timestamp_diff_is_no_real_change():
    """场景：两次抓取除时间戳外完全一样 → strip 后完全相等"""
    old = {
        "collected_at": "2026-07-05T17:47:54",
        "elapsed_sec": 61.3,
        "total_entries": 27,
        "workstation_pro": [{"version": "17.6.4", "sha256": "a" * 64}],
    }
    new = {
        "collected_at": "2026-07-05T18:15:30",  # 时间不同
        "elapsed_sec": 62.3,                    # 耗时不同
        "total_entries": 27,
        "workstation_pro": [{"version": "17.6.4", "sha256": "a" * 64}],
    }
    assert strip_noise(old) == strip_noise(new)


def test_real_data_change_is_detected():
    """场景：SHA256 变了（真实变化）→ strip 后仍不等"""
    old = {
        "collected_at": "2026-07-05T17:47:54",
        "workstation_pro": [{"version": "17.6.4", "sha256": "a" * 64}],
    }
    new = {
        "collected_at": "2026-07-05T18:15:30",
        "workstation_pro": [{"version": "17.6.4", "sha256": "b" * 64}],
    }
    assert strip_noise(old) != strip_noise(new)


def test_new_version_added_is_detected():
    """场景：新增版本 → strip 后仍不等"""
    old = {
        "collected_at": "2026-07-05T17:47:54",
        "workstation_pro": [{"version": "17.6.4", "sha256": "a" * 64}],
    }
    new = {
        "collected_at": "2026-07-05T18:15:30",
        "workstation_pro": [
            {"version": "17.6.4", "sha256": "a" * 64},
            {"version": "26H2", "sha256": "c" * 64},
        ],
    }
    assert strip_noise(old) != strip_noise(new)
