#!/usr/bin/env python3
"""侦查阶段 2：进入具体版本详情页，抓 SHA256"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("probe_output/detail")
OUT.mkdir(parents=True, exist_ok=True)

LOGIN_URL = "https://support.broadcom.com/c/portal/login"
# 选一个中间版本（17.6.4，最新非预发版）
DETAIL_URL = (
    "https://support.broadcom.com/group/ecx/productfiles"
    "?subFamily=VMware%20Workstation%20Pro"
    "&displayGroup=VMware%20Workstation%20Pro%2017.0%20for%20Windows"
    "&release=17.6.4&os=&servicePk=533272&language=EN&freeDownloads=true"
)


def mask(t):
    return re.sub(r"(dl\.broadcom\.com/)[A-Za-z0-9_-]{20,}", r"\1<TOK>", t)


def main():
    username = os.environ["BROADCOM_USERNAME"]
    password = os.environ["BROADCOM_PASSWORD"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
        )

        # 抓所有网络请求
        api_calls = []

        def on_request(req):
            if any(
                k in req.url
                for k in ["api", "productfiles", "download", "dl.broadcom", "checksum", "sha"]
            ):
                api_calls.append({"method": req.method, "url": mask(req.url)})

        def on_response(resp):
            u = resp.url
            if (
                any(k in u for k in ["productfiles", "download", "checksum", "sha", "api/v", "/o/"])
                and resp.status < 400
            ):
                try:
                    ct = resp.headers.get("content-type", "")
                    if "json" in ct or "xml" in ct:
                        body = resp.text()
                        if any(
                            kw in body.lower()
                            for kw in ["sha256", "sha1", "checksum", "vmware-workstation"]
                        ):
                            api_calls.append(
                                {
                                    "type": "response",
                                    "status": resp.status,
                                    "url": mask(u),
                                    "ct": ct,
                                    "body_snippet": mask(body[:2000]),
                                }
                            )
                except Exception:
                    pass

        page = ctx.new_page()
        page.on("request", on_request)
        page.on("response", on_response)

        # 登录
        print("[login]")
        page.goto(LOGIN_URL, wait_until="networkidle", timeout=45000)
        time.sleep(2)
        page.locator("#usernameInput").fill(username)
        page.locator("button.js-loginBtn").click()
        time.sleep(3)
        page.locator("input[type='password']").fill(password)
        page.locator("button[type='submit']").click()
        page.wait_for_url(re.compile(r"support\.broadcom\.com/(?!c/portal/login)"), timeout=30000)
        print("[login ✓]")

        # 详情页
        print(f"[detail] {DETAIL_URL[:120]}...")
        page.goto(DETAIL_URL, wait_until="networkidle", timeout=60000)
        time.sleep(8)  # SPA 数据加载
        page.screenshot(path=OUT / "detail.png", full_page=True)
        (OUT / "detail.html").write_text(mask(page.content()), encoding="utf-8")

        # 尝试点每个"i" info icon 或 SHA256 label
        for sel in [
            "text=SHA256",
            "text=SHA-256",
            "text=Checksum",
            "[title*='SHA' i]",
            "button[aria-label*='info' i]",
        ]:
            try:
                page.locator(sel).first.click(timeout=1500)
                time.sleep(1)
                print(f"  clicked: {sel}")
            except Exception:
                pass

        page.screenshot(path=OUT / "detail_expanded.png", full_page=True)
        (OUT / "detail_expanded.html").write_text(mask(page.content()), encoding="utf-8")

        # 抓页面上所有 SHA256
        html = page.content()
        sha256 = sorted(set(re.findall(r"\b[a-f0-9]{64}\b", html)))
        sha1 = sorted(set(re.findall(r"\b[a-f0-9]{40}\b", html)))
        md5 = sorted(set(re.findall(r"\b[a-f0-9]{32}\b", html)))
        files = sorted(set(re.findall(r"VMware[-_][A-Za-z0-9_.-]+\.(?:exe|bundle|dmg|zip)", html)))

        result = {
            "sha256": sha256,
            "sha1": sha1,
            "md5": md5,
            "filenames": files,
            "page_visible_text": page.evaluate("() => document.body.innerText")[:5000],
            "api_calls": api_calls[-30:],  # 最近 30 个
        }
        (OUT / "result.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        print(
            f"\nsha256={len(sha256)} sha1={len(sha1)} md5={len(md5)} files={len(files)} apis={len(api_calls)}"
        )
        if sha256:
            print("\nSHA256:")
            for h in sha256:
                print(f"  {h}")
        if files:
            print("\nFiles:")
            for f in files:
                print(f"  {f}")

        # 登出
        page.goto("https://support.broadcom.com/c/portal/logout", timeout=15000)
        browser.close()


if __name__ == "__main__":
    main()
