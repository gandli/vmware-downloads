"""Broadcom Support Portal 详情页 HTML 解析器

从版本详情页 HTML 中提取每个下载文件的元数据（文件名、SHA256、MD5、构建号、
发布日期等）。纯正则解析，无网络/浏览器依赖，方便复用与单测。

被 scripts/reparse_broadcom.py 使用（离线重新解析已缓存的 HTML）。
之前在 scripts/probe_broadcom_full.py 里，探测阶段清理后搬进 vmware_lib/。
"""

from __future__ import annotations

import re


def parse_detail_table(html: str) -> list[dict]:
    """解析 Broadcom 详情页 HTML，返回每个文件的元数据 list。

    详情页表格结构（从侦查得知）：
      File Name | Release Date | Last Updated | SHA2 | MD5

    策略：
      1. 用正则找到所有安装包文件名（*.exe / *.bundle / *.dmg / *.zip / *.iso）
      2. 每个文件名后取 2500 字节窗口，剥掉 HTML 标签
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
    file_pat = re.compile(
        r"(VMware[-_][A-Za-z0-9_.-]+\.(?:exe|bundle|dmg|zip|iso))",
        re.IGNORECASE,
    )
    results = []
    seen = set()
    for m in file_pat.finditer(html):
        fname = m.group(1)
        if fname in seen:
            continue
        seen.add(fname)

        # 取文件名后 2500 字节做窗口
        window = html[m.end() : m.end() + 2500]
        # 剥标签
        window_text = re.sub(r"<[^>]+>", " ", window)
        window_text = re.sub(r"&nbsp;", " ", window_text)
        window_text = re.sub(r"\s+", " ", window_text).strip()

        size_m = re.search(r"\((\d+(?:\.\d+)?\s*(?:KB|MB|GB))\)", window_text, re.IGNORECASE)
        build_m = re.search(r"Build\s+Number:?\s*(\d+)", window_text, re.IGNORECASE)
        sha256_m = re.search(r"\b([a-fA-F0-9]{64})\b", window_text)
        md5_m = re.search(r"\b([a-fA-F0-9]{32})\b", window_text)
        dates = re.findall(r"([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})", window_text)

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
