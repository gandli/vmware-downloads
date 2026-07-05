"""测试从 archive.org metadata 收集"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vmware_lib.collector import build_download_url, group_files_by_version, sort_versions
from vmware_lib.parser import VMwareFile


class TestBuildDownloadURL:
    def test_url_matches_archive_org_path(self):
        url = build_download_url("26H1/VMware-Workstation-Full-26H1-25388281.exe")
        assert (
            url
            == "https://archive.org/download/vmwareworkstationarchive/26H1/VMware-Workstation-Full-26H1-25388281.exe"
        )


class TestGroupFilesByVersion:
    def test_groups_windows_and_linux_of_same_version(self):
        files = [
            VMwareFile(
                product="workstation",
                platform="windows",
                version="26H1",
                build="25388281",
                path="26H1/VMware-Workstation-Full-26H1-25388281.exe",
                filename="VMware-Workstation-Full-26H1-25388281.exe",
                size_bytes=287670872,
                sha1="a" * 40,
                md5="",
            ),
            VMwareFile(
                product="workstation",
                platform="linux",
                version="26H1",
                build="25388281",
                path="Linux/26H1/VMware-Workstation-Full-26H1-25388281.x86_64.bundle",
                filename="VMware-Workstation-Full-26H1-25388281.x86_64.bundle",
                size_bytes=340787200,
                sha1="b" * 40,
                md5="",
            ),
        ]
        groups = group_files_by_version(files)
        assert len(groups["workstation"]) == 1
        v26h1 = groups["workstation"][0]
        assert v26h1["version"] == "26H1"
        assert v26h1["build"] == "25388281"
        assert "windows" in v26h1["downloads"]
        assert "linux" in v26h1["downloads"]


class TestSortVersions:
    def test_newest_first_modern(self):
        """26H1 > 25H2u1 > 25H2 > 17.6.4"""
        versions = ["17.6.4", "25H2", "26H1", "25H2u1"]
        sorted_v = sort_versions(versions)
        assert sorted_v[0] == "26H1"
        # 25H2u1 应排在 25H2 之前
        i_u1 = sorted_v.index("25H2u1")
        i_no = sorted_v.index("25H2")
        assert i_u1 < i_no
        assert sorted_v[-1] == "17.6.4"

    def test_semver_sort(self):
        versions = ["17.6.2", "17.6.4", "17.6.3", "17.5.2"]
        sorted_v = sort_versions(versions)
        assert sorted_v == ["17.6.4", "17.6.3", "17.6.2", "17.5.2"]
