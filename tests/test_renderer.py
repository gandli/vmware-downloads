"""测试 README 渲染器"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vmware_lib.renderer import render_readme

SAMPLE_DATA = {
    "collected_at": "2026-07-06T00:00:00+00:00",
    "workstation_pro": [
        {
            "version": "26H1",
            "build": "25388281",
            "date": "2026-04-15",
            "downloads": {
                "windows": {
                    "url": "https://archive.org/download/vmwareworkstationarchive/26H1/VMware-Workstation-Full-26H1-25388281.exe",
                    "filename": "VMware-Workstation-Full-26H1-25388281.exe",
                    "size": "274.3 MB",
                    "sha1": "abc123",
                    "sha256": "a0ef9087607d9cad20b08139e73e41242e044ad5bd8cee141d3bad314586737f",
                },
                "linux": {
                    "url": "https://archive.org/download/vmwareworkstationarchive/Linux/26H1/VMware-Workstation-Full-26H1-25388281.x86_64.bundle",
                    "filename": "VMware-Workstation-Full-26H1-25388281.x86_64.bundle",
                    "size": "325.0 MB",
                    "sha1": "def456",
                    "sha256": "3f6d2501e654dbc7701a8290ff6ffcfba6c5444cd5f35f4933cd08c9499f6d84",
                },
            },
        }
    ],
    "fusion_pro": [
        {
            "version": "26H1",
            "build": "25388279",
            "date": "2026-04-15",
            "downloads": {
                "macos": {
                    "url": "https://archive.org/download/vmwareworkstationarchive/Fusion/26H1/VMware-Fusion-26H1-25388279_universal.dmg",
                    "filename": "VMware-Fusion-26H1-25388279_universal.dmg",
                    "size": "480.7 MB",
                    "sha1": "ghi789",
                    "sha256": "c1d373aa21be25674e3ecc518819e255785dea9d456d8747bcb0a2a59244bdf6",
                },
            },
        }
    ],
}


class TestRenderReadme:
    def test_contains_title(self):
        md = render_readme(SAMPLE_DATA)
        assert "# VMware 下载链接" in md

    def test_platform_display_is_pretty(self):
        """回归 bug: macos.title() = 'Macos' 是错的，应该是 macOS"""
        md = render_readme(SAMPLE_DATA)
        assert "macOS" in md
        assert "Macos" not in md
        assert "**Windows**" in md
        assert "**Linux**" in md

    def test_link_text_is_filename_not_url(self):
        """回归 bug: 老版本用完整 URL 做链接文本"""
        md = render_readme(SAMPLE_DATA)
        # 应该用文件名做 anchor
        assert "[VMware-Workstation-Full-26H1-25388281.exe]" in md
        # 不应该出现 [https://...](https://...) 这种冗余
        assert "[https://archive.org" not in md

    def test_has_full_sha256_in_table(self):
        md = render_readme(SAMPLE_DATA)
        assert "a0ef9087607d9cad20b08139e73e41242e044ad5bd8cee141d3bad314586737f" in md

    def test_workstation_and_fusion_sections(self):
        md = render_readme(SAMPLE_DATA)
        assert "VMware Workstation Pro" in md
        assert "VMware Fusion Pro" in md

    def test_no_utcnow_deprecation(self):
        """确保输出中的时间戳是 aware 的（+00:00 或 UTC 显示）"""
        md = render_readme(SAMPLE_DATA)
        assert "UTC" in md or "+00:00" in md


class TestRenderChecksums:
    def test_generates_checksums_txt(self):
        """checksums.txt 应可用 sha256sum -c 校验"""
        from vmware_lib.renderer import render_checksums

        txt = render_checksums(SAMPLE_DATA)
        # 格式: <hash>  <filename>
        assert (
            "a0ef9087607d9cad20b08139e73e41242e044ad5bd8cee141d3bad314586737f  VMware-Workstation-Full-26H1-25388281.exe"
            in txt
        )
        assert (
            "c1d373aa21be25674e3ecc518819e255785dea9d456d8747bcb0a2a59244bdf6  VMware-Fusion-26H1-25388279_universal.dmg"
            in txt
        )
