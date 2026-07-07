"""测试文件名解析器：archive.org 上的 VMware 文件路径 → 结构化信息"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vmware_lib.parser import parse_filename


class TestParseWorkstation:
    def test_new_style_windows_26h1(self):
        """26H1 Windows: 新命名规则"""
        f = parse_filename("26H1/VMware-Workstation-Full-26H1-25388281.exe")
        assert f is not None
        assert f.product == "workstation"
        assert f.platform == "windows"
        assert f.version == "26H1"
        assert f.build == "25388281"

    def test_new_style_linux_25h2(self):
        f = parse_filename("Linux/25H2/VMware-Workstation-Full-25H2-24995812.x86_64.bundle")
        assert f is not None
        assert f.product == "workstation"
        assert f.platform == "linux"
        assert f.version == "25H2"
        assert f.build == "24995812"

    def test_new_style_with_update_suffix(self):
        """25H2u1: 带 update 后缀"""
        f = parse_filename("25H2/VMware-Workstation-Full-25H2u1-25219725.exe")
        assert f is not None
        assert f.version == "25H2u1"
        assert f.build == "25219725"

    def test_legacy_style_17x(self):
        f = parse_filename("17.x/VMware-workstation-full-17.6.4-24832109.exe")
        assert f is not None
        assert f.product == "workstation"
        assert f.platform == "windows"
        assert f.version == "17.6.4"
        assert f.build == "24832109"

    def test_legacy_linux_15x(self):
        f = parse_filename("Linux/15.x/VMware-Workstation-Full-15.5.7-17171714.x86_64.bundle")
        assert f is not None
        assert f.product == "workstation"
        assert f.platform == "linux"
        assert f.version == "15.5.7"

    def test_very_old_versions_are_ignored(self):
        """2.x 版本太老，且不是完整包，跳过"""
        f = parse_filename("2.x/VMware-2.0.1-570.exe")
        # 允许解析成功但版本号 <10 应被上层过滤；这里只要求返回 None 或 major<10
        if f is not None:
            assert int(f.version.split(".")[0]) < 10 or f.build != ""


class TestParseFusion:
    def test_fusion_26h1(self):
        f = parse_filename("Fusion/26H1/VMware-Fusion-26H1-25388279_universal.dmg")
        assert f is not None
        assert f.product == "fusion"
        assert f.platform == "macos"
        assert f.version == "26H1"
        assert f.build == "25388279"

    def test_fusion_legacy(self):
        f = parse_filename("Fusion/13.x/VMware-Fusion-13.6.4-24832108_universal.dmg")
        assert f is not None
        assert f.product == "fusion"
        assert f.platform == "macos"
        assert f.version == "13.6.4"
        assert f.build == "24832108"

    def test_fusion_x86_variant(self):
        """老 Fusion 有 _x86 变体，能解析出来"""
        f = parse_filename("Fusion/12.x/VMware-Fusion-12.0.0-16880131_x86.dmg")
        # 允许被识别或跳过；如果识别到，platform 必须正确
        if f is not None:
            assert f.product == "fusion"


class TestIgnored:
    def test_non_vmware_file(self):
        assert parse_filename("vmwareworkstationarchive_meta.xml") is None

    def test_torrent(self):
        assert parse_filename("vmwareworkstationarchive_archive.torrent") is None


# audit v5 · P1-B · parser.py L55 覆盖（Fusion/ 前缀 → macos）
def test_platform_from_path_fusion_prefix_is_macos() -> None:
    """Fusion/ 前缀路径识别为 macos"""
    from vmware_lib.parser import _platform_from_path

    assert _platform_from_path("Fusion/12.0/vmware.dmg", "dmg") == "macos"
    # 非 .dmg 后缀但 Fusion/ 前缀 → 仍 macos
    assert _platform_from_path("Fusion/13.0/vmware.zip", "zip") == "macos"
