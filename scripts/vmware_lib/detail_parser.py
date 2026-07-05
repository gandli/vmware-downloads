"""Broadcom Support Portal 详情页 HTML 解析器

从版本详情页 HTML 中提取每个下载文件的元数据（文件名、SHA256、MD5、构建号、
发布日期等）。纯正则解析，无网络/浏览器依赖，方便复用与单测。

被 scripts/reparse_broadcom.py 使用（离线重新解析已缓存的 HTML）。
之前在 scripts/probe_broadcom_full.py 里，探测阶段清理后搬进 vmware_lib/。
"""

from __future__ import annotations

import re


# ============================================================
# 常量
# ============================================================

#: 每个文件名后取的字节窗口大小。经过侦查阶段验证，Broadcom 详情页每个文件行的
#: HTML 剥标签后长度通常 < 1500 字节；2500 留了充足冗余覆盖多标签嵌套。
#: 若 Broadcom 改版后单行结构膨胀，可调此值。
_DETAIL_WINDOW_BYTES = 2500


# ============================================================
# 预编译正则（模块级，避免每次调用都重新编译）
# ============================================================

#: 安装包文件名：以 VMware 开头，5 种官方扩展名
_FILE_PAT = re.compile(
    r"(VMware[-_][A-Za-z0-9_.-]+\.(?:exe|bundle|dmg|zip|iso))",
    re.IGNORECASE,
)

#: 剥 HTML 标签
_HTML_TAG_PAT = re.compile(r"<[^>]+>")

#: HTML 空格实体
_NBSP_PAT = re.compile(r"&nbsp;")

#: 连续空白折叠为单空格
_WHITESPACE_PAT = re.compile(r"\s+")

#: 文件大小 "(525.55 MB)"
_SIZE_PAT = re.compile(r"\((\d+(?:\.\d+)?\s*(?:KB|MB|GB))\)", re.IGNORECASE)

#: 构建号 "Build Number: 24832109"
_BUILD_PAT = re.compile(r"Build\s+Number:?\s*(\d+)", re.IGNORECASE)

#: SHA256 严格 64 位十六进制
_SHA256_PAT = re.compile(r"\b([a-fA-F0-9]{64})\b")

#: MD5 严格 32 位十六进制
_MD5_PAT = re.compile(r"\b([a-fA-F0-9]{32})\b")

#: 英文月份日期 "May 14, 2024"
_DATE_PAT = re.compile(r"([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})")


def parse_detail_table(html: str) -> list[dict]:
    """解析 Broadcom 详情页 HTML，返回每个文件的元数据 list。

    详情页表格结构（从侦查得知）：
      File Name | Release Date | Last Updated | SHA2 | MD5

    策略：
      1. 用正则找到所有安装包文件名（*.exe / *.bundle / *.dmg / *.zip / *.iso）
      2. 每个文件名后取 `_DETAIL_WINDOW_BYTES` 字节窗口，剥掉 HTML 标签
      3. 在窗口内二次匹配 size / build / sha256 / md5 / dates
      4. 用 seen 集合避免重复文件（详情页里同一文件可能出现多次）

    Args:
        html: 详情页完整 HTML 文本

    Returns:
        list of dict，每个 dict 键：
          - filename: 文件名
          - size: "525.55 MB" 等，可能为空
          - build: 构建号，可能为空
          - sha256: 64 位十六进制哈希，可能为空
          - md5: 32 位十六进制哈希，可能为空
          - release_date: 首个匹配到的日期字符串（如 "Apr 4, 2024"）
          - last_updated: 第二个匹配到的日期字符串
    """
    results = []
    seen = set()
    for m in _FILE_PAT.finditer(html):
        fname = m.group(1)
        if fname in seen:
            continue
        seen.add(fname)

        # 取文件名后 2500 字节做窗口
        window = html[m.end() : m.end() + _DETAIL_WINDOW_BYTES]
        # 剥标签 + 归一化空白
        window_text = _HTML_TAG_PAT.sub(" ", window)
        window_text = _NBSP_PAT.sub(" ", window_text)
        window_text = _WHITESPACE_PAT.sub(" ", window_text).strip()

        size_m = _SIZE_PAT.search(window_text)
        build_m = _BUILD_PAT.search(window_text)
        sha256_m = _SHA256_PAT.search(window_text)
        md5_m = _MD5_PAT.search(window_text)
        dates = _DATE_PAT.findall(window_text)

        results.append(
            {
                "filename": fname,
                "size": size_m.group(1) if size_m else "",
                "build": build_m.group(1) if build_m else "",
                "sha256": sha256_m.group(1) if sha256_m else "",
                "md5": md5_m.group(1) if md5_m else "",
                "release_date": dates[0] if len(dates) >= 1 else "",
                "last_updated": dates[1] if len(dates) >= 2 else "",
            }
        )
    return results
