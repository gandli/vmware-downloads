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

# VMware Workstation Pro 版本
WORKSTATION_VERSIONS = {
    "26H1": {"build": "25388281", "date": "2026-04-15"},
    "25H2u1": {"build": "25219725", "date": "2026-02-26"},
    "25H2": {"build": "24995812", "date": "2025-10-14"},
    "17.6.4": {"build": "24832109", "date": "2025-07-15"},
    "17.6.3": {"build": "24583834", "date": "2025-02-24"},
    "17.6.2": {"build": "24409262", "date": "2024-12-15"},
    "17.6.1": {"build": "24319023", "date": "2024-10-08"},
    "17.6.0": {"build": "24238078", "date": "2024-08-28"},
    "17.5.2": {"build": "23775571", "date": "2024-05-10"},
}

# VMware Fusion Pro 版本
FUSION_VERSIONS = {
    "26H1": {"build": "25388279", "date": "2026-04-15"},
    "25H2u1": {"build": "25219963", "date": "2026-02-26"},
    "25H2": {"build": "24995814", "date": "2025-10-14"},
    "13.6.4": {"build": "24832108", "date": "2025-07-15"},
    "13.6.3": {"build": "24585314", "date": "2025-02-24"},
    "13.6.1": {"build": "23298819", "date": "2024-11-19"},
    "13.6.0": {"build": "23278157", "date": "2024-09-17"},
    "13.5.2": {"build": "23324145", "date": "2024-06-25"},
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
            linux = f"{base}/{folder}/VMware-Workstation-Full-{version}-{info['build']}.x86_64.bundle"
        
        result["workstation_pro"].append({
            "version": version,
            "build": info["build"],
            "date": info["date"],
            "windows": win,
            "linux": linux,
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
        "## 官方下载（需要登录）",
        "",
        "Broadcom 官方下载页面，需要注册或登录账号：",
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
        "",
        "#### VMware Fusion Pro",
        "",
        f"**{fusion_latest['version']}** (Build {fusion_latest['build']})",
        "",
        f"- macOS: [{fusion_latest['macos']}]({fusion_latest['macos']})",
        "",
        "### 所有版本",
        "",
        "#### VMware Workstation Pro",
        "",
        "| 版本 | Build | 日期 | Windows | Linux |",
        "|------|-------|------|---------|-------|",
    ]

    for v in data["workstation_pro"]:
        lines.append(f"| {v['version']} | {v['build']} | {v['date']} | [下载]({v['windows']}) | [下载]({v['linux']}) |")

    lines.extend([
        "",
        "#### VMware Fusion Pro",
        "",
        "| 版本 | Build | 日期 | macOS |",
        "|------|-------|------|-------|",
    ])

    for v in data["fusion_pro"]:
        lines.append(f"| {v['version']} | {v['build']} | {v['date']} | [下载]({v['macos']}) |")

    lines.extend([
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
