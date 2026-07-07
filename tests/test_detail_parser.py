"""测试 detail_parser.parse_detail_table

保证从 fetch_broadcom.py 搬到 vmware_lib/ 后逻辑一致。
用 mock HTML 覆盖典型 Broadcom 详情页结构。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vmware_lib.detail_parser import parse_detail_table

# ============================================================
# 典型完整详情页片段
# ============================================================

TYPICAL_HTML = """
<table>
<tr>
  <td>VMware-Workstation-Full-17.6.4-24832109.exe</td>
  <td>(525.55 MB)</td>
  <td>Build Number: 24832109</td>
  <td>Release Date: May 14, 2024</td>
  <td>Last Updated: Nov 20, 2024</td>
  <td>SHA2: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa</td>
  <td>MD5: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb</td>
</tr>
</table>
"""


def test_parses_single_file_full_metadata():
    """典型完整 HTML → 全字段正确解析"""
    r = parse_detail_table(TYPICAL_HTML)
    assert len(r) == 1
    e = r[0]
    assert e["filename"] == "VMware-Workstation-Full-17.6.4-24832109.exe"
    assert e["size"] == "525.55 MB"
    assert e["build"] == "24832109"
    assert e["sha256"] == "a" * 64
    assert e["md5"] == "b" * 32
    assert e["release_date"] == "May 14, 2024"
    assert e["last_updated"] == "Nov 20, 2024"


def test_deduplicates_repeated_filenames():
    """同一文件在 HTML 中出现两次只保留第一次"""
    html = TYPICAL_HTML + TYPICAL_HTML
    r = parse_detail_table(html)
    assert len(r) == 1


def test_matches_all_supported_extensions():
    """支持的扩展名：exe/bundle/dmg/zip/iso"""
    html = """
    VMware-Workstation-1.exe(1 MB)
    VMware-Fusion-2.dmg(2 MB)
    VMware-Linux-3.bundle(3 MB)
    VMware-OVF-4.zip(4 MB)
    VMware-VC-5.iso(5 MB)
    """
    r = parse_detail_table(html)
    filenames = [e["filename"] for e in r]
    assert "VMware-Workstation-1.exe" in filenames
    assert "VMware-Fusion-2.dmg" in filenames
    assert "VMware-Linux-3.bundle" in filenames
    assert "VMware-OVF-4.zip" in filenames
    assert "VMware-VC-5.iso" in filenames


def test_case_insensitive_extension():
    """扩展名大小写不敏感"""
    html = "VMware-Something.EXE(1 MB)"
    r = parse_detail_table(html)
    assert len(r) == 1
    assert r[0]["filename"] == "VMware-Something.EXE"


def test_missing_fields_return_empty_string():
    """字段缺失时返回空字符串，不 crash"""
    html = "VMware-Test.exe just a filename with nothing else"
    r = parse_detail_table(html)
    assert len(r) == 1
    e = r[0]
    assert e["filename"] == "VMware-Test.exe"
    assert e["size"] == ""
    assert e["build"] == ""
    assert e["sha256"] == ""
    assert e["md5"] == ""
    assert e["release_date"] == ""


def test_html_tags_stripped_before_matching():
    """HTML 标签 + &nbsp; 应被剥除后匹配"""
    # size 正则要求 (N MB) 括号，剥标签后合成 "( 100.5 MB )" 会因空格失败
    # 实测：括号紧贴数字才能匹配
    html = (
        "VMware-A.exe"
        "<span>(100.5&nbsp;MB)</span>"
        "<b>Build Number:</b>&nbsp;12345"
    )
    r = parse_detail_table(html)
    assert r[0]["size"] == "100.5 MB"
    assert r[0]["build"] == "12345"


def test_empty_html_returns_empty_list():
    """空 HTML → 空 list（不 crash）"""
    assert parse_detail_table("") == []
    assert parse_detail_table("<html></html>") == []


def test_sha256_length_exactly_64():
    """SHA256 匹配严格 64 位（不吃 65 位或 63 位）"""
    html = "VMware-A.exe " + "a" * 63 + " oops-too-short"
    r = parse_detail_table(html)
    # 只有 63 位应该匹配不到
    assert r[0]["sha256"] == ""


def test_md5_length_exactly_32():
    """MD5 匹配严格 32 位"""
    html = "VMware-A.exe MD5: " + "c" * 32 + " end"
    r = parse_detail_table(html)
    assert r[0]["md5"] == "c" * 32


def test_only_first_two_dates_used():
    """dates 有 3+ 时只用前两个"""
    html = "VMware-A.exe Jan 1, 2024 Feb 2, 2024 Mar 3, 2024"
    r = parse_detail_table(html)
    assert r[0]["release_date"] == "Jan 1, 2024"
    assert r[0]["last_updated"] == "Feb 2, 2024"


def test_only_one_date_leaves_last_updated_empty():
    """只有 1 个日期时 last_updated 为空"""
    html = "VMware-A.exe Jan 1, 2024"
    r = parse_detail_table(html)
    assert r[0]["release_date"] == "Jan 1, 2024"
    assert r[0]["last_updated"] == ""


# ============================================================
# 常量与预编译验证（回归保底：Gemini/Sourcery review 采纳的重构）
# ============================================================

def test_regex_patterns_precompiled_at_module_level():
    """所有正则常量应在模块导入时预编译（避免每次调用重复编译）"""
    import re

    from vmware_lib import detail_parser as dp

    for pat_name in ("_FILE_PAT", "_SIZE_PAT", "_BUILD_PAT",
                     "_SHA256_PAT", "_MD5_PAT", "_DATE_PAT",
                     "_HTML_TAG_PAT", "_NBSP_PAT", "_WHITESPACE_PAT"):
        pat = getattr(dp, pat_name)
        assert isinstance(pat, re.Pattern), f"{pat_name} 应是预编译 re.Pattern"


def test_window_size_constant_exposed():
    """魔法数字 2500 应通过具名常量暴露，便于 Broadcom 改版时调整"""
    from vmware_lib import detail_parser as dp

    assert dp._DETAIL_WINDOW_BYTES == 2500


def test_parse_is_deterministic_across_calls():
    """预编译后多次调用结果一致（预编译不能引入状态）"""
    html = "VMware-Test.exe (10 MB) Build Number: 999 " + "a" * 64 + " Jan 1, 2024"
    r1 = parse_detail_table(html)
    r2 = parse_detail_table(html)
    r3 = parse_detail_table(html)
    assert r1 == r2 == r3
