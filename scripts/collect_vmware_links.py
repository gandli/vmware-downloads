#!/usr/bin/env python3
"""
VMware Download Link Collector
收集 VMware Workstation Pro 和 Fusion Pro 的下载链接
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Archive.org 集合地址
ARCHIVE_ORG_COLLECTION = "vmwareworkstationarchive"

# Broadcom 官方下载页面
BROADCOM_URLS = {
    "workstation_pro": "https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro&freeDownloads=true",
    "fusion_pro": "https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Fusion%20Pro&freeDownloads=true",
}

# VMware Workstation Pro 版本（包含 SHA256 校验值）
WORKSTATION_VERSIONS = {
    "26H1": {
        "build": "25388281",
        "date": "2026-04-15",
        "sha256": {
            "windows": "a0ef9087607d9cad20b08139e73e41242e044ad5bd8cee141d3bad314586737f",
            "linux": "",
        },
    },
    "25H2": {
        "build": "24995812",
        "date": "2025-10-14",
        "sha256": {
            "windows": "",
            "linux": "",
        },
    },
    "17.6.4": {
        "build": "24832109",
        "date": "2025-07-15",
        "sha256": {
            "windows": "",
            "linux": "",
        },
    },
}

# VMware Fusion Pro 版本
FUSION_VERSIONS = {
    "26H1": {
        "build": "25388279",
        "date": "2026-04-15",
        "sha256": {
            "macos": "",
        },
    },
    "13.6.4": {
        "build": "24832108",
        "date": "2025-07-15",
        "sha256": {
            "macos": "",
        },
    },
}


def get_folder(version: str) -> str:
    """获取 Archive.org 文件夹名"""
    if version.startswith("25H") or version.startswith("26H"):
        if "u" in version:
            return version.split("u")[0]
        return version
    return f"{version.split('.')[0]}.x"


def collect_downloads() -> dict:
    """收集下载链接"""
    base = f"https://archive.org/download/{ARCHIVE_ORG_COLLECTION}"
    
    result = {
        "collected_at": datetime.utcnow().isoformat(),
        "official": BROADCOM_URLS,
        "archive_org": f"https://archive.org/details/{ARCHIVE_ORG_COLLECTION}",
        "workstation_pro": [],
        "fusion_pro": [],
    }

    # Workstation Pro
    for version, info in WORKSTATION_VERSIONS.items():
        folder = get_folder(version)
        if version.startswith("25H") or version.startswith("26H"):
            win = f"{base}/{folder}/VMware-Workstation-Full-{version}-{info['build']}.exe"
            linux = f"{base}/Linux/{folder}/VMware-Workstation-Full-{version}-{info['build']}.x86_64.bundle"
        else:
            win = f"{base}/{folder}/VMware-workstation-full-{version}-{info['build']}.exe"
            linux = f"{base}/Linux/{folder}/VMware-Workstation-Full-{version}-{info['build']}.x86_64.bundle"
        
        result["workstation_pro"].append({
            "version": version,
            "build": info["build"],
            "date": info["date"],
            "windows": win,
            "linux": linux,
            "sha256": info["sha256"],
        })

    # Fusion Pro
    for version, info in FUSION_VERSIONS.items():
        folder = get_folder(version)
        macos = f"{base}/Fusion/{folder}/VMware-Fusion-{version}-{info['build']}_universal.dmg"
        
        result["fusion_pro"].append({
            "version": version,
            "build": info["build"],
            "date": info["date"],
            "macos": macos,
            "sha256": info["sha256"],
        })

    return result


def save_json(data: dict, path: Path) -> None:
    """保存 JSON"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"已保存: {path}")


def generate_readme(data: dict, path: Path) -> None:
    """生成 README"""
    ws_latest = data["workstation_pro"][0]
    fusion_latest = data["fusion_pro"][0]
    
    lines = [
        "# VMware 下载链接",
        "",
        f"最后更新: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## 官方下载（下载文件时需登录）",
        "",
        "Broadcom 官方下载页面，浏览页面无需登录，点击下载具体文件时需登录：",
        "",
        f"- [VMware Workstation Pro]({data['official']['workstation_pro']})",
        f"- [VMware Fusion Pro]({data['official']['fusion_pro']})",
        "",
        "## Archive.org 镜像（无需登录）",
        "",
        f"所有链接来自 [Archive.org]({data['archive_org']})，无需登录即可下载。",
        "",
        "### 最新版本",
        "",
        "#### VMware Workstation Pro",
        "",
        f"**{ws_latest['version']}** (Build {ws_latest['build']})",
        "",
        f"- Windows: [{ws_latest['windows']}]({ws_latest['windows']})",
        f"- Linux: [{ws_latest['linux']}]({ws_latest['linux']})",
    ]

    # 添加 SHA256 校验值
    if ws_latest["sha256"]["windows"]:
        lines.append(f"- Windows SHA256: `{ws_latest['sha256']['windows']}`")
    if ws_latest["sha256"]["linux"]:
        lines.append(f"- Linux SHA256: `{ws_latest['sha256']['linux']}`")

    lines.extend([
        "",
        "#### VMware Fusion Pro",
        "",
        f"**{fusion_latest['version']}** (Build {fusion_latest['build']})",
        "",
        f"- macOS: [{fusion_latest['macos']}]({fusion_latest['macos']})",
    ])

    if fusion_latest["sha256"]["macos"]:
        lines.append(f"- macOS SHA256: `{fusion_latest['sha256']['macos']}`")

    lines.extend([
        "",
        "### 所有版本",
        "",
        "#### VMware Workstation Pro",
        "",
        "| 版本 | Build | 日期 | Windows | Linux | SHA256 (Windows) |",
        "|------|-------|------|---------|-------|------------------|",
    ])

    for v in data["workstation_pro"]:
        sha256_win = v["sha256"]["windows"][:16] + "..." if v["sha256"]["windows"] else "N/A"
        lines.append(f"| {v['version']} | {v['build']} | {v['date']} | [下载]({v['windows']}) | [下载]({v['linux']}) | {sha256_win} |")

    lines.extend([
        "",
        "#### VMware Fusion Pro",
        "",
        "| 版本 | Build | 日期 | macOS | SHA256 |",
        "|------|-------|------|-------|--------|",
    ])

    for v in data["fusion_pro"]:
        sha256_mac = v["sha256"]["macos"][:16] + "..." if v["sha256"]["macos"] else "N/A"
        lines.append(f"| {v['version']} | {v['build']} | {v['date']} | [下载]({v['macos']}) | {sha256_mac} |")

    lines.extend([
        "",
        "## 文件校验",
        "",
        "下载后请校验文件完整性：",
        "",
        "```bash",
        "# Linux/macOS",
        "sha256sum VMware-Workstation-Full-26H1-25388281.exe",
        "",
        "# Windows PowerShell",
        "Get-FileHash -Algorithm SHA256 VMware-Workstation-Full-26H1-25388281.exe",
        "```",
        "",
        "## 说明",
        "",
        "- VMware Workstation Pro 和 Fusion Pro 自 2024 年 11 月起对所有用户免费",
        "- 下载后可直接安装，无需许可证密钥",
        "- 安装时选择 个人使用 即可",
    ])

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"已生成: {path}")


def main() -> int:
    """主函数"""
    print("VMware 下载链接收集器")
    print("=" * 40)

    data = collect_downloads()

    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    save_json(data, repo_root / "data" / "vmware_downloads.json")
    generate_readme(data, repo_root / "README.md")

    print(f"\nWorkstation Pro: {len(data['workstation_pro'])} 个版本")
    print(f"Fusion Pro: {len(data['fusion_pro'])} 个版本")

    return 0


if __name__ == "__main__":
    sys.exit(main())
