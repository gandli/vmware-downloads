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


# ============================================================
# README 时间戳正则匹配（不依赖硬编码前缀）
# ============================================================

def test_readme_strip_regex_matches_various_prefixes():
    """正则应识别任意包含 YYYY-MM-DD HH:MM UTC 的行，不限前缀"""
    import re
    ts_line = re.compile(
        r"^.*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s*UTC.*$",
        re.MULTILINE,
    )

    # 三种前缀都应被清除
    text_zh = "最后更新: 2026-07-05 17:47 UTC\n真实内容"
    text_en = "Last updated: 2026-07-05 17:47 UTC\n真实内容"
    text_mixed = "更新时间：2026-07-05 17:47 UTC · 数据来源 Broadcom\n真实内容"

    for text in (text_zh, text_en, text_mixed):
        stripped = ts_line.sub("", text)
        assert "2026-07-05" not in stripped
        assert "真实内容" in stripped


def test_readme_strip_regex_ignores_dates_without_time():
    """只带日期无 UTC 时间戳的行不应被误删（保留发布日期等）"""
    import re
    ts_line = re.compile(
        r"^.*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s*UTC.*$",
        re.MULTILINE,
    )
    text = "Workstation Pro 17.6.4 发布于 2024-05-14\n最后更新: 2026-07-05 17:47 UTC"
    stripped = ts_line.sub("", text)
    assert "2024-05-14" in stripped  # 保留
    assert "17:47 UTC" not in stripped  # 清除


def test_last_analysis_date_is_stripped_as_noise():
    """VirusTotal 的 last_analysis_date 每次查询可能变化，应视为噪声"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from detect_data_changes import NOISE_FIELDS, strip_noise

    assert "last_analysis_date" in NOISE_FIELDS

    old = {
        "workstation_pro": [{
            "downloads": {
                "windows": {
                    "sha256": "a" * 64,
                    "virustotal": {
                        "status": "clean",
                        "harmless": 70,
                        "last_analysis_date": "2026-01-01T00:00:00+00:00",
                    }
                }
            }
        }]
    }
    new = {
        "workstation_pro": [{
            "downloads": {
                "windows": {
                    "sha256": "a" * 64,
                    "virustotal": {
                        "status": "clean",
                        "harmless": 70,
                        "last_analysis_date": "2026-07-05T18:00:00+00:00",
                    }
                }
            }
        }]
    }
    # strip 后应相等（因为只是时间戳差异）
    assert strip_noise(old) == strip_noise(new)


def test_vt_status_change_is_detected_as_real():
    """VT status 从 clean 变 malicious 必须被检测为真变化（供应链攻击信号）"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from detect_data_changes import strip_noise

    old = {"downloads": {"win": {"virustotal": {"status": "clean", "malicious": 0}}}}
    new = {"downloads": {"win": {"virustotal": {"status": "malicious", "malicious": 5}}}}
    assert strip_noise(old) != strip_noise(new)
