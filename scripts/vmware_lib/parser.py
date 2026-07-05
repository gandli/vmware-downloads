"""解析 archive.org 上的 VMware 文件名。

不依赖网络，只根据文件路径识别 product/platform/version/build。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class VMwareFile:
    """已识别的 VMware 安装包"""

    product: str  # "workstation" | "fusion"
    platform: str  # "windows" | "linux" | "macos"
    version: str  # "26H1" | "25H2u1" | "17.6.4"
    build: str  # "25388281"
    path: str  # archive.org 上的相对路径
    filename: str  # 纯文件名
    size_bytes: int = 0
    sha1: str = ""
    md5: str = ""
    mtime: str = ""  # archive.org 上的修改时间 (unix ts)
    extra: dict = field(default_factory=dict)


# 新命名规则：26H1 / 25H2 / 25H2u1
# 例: VMware-Workstation-Full-26H1-25388281.exe
#     VMware-Workstation-Full-25H2u1-25219725.exe
_RE_WS_NEW = re.compile(r"^VMware-Workstation-Full-(\d{2}H\d(?:u\d)?)-(\d+)\.(exe|x86_64\.bundle)$")

# 传统语义化版本
# 例: VMware-workstation-full-17.6.4-24832109.exe
#     VMware-Workstation-Full-15.5.7-17171714.x86_64.bundle
_RE_WS_LEGACY = re.compile(
    r"^VMware-[Ww]orkstation-[Ff]ull-(\d+\.\d+\.\d+)-(\d+)\.(exe|x86_64\.bundle)$"
)

# Fusion 新规则
_RE_FUSION_NEW = re.compile(r"^VMware-Fusion-(\d{2}H\d(?:u\d)?)-(\d+)_universal\.dmg$")

# Fusion 传统
# 例: VMware-Fusion-13.6.4-24832108_universal.dmg
#     VMware-Fusion-12.0.0-16880131.dmg (无 universal 后缀)
_RE_FUSION_LEGACY = re.compile(r"^VMware-Fusion-(\d+\.\d+\.\d+)-(\d+)(?:_universal|_x86)?\.dmg$")


def _platform_from_path(path: str, ext: str) -> str:
    """推断平台：路径以 Linux/ 开头则 linux；.dmg 则 macos；否则 windows"""
    if path.startswith("Linux/") or ext == "x86_64.bundle":
        return "linux"
    if ext == "dmg" or path.startswith("Fusion/"):
        return "macos"
    return "windows"


def parse_filename(path: str) -> VMwareFile | None:
    """解析 archive.org 上的完整路径，识别不了返回 None。

    Args:
        path: 如 "26H1/VMware-Workstation-Full-26H1-25388281.exe"
    """
    if "/" not in path:
        # 顶级元文件（torrent/meta）跳过
        return None

    filename = path.rsplit("/", 1)[-1]

    # Workstation 新规则
    m = _RE_WS_NEW.match(filename)
    if m:
        version, build, ext = m.group(1), m.group(2), m.group(3)
        return VMwareFile(
            product="workstation",
            platform=_platform_from_path(path, ext),
            version=version,
            build=build,
            path=path,
            filename=filename,
        )

    # Workstation 传统
    m = _RE_WS_LEGACY.match(filename)
    if m:
        version, build, ext = m.group(1), m.group(2), m.group(3)
        return VMwareFile(
            product="workstation",
            platform=_platform_from_path(path, ext),
            version=version,
            build=build,
            path=path,
            filename=filename,
        )

    # Fusion 新规则
    m = _RE_FUSION_NEW.match(filename)
    if m:
        return VMwareFile(
            product="fusion",
            platform="macos",
            version=m.group(1),
            build=m.group(2),
            path=path,
            filename=filename,
        )

    # Fusion 传统
    m = _RE_FUSION_LEGACY.match(filename)
    if m:
        return VMwareFile(
            product="fusion",
            platform="macos",
            version=m.group(1),
            build=m.group(2),
            path=path,
            filename=filename,
        )

    return None
