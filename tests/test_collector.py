"""测试 collector 融合层：archive index 构建 + Broadcom 融合"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vmware_lib.collector import (
    build_archive_filename_index,
    build_download_url,
    merge_broadcom_with_archive,
)


class TestBuildDownloadURL:
    def test_url_matches_archive_org_path(self):
        url = build_download_url("26H1/VMware-Workstation-Full-26H1-25388281.exe")
        assert url == (
            "https://archive.org/download/vmwareworkstationarchive/"
            "26H1/VMware-Workstation-Full-26H1-25388281.exe"
        )


class TestBuildArchiveFilenameIndex:
    def test_indexes_installer_by_lowercase_basename(self):
        meta = {
            "files": [
                {
                    "name": "26H1/VMware-Workstation-Full-26H1-25388281.exe",
                    "size": "287670872",
                    "md5": "83f9b6cc7cf0e74ad3b15ccca27860af",
                    "sha1": "0c892b81cc3519b5159e186c6215b379e5a425ab",
                    "mtime": "1717200000",
                },
                # 非 VMware 安装包应被忽略
                {"name": "somefile.txt", "size": "100"},
            ]
        }
        idx = build_archive_filename_index(meta)
        assert "vmware-workstation-full-26h1-25388281.exe" in idx
        entry = idx["vmware-workstation-full-26h1-25388281.exe"]
        assert entry["size_bytes"] == 287670872
        assert entry["md5_archive"] == "83f9b6cc7cf0e74ad3b15ccca27860af"
        assert entry["sha1"] == "0c892b81cc3519b5159e186c6215b379e5a425ab"
        assert entry["url"].endswith("VMware-Workstation-Full-26H1-25388281.exe")

    def test_basename_conflict_keeps_larger(self):
        meta = {
            "files": [
                {
                    "name": "old/VMware-Workstation-Full-26H1-25388281.exe",
                    "size": "100",
                },
                {
                    "name": "26H1/VMware-Workstation-Full-26H1-25388281.exe",
                    "size": "287670872",
                },
            ]
        }
        idx = build_archive_filename_index(meta)
        # 保留 size 更大的那份
        assert idx["vmware-workstation-full-26h1-25388281.exe"]["size_bytes"] == 287670872


class TestMergeBroadcomWithArchive:
    def _broadcom(self):
        return {
            "workstation": [
                {
                    "version": "17.6.4",
                    "platform": "windows",
                    "build": "24832109",
                    "filename": "VMware-workstation-full-17.6.4-24832109.exe",
                    "size": "525.55 MB",
                    "sha256": "10fe3a36f525d88aa133118ab3b5a16b18da88d4aa11b14d74e4164b3fb94ba9",
                    "md5": "aaaa1111",
                    "release_date": "2025-07-15",
                    "last_updated": "2025-07-09",
                },
            ]
        }

    def test_broadcom_plus_archive_hit(self):
        arch_idx = {
            "vmware-workstation-full-17.6.4-24832109.exe": {
                "url": "https://archive.org/download/x/vmware-workstation-full-17.6.4-24832109.exe",
                "sha1": "abc",
                "md5_archive": "aaaa1111",
            }
        }
        out = merge_broadcom_with_archive(self._broadcom(), arch_idx)
        dl = out["workstation"][0]["downloads"]["windows"]
        assert dl["source"] == "broadcom+archive"
        assert dl["url"].startswith("https://archive.org/")
        assert "md5_mismatch" not in dl

    def test_broadcom_only_when_no_archive(self):
        out = merge_broadcom_with_archive(self._broadcom(), {})
        dl = out["workstation"][0]["downloads"]["windows"]
        assert dl["source"] == "broadcom-only"
        assert dl["url"] == ""

    def test_md5_mismatch_flag_on_supply_chain_drift(self):
        arch_idx = {
            "vmware-workstation-full-17.6.4-24832109.exe": {
                "url": "https://archive.org/x",
                "sha1": "abc",
                "md5_archive": "bbbb2222",  # 与 Broadcom aaaa1111 不一致
            }
        }
        out = merge_broadcom_with_archive(self._broadcom(), arch_idx)
        dl = out["workstation"][0]["downloads"]["windows"]
        assert dl["md5_mismatch"] == "bbbb2222"

    def test_output_sorted_newest_first(self):
        bc = {
            "workstation": [
                {
                    "version": "17.5.2",
                    "platform": "windows",
                    "build": "1",
                    "filename": "a",
                    "sha256": "s",
                    "md5": "m",
                    "size": "",
                    "release_date": "",
                    "last_updated": "",
                },
                {
                    "version": "26H1",
                    "platform": "windows",
                    "build": "2",
                    "filename": "b",
                    "sha256": "s",
                    "md5": "m",
                    "size": "",
                    "release_date": "",
                    "last_updated": "",
                },
            ]
        }
        out = merge_broadcom_with_archive(bc, {})
        assert [v["version"] for v in out["workstation"]] == ["26H1", "17.5.2"]


# ============================================================
# audit v4 · P1-C · 补齐 collector.py 未覆盖分支
# ============================================================


def test_fetch_metadata_calls_urlopen(monkeypatch):
    """L33-37: fetch_metadata 应发起 urllib 请求并解析 JSON"""
    import io
    import json as _json

    from vmware_lib import collector

    captured = {}

    class FakeResponse:
        def __init__(self, body):
            self._body = body
        def __enter__(self):
            return io.BytesIO(self._body)
        def __exit__(self, *args):
            return False

    def fake_urlopen(req, timeout=30):
        captured["url"] = req.full_url
        captured["ua"] = req.headers.get("User-agent")
        captured["timeout"] = timeout
        return FakeResponse(_json.dumps({"files": []}).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = collector.fetch_metadata()
    assert result == {"files": []}
    assert "archive.org" in captured["url"]
    assert captured["ua"] and "vmware-downloads" in captured["ua"]
    assert captured["timeout"] == 30


def test_build_index_skips_empty_name():
    """L48-50: file_info 无 name 字段应被 skip"""
    from vmware_lib.collector import build_archive_filename_index

    metadata = {
        "files": [
            {"name": "", "size": "100"},        # empty name → skip
            {"size": "200"},                    # no name key → default "" → skip
            {"name": "26H1/VMware-Workstation-Full-17.5.0-22583795.exe", "size": "603000000"},
        ]
    }
    index = build_archive_filename_index(metadata)
    # 只有第 3 个有效
    assert len(index) == 1


def test_build_index_handles_non_int_size():
    """L55-58: size 是 str 非数字 (ValueError) → size_bytes=0 兜底"""
    from vmware_lib.collector import build_archive_filename_index

    metadata = {
        "files": [
            {
                "name": "26H1/VMware-Workstation-Full-17.5.0-22583795.exe",
                "size": "not-a-number",   # ← ValueError
            },
        ]
    }
    index = build_archive_filename_index(metadata)
    assert len(index) == 1
    entry = next(iter(index.values()))
    assert entry["size_bytes"] == 0


def test_build_index_handles_none_size():
    """L55-58: size 是 None (TypeError) → size_bytes=0 兜底"""
    from vmware_lib.collector import build_archive_filename_index

    metadata = {
        "files": [
            {
                "name": "26H1/VMware-Workstation-Full-17.5.0-22583795.exe",
                "size": None,   # ← TypeError
            },
        ]
    }
    index = build_archive_filename_index(metadata)
    assert next(iter(index.values()))["size_bytes"] == 0


def test_build_index_conflict_keeps_larger(caplog):
    """L69-78: 同名冲突时保留 size 更大的"""
    import logging

    from vmware_lib.collector import build_archive_filename_index

    metadata = {
        "files": [
            {
                "name": "old/VMware-Workstation-Full-17.5.0-22583795.exe",
                "size": "100",
                "sha1": "old",
            },
            {
                "name": "new/VMware-Workstation-Full-17.5.0-22583795.exe",
                "size": "200",
                "sha1": "new",
            },
        ]
    }
    with caplog.at_level(logging.WARNING, logger="vmware_lib.collector"):
        index = build_archive_filename_index(metadata)
    # 保留 size=200 的
    key = "vmware-workstation-full-17.5.0-22583795.exe"
    assert index[key]["size_bytes"] == 200
    assert index[key]["sha1"] == "new"
    assert any("冲突" in r.message for r in caplog.records)


def test_build_index_conflict_keeps_first_when_larger(caplog):
    """L79-86: 已存在的更大，忽略新的"""
    import logging

    from vmware_lib.collector import build_archive_filename_index

    metadata = {
        "files": [
            {
                "name": "big/VMware-Workstation-Full-17.5.0-22583795.exe",
                "size": "999",
                "sha1": "keep",
            },
            {
                "name": "small/VMware-Workstation-Full-17.5.0-22583795.exe",
                "size": "100",
                "sha1": "ignore",
            },
        ]
    }
    with caplog.at_level(logging.WARNING, logger="vmware_lib.collector"):
        index = build_archive_filename_index(metadata)
    key = "vmware-workstation-full-17.5.0-22583795.exe"
    # 保留 size=999
    assert index[key]["size_bytes"] == 999
    assert index[key]["sha1"] == "keep"
    assert any("忽略" in r.message for r in caplog.records)


# audit v5 · P1-C · Bandit B310 白名单断言
def test_fetch_metadata_rejects_file_scheme() -> None:
    """file:// scheme 被 assert 拒绝（防未来 URL 变量化开门后门）"""
    import pytest
    from vmware_lib.collector import fetch_metadata

    with pytest.raises(AssertionError, match="unexpected URL scheme"):
        fetch_metadata(url="file:///etc/passwd")


def test_fetch_metadata_rejects_ftp_scheme() -> None:
    import pytest
    from vmware_lib.collector import fetch_metadata

    with pytest.raises(AssertionError, match="unexpected URL scheme"):
        fetch_metadata(url="ftp://evil.com/x")


def test_fetch_metadata_accepts_archive_https() -> None:
    """https://archive.org/ 通过 assert（不实际发起网络）"""
    from unittest.mock import patch

    from vmware_lib.collector import fetch_metadata

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.return_value = b'{}'
        mock_urlopen.return_value.__enter__.return_value.__iter__ = lambda s: iter([b'{}'])
        # json.load 用 fp.read() 后 loads → 直接 patch
        import json
        with patch.object(json, "load", return_value={"ok": True}):
            result = fetch_metadata(url="https://archive.org/metadata/x")
            assert result == {"ok": True}
