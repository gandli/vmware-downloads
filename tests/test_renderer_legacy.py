"""测试 renderer 对 legacy (archive.org) 版本的展示 — 📼 标记与 MD5 fallback"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vmware_lib.renderer import render_readme


def _make_broadcom_ws():
    return {
        "version": "17.6.4",
        "build": "24832109",
        "date": "2025-07-15",
        "source": "broadcom",
        "downloads": {
            "windows": {
                "filename": "VMware-workstation-full-17.6.4-24832109.exe",
                "url": "https://example.com/win.exe",
                "size": "405 MB",
                "sha256": "official_sha256_win",
            },
            "linux": {
                "filename": "VMware-Workstation-Full-17.6.4-24832109.x86_64.bundle",
                "url": "https://example.com/lin.bundle",
                "size": "339 MB",
                "sha256": "official_sha256_linux",
            },
        },
    }


def _make_archive_ws():
    return {
        "version": "17.5.1",
        "build": "23298084",
        "source": "archive.org",
        "downloads": {
            "windows": {
                "filename": "VMware-workstation-full-17.5.1-23298084.exe",
                "url": "https://archive.org/x.exe",
                "size": "594 MB",
                "md5": "archive_md5",
                "sha256": "",
                "sha256_verified": False,
            }
        },
    }


def test_broadcom_version_gets_check_mark():
    data = {"workstation_pro": [_make_broadcom_ws()], "fusion_pro": []}
    md = render_readme(data)
    # 官方 17.6.4 应有 ✅ 标记
    assert "| 17.6.4 |" in md
    ws_row = next(line for line in md.split("\n") if "| 17.6.4 |" in line)
    assert "✅" in ws_row


def test_archive_org_version_gets_tape_mark():
    """archive.org 版本必须显示 📼 而不是 ✅"""
    data = {"workstation_pro": [_make_archive_ws()], "fusion_pro": []}
    md = render_readme(data)
    row = next(line for line in md.split("\n") if "| 17.5.1 |" in line)
    assert "📼" in row
    assert "✅" not in row


def test_archive_version_shows_md5_only_when_no_sha256():
    """没 SHA256 时应显示 'MD5 only'"""
    data = {"workstation_pro": [_make_archive_ws()], "fusion_pro": []}
    md = render_readme(data)
    row = next(line for line in md.split("\n") if "| 17.5.1 |" in line)
    assert "MD5 only" in row


def test_legend_present_before_ws_table():
    """表格前应有 ✅/📼 图例说明"""
    data = {
        "workstation_pro": [_make_broadcom_ws(), _make_archive_ws()],
        "fusion_pro": [],
    }
    md = render_readme(data)
    assert "Broadcom 官方数据" in md
    assert "archive.org 历史存档" in md


def test_fusion_table_also_uses_flags():
    """Fusion 表格同样支持 ✅/📼"""
    data = {
        "workstation_pro": [],
        "fusion_pro": [
            {
                "version": "13.5.1",
                "build": "23298085",
                "source": "archive.org",
                "downloads": {
                    "macos": {
                        "filename": "F.dmg",
                        "url": "https://x.dmg",
                        "size": "692 MB",
                        "md5": "abc",
                        "sha256": "",
                    }
                },
            }
        ],
    }
    md = render_readme(data)
    row = next(line for line in md.split("\n") if "| 13.5.1 |" in line)
    assert "📼" in row


def test_backwards_compat_no_source_field_defaults_to_check():
    """老数据无 source 字段时（向后兼容），默认视为 Broadcom (✅)"""
    v = _make_broadcom_ws()
    v.pop("source")  # 无 source 字段
    data = {"workstation_pro": [v], "fusion_pro": []}
    md = render_readme(data)
    row = next(line for line in md.split("\n") if "| 17.6.4 |" in line)
    assert "✅" in row
    assert "📼" not in row
