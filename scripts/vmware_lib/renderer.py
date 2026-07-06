"""README / checksums.txt 渲染器"""

from __future__ import annotations

from datetime import datetime, timezone

PLATFORM_DISPLAY = {
    "windows": "Windows",
    "linux": "Linux",
    "macos": "macOS",
}


def _pretty_platform(key: str) -> str:
    return PLATFORM_DISPLAY.get(key, key.title())


def _short_sha256(h: str) -> str:
    return f"{h[:16]}..." if h else ""


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


def render_readme(data: dict) -> str:
    """生成完整 README Markdown"""
    ws_list = data.get("workstation_pro", [])
    fusion_list = data.get("fusion_pro", [])
    ws_latest = ws_list[0] if ws_list else None
    fusion_latest = fusion_list[0] if fusion_list else None

    lines: list[str] = [
        "# VMware 下载链接",
        "",
        f"最后更新: {_now_utc_str()}",
        "",
        "> **下载链接由 [archive.org](https://archive.org/details/vmwareworkstationarchive) 提供，SHA256/MD5 与发布日期来自 [Broadcom Support Portal](https://support.broadcom.com/group/ecx/productdownloads) 官方元数据。**",
        "",
        "## 快速下载",
        "",
    ]

    if ws_latest:
        lines += [
            "### VMware Workstation Pro",
            "",
            f"**{ws_latest['version']}** (Build {ws_latest['build']}, {ws_latest.get('date', '')})",
            "",
        ]
        for plat, info in ws_latest["downloads"].items():
            sha256 = info.get("sha256", "")
            sha_str = f" · SHA256: `{_short_sha256(sha256)}`" if sha256 else ""
            lines.append(
                f"- **{_pretty_platform(plat)}**: {_filename_link(info)} "
                f"({info['size']}{sha_str})"
            )
        lines.append("")

    if fusion_latest:
        lines += [
            "### VMware Fusion Pro",
            "",
            f"**{fusion_latest['version']}** (Build {fusion_latest['build']}, {fusion_latest.get('date', '')})",
            "",
        ]
        for plat, info in fusion_latest["downloads"].items():
            sha256 = info.get("sha256", "")
            sha_str = f" · SHA256: `{_short_sha256(sha256)}`" if sha256 else ""
            lines.append(
                f"- **{_pretty_platform(plat)}**: {_filename_link(info)} "
                f"({info['size']}{sha_str})"
            )
        lines.append("")

    # 所有版本表格
    if ws_list:
        lines += [
            "## 所有版本",
            "",
            "### VMware Workstation Pro",
            "",
            "> ✅ = Broadcom 官方数据（SHA256 权威）· 📼 = archive.org 历史存档（仅 MD5/SHA1，无 SHA256）",
            "",
            "| 版本 | Build | 发布日期 | Windows | Linux | SHA256 | 来源 |",
            "|------|-------|------|---------|-------|--------|:---:|",
        ]
        for v in ws_list:
            win = v["downloads"].get("windows")
            linux = v["downloads"].get("linux")
            win_str = _download_cell(win)
            linux_str = _download_cell(linux)
            sha_parts = []
            if win and win.get("sha256"):
                sha_parts.append(f"Win: `{win['sha256']}`")
            if linux and linux.get("sha256"):
                sha_parts.append(f"Linux: `{linux['sha256']}`")
            sha_str = "<br>".join(sha_parts) or ("MD5 only" if v.get("source") == "archive.org" else "详见 checksums.txt")
            src_flag = "📼" if v.get("source") == "archive.org" else "✅"
            lines.append(
                f"| {v['version']} | {v['build']} | {v.get('date', '—')} | {win_str} | {linux_str} | {sha_str} | {src_flag} |"
            )
        lines.append("")

    if fusion_list:
        lines += [
            "### VMware Fusion Pro",
            "",
            "> ✅ = Broadcom 官方数据（SHA256 权威）· 📼 = archive.org 历史存档（仅 MD5/SHA1，无 SHA256）",
            "",
            "| 版本 | Build | 发布日期 | macOS | SHA256 | 来源 |",
            "|------|-------|------|-------|--------|:---:|",
        ]
        for v in fusion_list:
            macos = v["downloads"].get("macos")
            macos_str = _download_cell(macos)
            sha256 = macos.get("sha256", "") if macos else ""
            sha_str = f"`{sha256}`" if sha256 else ("MD5 only" if v.get("source") == "archive.org" else "详见 checksums.txt")
            src_flag = "📼" if v.get("source") == "archive.org" else "✅"
            lines.append(
                f"| {v['version']} | {v['build']} | {v.get('date', '—')} | {macos_str} | {sha_str} | {src_flag} |"
            )
        lines.append("")

    lines += [
        "## 校验完整性",
        "",
        "所有 SHA256/MD5/文件字节大小由 **Broadcom Support Portal 官方元数据**导出，保存在：",
        "",
        "- [`data/checksums.txt`](data/checksums.txt) — SHA256（可直接喂给 `shasum -c` / `sha256sum -c`）",
        "- [`data/vmware_downloads.json`](data/vmware_downloads.json) — 每个文件的 `size`（人类可读）/ SHA256 / MD5 / build 号等",
        "",
        "先把 `data/checksums.txt` 与下载好的 `.exe`/`.bundle`/`.dmg` 放在**同一目录**，然后：",
        "",
        "### 1️⃣ 快速预检（秒级） — 看文件大小对不对",
        "",
        "```bash",
        "# 与 vmware_downloads.json 里的 size 字段对比（比如 '405.72 MB'）",
        "ls -lh VMware-workstation-full-17.6.4-24832109.exe",
        "```",
        "",
        "如果尺寸差得多，说明**下载不完整或下错了**，无需再算哈希，直接重新下。",
        "",
        "### 2️⃣ SHA256 完整性校验（推荐，唯一权威）",
        "",
        "```bash",
        "# Linux（GNU coreutils）",
        "sha256sum -c checksums.txt --ignore-missing",
        "",
        "# macOS（系统自带 shasum，无需安装 coreutils）",
        "shasum -a 256 -c checksums.txt --ignore-missing",
        "```",
        "",
        "```powershell",
        "# Windows PowerShell 5.1+（一键校验，非匹配报 FAIL）",
        "Get-Content checksums.txt | ForEach-Object {",
        "    $h, $f = $_ -split '  ', 2",
        "    if (-not (Test-Path $f)) { return }",
        "    $actual = (Get-FileHash $f).Hash.ToLower()",
        "    $ok = $actual -eq $h.ToLower()",
        "    '{0}  {1}' -f $(if ($ok) {'OK  '} else {'FAIL'}), $f",
        "}",
        "```",
        "",
        "> `--ignore-missing` 让工具跳过当前目录不存在的文件，只校验你下载的那几个。",
        "",
        "### 3️⃣ 期望输出",
        "",
        "```",
        "VMware-workstation-full-17.6.4-24832109.exe: OK",
        "```",
        "",
        "看到 `OK` 就是**逐字节校验通过**，可以放心安装；出现 `FAILED` 或 `WARNING` 一律**别装**，重下。",
        "",
        "## 数据来源",
        "",
        "- **SHA256 / MD5 / 文件大小 / 发布日期**：Broadcom Support Portal（登录抓取，权威）",
        "  - Workstation：<https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro&freeDownloads=true>",
        "  - Fusion：<https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Fusion%20Pro&freeDownloads=true>",
        "- **下载链接**：archive.org 上的 [vmwareworkstationarchive](https://archive.org/details/vmwareworkstationarchive) 集合（免费，无需登录）",
        "",
        "## 免费使用说明",
        "",
        "- **2024-05-14**（17.5.2 起）：VMware Workstation Pro 免费供**个人用户**使用。",
        "- **2024-11-11**（17.6.2 起）：Workstation & Fusion 免费供**所有用户**（个人、教育、商业）使用。",
        "",
        "> 参考：",
        "> - [Desktop Hypervisor Pro Apps Now Available for Personal Use](https://blogs.vmware.com/cloud-foundation/2024/05/14/vmware-desktop-hypervisor-pro-apps-now-available-for-personal-use/)",
        "> - [Fusion and Workstation Now Free for All Users](https://blogs.vmware.com/cloud-foundation/2024/11/11/vmware-fusion-and-workstation-are-now-free-for-all-users/)",
        "",
        "## 系统兼容性",
        "",
        "| 操作系统 | 最终支持版本 |",
        "|----------|-------------|",
        "| Windows 7 | VMware Workstation 15.5.7 |",
        "| Windows XP / 32 位 | VMware Workstation 10.0.7 |",
        "",
        "## 说明",
        "",
        "- 下载后可直接安装，无需许可证密钥。",
        "- 安装时选择「个人使用」即可。",
        "- 本仓库不承载任何文件；仅提供整理好的元数据 + archive.org 公开镜像链接。",
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
