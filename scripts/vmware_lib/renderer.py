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
    """从 data.collected_at 提取时间戳，保证渲染幂等。

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


def _render_badges(ws_count: int, fusion_count: int, dt: datetime) -> list[str]:
    """顶部徽章：精简到 4 个核心 —— 版本数（合并 WS+Fusion）+ 更新 + License + 自动化

    视觉审美建议：删除重复的 SHA256/auto-update 徽章（正文已述）
    """
    # 注意：shields.io 徽章语法用双连字符 -- 表示字面 - 字符
    # 单连字符会被识别为 label/value 分隔符，导致 404 badge not found
    last_updated = dt.strftime("%Y--%m--%d")
    return [
        (
            f"![Workstation](https://img.shields.io/badge/Workstation%20Pro-{ws_count}%20versions-0071c5?style={BADGE_STYLE}&logo=vmware) "
            f"![Fusion](https://img.shields.io/badge/Fusion%20Pro-{fusion_count}%20versions-0071c5?style={BADGE_STYLE}&logo=vmware) "
            f"![Last Updated](https://img.shields.io/badge/updated-{last_updated}-brightgreen?style={BADGE_STYLE}) "
            f"![License](https://img.shields.io/github/license/{REPO_OWNER_REPO}?style={BADGE_STYLE})"
        ),
        "",
    ]


def _render_intro(dt: datetime) -> list[str]:
    """开场白 — 合并成一个引用块，时间戳用 <sub> 弱化"""
    ts = dt.strftime("%Y-%m-%d %H:%M UTC")
    return [
        "> **一站式 VMware Workstation Pro & Fusion Pro 免费下载导航**  ",
        "> 📥 archive.org 免费镜像 · 🔐 Broadcom 官方 SHA256 · 🤖 每月自动更新",
        "",
        f"<sub>_Last sync: {ts}_</sub>",
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
        "- [免费使用政策](#-免费使用政策)",
        "- [老系统兼容性](#️-老系统兼容性)",
        "- [数据来源与说明](#-数据来源与说明)",
        "- [贡献与反馈](#贡献与反馈)",
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
        sha256 = info.get("sha256", "")
        sha_str = f" · SHA256 `{_short_sha256(sha256)}`" if sha256 else ""
        lines.append(
            f"- **{_pretty_platform(plat)}** — {_filename_link(info)} "
            f"({info['size']}{sha_str})"
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

        # SHA256 短显 + <details> 完整值（避免撑破表格）
        sha_parts = []
        if win and win.get("sha256"):
            sha_parts.append(
                f"Win `{_short_sha256(win['sha256'])}` "
                f"<details><summary>full</summary><code>{win['sha256']}</code></details>"
            )
        if linux and linux.get("sha256"):
            sha_parts.append(
                f"Linux `{_short_sha256(linux['sha256'])}` "
                f"<details><summary>full</summary><code>{linux['sha256']}</code></details>"
            )
        sha_str = "<br>".join(sha_parts) or (
            "MD5 only" if v.get("source") == "archive.org" else "详见 checksums.txt"
        )
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
        sha256 = macos.get("sha256", "") if macos else ""
        if sha256:
            sha_str = (
                f"`{_short_sha256(sha256)}` "
                f"<details><summary>full</summary><code>{sha256}</code></details>"
            )
        else:
            sha_str = (
                "MD5 only" if v.get("source") == "archive.org" else "详见 checksums.txt"
            )
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
        "# 🎯 VMware Workstation & Fusion 下载中心",
        "",
    ]
    dt = _data_time(data)
    lines += _render_badges(len(ws_list), len(fusion_list), dt)
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
        "所有 SHA256 由 **Broadcom Support Portal 官方元数据**导出，保存在：",
        "",
        "- 📄 [`data/checksums.txt`](data/checksums.txt) — 可直接喂给 `shasum -c` / `sha256sum -c`",
        "- 📄 [`data/vmware_downloads.json`](data/vmware_downloads.json) — 完整元数据 (size / SHA256 / MD5 / build)",
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

    # ============ 免费使用政策 ============
    lines += [
        "## 💡 免费使用政策",
        "",
        "| 日期 | 里程碑 |",
        "|:-----|:-------|",
        "| **2024-05-14**（17.5.2 起） | Workstation Pro 免费供 **个人用户** |",
        "| **2024-11-11**（17.6.2 起） | Workstation & Fusion 免费供 **所有用户**（个人 / 教育 / 商业） |",
        "",
        "> 📖 官方公告：",
        "> - [Desktop Hypervisor Pro Apps Now Available for Personal Use](https://blogs.vmware.com/cloud-foundation/2024/05/14/vmware-desktop-hypervisor-pro-apps-now-available-for-personal-use/)",
        "> - [Fusion and Workstation Now Free for All Users](https://blogs.vmware.com/cloud-foundation/2024/11/11/vmware-fusion-and-workstation-are-now-free-for-all-users/)",
        "",
        "> ⚠️ 安装时选择「个人使用」即可，**无需许可证密钥**。",
        "",
        "## 🖥️ 老系统兼容性",
        "",
        "| 操作系统 | 最终支持的 Workstation 版本 |",
        "|:---------|:---------------------------|",
        "| Windows 7 | 15.5.7 |",
        "| Windows XP / 32 位 | 10.0.7 |",
        "",
        "## 📖 数据来源与说明",
        "",
        "### 数据溯源",
        "",
        "- **SHA256 / MD5 / 文件大小 / 发布日期**",
        "  Broadcom Support Portal（登录抓取，官方权威）",
        "  - [Workstation Pro Downloads](https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro&freeDownloads=true)",
        "  - [Fusion Pro Downloads](https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Fusion%20Pro&freeDownloads=true)",
        "- **安装包 URL**",
        "  archive.org [vmwareworkstationarchive 集合](https://archive.org/details/vmwareworkstationarchive)（免费，无需登录）",
        "",
        "### 自动化",
        "",
        f"- 🤖 每月首日 06:00 UTC 自动抓取最新版本并开 PR ([workflow](.github/workflows/monthly-update.yml))",
        "- 🧪 TDD 保护：145+ 个单测覆盖抓取 / 合并 / 渲染全链路",
        f"- 📁 仓库不承载任何安装包，仅提供**整理好的元数据** + **archive.org 公开镜像链接**",
        "",
        "## 贡献与反馈",
        "",
        f"发现某版本下载失效？欢迎 [开 Issue](https://github.com/{REPO_OWNER_REPO}/issues/new) 或 [提 PR](https://github.com/{REPO_OWNER_REPO}/compare) 🙏",
        "",
        "---",
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
