"""archive.org VMware 镜像相关的公共辅助函数

由 legacy_merger.py 和 probe_archive_org.py 共享，避免重复实现。

所有函数纯逻辑无网络依赖，方便单测。
"""

from __future__ import annotations

import re

# ==============================================================
# 常量
# ==============================================================

ARCHIVE_META_URL = "https://archive.org/metadata/vmwareworkstationarchive"
ARCHIVE_DL_BASE = "https://archive.org/download/vmwareworkstationarchive/"


# ==============================================================
# 文件识别
# ==============================================================


def is_installer(name: str) -> bool:
    """判断是否是 VMware 主安装包（排除 tools/ossp 等附件）"""
    lower = name.lower()
    if not (lower.endswith(".exe") or lower.endswith(".bundle") or lower.endswith(".dmg")):
        return False
    return not any(x in lower for x in ["tools", "ossp", "source", "guest"])


def detect_platform(name: str) -> str:
    """从文件名后缀识别平台（大小写不敏感，防 .EXE / .DMG 漏识别）"""
    lower = name.lower()
    if lower.endswith(".exe"):
        return "windows"
    if lower.endswith(".bundle"):
        return "linux"
    if lower.endswith(".dmg"):
        return "macos"
    return "unknown"


# ==============================================================
# 版本解析
# ==============================================================


def parse_ws_version(name: str) -> tuple[str, str] | None:
    """从 Workstation 文件名提取 (version, build)

    示例：
      "17.x/VMware-workstation-full-17.5.1-23298084.exe" → ("17.5.1", "23298084")
      "25H2/VMware-Workstation-Full-25H2u1-25219725.exe" → ("25H2u1", "25219725")
    """
    if "fusion" in name.lower():
        return None
    m = re.search(
        r"[Ww]orkstation.*?(\d+\.\d+\.\d+|\d+[Hh]\d+(?:u\d+)?)-(\d+)", name
    )
    return (m.group(1), m.group(2)) if m else None


def parse_fusion_version(name: str) -> tuple[str, str] | None:
    """从 Fusion 文件名提取 (version, build)"""
    m = re.search(r"Fusion-(\d+\.\d+\.\d+|\d+[Hh]\d+(?:u\d+)?)-(\d+)", name)
    return (m.group(1), m.group(2)) if m else None


# ==============================================================
# 尺寸格式化
# ==============================================================


def human_size(n) -> str:
    """字节数 → 易读大小

    None / 非数字 → 空字符串（用于渲染层判空）
    0 → "0 B"（合法零字节）
    """
    if n is None:
        return ""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return ""
    if n >= 1024 ** 3:
        return f"{n / 1024 ** 3:.2f} GB"
    if n >= 1024 ** 2:
        return f"{n / 1024 ** 2:.2f} MB"
    if n >= 1024:
        return f"{n / 1024:.2f} KB"
    return f"{n} B"


# ==============================================================
# 排序辅助
# ==============================================================


def build_sort_key(build: object) -> int:
    """把 build 号规范化为可比较的整数（防 int / str / 非数字混杂）

    - int → 直接返回
    - str 数字 → 转 int
    - 其他（None / 非数字字符串）→ 0
    """
    if isinstance(build, int):
        return build
    if build is None:
        return 0
    b_str = str(build)
    return int(b_str) if b_str.isdigit() else 0


# 版本号排序 —— 年份命名（26H1、25H2）视为 100+ 大版号
# Broadcom 从 2025 年起启用年份命名代替语义版本
# 例：26H1 = 主版 126（100 + 26），25H2 = 主版 125，25H2u1 = 125.2 后缀 1
_YEAR_VERSION_RE = re.compile(r"^(\d{2,4})H([12])(?:u(\d+))?$", re.IGNORECASE)
_SEMVER_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-+].*)?$")


def version_sort_key(version: object) -> tuple[int, int, int, int]:
    """把版本号规范化为 (major, minor, patch, sub) 元组用于降序排序

    支持格式：
    - 语义版本：``17.6.4`` → (17, 6, 4, 0)
    - 两段语义：``17.6``   → (17, 6, 0, 0)
    - 预发布/构建后缀：``17.6.4-RC1`` / ``17.6.4+build123`` → (17, 6, 4, 0)
      （后缀被忽略；如需区分预发布版，需要更细的规则）
    - 年份命名 2 位：``26H1``   → (126, 1, 0, 0)  ← 100+ 保证比 v99 都大
    - 年份命名 4 位：``2026H1`` → (2026, 1, 0, 0) ← 未来兼容
    - 年份 + 更新：``25H2u1`` → (125, 2, 0, 1)
    - 未知格式 → (0, 0, 0, 0)

    降序排序时会得到：
      2026H1 > 26H1 > 25H2u1 > 25H2 > 17.6.4 > 17.6.0 > 17.5.2 > ... > 3.0.0
    """
    if version is None:
        return (0, 0, 0, 0)
    v = str(version).strip()

    # 优先匹配年份命名（兼容 2 位和 4 位年份）
    m = _YEAR_VERSION_RE.match(v)
    if m:
        year = int(m.group(1))
        # 2 位年份加 100 归一化到 >99，防止与语义版本 v99 冲突
        # 4 位年份直接使用（远大于任何合理主版本号）
        if year < 100:
            year += 100
        half = int(m.group(2))
        sub = int(m.group(3)) if m.group(3) else 0
        return (year, half, 0, sub)

    # 语义版本（容忍 -RC1 / +build123 等后缀）
    m = _SEMVER_RE.match(v)
    if m:
        major = int(m.group(1))
        minor = int(m.group(2)) if m.group(2) else 0
        patch = int(m.group(3)) if m.group(3) else 0
        return (major, minor, patch, 0)

    return (0, 0, 0, 0)


def safe_size_int(v) -> int:
    """安全把 size 转 int（archive.org 偶尔返回 "" 或非数字）"""
    if v is None or v == "":
        return 0
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0
