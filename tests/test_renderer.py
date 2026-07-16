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
        # 标题含 VMware icon SVG + "VMware" + "下载"（v6：🎯 emoji 换成 vmware-icon.svg）
        first_line = md.split("\n")[0]
        assert first_line.startswith("# ")
        assert "VMware" in first_line
        assert "下载" in first_line
        assert "vmware-icon.svg" in first_line

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


# audit v5 · P1-B · renderer.py L60/L74-75 覆盖
def test_download_cell_broadcom_only_no_size() -> None:
    """broadcom-only 且 size 为空 → 返回 '仅 Broadcom' 不带 size"""
    from vmware_lib.renderer import _download_cell

    # size 空，走 L56 else 分支
    result = _download_cell({"filename": "x.exe", "url": "", "size": ""})
    assert result == "仅 Broadcom"


def test_data_time_missing_collected_at() -> None:
    """collected_at 缺失 → 回落到当前时间（走 L74-75 return datetime.now）"""
    from datetime import datetime, timezone

    from vmware_lib.renderer import _data_time

    result = _data_time({})  # 无 collected_at 键
    assert isinstance(result, datetime)
    # 允许 2 秒漂移
    delta = abs((result - datetime.now(timezone.utc)).total_seconds())
    assert delta < 2


def test_data_time_invalid_iso_falls_back() -> None:
    """collected_at 是非法 ISO 字符串 → 走 except 后回落到 now"""
    from datetime import datetime, timezone

    from vmware_lib.renderer import _data_time

    result = _data_time({"collected_at": "not-an-iso-date"})
    assert isinstance(result, datetime)
    delta = abs((result - datetime.now(timezone.utc)).total_seconds())
    assert delta < 2


def test_now_utc_str_returns_valid_iso_format() -> None:
    """_now_utc_str 覆盖 L60 · 直接调用验证返回格式"""
    import re

    from vmware_lib.renderer import _now_utc_str

    result = _now_utc_str()
    # 格式：YYYY-MM-DD HH:MM UTC
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC$", result)


# ============ SHA1 兜底显示 ============

SAMPLE_DATA_ARCHIVE_ONLY = {
    "collected_at": "2026-07-06T00:00:00+00:00",
    "workstation_pro": [
        {
            "version": "17.5.1",
            "build": "23298084",
            "date": "2024-03-05",
            "source": "archive.org",
            "downloads": {
                "windows": {
                    "url": "https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.5.1-23298084.exe",
                    "filename": "VMware-workstation-full-17.5.1-23298084.exe",
                    "size": "594.29 MB",
                    "md5": "5151f645be318233e20e2b52c329b529",
                    "sha1": "1118f68f6316a0ec573c55e77f5bf1e355db1e6a",
                    "sha256": "",  # archive.org 未镜像
                    "sha256_verified": False,
                }
            },
        }
    ],
    "fusion_pro": [
        {
            "version": "13.5.2",
            "build": "23775688",
            "date": "2024-02-27",
            "source": "archive.org",
            "downloads": {
                "macos": {
                    "url": "https://archive.org/download/vmwareworkstationarchive/Fusion/VMware-Fusion-13.5.2-23775688_universal.dmg",
                    "filename": "VMware-Fusion-13.5.2-23775688_universal.dmg",
                    "size": "603.11 MB",
                    "md5": "abc123",
                    "sha1": "7bda2af8ec456c2f3f2e9e8fd12ffdad39e0f8ff",
                    "sha256": "",
                    "sha256_verified": False,
                }
            },
        }
    ],
}


def test_render_sha1_checksums_returns_sha1_format() -> None:
    """新函数 render_sha1_checksums：sha1sum -c 兼容"""
    from vmware_lib.renderer import render_sha1_checksums

    txt = render_sha1_checksums(SAMPLE_DATA_ARCHIVE_ONLY)
    # 每行「sha1  filename」格式
    assert "1118f68f6316a0ec573c55e77f5bf1e355db1e6a  VMware-workstation-full-17.5.1-23298084.exe" in txt
    assert "7bda2af8ec456c2f3f2e9e8fd12ffdad39e0f8ff  VMware-Fusion-13.5.2-23775688_universal.dmg" in txt


def test_render_sha1_checksums_skips_empty_sha1() -> None:
    """无 sha1 的条目不产出（比如 Broadcom 主线只有 sha256）"""
    from vmware_lib.renderer import render_sha1_checksums

    txt = render_sha1_checksums(SAMPLE_DATA)  # 上面 SAMPLE_DATA 全是 abc123/def456 短假 sha1
    # SAMPLE_DATA 里 sha1 是 abc123 等（虽然假但非空），应产出
    lines = [ln for ln in txt.strip().split("\n") if ln]
    assert len(lines) == 3  # win + linux + macos
    assert all("  " in ln for ln in lines)


def test_render_sha1_checksums_skips_when_no_sha1_field() -> None:
    """条目没有 sha1 字段时应跳过而非崩溃"""
    from vmware_lib.renderer import render_sha1_checksums

    data = {"workstation_pro": [{"version": "x", "build": "1", "downloads": {"windows": {"filename": "a.exe", "sha256": "x"}}}], "fusion_pro": []}
    txt = render_sha1_checksums(data)
    assert txt.strip() == ""  # 无 sha1 → 空文件


def test_render_readme_shows_sha1_when_sha256_missing() -> None:
    """archive.org 老版本 sha256 空时，表格应显示 sha1 兜底而非 'MD5 only'"""
    from vmware_lib.renderer import render_readme

    md = render_readme(SAMPLE_DATA_ARCHIVE_ONLY)
    # sha1 应以短 hash 形式出现在表格
    assert "1118f68f" in md
    # 应标注 SHA1（明示弱哈希）
    assert "SHA1" in md
    # 不应回落到 "MD5 only" 提示（因为我们已升级到 sha1 兜底）
    assert "MD5 only" not in md


def test_render_readme_still_uses_sha256_when_present() -> None:
    """当 sha256 存在时（Broadcom 主线），仍优先显示 sha256 而非 sha1"""
    from vmware_lib.renderer import render_readme

    md = render_readme(SAMPLE_DATA)  # 全部有 sha256
    # sha256 短前缀应出现
    assert "a0ef9087" in md
    # sha1 假值不应出现（因为 sha256 优先）
    assert "abc123" not in md
    assert "def456" not in md
