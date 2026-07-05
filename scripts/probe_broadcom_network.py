#!/usr/bin/env python3
"""侦查 Broadcom Support Portal 的 XHR/fetch 请求

目标：找到详情页真正的 REST 数据源（productfiles 接口），
把响应 JSON dump 下来看结构。

不做 HTML 解析，纯监听网络。
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright

# 复用已跑通的 login
from probe_broadcom import login as broadcom_login

OUT_DIR = Path("probe_output/network")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 用之前抓到的 17.6.4 详情页
DETAIL_URL = (
    "https://support.broadcom.com/group/ecx/productfiles"
    "?subFamily=VMware+Workstation+Pro"
    "&displayGroup=VMware+Workstation+Pro+17.0+for+Windows"
    "&release=17.6.4"
    "&servicePk=533272"
    "&language=EN"
    "&freeDownloads=true"
)


def mask_sensitive(s: str) -> str:
    """把凭证从字符串里抹掉"""
    for env_key in ("BROADCOM_USERNAME", "BROADCOM_PASSWORD"):
        val = os.environ.get(env_key, "")
        if val and val in s:
            s = s.replace(val, f"<{env_key}_MASKED>")
    return s


def main() -> int:
    username = os.environ.get("BROADCOM_USERNAME")
    password = os.environ.get("BROADCOM_PASSWORD")
    if not username or not password:
        print("需要环境变量 BROADCOM_USERNAME / BROADCOM_PASSWORD")
        return 2

    captured: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        # === 监听所有 response ===
        def on_response(resp):
            try:
                url = resp.url
                ct = resp.headers.get("content-type", "")
                # 只关心 JSON 或 API 类型
                if ("json" not in ct and "javascript" not in ct
                        and "/api/" not in url and "/ecx/" not in url):
                    return
                # 只关心 broadcom 域
                if "broadcom.com" not in url:
                    return
                # 排除 static 资源
                if any(x in url for x in ("/js/", "/css/", "/fonts/", ".woff", ".png", ".jpg")):
                    return
                entry = {
                    "url": url,
                    "status": resp.status,
                    "content_type": ct,
                    "method": resp.request.method,
                }
                # 抓 body（可能是 JSON）
                try:
                    if "json" in ct:
                        entry["json"] = resp.json()
                    else:
                        body = resp.text()
                        if len(body) < 200000:
                            entry["body_preview"] = body[:2000]
                except Exception as e:
                    entry["read_error"] = str(e)
                captured.append(entry)
            except Exception as e:
                print(f"  [listener err] {e}")

        page.on("response", on_response)

        # === 登录（复用已跑通的） ===
        ok, msg = broadcom_login(page, username, password)
        if not ok:
            print(f"[login ✗] {msg}")
            browser.close()
            return 1
        print(f"[login ✓] {msg}")

        # === 现在清空 captured，只抓详情页的请求 ===
        print(f"\n[detail] 清空 captured (共 {len(captured)} 条登录期请求)")
        captured.clear()

        print(f"[detail] 打开 17.6.4 详情页")
        print(f"  URL: {DETAIL_URL}")
        page.goto(DETAIL_URL, wait_until="domcontentloaded", timeout=60000)
        # 等 SHA256 出现在 DOM 里，同时 API 请求也已完成
        for i in range(30):
            body_text = page.evaluate("() => document.body.innerText")
            if re.search(r"\b[a-f0-9]{64}\b", body_text):
                print(f"  ✓ SHA256 已出现（用时 {i+1}s）")
                break
            page.wait_for_timeout(1000)
        # 再等 2 秒确保所有异步请求完成
        page.wait_for_timeout(2000)

        print(f"\n[capture] 抓到 {len(captured)} 条相关响应\n")

        browser.close()

    # === 分析 ===
    # 分类：REST API vs static
    api_calls = [c for c in captured if "json" in c.get("content_type", "").lower()]
    print(f"其中 JSON 响应: {len(api_calls)} 条\n")

    for i, c in enumerate(api_calls, 1):
        # 掩码 URL 里的 email (若有 token)
        safe_url = mask_sensitive(c["url"])
        # 截短显示
        print(f"[{i}] {c['method']} {c['status']} {safe_url[:120]}")
        if "json" in c:
            body = c["json"]
            if isinstance(body, dict):
                keys = list(body.keys())[:10]
                print(f"    keys: {keys}")
            elif isinstance(body, list):
                print(f"    list of {len(body)} items")

    # dump 全部到磁盘（去凭证）
    out_json = OUT_DIR / "all_responses.json"
    # 掩码后写入
    safe = json.loads(mask_sensitive(json.dumps(captured, default=str)))
    out_json.write_text(json.dumps(safe, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n完整响应已 dump: {out_json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
