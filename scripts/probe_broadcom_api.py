#!/usr/bin/env python3
"""Broadcom Support Portal 全量元数据抓取 v2 —— **API 拦截版**

架构切换：
  v1: 打开详情页 → 等 SHA256 出现在 DOM → 解析 HTML 表格 → 抽字段
  v2: 打开详情页 → 拦截 XHR `/productFiles/getDownloadableFiles` → 直接拿 JSON

优势：
  - SHA256/MD5/fileSize/gaDate/buildNumber 100% 权威（服务端字段名）
  - fileSize 精确到字节（v1 只有 "425.72 MB" 显示串）
  - 免懒惰正则 + 免 DOM 轮询 + 免 sleep 兜底
  - 服务端响应变化时能立即在 JSON 层察觉

只读约束：
  - 不点 Download / Accept T&C 按钮
  - 凭证只从环境变量读
  - Token/URL 掩码后落盘
  - 每个版本详情页限流 2 秒
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PWTimeout

# 复用 v1 里跑通的 login
from probe_broadcom import login as broadcom_login

OUT_DIR = Path("probe_output/full_api")
OUT_DIR.mkdir(parents=True, exist_ok=True)

WORKSTATION_LIST = (
    "https://support.broadcom.com/group/ecx/productdownloads"
    "?subfamily=VMware%20Workstation%20Pro&freeDownloads=true"
)
FUSION_LIST = (
    "https://support.broadcom.com/group/ecx/productdownloads"
    "?subfamily=VMware%20Fusion&freeDownloads=true"
)
BASE = "https://support.broadcom.com"

# API 端点关键字（服务端 content-type 声称 text/html，但内容是 JSON）
API_ENDPOINT = "/productFiles/getDownloadableFiles"


def mask(t: str) -> str:
    """打码 URL 中的 token / 邮箱"""
    t = re.sub(r"(dl\.broadcom\.com/)[A-Za-z0-9_-]{20,}", r"\1<TOK>", t)
    for env_key in ("BROADCOM_USERNAME", "BROADCOM_PASSWORD"):
        val = os.environ.get(env_key, "")
        if val and val in t:
            t = t.replace(val, f"<{env_key}_MASKED>")
    return t


def collect_detail_urls(page: Page, list_url: str, product_tag: str) -> list[dict]:
    """打开列表页，抓所有版本详情页 URL"""
    print(f"\n[list] {product_tag}: {list_url[:100]}...")
    page.goto(list_url, wait_until="networkidle", timeout=60000)
    time.sleep(4)  # SPA 需要额外时间渲染完整版本树

    html = page.content()
    pattern = r'"(/group/ecx/productfiles\?[^"]+freeDownloads=true)"'
    urls = re.findall(pattern, html)

    entries = []
    seen = set()
    for u in urls:
        clean = u.replace("&amp;", "&")
        if clean in seen:
            continue
        seen.add(clean)
        q = parse_qs(urlparse(clean).query)
        entries.append({
            "product": product_tag,
            "subFamily": q.get("subFamily", [""])[0],
            "displayGroup": q.get("displayGroup", [""])[0],
            "release": q.get("release", [""])[0],
            "servicePk": q.get("servicePk", [""])[0],
            "path": clean,
            "full_url": BASE + clean,
        })
    print(f"  发现 {len(entries)} 个版本")
    return entries


def normalize_file(raw: dict) -> dict:
    """把 API 返回的原始字段规范化"""
    return {
        "filename": raw.get("fileName", ""),
        "path": raw.get("filePath", ""),
        "description": raw.get("fileDescription", ""),
        "package": raw.get("filePackageName", ""),
        "size_bytes": raw.get("fileSize", 0),
        "size_human": _human_size(raw.get("fileSize", 0)),
        "build": str(raw.get("buildNumber", "")),
        "sha256": raw.get("sha2Chksum", ""),
        "md5": raw.get("md5Chksum", ""),
        "release_date": raw.get("gaDate", ""),
        "last_updated": raw.get("fileLastUpdatedDate", ""),
        "export_control": raw.get("exportControlStatus", ""),
    }


def _human_size(n: int) -> str:
    """字节 → MB/GB（保留 2 位小数）"""
    if not n:
        return ""
    if n >= 1024 ** 3:
        return f"{n / 1024 ** 3:.2f} GB"
    if n >= 1024 ** 2:
        return f"{n / 1024 ** 2:.2f} MB"
    if n >= 1024:
        return f"{n / 1024:.2f} KB"
    return f"{n} B"


def probe_detail_via_api(
    page: Page, entry: dict, idx: int, total: int
) -> dict:
    """访问详情页，同步等 getDownloadableFiles 响应到达再读 body

    关键：**不用 page.on() 事件监听**（会遇到 Network.getResponseBody 资源已释放）。
    改用 page.expect_response() —— 在导航开始前挂 hook，导航期间内部持有引用，
    结束后即可安全 .json() 读取 body。
    """
    tag = f"{entry['subFamily']}/{entry['release']}"
    print(f"[{idx}/{total}] {tag} (pk={entry['servicePk']})")

    payloads: list = []

    try:
        # 第一次 API 响应（可能是分页第 0 页；多数版本只有 1 页）
        with page.expect_response(
            lambda r: API_ENDPOINT in r.url and r.status == 200,
            timeout=25000,
        ) as first_wait:
            page.goto(entry["full_url"], wait_until="domcontentloaded", timeout=45000)
        resp = first_wait.value
        try:
            body_text = resp.text()
            payloads.append(json.loads(body_text))
        except Exception as e:
            print(f"  ⚠️ 读取 body 失败: {mask(str(e))}")

    except PWTimeout:
        print("  ❌ 未拦截到 getDownloadableFiles 响应（25s 超时）")
        entry["files"] = []
        entry["api_error"] = "timeout"
        return entry

    # 收 file details
    all_file_details = []
    for payload in payloads:
        if not payload.get("success"):
            continue
        content = payload.get("data", {}).get("packlistDetails", {}).get("content", [])
        for pack in content:
            for f in pack.get("fileDetails", []):
                all_file_details.append(f)

    files = [normalize_file(f) for f in all_file_details]
    entry["files"] = files

    if not files:
        print("  ⚠️ 响应到了但 fileDetails 为空")
    else:
        for f in files:
            marker = "✅" if f["sha256"] else "⚠️"
            print(
                f"  {marker} {f['filename']}  "
                f"{f['size_human']}  build={f['build']}  "
                f"sha256={f['sha256'][:12] if f['sha256'] else '—'}"
            )

    return entry


def main() -> int:
    username = os.environ.get("BROADCOM_USERNAME", "").strip()
    password = os.environ.get("BROADCOM_PASSWORD", "").strip()
    if not (username and password):
        print("❌ 缺少环境变量 BROADCOM_USERNAME / BROADCOM_PASSWORD")
        return 2

    all_entries = []
    started_at = datetime.now(timezone.utc).isoformat()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
        )
        page = ctx.new_page()

        try:
            ok, msg = broadcom_login(page, username, password)
            if not ok:
                print(f"[login ✗] {msg}")
                return 2
            print(f"[login ✓] {msg}")

            # 收集两个产品的详情页 URL
            entries = []
            entries += collect_detail_urls(page, WORKSTATION_LIST, "workstation")
            entries += collect_detail_urls(page, FUSION_LIST, "fusion")

            print(f"\n[total] 共 {len(entries)} 个版本待抓\n")

            # 逐个抓
            for i, entry in enumerate(entries, 1):
                probe_detail_via_api(page, entry, i, len(entries))
                all_entries.append(entry)
                time.sleep(2)  # 温柔限流

            # 登出
            print("\n[logout]")
            try:
                page.goto("https://support.broadcom.com/c/portal/logout", timeout=15000)
            except Exception:
                pass
        finally:
            browser.close()

    # dump
    result = {
        "collected_at": started_at,
        "source": "Broadcom Support Portal API (getDownloadableFiles)",
        "method": "playwright response interception",
        "total_entries": len(all_entries),
        "total_files": sum(len(e.get("files", [])) for e in all_entries),
        "entries": all_entries,
    }
    out_json = OUT_DIR / "broadcom_official.json"
    out_json.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # 汇总
    print("\n" + "=" * 60)
    print("抓取完成")
    print(f"  版本条目: {result['total_entries']}")
    print(f"  文件条目: {result['total_files']}")
    print(f"  产出:     {out_json}")

    with_sha = sum(
        1 for e in all_entries for f in e.get("files", []) if f.get("sha256")
    )
    with_md5 = sum(
        1 for e in all_entries for f in e.get("files", []) if f.get("md5")
    )
    total = result["total_files"]
    if total:
        print(f"  SHA256:    {with_sha}/{total} ({100 * with_sha // total}%)")
        print(f"  MD5:       {with_md5}/{total} ({100 * with_md5 // total}%)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
