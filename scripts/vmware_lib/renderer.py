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
            f"![License](https://img.shields.io/github/license/{REPO_OWNER_REPO}?style={BADGE_STYLE})"
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
        "- [Linux 安装 `.bundle`](#-linux-安装-bundle)",
        "- [所有历史版本](#-所有历史版本)",
        "- [免费使用政策](#-免费使用政策)",
        "- [老系统兼容性](#️-老系统兼容性)",
        "- [数据来源与说明](#-数据来源与说明)",
        "- [贡献与反馈](#贡献与反馈)",
        "- [License](#-license)",
        "",
    ]


def _render_linux_install() -> list[str]:
    """Linux .bundle 安装指南（静态段，不依赖数据）"""
    return [
        "## 🐧 Linux 安装 `.bundle`",
        "",
        "VMware 官方 Linux 安装包是自解压 shell 脚本（`.bundle`），"
        "不是 rpm/deb。安装、卸载都用同一个二进制。",
        "",
        "### 前置：内核头文件",
        "",
        "VMware 会在安装过程中编译 `vmmon` / `vmnet` 两个内核模块。必须先装匹配当前内核的 header：",
        "",
        "<details open>",
        "<summary><b>Debian / Ubuntu</b></summary>",
        "",
        "```bash",
        "sudo apt update",
        "sudo apt install -y build-essential linux-headers-$(uname -r)",
        "```",
        "",
        "</details>",
        "",
        "<details>",
        "<summary><b>Fedora / RHEL / Rocky / AlmaLinux</b></summary>",
        "",
        "```bash",
        "sudo dnf install -y gcc make kernel-devel kernel-headers",
        "# kernel-devel 会拉取匹配运行内核的版本; 若内核刚升级过, 先 reboot 再装",
        "```",
        "",
        "</details>",
        "",
        "<details>",
        "<summary><b>Arch / Manjaro</b></summary>",
        "",
        "```bash",
        "sudo pacman -S --needed base-devel linux-headers",
        "# 若用 linux-lts 内核，装 linux-lts-headers",
        "```",
        "",
        "</details>",
        "",
        "<details>",
        "<summary><b>openSUSE / SLES</b></summary>",
        "",
        "```bash",
        "sudo zypper install -y kernel-syms gcc make",
        "# kernel-syms 自动匹配当前内核变体 (default / preempt / ...) 的开发包",
        "```",
        "",
        "</details>",
        "",
        "### 安装",
        "",
        "```bash",
        "# 1. 校验完整性 (先做, 见上一节)",
        "sha256sum -c checksums.txt --ignore-missing",
        "",
        "# 2. 加执行权限",
        "chmod +x VMware-Workstation-Full-*.x86_64.bundle",
        "",
        "# 3. 运行安装器 (需 root)",
        "sudo ./VMware-Workstation-Full-*.x86_64.bundle",
        "",
        "# 或静默安装 (不弹 GUI, 自动接受 EULA)",
        "sudo ./VMware-Workstation-Full-*.x86_64.bundle --console --required --eulas-agreed",
        "```",
        "",
        "首次启动 `vmware` 命令时会触发模块编译。如果编译失败（新内核常见），装社区维护的补丁：",
        "",
        "```bash",
        "git clone https://github.com/mkubecek/vmware-host-modules.git",
        "cd vmware-host-modules",
        "git checkout workstation-17.6.4  # 换成你装的版本 tag",
        "make",
        "sudo make install",
        "sudo systemctl restart vmware",
        "```",
        "",
        "### 卸载",
        "",
        "```bash",
        "# 列出已安装组件",
        "vmware-installer -l",
        "",
        "# 卸载 Workstation (组件名一般是 vmware-workstation)",
        "sudo vmware-installer -u vmware-workstation",
        "```",
        "",
        "### 常见坑",
        "",
        "| 现象 | 原因 | 处理 |",
        "|:-----|:-----|:-----|",
        "| `Unable to find kernel headers` | header 版本对不上当前 "
        "`uname -r` | 内核刚升级过没重启; 或装 `linux-headers-$(uname -r)` |",
        "| 首次启动卡在 `Compiling modules...` | 新内核 API 不兼容旧 VMware "
        "| 装 [mkubecek/vmware-host-modules]"
        "(https://github.com/mkubecek/vmware-host-modules) 补丁 |",
        "| `SecureBoot` 报错模块签名 | 内核开了 lockdown "
        "| 关 SecureBoot, 或用 `mokutil` 给编出的模块签名 |",
        "| Wayland 下窗口异常 | VMware GUI 走 X11 | 命令行 `env GDK_BACKEND=x11 vmware` 启动 |",
        "",
        "> 官方安装文档：[Broadcom · Installing Workstation Pro on Linux]"
        "(https://techdocs.broadcom.com/us/en/vmware-cis/desktop-hypervisors/"
        "workstation-pro/17-0/vmware-workstation-pro-installation.html)",
        "",
    ]


def _render_license() -> list[str]:
    """License 分层授权说明（静态段）"""
    return [
        "## 📜 License",
        "",
        "本仓库分成两部分授权，请分清：",
        "",
        "| 内容 | 授权 |",
        "|:-----|:-----|",
        "| **仓库脚本 & 文档** — `scripts/`、`.github/`、README、CHANGELOG、"
        "data 目录里 gandli 汇编的 JSON/TXT 元数据 | "
        "[MIT License](./LICENSE) © 2024-2026 gandli |",
        "| **VMware Workstation / Fusion 安装包本体** | **Broadcom Inc.** 所有，"
        "遵循其 [EULA](https://www.broadcom.com/company/legal/licensing) "
        "与商标条款；2024-11-11 起对所有用户（个人 / 教育 / 商业）免费 |",
        "| **archive.org 镜像内容** | 由 "
        "[Internet Archive](https://archive.org/about/terms.php) 托管，"
        "本仓库不重发不镜像，仅提供跳转链接 |",
        "",
        "> 🛡️ 使用规则：",
        '> - 商标 "VMware"、"Workstation"、"Fusion" 归 **Broadcom Inc.** 所有，'
        "本仓库不隶属于、也未获 Broadcom 官方背书",
        "> - 本仓库 MIT 授权**仅覆盖 gandli 亲自编写的脚本与文档**，"
        "不授予任何 VMware 软件本身的再分发权",
        "> - VMware Workstation Pro / Fusion Pro 自 2024-11-11 起对所有用户免费，"
        "安装时选「个人使用」即可，无需许可证密钥（详见上文[免费使用政策](#-免费使用政策)）",
        f"> - 若你是版权持有方或权利人，需要撤下某版本，"
        f"[开 Issue](https://github.com/{REPO_OWNER_REPO}/issues/new) 说明即可",
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

    # ============ Linux 安装 .bundle ============
    lines += _render_linux_install()

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
        "- 🤖 每月首日 06:00 UTC 自动抓取最新版本并开 PR ([workflow](.github/workflows/monthly-update.yml))",
        "- 🧪 TDD 保护：单元测试覆盖抓取 / 合并 / 渲染全链路",
        "- 📁 仓库不承载任何安装包，仅提供**整理好的元数据** + **archive.org 公开镜像链接**",
        "",
        "## 贡献与反馈",
        "",
        f"发现某版本下载失效？欢迎 [开 Issue](https://github.com/{REPO_OWNER_REPO}/issues/new) 或 [提 PR](https://github.com/{REPO_OWNER_REPO}/compare) 🙏",
        "",
    ]

    lines += _render_license()

    lines += [
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
