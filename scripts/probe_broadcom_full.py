#!/usr/bin/env python3
"""侦查阶段 3：全量抓 Broadcom 官方元数据（只读）

流程：
  登录 → 分别打开 Workstation Pro 和 Fusion Pro 列表页 →
  收集所有版本详情页 URL → 依次访问 → 抓每个文件的官方元数据 →
  dump 到 probe_output/broadcom_official.json

只读约束：
  - 不点 Download / Accept T&C 按钮
  - 凭证只从环境变量读
  - Token/URL 掩码后落盘
  - 每个版本详情页限流 5 秒，避免风控
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PWTimeout

OUT_DIR = Path("probe_output/full")
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOGIN_URL = "https://support.broadcom.com/c/portal/login"
WORKSTATION_LIST = (
    "https://support.broadcom.com/group/ecx/productdownloads"
    "?subfamily=VMware%20Workstation%20Pro&freeDownloads=true"
)
FUSION_LIST = (
    "https://support.broadcom.com/group/ecx/productdownloads"
    "?subfamily=VMware%20Fusion&freeDownloads=true"
)
BASE = "https://support.broadcom.com"


def mask(t: str) -> str:
    """打码 URL 中的 token"""
    return re.sub(r"(dl\.broadcom\.com/)[A-Za-z0-9_-]{20,}", r"\1<TOK>", t)


def login(page: Page, username: str, password: str) -> None:
    """两步登录"""
    print("[login] 打开登录页...")
    page.goto(LOGIN_URL, wait_until="networkidle", timeout=45000)
    time.sleep(2)
    page.locator("#usernameInput").fill(username)
    page.locator("button.js-loginBtn").click()
    time.sleep(3)
    page.locator("input[type='password']").fill(password)
    page.locator("button[type='submit']").click()
    page.wait_for_url(
        re.compile(r"support\.broadcom\.com/(?!c/portal/login)"),
        timeout=30000,
    )
    print("[login ✓]")


def collect_detail_urls(page: Page, list_url: str, product_tag: str) -> list[dict]:
    """打开列表页，抓所有版本详情页 URL"""
    print(f"\n[list] {product_tag}: 打开 {list_url[:100]}...")
    page.goto(list_url, wait_until="networkidle", timeout=60000)
    time.sleep(6)  # SPA 加载
    html = page.content()
    (OUT_DIR / f"list_{product_tag}.html").write_text(mask(html), encoding="utf-8")
    page.screenshot(path=OUT_DIR / f"list_{product_tag}.png", full_page=True)

    # 抓所有 productfiles?... URL
    pattern = r'"(/group/ecx/productfiles\?[^"]+freeDownloads=true)"'
    urls = re.findall(pattern, html)

    entries = []
    seen = set()
    for u in urls:
        # 反 HTML 实体
        clean = u.replace("&amp;", "&")
        if clean in seen:
            continue
        seen.add(clean)
        # 解析参数
        q = parse_qs(urlparse(clean).query)
        entries.append(
            {
                "product": product_tag,
                "subFamily": q.get("subFamily", [""])[0],
                "displayGroup": q.get("displayGroup", [""])[0],
                "release": q.get("release", [""])[0],
                "servicePk": q.get("servicePk", [""])[0],
                "path": clean,
                "full_url": BASE + clean,
            }
        )
    print(f"  发现 {len(entries)} 个版本详情页")
    return entries


def parse_detail_table(html: str) -> list[dict]:
    """
    解析详情页表格。每行包含：文件名、大小、build、发布日期、更新日期、SHA256、MD5
    结构（从侦查得知）：
    File Name | Release Date | Last Updated | SHA2 | MD5
    """
    # 找每个文件名位置，然后取后续 2000 字节窗口做二次匹配
    # 用非懒惰边界，避免 `.{0,N}?` 匹配到空
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
        sha256_m = re.search(r"\b([a-f0-9]{64})\b", window_text)
        md5_m = re.search(r"\b([a-f0-9]{32})\b", window_text)
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


def probe_detail(page: Page, entry: dict, idx: int, total: int) -> dict:
    """访问一个详情页，抓数据"""
    tag = f"{entry['subFamily']}_{entry['release']}".replace(" ", "_").replace("/", "_")
    tag = re.sub(r"[^A-Za-z0-9_.-]", "", tag)
    print(f"[{idx}/{total}] {entry['displayGroup']} / {entry['release']} (pk={entry['servicePk']})")

    try:
        page.goto(entry["full_url"], wait_until="domcontentloaded", timeout=60000)
    except PWTimeout:
        print("  ⚠️  domcontentloaded 超时")

    # 关键：等 SHA256 hex 真正出现在 DOM 里（表格由 Angular 异步渲染）
    # 最多等 30 秒，每秒检查一次
    sha256_found = False
    for wait_sec in range(30):
        try:
            body_text = page.evaluate("() => document.body.innerText")
            if re.search(r"\b[a-f0-9]{64}\b", body_text):
                sha256_found = True
                break
            # 或者遇到 VMware- 文件名且过了 12 秒也算加载完（部分版本可能没 SHA）
            if wait_sec >= 12 and re.search(
                r"VMware[-_][A-Za-z0-9_.]+\.(exe|bundle|dmg)", body_text
            ):
                break
        except Exception:
            pass
        time.sleep(1)

    if not sha256_found:
        print("  ⏱️  等待 SHA256 超时（30s），继续保存现有内容")

    html = page.content()
    (OUT_DIR / f"detail_{idx:02d}_{tag[:60]}.html").write_text(mask(html), encoding="utf-8")

    files = parse_detail_table(html)
    if not files:
        print("  ❌ 未提取到文件")
        page.screenshot(path=OUT_DIR / f"detail_{idx:02d}_{tag[:60]}_fail.png", full_page=True)
    else:
        for f in files:
            marker = "✅" if f["sha256"] else "⚠️"
            print(
                f"  {marker} {f['filename']} ({f['size']}) build={f['build']} sha256={f['sha256'][:12] if f['sha256'] else '—'}"
            )

    entry["files"] = files
    return entry


def main() -> int:
    username = os.environ["BROADCOM_USERNAME"]
    password = os.environ["BROADCOM_PASSWORD"]

    all_entries = []
    started_at = datetime.now(timezone.utc).isoformat()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
        )
        page = ctx.new_page()

        try:
            login(page, username, password)

            # 收集两个产品的详情页 URL
            entries = []
            entries += collect_detail_urls(page, WORKSTATION_LIST, "workstation")
            entries += collect_detail_urls(page, FUSION_LIST, "fusion")

            print(f"\n[total] 共 {len(entries)} 个版本详情页待侦查\n")

            # 逐个抓
            for i, entry in enumerate(entries, 1):
                probe_detail(page, entry, i, len(entries))
                all_entries.append(entry)
                time.sleep(2)  # 温柔限流

            # 登出
            print("\n[logout]")
            page.goto("https://support.broadcom.com/c/portal/logout", timeout=15000)
        finally:
            browser.close()

    # dump
    result = {
        "collected_at": started_at,
        "source": "Broadcom Support Portal (support.broadcom.com)",
        "total_entries": len(all_entries),
        "total_files": sum(len(e.get("files", [])) for e in all_entries),
        "entries": all_entries,
    }
    out_json = OUT_DIR / "broadcom_official.json"
    out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    # 汇总
    print("\n" + "=" * 60)
    print("侦查完成")
    print(f"  版本条目: {result['total_entries']}")
    print(f"  文件条目: {result['total_files']}")
    print(f"  产出:     {out_json.relative_to(Path.cwd())}")

    # SHA256 覆盖率
    with_sha = sum(1 for e in all_entries for f in e.get("files", []) if f.get("sha256"))
    total = result["total_files"]
    if total:
        print(f"  SHA256 覆盖: {with_sha}/{total} ({100 * with_sha // total}%)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
