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
        # 标题包含 "VMware" 和 "下载"（v2 优化后：🎯 VMware Workstation & Fusion 下载中心）
        first_line = md.split("\n")[0]
        assert first_line.startswith("# ")
        assert "VMware" in first_line
        assert "下载" in first_line

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

    def test_render_is_idempotent_with_collected_at(self):
        """回归 review: 数据 collected_at 相同时, render_readme 应完全幂等（不含 now()）

        月度 workflow 若在数据未变时也产生 diff, 会造成噪音 PR.
        """
        data = {
            **SAMPLE_DATA,
            "collected_at": "2026-06-15T10:30:00+00:00",
        }
        md1 = render_readme(data)
        md2 = render_readme(data)
        assert md1 == md2
        # Last sync 注脚来自 collected_at（抓取时间）
        assert "2026-06-15" in md1
        # 徽章日期使用最新版本发布日期（不是抓取时间戳），避免每天误刷"新"
        # SAMPLE_DATA 里最新版本 date = 2026-04-15
        assert "2026--04--15" in md1  # shields.io 双连字符

    def test_badge_date_uses_release_date_not_collected_at(self):
        """审计发现：徽章日期应反映数据本身新旧（版本发布日期），而不是抓取时间。

        抓取时间戳每天变，会让徽章看起来"总是最新的"，误导用户。
        """
        data = {
            **SAMPLE_DATA,
            # 抓取时间是"今天"，但最新版本 date 是 2026-04-15（几个月前）
            "collected_at": "2026-11-30T00:00:00+00:00",
        }
        md = render_readme(data)
        # 徽章仍应显示 2026-04-15（版本发布日期）
        assert "2026--04--15" in md
        # 抓取时间戳不该出现在徽章
        assert "2026--11--30" not in md


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


class TestBroadcomOnlyRendering:
    """回归 CodeRabbit review：archive.org 未镜像时 url='' 会渲染出空链接 [filename]()"""

    BROADCOM_ONLY_DATA = {
        "collected_at": "2026-07-06T00:00:00+00:00",
        "workstation_pro": [
            {
                "version": "26H2",
                "build": "99999999",
                "date": "2026-10-01",
                "downloads": {
                    "windows": {
                        "url": "",  # ← archive.org 还没镜像
                        "filename": "VMware-Workstation-Full-26H2-99999999.exe",
                        "size": "280.5 MB",
                        "sha256": "d" * 64,
                        "source": "broadcom-only",
                    },
                },
            }
        ],
        "fusion_pro": [
            {
                "version": "26H2",
                "build": "99999998",
                "date": "2026-10-01",
                "downloads": {
                    "macos": {
                        "url": "",
                        "filename": "VMware-Fusion-26H2-99999998_universal.dmg",
                        "size": "485.0 MB",
                        "sha256": "e" * 64,
                        "source": "broadcom-only",
                    },
                },
            }
        ],
    }

    def test_no_empty_markdown_link_in_readme(self):
        """不能出现 [xxx]() 空 href 链接"""
        md = render_readme(self.BROADCOM_ONLY_DATA)
        # 不应该有任何空 href 的 markdown 链接：]() 是明确信号
        assert "]()" not in md, "broadcom-only 条目渲染出空链接"

    def test_filename_still_visible_when_url_empty(self):
        """即便无 URL，文件名仍需显示，让用户知道有这个版本"""
        md = render_readme(self.BROADCOM_ONLY_DATA)
        assert "VMware-Workstation-Full-26H2-99999999.exe" in md
        assert "VMware-Fusion-26H2-99999998_universal.dmg" in md

    def test_broadcom_only_hint_shown(self):
        """应给出明确提示：仅 Broadcom 有 / 需登录官方"""
        md = render_readme(self.BROADCOM_ONLY_DATA)
        # 快速下载区块或表格里，其中之一应包含 Broadcom 关键词
        assert "Broadcom" in md
