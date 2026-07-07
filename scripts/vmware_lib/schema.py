"""VMware downloads JSON schema 校验 (audit v3 · P1-C)

用途：`data/vmware_downloads.json` 是本仓库唯一产品输出，用户通过
`sha256sum -c data/checksums.txt` 校验依赖它。
Broadcom API 若在某天悄悄改字段名 / 字段类型 → 静默产出坏数据 → 用户校验失败。

设计目标：
- **零外部依赖**（stdlib dataclass + 手工校验）
- 契约违规抛 `SchemaError` 且带上下文（哪个 version / 哪个字段坏）
- 全部字段可选宽松模式（新增字段不 break），关键字段强校验（sha256 / url / size）

使用：
    from vmware_lib.schema import validate_downloads_json, SchemaError

    with open("data/vmware_downloads.json") as f:
        data = json.load(f)
    errors = validate_downloads_json(data)
    if errors:
        raise SchemaError(f"schema violations: {errors}")

在 collect_vmware_links 末尾（写文件前）调一次即可拦截。
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------
# 常量：Broadcom / archive.org 契约字段
# ---------------------------------------------------------------

# sha256 = 64 位小写 hex；空串代表 archive.org 未镜像（合法）
_RE_SHA256 = re.compile(r"^[a-f0-9]{64}$")
# md5 = 32 位；同样允许空串
_RE_MD5 = re.compile(r"^[a-f0-9]{32}$")
# 文件名允许字母数字下划线连字符点及大写
_RE_FILENAME = re.compile(r"^[A-Za-z0-9._-]+$")
# size 字符串带单位：如 "274.34 MB"、"1.2 GB"
_RE_SIZE = re.compile(r"^[\d.]+\s*(KB|MB|GB|B|Bytes?)$", re.IGNORECASE)

REQUIRED_TOP_KEYS = {"collected_at", "workstation_pro", "fusion_pro"}
REQUIRED_ENTRY_KEYS = {"version", "build", "downloads"}
# source 可选：archive.org-only 的历史版本无该字段（legacy_merger 追加）
REQUIRED_DL_KEYS = {"filename", "size", "url"}
# 已知合法 source 值（若字段存在必须命中）
VALID_SOURCES = {"broadcom+archive", "broadcom-only", "archive-only"}


class SchemaError(ValueError):
    """schema 校验失败 —— 继承 ValueError 便于 except (SchemaError, ValueError)"""


def _check_download(prefix: str, dl: dict[str, Any]) -> list[str]:
    """校验单个下载入口。返回错误列表（空列表 = OK）"""
    errs: list[str] = []
    missing = REQUIRED_DL_KEYS - set(dl.keys())
    if missing:
        errs.append(f"{prefix}: 缺失必需字段 {sorted(missing)}")
        return errs  # 缺关键字段就不继续验，避免连锁误报

    # filename
    fn = dl.get("filename", "")
    if not isinstance(fn, str) or not fn:
        errs.append(f"{prefix}.filename: 应为非空字符串，实际 {fn!r}")
    elif not _RE_FILENAME.match(fn):
        errs.append(f"{prefix}.filename: 含非法字符 {fn!r}")

    # sha256 (允许空 = archive.org 未镜像；非空必须 64 hex)
    sha = dl.get("sha256", "")
    if not isinstance(sha, str):
        errs.append(f"{prefix}.sha256: 应为字符串，实际 {type(sha).__name__}")
    elif sha and not _RE_SHA256.match(sha):
        errs.append(
            f"{prefix}.sha256: 应为 64 位 hex 或空串，实际 {sha[:16]}... (len={len(sha)})"
        )

    # md5 (可选)
    md5 = dl.get("md5", "")
    if md5 and not isinstance(md5, str):
        errs.append(f"{prefix}.md5: 应为字符串，实际 {type(md5).__name__}")
    elif isinstance(md5, str) and md5 and not _RE_MD5.match(md5):
        errs.append(f"{prefix}.md5: 应为 32 位 hex，实际 {md5[:16]}... (len={len(md5)})")

    # size
    size = dl.get("size", "")
    if not isinstance(size, str) or not size:
        errs.append(f"{prefix}.size: 应为非空字符串（如 '274.34 MB'），实际 {size!r}")
    elif not _RE_SIZE.match(size):
        errs.append(f"{prefix}.size: 单位格式非法（应含 KB/MB/GB/B），实际 {size!r}")

    # url
    url = dl.get("url", "")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        errs.append(f"{prefix}.url: 应为 http(s) URL，实际 {url!r}")

    # source (可选，字段存在必须合法)
    if "source" in dl:
        source = dl["source"]
        if source not in VALID_SOURCES:
            errs.append(
                f"{prefix}.source: 未识别的来源 {source!r} (允许 {sorted(VALID_SOURCES)})"
            )

    return errs


def _check_entry(prefix: str, entry: dict[str, Any]) -> list[str]:
    """校验单个版本入口（一个 Workstation 或 Fusion 版本）"""
    errs: list[str] = []
    missing = REQUIRED_ENTRY_KEYS - set(entry.keys())
    if missing:
        errs.append(f"{prefix}: 缺失必需字段 {sorted(missing)}")
        return errs

    version = entry.get("version", "")
    if not isinstance(version, str) or not version:
        errs.append(f"{prefix}.version: 应为非空字符串，实际 {version!r}")

    build = entry.get("build", "")
    if not isinstance(build, str) or not build:
        errs.append(f"{prefix}.build: 应为非空字符串，实际 {build!r}")

    downloads = entry.get("downloads", {})
    if not isinstance(downloads, dict):
        errs.append(f"{prefix}.downloads: 应为 dict，实际 {type(downloads).__name__}")
        return errs

    for platform, dl in downloads.items():
        if not isinstance(dl, dict):
            errs.append(
                f"{prefix}.downloads.{platform}: 应为 dict，实际 {type(dl).__name__}"
            )
            continue
        errs.extend(_check_download(f"{prefix}.downloads.{platform}", dl))

    return errs


def validate_downloads_json(data: dict[str, Any]) -> list[str]:
    """校验完整 vmware_downloads.json 结构。返回错误列表（空 = OK）

    只做**最小契约校验**：新字段不 break；关键字段（sha256 / url / size）严格。
    """
    errs: list[str] = []

    if not isinstance(data, dict):
        return [f"root: 应为 dict，实际 {type(data).__name__}"]

    missing_top = REQUIRED_TOP_KEYS - set(data.keys())
    if missing_top:
        errs.append(f"root: 缺失必需字段 {sorted(missing_top)}")

    for prod in ("workstation_pro", "fusion_pro"):
        items = data.get(prod, [])
        if not isinstance(items, list):
            errs.append(f"root.{prod}: 应为 list，实际 {type(items).__name__}")
            continue
        for idx, entry in enumerate(items):
            if not isinstance(entry, dict):
                errs.append(
                    f"root.{prod}[{idx}]: 应为 dict，实际 {type(entry).__name__}"
                )
                continue
            entry_prefix = f"{prod}[{idx}]:{entry.get('version', '?')}"
            errs.extend(_check_entry(entry_prefix, entry))

    return errs
