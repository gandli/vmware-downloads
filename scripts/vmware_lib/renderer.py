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
                f"- **{_pretty_platform(plat)}**: [{info['filename']}]({info['url']}) "
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
                f"- **{_pretty_platform(plat)}**: [{info['filename']}]({info['url']}) "
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
            "| 版本 | Build | 发布日期 | Windows | Linux | SHA256 |",
            "|------|-------|------|---------|-------|--------|",
        ]
        for v in ws_list:
            win = v["downloads"].get("windows")
            linux = v["downloads"].get("linux")
            win_str = f"[下载]({win['url']}) ({win['size']})" if win else "—"
            linux_str = f"[下载]({linux['url']}) ({linux['size']})" if linux else "—"
            sha_parts = []
            if win and win.get("sha256"):
                sha_parts.append(f"Win: `{win['sha256']}`")
            if linux and linux.get("sha256"):
                sha_parts.append(f"Linux: `{linux['sha256']}`")
            sha_str = "<br>".join(sha_parts) or "详见 checksums.txt"
            lines.append(
                f"| {v['version']} | {v['build']} | {v.get('date', '—')} | {win_str} | {linux_str} | {sha_str} |"
            )
        lines.append("")

    if fusion_list:
        lines += [
            "### VMware Fusion Pro",
            "",
            "| 版本 | Build | 发布日期 | macOS | SHA256 |",
            "|------|-------|------|-------|--------|",
        ]
        for v in fusion_list:
            macos = v["downloads"].get("macos")
            macos_str = f"[下载]({macos['url']}) ({macos['size']})" if macos else "—"
            sha256 = macos.get("sha256", "") if macos else ""
            sha_str = f"`{sha256}`" if sha256 else "详见 checksums.txt"
            lines.append(
                f"| {v['version']} | {v['build']} | {v.get('date', '—')} | {macos_str} | {sha_str} |"
            )
        lines.append("")

    lines += [
        "## 校验完整性",
        "",
        "所有 SHA256/MD5 由 **Broadcom Support Portal 官方元数据**导出，保存在 [`data/checksums.txt`](data/checksums.txt)。",
        "",
        "先把 `data/checksums.txt` 与下载好的 `.exe`/`.bundle`/`.dmg` 放在**同一目录**，然后：",
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
