"""VMware 下载链接融合库

主入口：
- ``parse_filename`` — 解析 archive.org 上的 VMware 安装包路径
- ``render_readme`` — 生成 README.md 内容
- ``merge_broadcom_with_archive`` — 融合 Broadcom 权威源 + archive.org 镜像
"""

from vmware_lib.collector import (
    build_archive_filename_index,
    fetch_metadata,
    merge_broadcom_with_archive,
)
from vmware_lib.parser import VMwareFile, parse_filename
from vmware_lib.renderer import render_checksums, render_readme

__all__ = [
    "VMwareFile",
    "build_archive_filename_index",
    "fetch_metadata",
    "merge_broadcom_with_archive",
    "parse_filename",
    "render_checksums",
    "render_readme",
]
