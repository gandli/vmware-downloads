#!/usr/bin/env python3
"""Broadcom 门户侦查脚本 v2 —— 只读模式

侦查目标（不做任何写操作）：
  1. 用 BROADCOM_USERNAME / BROADCOM_PASSWORD 登录 access.broadcom.com IdP
  2. 检测常见风控：MFA、CAPTCHA、Trade Compliance、Account Pending
  3. 打开 VMware Workstation Pro 下载页
  4. 抓 SHA256/SHA1/build/文件名/T&C 勾选框状态
  5. 抓 dl.broadcom.com 出现的 token 化 URL 结构（**掩码**后保存）
  6. 立即 logout

严格限制：
  - 不点 Download / Accept T&C 按钮（避免账户被记录下载行为）
  - 凭证只从环境变量读，绝不打印到日志
  - 所有 URL / cookie 里的 token 都自动打码
  - 遇到未知交互立即截图并退出

用法：
  # 本地
  pip install playwright && python -m playwright install chromium
  BROADCOM_USERNAME='邮箱' BROADCOM_PASSWORD='密码' HEADLESS=0 python scripts/probe_broadcom.py

  # GitHub Actions（用 secrets）
  BROADCOM_USERNAME=${{ secrets.BROADCOM_USERNAME }} \\
  BROADCOM_PASSWORD=${{ secrets.BROADCOM_PASSWORD }} \\
      python scripts/probe_broadcom.py
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import Page, sync_playwright
    from playwright.sync_api import TimeoutError as PWTimeout
except ImportError:
    print("需要 Playwright：pip install playwright && python -m playwright install chromium")
    sys.exit(2)


LOGIN_URL = "https://support.broadcom.com/c/portal/login"
PRODUCT_URL = (
    "https://support.broadcom.com/group/ecx/productdownloads"
    "?subfamily=VMware%20Workstation%20Pro&freeDownloads=true"
)
LOGOUT_URL = "https://support.broadcom.com/c/portal/logout"

OUTPUT_DIR = Path("probe_output")

# 风控关键词
CAPTCHA_SIGNS = (
    "captcha",
    "recaptcha",
    "hcaptcha",
    "verify you are human",
    "unusual activity",
    "cloudflare challenge",
    "please prove",
)
MFA_SIGNS = (
    "verification code",
    "one-time password",
    "authenticator app",
    "two-factor",
    "mfa",
    "otp",
    "6-digit code",
    "security code",
)
COMPLIANCE_SIGNS = (
    "trade compliance",
    "export control",
    "restricted country",
    "trade sanctions",
    "ofac",
)
ACCOUNT_ISSUES = (
    "account verification is pending",
    "not entitled",
    "site id",
    "build your profile",
    "permission denied",
    "access denied",
    "unable to download",
)

# Token 掩码正则
TOKEN_MASK_PATTERNS = [
    (re.compile(r"(dl\.broadcom\.com/)([A-Za-z0-9_-]{20,})"), r"\1<TOKEN_MASKED>"),
    (re.compile(r"([?&]token=)[^&\s\"'<>]+", re.I), r"\1<MASKED>"),
    (re.compile(r"([?&]auth=)[^&\s\"'<>]+", re.I), r"\1<MASKED>"),
    (re.compile(r"(Authorization:\s*Bearer\s+)[A-Za-z0-9._~+/=-]+", re.I), r"\1<MASKED>"),
    (re.compile(r"(JSESSIONID=)[A-Za-z0-9._-]+", re.I), r"\1<MASKED>"),
]


def mask(text: str) -> str:
    """把敏感 token 打码"""
    for pat, repl in TOKEN_MASK_PATTERNS:
        text = pat.sub(repl, text)
    return text


def snap(page: Page, name: str) -> None:
    """截图 + 打码后 HTML"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    try:
        page.screenshot(path=OUTPUT_DIR / f"{name}.png", full_page=True)
        html = mask(page.content())
        (OUTPUT_DIR / f"{name}.html").write_text(html, encoding="utf-8")
        print(f"  📸 {name}.png (+ masked .html)")
    except Exception as e:
        print(f"  ⚠️  截图失败 {name}: {e}")


def _visible_text_lower(page: Page) -> str:
    """只提取 body 里对用户可见的文本，避免 CSS 类名 (.mfa-container 等) 误触发检测器"""
    try:
        return page.evaluate("() => document.body ? document.body.innerText.toLowerCase() : ''")
    except Exception:
        return ""


def detect_blockers(page_or_text) -> list[str]:
    """检测所有可能阻塞自动化的信号。传入 Page 走 innerText，传入 str 兼容旧调用。"""
    text = page_or_text if isinstance(page_or_text, str) else _visible_text_lower(page_or_text)
    blockers = []
    for sign in CAPTCHA_SIGNS:
        if sign in text:
            blockers.append(f"CAPTCHA:{sign}")
    for sign in MFA_SIGNS:
        if sign in text:
            blockers.append(f"MFA:{sign}")
    for sign in COMPLIANCE_SIGNS:
        if sign in text:
            blockers.append(f"COMPLIANCE:{sign}")
    for sign in ACCOUNT_ISSUES:
        if sign in text:
            blockers.append(f"ACCOUNT:{sign}")
    return blockers


def extract_data(html: str) -> dict:
    """从渲染后 HTML 挖数据"""
    return {
        "sha256": sorted(set(re.findall(r"\b[a-f0-9]{64}\b", html))),
        "sha1": sorted(set(re.findall(r"\b[a-f0-9]{40}\b", html))),
        "md5": sorted(set(re.findall(r"\b[a-f0-9]{32}\b", html))),
        "builds": sorted(set(re.findall(r"\b(2[0-9]{7})\b", html))),
        "filenames": sorted(
            set(re.findall(r"VMware[-_][A-Za-z0-9_.-]+\.(?:exe|bundle|dmg|zip|iso)", html))
        ),
        "dl_urls_masked": sorted(
            set(mask(u) for u in re.findall(r"https?://dl\.broadcom\.com/[^\s\"'<>]+", html))
        ),
        "has_tc_checkbox": bool(re.search(r"terms\s+and\s+conditions|i\s+agree", html, re.I)),
    }


def login(page: Page, username: str, password: str) -> tuple[bool, str]:
    """两步登录。返回 (成功?, 状态说明)"""
    print("[1/4] 打开登录页...")
    page.goto(LOGIN_URL, wait_until="networkidle", timeout=45000)
    time.sleep(2)
    snap(page, "01_login_page")

    # 检测登录页本身有没有反爬
    blockers = detect_blockers(page)
    if blockers:
        return False, f"登录页发现阻塞信号: {blockers}"

    # Step 1: username → Next
    print("[2/4] 输入用户名 → Next")
    try:
        page.locator("#usernameInput, input[name='userName']").first.fill(username)
        # Next 按钮初始 disabled，输入后才启用
        page.locator("button.js-loginBtn, button:has-text('Next')").first.click(timeout=10000)
    except PWTimeout:
        snap(page, "02a_username_fail")
        return False, "找不到用户名输入框或 Next 按钮"

    time.sleep(3)
    snap(page, "02b_after_username")

    blockers = detect_blockers(page)
    if blockers:
        return False, f"用户名后阻塞: {blockers}"

    # Step 2: password → Sign In
    print("[3/4] 输入密码 → Sign In")
    try:
        page.locator("input[type='password']").first.fill(password)
        page.locator(
            "button:has-text('Sign In'), button:has-text('Login'), button[type='submit']"
        ).first.click(timeout=10000)
    except PWTimeout:
        snap(page, "03a_password_fail")
        return False, "找不到密码输入框"

    # 等待登录后跳转
    try:
        page.wait_for_url(
            re.compile(r"support\.broadcom\.com/(?!c/portal/login)"),
            timeout=30000,
        )
    except PWTimeout:
        snap(page, "03b_login_stuck")
        blockers = detect_blockers(page)
        return False, f"登录后未跳转: blockers={blockers}"

    time.sleep(3)
    snap(page, "03c_login_success")
    return True, "登录成功"


def probe_product_page(page: Page) -> tuple[dict, list[str]]:
    """打开下载页，抓数据 + 检测阻塞"""
    print("[4/4] 打开 VMware Workstation Pro 下载页...")
    try:
        page.goto(PRODUCT_URL, wait_until="networkidle", timeout=60000)
    except PWTimeout:
        print("  ⚠️  networkidle 超时，继续抓当前内容")
    time.sleep(6)  # SPA 数据渲染
    snap(page, "04_product_page")

    blockers = detect_blockers(page)
    if blockers:
        print(f"  ⚠️  下载页有阻塞信号: {blockers}")

    # 尝试展开版本折叠面板（不点下载、不勾 T&C）
    for _ in range(5):
        clicked = False
        for text in ("VMware Workstation Pro", "Show More", "View All", "Expand All"):
            try:
                # 只点"展开"类，不点 Download / Accept
                locator = page.locator(
                    f"button:has-text('{text}'):not(:has-text('Download'))"
                ).first
                if locator.is_visible(timeout=1500):
                    locator.click(timeout=3000)
                    time.sleep(2)
                    clicked = True
            except Exception:
                pass
        if not clicked:
            break

    snap(page, "05_after_expand")

    html = page.content()
    data = extract_data(html)
    print(
        f"  📊 SHA256={len(data['sha256'])} SHA1={len(data['sha1'])} "
        f"builds={len(data['builds'])} files={len(data['filenames'])} "
        f"dl_urls={len(data['dl_urls_masked'])}"
    )

    return data, blockers


def main() -> int:
    username = os.environ.get("BROADCOM_USERNAME", "").strip()
    password = os.environ.get("BROADCOM_PASSWORD", "").strip()
    if not (username and password):
        print("❌ 缺少 BROADCOM_USERNAME / BROADCOM_PASSWORD 环境变量")
        return 2

    headless = os.environ.get("HEADLESS", "1") != "0"
    # 打码后的账户信息（只显示前 3 字符）
    user_mask = f"{username[:3]}***"
    if "@" in username:
        user_mask += f"@{username.split('@')[-1]}"
    print(f"账户: {user_mask} | headless={headless}")
    print("=" * 60)

    result = {
        "login_success": False,
        "login_message": "",
        "data": None,
        "product_blockers": [],
        "error": None,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        page = context.new_page()

        try:
            ok, msg = login(page, username, password)
            result["login_success"] = ok
            result["login_message"] = msg

            if ok:
                data, blockers = probe_product_page(page)
                result["data"] = data
                result["product_blockers"] = blockers

            print("\n[清理] 登出...")
            try:
                page.goto(LOGOUT_URL, timeout=15000)
                print("  ✅ 已登出")
            except Exception as e:
                print(f"  ⚠️  登出可能失败: {e}")
        except Exception as e:
            result["error"] = str(e)
            print(f"\n❌ 异常: {e}")
            with contextlib.suppress(Exception):
                snap(page, "99_exception")
        finally:
            browser.close()

    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # 汇总
    print("\n" + "=" * 60)
    print(f"侦查完成: {'成功' if result['login_success'] else '失败'}")
    print(f"登录状态: {result['login_message']}")
    if result["data"]:
        d = result["data"]
        print(
            f"抓到: SHA256×{len(d['sha256'])}, SHA1×{len(d['sha1'])}, "
            f"builds×{len(d['builds'])}, filenames×{len(d['filenames'])}"
        )
        if d["sha256"]:
            print("\nSHA256 样本（前 3）:")
            for h in d["sha256"][:3]:
                print(f"  {h}")
        if d["filenames"]:
            print("\n文件名样本（前 5）:")
            for f in d["filenames"][:5]:
                print(f"  {f}")
        if d["dl_urls_masked"]:
            print("\n下载 URL 结构（token 已打码）:")
            for u in d["dl_urls_masked"][:3]:
                print(f"  {u}")
    if result["product_blockers"]:
        print(f"\n⚠️ 下载页阻塞信号: {result['product_blockers']}")
    print(f"\n所有产出在: {OUTPUT_DIR}/")

    return 0 if result["login_success"] else 1


if __name__ == "__main__":
    sys.exit(main())
