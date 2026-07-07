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
