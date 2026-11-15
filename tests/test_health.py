"""测试 vmware_lib.health —— 无人值守流水线的数据健康判定

重点覆盖真实事故形态（2026-11-01 那次自动更新退化）：
- 26H1u1 的 windows 条目整个消失
- 17.6 的 linux 条目消失
- 某版本详情页抓空 → 文件数变 0
- 上游真实下架整个版本 → 必须放行（不能把正常收缩当抖动拦死）
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vmware_lib.health import (  # noqa: E402
    compare,
    inventory,
    label,
    metadata_file_counts,
    metadata_regressions,
    regressions,
    versions,
)


def make_data(workstation_downloads, fusion_downloads=None) -> dict:
    """构造最小可用的 vmware_downloads.json 结构"""
    return {
        "workstation_pro": workstation_downloads,
        "fusion_pro": fusion_downloads or [],
    }


def version_block(version, **downloads) -> dict:
    return {"version": version, "build": "123", "downloads": downloads}


def dl(url="https://archive.org/x", source="broadcom+archive") -> dict:
    return {"url": url, "filename": "f", "source": source, "sha256": "abc"}


# ---------------------------------------------------------------- inventory


def test_inventory_flattens_by_product_version_platform():
    data = make_data(
        [version_block("17.6", windows=dl(), linux=dl())],
        [version_block("13.6.4", macos=dl())],
    )
    inv = inventory(data)
    assert set(inv) == {
        ("workstation", "17.6", "windows"),
        ("workstation", "17.6", "linux"),
        ("fusion", "13.6.4", "macos"),
    }


def test_inventory_skips_non_mapping_download_and_missing_groups():
    data = {
        "workstation_pro": [{"version": "17.6", "downloads": {"windows": "oops"}}],
    }
    assert inventory(data) == {}


def test_inventory_tolerates_missing_downloads_key():
    data = {"workstation_pro": [{"version": "17.6"}], "fusion_pro": None}
    assert inventory(data) == {}


def test_versions_and_label():
    data = make_data([version_block("26H1u1", windows=dl(), linux=dl())])
    assert versions(data) == {("workstation", "26H1u1")}
    assert label(("workstation", "26H1u1", "windows")) == "workstation/26H1u1/windows"


# ------------------------------------------------------------------ compare


def test_compare_detects_lost_entries():
    """真实事故：26H1u1 windows + 17.6 linux 同时消失"""
    old = make_data(
        [
            version_block("26H1u1", linux=dl(""), windows=dl()),
            version_block("17.6", windows=dl(), linux=dl()),
        ]
    )
    new = make_data(
        [
            version_block("26H1u1", linux=dl("")),
            version_block("17.6", windows=dl()),
        ]
    )
    diff = compare(old, new)
    assert diff["lost"] == ["workstation/17.6/linux", "workstation/26H1u1/windows"]
    assert diff["added"] == []
    assert diff["degraded"] == []


def test_compare_detects_added_entries():
    old = make_data([version_block("17.6", windows=dl())])
    new = make_data([version_block("17.6", windows=dl(), linux=dl())])
    assert compare(old, new)["added"] == ["workstation/17.6/linux"]


def test_compare_detects_degraded_url():
    """条目还在，但直链没了（archive.org 抖动 → 退回需登录）"""
    old = make_data([version_block("17.6", windows=dl("https://archive.org/a"))])
    new = make_data([version_block("17.6", windows=dl(""))])
    assert compare(old, new)["degraded"] == ["workstation/17.6/windows"]


def test_compare_ignores_gaining_url():
    old = make_data([version_block("26H1u1", linux=dl(""))])
    new = make_data(
        [version_block("26H1u1", linux=dl("https://archive.org/linux.bundle"))]
    )
    assert compare(old, new)["degraded"] == []


def test_compare_ignores_broadcom_only_without_url_both_sides():
    old = make_data([version_block("26H1u1", linux=dl("", "broadcom-only"))])
    new = make_data([version_block("26H1u1", linux=dl(None, "broadcom-only"))])
    assert compare(old, new)["degraded"] == []


# --------------------------------------------------------------- regressions


def test_regressions_empty_for_identical_data():
    data = make_data([version_block("17.6", windows=dl())])
    assert regressions(data, data) == []


def test_regressions_reports_lost_entry_and_degraded():
    old = make_data(
        [
            version_block("17.6", windows=dl("https://archive.org/a"), linux=dl()),
        ]
    )
    new = make_data([version_block("17.6", windows=dl(""))])
    reasons = regressions(old, new)
    assert any("workstation/17.6/linux" in r for r in reasons)
    assert any("链接退化" in r and "windows" in r for r in reasons)


def test_regressions_reports_wholesale_version_loss():
    old = make_data([version_block("26H1u1", windows=dl())])
    new = make_data([])
    reasons = regressions(old, new)
    assert any("版本整体消失：workstation/26H1u1" in r for r in reasons)


def test_regressions_empty_when_new_data_is_a_superset():
    old = make_data([version_block("17.6", windows=dl())])
    new = make_data(
        [
            version_block("26H1u1", windows=dl(), linux=dl()),
            version_block("17.6", windows=dl()),
        ]
    )
    assert regressions(old, new) == []


# ---------------------------------------------------------------- metadata


def make_meta(entries) -> dict:
    return {"entries": entries}


def meta_entry(product, release, group, files) -> dict:
    return {
        "product": product,
        "release": release,
        "displayGroup": group,
        "files": [{"filename": f"f{i}"} for i in range(files)],
    }


def test_metadata_file_counts():
    meta = make_meta(
        [
            meta_entry("workstation", "26H1u1", "VMware Workstation Pro 26H1", 2),
            meta_entry("fusion", "26H1u1", "VMware Fusion 26H1", 1),
            "not-a-mapping",
        ]
    )
    counts = metadata_file_counts(meta)
    assert counts[("workstation", "26H1u1", "VMware Workstation Pro 26H1")] == 2
    assert counts[("fusion", "26H1u1", "VMware Fusion 26H1")] == 1
    assert len(counts) == 2


def test_metadata_regressions_flags_partial_detail_page():
    """detail 页抓空：同版本文件数从 1 变 0"""
    old = make_meta([meta_entry("workstation", "26H1u1", "WS 26H1", 1)])
    new = make_meta([meta_entry("workstation", "26H1u1", "WS 26H1", 0)])
    reasons = metadata_regressions(old, new)
    assert len(reasons) == 1
    assert "从 1 个降到 0 个" in reasons[0]


def test_metadata_regressions_allows_upstream_retirement():
    """上游撤掉整版本（entry 消失）属正常，不能拦"""
    old = make_meta(
        [
            meta_entry("workstation", "17.6", "WS", 1),
            meta_entry("workstation", "26H1u1", "WS 26H1", 1),
        ]
    )
    new = make_meta([meta_entry("workstation", "26H1u1", "WS 26H1", 1)])
    assert metadata_regressions(old, new) == []


def test_metadata_regressions_flags_per_entry_decrease():
    old = make_meta([meta_entry("ws", "1", "g", 10), meta_entry("ws", "2", "g", 10)])
    new = make_meta([meta_entry("ws", "1", "g", 10), meta_entry("ws", "2", "g", 5)])
    reasons = metadata_regressions(old, new)
    assert any("版本文件数减少" in r and "ws/2/g" in r for r in reasons)
    # 只丢一半文件不算"大面积版本消失"（版本都还在）
    assert not any("大面积版本消失" in r for r in reasons)


def test_metadata_regressions_flags_mass_disappearance():
    """列表页整页没抓到：10 个版本只剩 3 个"""
    old = make_meta([meta_entry("ws", str(i), "g", 1) for i in range(10)])
    new = make_meta([meta_entry("ws", str(i), "g", 1) for i in range(3)])
    reasons = metadata_regressions(old, new)
    assert any("大面积版本消失" in r for r in reasons)


def test_metadata_regressions_threshold_configurable():
    """零散下架默认放行；把阈值放宽后，连"大面积消失"也不拦"""
    old = make_meta([meta_entry("ws", str(i), "g", 1) for i in range(10)])
    new = make_meta([meta_entry("ws", str(i), "g", 1) for i in range(3)])
    assert metadata_regressions(old, new, missing_ratio=0.9) == []


def test_metadata_regressions_empty_inputs():
    assert metadata_regressions({}, {}) == []
    assert metadata_regressions(make_meta([]), make_meta([])) == []
