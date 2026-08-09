"""README / checksums.txt 渲染器

设计原则（README 优化 v2）：
1. 头部徽章即刻传达仓库价值（版本数、最后更新、许可、来源可信度）
2. TL;DR 顶部快速下载 —— 用户 30 秒内拿到最新 exe/bundle/dmg
3. 校验步骤紧跟下载 —— 拿到文件就直接算哈希
4. "所有版本"表折叠 <details>，不占首屏
5. SHA256 短显（前 16 位）+ 完整值折叠，宽度不炸
"""

from __future__ import annotations

from datetime import datetime, timezone

PLATFORM_DISPLAY = {
    "windows": "Windows",
    "linux": "Linux",
    "macos": "macOS",
}

REPO_OWNER_REPO = "gandli/vmware-downloads"

BADGE_STYLE = "flat-square"


def _pretty_platform(key: str) -> str:
    return PLATFORM_DISPLAY.get(key, key.title())


def _short_sha256(h: str) -> str:
    return f"{h[:16]}…" if h else ""


def _short_sha1(h: str) -> str:
    """SHA1 40 hex → 前 12 位摘要（区别于 SHA256 的 16 位）"""
    return f"{h[:12]}…" if h else ""


def _hash_display(info: dict) -> tuple[str, str, str]:
    """统一哈希展示：sha256 优先 → sha1 兜底 → 空。

    返回 (algo_label, short_hash, full_hash)。
    - sha256 存在 → ("SHA256", short16, full64)
    - sha256 空但 sha1 存在 → ("SHA1", short12, full40)
    - 都无 → ("", "", "")
    """
    sha256 = info.get("sha256", "").strip() if info else ""
    if sha256:
        return ("SHA256", _short_sha256(sha256), sha256)
    sha1 = info.get("sha1", "").strip() if info else ""
    if sha1:
        return ("SHA1", _short_sha1(sha1), sha1)
    return ("", "", "")


def _filename_link(info: dict) -> str:
    """快速下载区块的文件名渲染。

    有 archive.org URL → Markdown 链接
    仅 Broadcom 有（url 为空）→ 纯 code 文件名 + 官方提示，避免生成 `[filename]()`
    """
    filename = info.get("filename", "")
    url = info.get("url", "").strip()
    if url:
        return f"[{filename}]({url})"
    return f"`{filename}` · 需登录 Broadcom Support Portal 获取"


def _download_cell(info: dict | None) -> str:
    """表格里"下载"单元格。archive.org 未镜像时给出提示，不生成空链接"""
    if not info:
        return "—"
    url = info.get("url", "").strip()
    size = info.get("size", "")
    if url:
        return f"[下载]({url}) ({size})"
    # broadcom-only 情况：archive.org 未镜像，Broadcom 官方需要登录
    return f"仅 Broadcom · {size}" if size else "仅 Broadcom"


def _now_utc_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _data_time(data: dict) -> datetime:
    """从 data.collected_at 提取时间戳，用于顶部"Last sync"注脚。

    该字段仅反映抓取时刻，不代表数据变化 —— 徽章日期请勿使用此值。
    review 采纳：数据未变化时不应产生 git diff（避免月度 workflow 空提交）
    """
    collected_at = data.get("collected_at")
    if collected_at:
        try:
            # ISO 8601 格式（含 +00:00 时区）
            return datetime.fromisoformat(collected_at)
        except (ValueError, TypeError):
            pass
    return datetime.now(timezone.utc)


def _latest_release_date(data: dict) -> str:
    """取所有产品线最新版本发布日期，用作徽章 "updated" 字段。

    抓取时间戳每天变但内容未变 → 徽章会误导；改用发布日期能真实反映数据新旧。
    找不到日期时回退到当前 UTC 日期。
    """
    candidates = []
    for key in ("workstation_pro", "fusion_pro"):
        items = data.get(key, [])
        if items:
            d = items[0].get("date", "")
            if d:
                candidates.append(d)
    if candidates:
        # 字符串比较 YYYY-MM-DD 即可
        return max(candidates)
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _render_badges(ws_count: int, fusion_count: int, release_date: str) -> list[str]:
    """顶部徽章：精简到 4 个核心 —— 版本数（合并 WS+Fusion）+ 更新 + License + 自动化

    ``release_date`` 使用最新版本的发布日期（"YYYY-MM-DD"），而非抓取时间戳。
    抓取时间戳每天都刷新但内容未变，会让徽章日期误导性地"每天变新"。
    视觉审美建议：删除重复的 SHA256/auto-update 徽章（正文已述）
    """
    # 注意：shields.io 徽章语法用双连字符 -- 表示字面 - 字符
    # 单连字符会被识别为 label/value 分隔符，导致 404 badge not found
    last_updated = release_date.replace("-", "--")
    return [
        (
            f"![Workstation](https://img.shields.io/badge/Workstation%20Pro-{ws_count}%20versions-0071c5?style={BADGE_STYLE}&logo=vmware) "
            f"![Fusion](https://img.shields.io/badge/Fusion%20Pro-{fusion_count}%20versions-0071c5?style={BADGE_STYLE}&logo=vmware) "
            f"![Last Updated](https://img.shields.io/badge/updated-{last_updated}-brightgreen?style={BADGE_STYLE}) "
            # 双层授权：仓库代码 MIT（仅脚本/文档），VMware 二进制遵循 Broadcom EULA
            # 显式标注「代码 MIT」避免误读为全仓库 MIT（与 README License 段分层一致）
            # 做成可点击链接：code→./LICENSE，VMware→Broadcom EULA
            f"[![code license](https://img.shields.io/badge/code-MIT-blue?style={BADGE_STYLE})](./LICENSE) "
            f"[![VMware](https://img.shields.io/badge/VMware-Broadcom%20EULA-0071c5?style={BADGE_STYLE}&logo=vmware)](https://www.broadcom.com/company/legal/licensing)"
        ),
        "",
    ]


def _render_hero() -> list[str]:
    """视觉 hero —— 项目名 + 校验终端卡片 proof (静态 SVG)"""
    return [
        '<p align="center">',
        '  <img src="./assets/readme/hero.svg" width="100%" '
        'alt="VMware Workstation &amp; Fusion 下载中心：128 个历史版本、54 个 Fusion 版本，'
        'Broadcom 官方 SHA256 校验 + archive.org 免费镜像，每月自动更新">',
        '</p>',
        '',
    ]


def _render_intro(dt: datetime) -> list[str]:
    """开场白 — 一句话定位 + 数据新鲜度时间戳 (hero 已含核心卖点, 避免重复)"""
    ts = dt.strftime("%Y-%m-%d %H:%M UTC")
    return [
        "> **一站式 VMware Workstation Pro & Fusion Pro 免费下载导航**",
        "",
        f"<sub>_数据抓取时间：{ts}_</sub>",
        "",
    ]


def _render_toc() -> list[str]:
    """目录锚点 — TOC 无 emoji，锚点仍需匹配正文标题的 GitHub slug（emoji → `-`）"""
    return [
        "## 目录",
        "",
        "- [快速下载（最新版）](#-快速下载最新版)",
        "- [校验完整性](#-校验完整性)",
        "- [所有历史版本](#-所有历史版本)",
        "",
    ]


def _render_latest_block(product_name: str, latest: dict, emoji: str) -> list[str]:
    """快速下载 —— 单个产品的最新版块"""
    lines = [
        f"### {emoji} {product_name}",
        "",
        f"**{latest['version']}** · Build `{latest['build']}` · 发布于 **{latest.get('date', '—')}**",
        "",
    ]
    for plat, info in latest["downloads"].items():
        algo, short, _full = _hash_display(info)
        sha_str = f" · {algo} `{short}`" if algo else ""
        lines.append(
            f"- **{_pretty_platform(plat)}** — {_filename_link(info)} ({info['size']}{sha_str})"
        )
    lines.append("")
    return lines


def _render_ws_rows(v_list: list[dict]) -> list[str]:
    """Workstation 表格每行"""
    rows = []
    for v in v_list:
        win = v["downloads"].get("windows")
        linux = v["downloads"].get("linux")
        win_str = _download_cell(win)
        linux_str = _download_cell(linux)

        # SHA256 优先 · SHA1 兜底（archive.org 老版本）
        sha_parts = []
        if win:
            algo, short, full = _hash_display(win)
            if algo:
                sha_parts.append(
                    f"Win {algo} `{short}` "
                    f"<details><summary>full</summary><code>{full}</code></details>"
                )
        if linux:
            algo, short, full = _hash_display(linux)
            if algo:
                sha_parts.append(
                    f"Linux {algo} `{short}` "
                    f"<details><summary>full</summary><code>{full}</code></details>"
                )
        sha_str = "<br>".join(sha_parts) or "MD5 only"
        src_flag = "📼" if v.get("source") == "archive.org" else "✅"

        rows.append(
            f"| {v['version']} | `{v['build']}` | {v.get('date', '—')} | "
            f"{win_str} | {linux_str} | {sha_str} | {src_flag} |"
        )
    return rows


def _render_fusion_rows(v_list: list[dict]) -> list[str]:
    """Fusion 表格每行"""
    rows = []
    for v in v_list:
        macos = v["downloads"].get("macos")
        macos_str = _download_cell(macos)
        algo, short, full = _hash_display(macos) if macos else ("", "", "")
        if algo:
            sha_str = (
                f"{algo} `{short}` <details><summary>full</summary><code>{full}</code></details>"
            )
        else:
            sha_str = "MD5 only"
        src_flag = "📼" if v.get("source") == "archive.org" else "✅"
        rows.append(
            f"| {v['version']} | `{v['build']}` | {v.get('date', '—')} | "
            f"{macos_str} | {sha_str} | {src_flag} |"
        )
    return rows


def render_readme(data: dict) -> str:
    """生成完整 README Markdown"""
    ws_list = data.get("workstation_pro", [])
    fusion_list = data.get("fusion_pro", [])
    ws_latest = ws_list[0] if ws_list else None
    fusion_latest = fusion_list[0] if fusion_list else None

    lines: list[str] = [
        '# <img src="./assets/readme/vmware-icon.svg" width="28" height="28" '
        'align="middle" alt=""> VMware Workstation & Fusion 下载中心',
        "",
    ]
    dt = _data_time(data)
    release_date = _latest_release_date(data)
    lines += _render_badges(len(ws_list), len(fusion_list), release_date)
    lines += _render_hero()
    lines += _render_intro(dt)

    lines += [
        "---",
        "",
    ]

    lines += _render_toc()

    # ============ 快速下载 ============
    lines += [
        "## 🚀 快速下载（最新版）",
        "",
        "> 直接点击文件名下载，无需登录。哈希在下方，下载后请务必[校验完整性](#-校验完整性)。",
        "",
    ]
    if ws_latest:
        lines += _render_latest_block("VMware Workstation Pro", ws_latest, "🪟")
    if fusion_latest:
        lines += _render_latest_block("VMware Fusion Pro", fusion_latest, "🍎")

    # ============ 校验完整性（提前到下载后）============
    lines += [
        "## 🔐 校验完整性",
        "",
        "所有哈希由 **Broadcom Support Portal（主线版）** + **archive.org 官方元数据（历史版）** 导出，保存在：",
        "",
        "- 📄 [`data/checksums.txt`](data/checksums.txt) — **SHA256** 清单，喂给 `sha256sum -c` / `shasum -a 256 -c`",
        "- 📄 [`data/checksums.sha1.txt`](data/checksums.sha1.txt) — **SHA1** 兜底清单（archive.org 历史版本无 sha256，喂给 `sha1sum -c` / `shasum -a 1 -c`）",
        "- 📄 [`data/vmware_downloads.json`](data/vmware_downloads.json) — 完整元数据 (size / SHA256 / SHA1 / MD5 / build)",
        "",
        "> **为什么有 SHA1？** Broadcom 收购 VMware 后下架了老版本 support 页面，官网 SHA256 只保留当前主线版本。archive.org 镜像了历史包但其元数据只提供 SHA1/MD5。SHA1 密码学强度虽弱于 SHA256，但用于**校验下载完整性**（防传输损坏 & 官方镜像投毒）依然足够。",
        "",
        "把 `checksums.txt` 与下载的 `.exe`/`.bundle`/`.dmg` **放在同一目录**：",
        "",
        "<details open>",
        "<summary><b>🐧 Linux / 🍎 macOS</b></summary>",
        "",
        "```bash",
        "# Linux（GNU coreutils）",
        "sha256sum -c checksums.txt --ignore-missing",
        "",
        "# macOS（系统自带 shasum）",
        "shasum -a 256 -c checksums.txt --ignore-missing",
        "```",
        "",
        "</details>",
        "",
        "<details>",
        "<summary><b>🪟 Windows PowerShell</b></summary>",
        "",
        "```powershell",
        "Get-Content checksums.txt | ForEach-Object {",
        "    $h, $f = $_ -split '  ', 2",
        "    if (-not (Test-Path $f)) { return }",
        "    $actual = (Get-FileHash $f).Hash.ToLower()",
        "    $ok = $actual -eq $h.ToLower()",
        "    '{0}  {1}' -f $(if ($ok) {'OK  '} else {'FAIL'}), $f",
        "}",
        "```",
        "",
        "</details>",
        "",
        "**期望输出**：",
        "",
        "```",
        "VMware-workstation-full-17.6.4-24832109.exe: OK",
        "```",
        "",
        "> ✅ 看到 `OK` 就是**逐字节校验通过**，可以放心安装。",
        "> ❌ 看到 `FAILED` / `WARNING` 一律**别装**，重新下载。",
        "",
        "> 💡 `--ignore-missing` 让工具只校验当前目录已有的文件，不必下齐全部。",
        "",
    ]

    # ============ 所有版本（默认折叠）============
    lines += [
        "## 📦 所有历史版本",
        "",
        "> **图例**：✅ Broadcom 官方数据（SHA256 权威）· 📼 archive.org 历史存档（仅 MD5/SHA1）",
        "",
    ]

    if ws_list:
        lines += [
            "<details>",
            f"<summary><b>🪟 VMware Workstation Pro（{len(ws_list)} 版）</b></summary>",
            "",
            "| 版本 | Build | 发布日期 | Windows | Linux | SHA256 | 来源 |",
            "|:-----|:------|:---------|:--------|:------|:-------|:---:|",
        ]
        lines += _render_ws_rows(ws_list)
        lines += ["", "</details>", ""]

    if fusion_list:
        lines += [
            "<details>",
            f"<summary><b>🍎 VMware Fusion Pro（{len(fusion_list)} 版）</b></summary>",
            "",
            "| 版本 | Build | 发布日期 | macOS | SHA256 | 来源 |",
            "|:-----|:------|:---------|:------|:-------|:---:|",
        ]
        lines += _render_fusion_rows(fusion_list)
        lines += ["", "</details>", ""]

    # ============ 更多文档链接 ============
    lines += [
        "---",
        "",
        "> 📚 **更多**：[🐧 Linux 安装 `.bundle`](docs/linux-install.md) · [💡 免费使用政策 & 老系统兼容性](docs/policy.md) · [📖 数据来源 & 贡献](docs/data-sources.md) · [📜 License](docs/licensing.md)",
        "",
        "<sub>本仓库仅提供元数据整理服务。VMware / Workstation / Fusion 是 Broadcom Inc. 的注册商标。</sub>",
    ]

    return "\n".join(lines) + "\n"


def render_checksums(data: dict) -> str:
    """生成 sha256sum -c 兼容的 checksums.txt"""
    lines: list[str] = []
    for product_key in ("workstation_pro", "fusion_pro"):
        for v in data.get(product_key, []):
            for _plat, info in v["downloads"].items():
                sha256 = info.get("sha256")
                if sha256:
                    lines.append(f"{sha256}  {info['filename']}")
    return "\n".join(lines) + "\n"


def render_sha1_checksums(data: dict) -> str:
    """生成 sha1sum -c 兼容的 checksums.sha1.txt。

    补 sha256 缺失的兜底：archive.org 老版本官方元数据只提供 sha1/md5，
    这里产出 sha1 校验清单，让用户下载后仍能验证完整性。

    格式：`<sha1_hex>  <filename>\\n`（与 sha256sum -c 一致）。
    """
    lines: list[str] = []
    for product_key in ("workstation_pro", "fusion_pro"):
        for v in data.get(product_key, []):
            for _plat, info in v["downloads"].items():
                sha1 = (info.get("sha1") or "").strip()
                filename = (info.get("filename") or "").strip()
                if sha1 and filename:
                    lines.append(f"{sha1}  {filename}")
    return ("\n".join(lines) + "\n") if lines else ""
