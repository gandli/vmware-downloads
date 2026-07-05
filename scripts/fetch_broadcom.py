#!/usr/bin/env python3
"""Broadcom Support Portal 生产 fetcher —— **API 拦截 + asyncio 并发**

架构：
  1. Playwright async API（sync 版不支持多线程共享 browser）
  2. 登录一次 → storage_state 复用
  3. 用 asyncio.Semaphore 限并发到 N，每次开新 page 抓详情
  4. 输出 data/broadcom_metadata.json（shape 与旧版兼容）

只读约束：
  - 不点 Download / Accept T&C 按钮
  - 凭证只从环境变量读
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.async_api import (
    BrowserContext,
    Page,
    async_playwright,
)
from playwright.async_api import TimeoutError as PWTimeout

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
OUT_JSON = DATA_DIR / "broadcom_metadata.json"

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
API_ENDPOINT = "/productFiles/getDownloadableFiles"

WORKER_COUNT = int(os.environ.get("BROADCOM_WORKERS", "5"))
API_TIMEOUT_MS = 30000
NAV_TIMEOUT_MS = 45000


def log(msg: str) -> None:
    print(msg, flush=True)


async def do_login(page: Page, username: str, password: str) -> tuple[bool, str]:
    """两步登录（复用 probe_broadcom 逻辑，async 版）"""
    log("[login] 打开登录页...")
    await page.goto(LOGIN_URL, wait_until="networkidle", timeout=45000)
    await asyncio.sleep(2)

    # Step 1: username → Next
    try:
        await page.locator("#usernameInput, input[name='userName']").first.fill(username)
        await page.locator("button.js-loginBtn, button:has-text('Next')").first.click(
            timeout=10000
        )
    except PWTimeout:
        return False, "找不到用户名输入框"

    await asyncio.sleep(3)

    # Step 2: password → Sign In
    try:
        await page.locator("input[type='password']").first.fill(password)
        await page.locator(
            "button:has-text('Sign In'), button:has-text('Login'), button[type='submit']"
        ).first.click(timeout=10000)
    except PWTimeout:
        return False, "找不到密码输入框"

    # 等跳走
    for _ in range(30):
        cur = page.url
        if "support.broadcom.com" in cur and "login" not in cur:
            return True, "登录成功"
        await asyncio.sleep(1)
    return False, "登录后未跳转"


async def collect_detail_urls(
    page: Page, list_url: str, product_tag: str
) -> list[dict]:
    log(f"[list] {product_tag}: {list_url[:100]}...")
    await page.goto(list_url, wait_until="networkidle", timeout=60000)
    await asyncio.sleep(4)

    html = await page.content()
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
    log(f"  发现 {len(entries)} 个版本")
    return entries


def _human_size(n: int) -> str:
    if not n:
        return ""
    if n >= 1024 ** 3:
        return f"{n / 1024 ** 3:.2f} GB"
    if n >= 1024 ** 2:
        return f"{n / 1024 ** 2:.2f} MB"
    if n >= 1024:
        return f"{n / 1024:.2f} KB"
    return f"{n} B"


def normalize_file(raw: dict) -> dict:
    return {
        "filename": raw.get("fileName", ""),
        "size": _human_size(raw.get("fileSize", 0)),
        "size_bytes": raw.get("fileSize", 0),
        "build": str(raw.get("buildNumber", "")),
        "sha256": raw.get("sha2Chksum", ""),
        "md5": raw.get("md5Chksum", ""),
        "release_date": raw.get("gaDate", ""),
        "last_updated": raw.get("fileLastUpdatedDate", ""),
        "description": raw.get("fileDescription", ""),
        "package": raw.get("filePackageName", ""),
        "path": raw.get("filePath", ""),
        "export_control": raw.get("exportControlStatus", ""),
    }


async def probe_one(
    ctx: BrowserContext,
    entry: dict,
    idx: int,
    total: int,
    sem: asyncio.Semaphore,
) -> dict:
    """一个版本详情页 → 抓 API JSON。sem 限并发"""
    async with sem:
        tag = f"{entry['subFamily']}/{entry['release']}"
        page = await ctx.new_page()
        try:
            try:
                async with page.expect_response(
                    lambda r: API_ENDPOINT in r.url and r.status == 200,
                    timeout=API_TIMEOUT_MS,
                ) as w:
                    await page.goto(
                        entry["full_url"],
                        wait_until="domcontentloaded",
                        timeout=NAV_TIMEOUT_MS,
                    )
                resp = await w.value
                body = await resp.text()
                payload = json.loads(body)
            except PWTimeout:
                log(f"[{idx}/{total}] ❌ {tag} 超时")
                entry["files"] = []
                entry["api_error"] = "timeout"
                return entry
            except Exception as e:
                log(f"[{idx}/{total}] ❌ {tag} {type(e).__name__}: {e}")
                entry["files"] = []
                entry["api_error"] = type(e).__name__
                return entry

            details = []
            if payload.get("success"):
                content = (
                    payload.get("data", {})
                    .get("packlistDetails", {})
                    .get("content", [])
                )
                for pack in content:
                    for f in pack.get("fileDetails", []):
                        details.append(f)

            entry["files"] = [normalize_file(d) for d in details]

            if entry["files"]:
                first = entry["files"][0]
                mark = "✅" if first["sha256"] else "⚠️"
                log(
                    f"[{idx}/{total}] {mark} {tag}  "
                    f"{first['filename']}  {first['size']}"
                )
            else:
                log(f"[{idx}/{total}] ⚠️ {tag} 响应到但 fileDetails 为空")

            return entry
        finally:
            await page.close()


async def main() -> int:
    username = os.environ.get("BROADCOM_USERNAME", "").strip()
    password = os.environ.get("BROADCOM_PASSWORD", "").strip()
    if not (username and password):
        print("❌ 缺少环境变量 BROADCOM_USERNAME / BROADCOM_PASSWORD")
        return 2
    started_at = datetime.now(timezone.utc).isoformat()
    t_start = time.monotonic()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # === 登录 context ===
        auth_ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
        )
        auth_page = await auth_ctx.new_page()

        ok, msg = await do_login(auth_page, username, password)
        if not ok:
            log(f"[login ✗] {msg}")
            await browser.close()
            return 2
        log(f"[login ✓] {msg}")

        # 收集列表
        entries = []
        entries += await collect_detail_urls(auth_page, WORKSTATION_LIST, "workstation")
        entries += await collect_detail_urls(auth_page, FUSION_LIST, "fusion")
        log(f"\n[total] {len(entries)} 版本，并发 {WORKER_COUNT}\n")

        storage_state = await auth_ctx.storage_state()
        await auth_ctx.close()

        # === 抓取 context（复用 storage_state）===
        work_ctx = await browser.new_context(
            storage_state=storage_state,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
        )

        sem = asyncio.Semaphore(WORKER_COUNT)
        tasks = [
            probe_one(work_ctx, e, i + 1, len(entries), sem)
            for i, e in enumerate(entries)
        ]
        ordered = await asyncio.gather(*tasks)

        await work_ctx.close()
        await browser.close()

    elapsed = time.monotonic() - t_start

    result = {
        "collected_at": started_at,
        "source": "Broadcom Support Portal API (getDownloadableFiles)",
        "method": "playwright async + asyncio.Semaphore",
        "worker_count": WORKER_COUNT,
        "elapsed_sec": round(elapsed, 1),
        "total_entries": len(ordered),
        "total_files": sum(len(e.get("files", [])) for e in ordered),
        "entries": ordered,
    }
    OUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    with_sha = sum(1 for e in ordered for f in e.get("files", []) if f.get("sha256"))
    with_md5 = sum(1 for e in ordered for f in e.get("files", []) if f.get("md5"))
    total = result["total_files"]

    print("\n" + "=" * 60)
    print(f"生产抓取完成，耗时 {elapsed:.1f}s")
    print(f"  版本条目: {result['total_entries']}")
    print(f"  文件条目: {result['total_files']}")
    print(f"  产出:     {OUT_JSON.relative_to(REPO_ROOT)}")
    if total:
        print(f"  SHA256:    {with_sha}/{total} ({100 * with_sha // total}%)")
        print(f"  MD5:       {with_md5}/{total} ({100 * with_md5 // total}%)")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
