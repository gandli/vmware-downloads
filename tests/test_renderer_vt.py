"""测试 renderer._vt_badge - VirusTotal 徽章渲染"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vmware_lib.renderer import _vt_badge, render_readme


def test_badge_clean_shows_green_ratio():
    """clean 状态 → 🟢 harmless/total 洁净"""
    info = {
        "virustotal": {
            "status": "clean",
            "malicious": 0,
            "suspicious": 0,
            "harmless": 68,
            "undetected": 2,
            "vt_url": "https://www.virustotal.com/gui/file/abc",
        }
    }
    r = _vt_badge(info)
    assert "🟢" in r
    assert "68/70" in r
    assert "洁净" in r
    assert "https://www.virustotal.com/gui/file/abc" in r


def test_badge_malicious_shows_red_count():
    """malicious → 🔴 N 引擎报毒"""
    info = {
        "virustotal": {
            "status": "malicious",
            "malicious": 5,
            "harmless": 60,
            "undetected": 5,
            "vt_url": "https://vt.com/x",
        }
    }
    r = _vt_badge(info)
    assert "🔴" in r
    assert "5" in r
    assert "报毒" in r


def test_badge_suspicious_shows_yellow():
    """suspicious → 🟡"""
    info = {"virustotal": {"status": "suspicious", "suspicious": 2, "vt_url": "http://x"}}
    r = _vt_badge(info)
    assert "🟡" in r


def test_badge_unknown_shows_waiting():
    """unknown（VT 未见过）→ ⚪ VT 待扫"""
    info = {"virustotal": {"status": "unknown", "vt_url": "http://x"}}
    r = _vt_badge(info)
    assert "⚪" in r
    assert "待扫" in r


def test_badge_missing_virustotal_returns_empty():
    """无 virustotal 字段 → 空字符串（不破坏原有渲染）"""
    assert _vt_badge({"sha256": "abc"}) == ""
    assert _vt_badge({}) == ""
    assert _vt_badge(None) == ""


def test_badge_error_status_returns_empty():
    """error 状态 → 不渲染徽章（避免展示技术错误给用户）"""
    info = {"virustotal": {"status": "error", "error": "network"}}
    assert _vt_badge(info) == ""


def test_readme_shows_vt_badge_when_data_present():
    """render_readme：downloads 里有 virustotal 时，README 应包含徽章"""
    data = {
        "workstation_pro": [
            {
                "version": "26H1",
                "build": "25388281",
                "date": "2026-05-14",
                "downloads": {
                    "windows": {
                        "filename": "VMware-Workstation.exe",
                        "url": "https://archive.org/x",
                        "size": "274.34 MB",
                        "sha256": "a" * 64,
                        "virustotal": {
                            "status": "clean",
                            "harmless": 70,
                            "undetected": 0,
                            "malicious": 0,
                            "vt_url": "https://vt.com/a",
                        },
                    }
                },
            }
        ],
        "fusion_pro": [],
    }
    readme = render_readme(data)
    assert "🟢" in readme
    assert "70/70" in readme
    assert "洁净" in readme


def test_readme_omits_badge_when_no_vt_data():
    """render_readme：无 virustotal 字段时，README 不应出现徽章符号（向后兼容）"""
    data = {
        "workstation_pro": [
            {
                "version": "26H1",
                "build": "25388281",
                "date": "2026-05-14",
                "downloads": {
                    "windows": {
                        "filename": "VMware-Workstation.exe",
                        "url": "https://archive.org/x",
                        "size": "274.34 MB",
                        "sha256": "a" * 64,
                    }
                },
            }
        ],
        "fusion_pro": [],
    }
    readme = render_readme(data)
    # 无 VT 数据时不应出现任何 VT 徽章符号
    assert "🟢" not in readme
    assert "🔴" not in readme
    assert "🟡" not in readme
    assert "⚪" not in readme
