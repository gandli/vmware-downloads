#!/usr/bin/env python3
"""
VMware Download Link Collector
收集 VMware 产品的直链下载地址（无需登录）
使用 Archive.org 镜像作为主要来源
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Archive.org 集合地址
ARCHIVE_ORG_COLLECTION = "vmwareworkstationarchive"

# VMware Workstation 版本和 Build 号对照表
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

# VMware Fusion 版本信息
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


def get_archive_org_folder(version: str) -> str:
    """获取 Archive.org 文件夹名"""
    if version.startswith("25H") or version.startswith("26H"):
        # 25H2u1 -> 25H2, 26H1 -> 26H1
        if "u" in version:
            return version.split("u")[0]
        return version
    major = version.split(".")[0]
    return f"{major}.x"


def generate_workstation_downloads(version: str, build: str) -> dict:
    """生成 Workstation 下载链接"""
    folder = get_archive_org_folder(version)
    base_url = f"https://archive.org/download/{ARCHIVE_ORG_COLLECTION}"

    # 新版本格式（25H2+）使用不同文件名
    if version.startswith("25H") or version.startswith("26H"):
        windows_url = f"{base_url}/{folder}/VMware-Workstation-Full-{version}-{build}.exe"
        linux_url = f"{base_url}/{folder}/VMware-Workstation-Full-{version}-{build}.x86_64.bundle"
    else:
        windows_url = f"{base_url}/{folder}/VMware-workstation-full-{version}-{build}.exe"
        linux_url = f"{base_url}/{folder}/VMware-Workstation-Full-{version}-{build}.x86_64.bundle"

    return {
        "windows": windows_url,
        "linux": linux_url,
    }


def generate_fusion_downloads(version: str, build: str) -> dict:
    """生成 Fusion 下载链接"""
    folder = get_archive_org_folder(version)
    base_url = f"https://archive.org/download/{ARCHIVE_ORG_COLLECTION}"

    # Fusion 使用 universal.dmg
    macos_url = f"{base_url}/Fusion/{folder}/VMware-Fusion-{version}-{build}_universal.dmg"

    return {
        "macos": macos_url,
    }


def collect_vmware_downloads() -> dict:
    """收集 VMware 下载链接"""
    result = {
        "collected_at": datetime.utcnow().isoformat(),
        "source": "Archive.org (无需登录)",
        "collection_url": f"https://archive.org/details/{ARCHIVE_ORG_COLLECTION}",
        "products": {
            "workstation-pro": {
                "name": "VMware Workstation Pro",
                "platforms": ["Windows", "Linux"],
                "description": "行业标准的桌面虚拟化软件",
                "license": "免费（个人和商业使用）",
                "versions": [],
            },
            "fusion-pro": {
                "name": "VMware Fusion Pro",
                "platforms": ["macOS"],
                "description": "macOS 上的专业虚拟化软件",
                "license": "免费（个人和商业使用）",
                "versions": [],
            },
        },
    }

    # 收集 Workstation 版本
    print("正在收集 VMware Workstation Pro 下载链接...")
    for version, info in WORKSTATION_VERSIONS.items():
        links = generate_workstation_downloads(version, info["build"])
        version_info = {
            "version": version,
            "build": info["build"],
            "release_date": info["date"],
            "downloads": links,
        }
        result["products"]["workstation-pro"]["versions"].append(version_info)
        print(f"  v{version} (build {info['build']})")

    # 收集 Fusion 版本
    print("正在收集 VMware Fusion Pro 下载链接...")
    for version, info in FUSION_VERSIONS.items():
        links = generate_fusion_downloads(version, info["build"])
        version_info = {
            "version": version,
            "build": info["build"],
            "release_date": info["date"],
            "downloads": links,
        }
        result["products"]["fusion-pro"]["versions"].append(version_info)
        print(f"  v{version} (build {info['build']})")

    return result


def save_to_json(data: dict, output_path: Path) -> None:
    """保存到 JSON 文件"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"已保存 JSON 到 {output_path}")


def generate_readme(data: dict, readme_path: Path) -> None:
    """生成 README.md"""
    lines = [
        "# VMware 下载链接（无需登录）",
        "",
        f"最后更新: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "> **所有链接均可直接下载，无需注册或登录任何账号。**",
        "",
        "## 快速下载",
        "",
        "### VMware Workstation Pro（最新版本）",
        "",
    ]

    # 获取最新版本
    latest_ws = data["products"]["workstation-pro"]["versions"][0]
    lines.extend([
        f"**版本 {latest_ws['version']}** (Build {latest_ws['build']})",
        "",
        "| 平台 | 下载链接 |",
        "|------|----------|",
        f"| Windows | [直接下载]({latest_ws['downloads']['windows']}) |",
        f"| Linux | [直接下载]({latest_ws['downloads']['linux']}) |",
        "",
    ])

    # Fusion
    latest_fusion = data["products"]["fusion-pro"]["versions"][0]
    lines.extend([
        "### VMware Fusion Pro（最新版本）",
        "",
        f"**版本 {latest_fusion['version']}** (Build {latest_fusion['build']})",
        "",
        "| 平台 | 下载链接 |",
        "|------|----------|",
        f"| macOS | [直接下载]({latest_fusion['downloads']['macos']}) |",
        "",
    ])

    # 所有版本
    lines.extend([
        "## 所有版本",
        "",
        "### VMware Workstation Pro",
        "",
        "| 版本 | Build | 发布日期 | Windows | Linux |",
        "|------|-------|----------|---------|-------|",
    ])

    for v in data["products"]["workstation-pro"]["versions"]:
        lines.append(
            f"| {v['version']} | {v['build']} | {v['release_date']} | "
            f"[下载]({v['downloads']['windows']}) | "
            f"[下载]({v['downloads']['linux']}) |"
        )

    lines.extend([
        "",
        "### VMware Fusion Pro",
        "",
        "| 版本 | Build | 发布日期 | macOS |",
        "|------|-------|----------|-------|",
    ])

    for v in data["products"]["fusion-pro"]["versions"]:
        lines.append(
            f"| {v['version']} | {v['build']} | {v['release_date']} | "
            f"[下载]({v['downloads']['macos']}) |"
        )

    lines.extend([
        "",
        "## 数据来源",
        "",
        "本项目使用 [Archive.org](https://archive.org) 的 VMware 镜像作为主要来源。",
        "",
        f"- **Archive.org 集合**: [{ARCHIVE_ORG_COLLECTION}](https://archive.org/details/{ARCHIVE_ORG_COLLECTION})",
        "- **维护者**: TheLightDeveloper",
        "- **覆盖范围**: Workstation 2.x - 26H1, Fusion 8.x - 26H1",
        "",
        "## VMware Tools",
        "",
        "- 最新版本: https://packages-prod.broadcom.com/tools/releases/latest/",
        "- 历史版本: https://packages-prod.broadcom.com/tools/frozen/",
        "",
        "## 许可证",
        "",
        "自 2024 年 11 月起，VMware Workstation Pro 和 Fusion Pro 对所有用户（个人、教育、商业）免费。",
        "",
        "## 相关项目",
        "",
        "- [moonheart/vmware-index](https://github.com/moonheart/vmware-index) - VMware 下载索引",
        "- [201853910/VMwareWorkstation](https://github.com/201853910/VMwareWorkstation) - GitHub 镜像",
        "",
        "## License",
        "",
        "本项目仅供学习用途。",
    ])

    readme_path.parent.mkdir(parents=True, exist_ok=True)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"已生成 README 到 {readme_path}")


def main() -> int:
    """主函数"""
    print("VMware 下载链接收集器（无需登录版）")
    print("=" * 50)

    # 收集下载链接
    data = collect_vmware_downloads()

    # 确定输出路径
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    json_path = repo_root / "data" / "vmware_downloads.json"
    readme_path = repo_root / "README.md"

    # 保存结果
    save_to_json(data, json_path)
    generate_readme(data, readme_path)

    # 打印摘要
    print("\n" + "=" * 50)
    print("收集完成！")
    print(f"  Workstation Pro: {len(data['products']['workstation-pro']['versions'])} 个版本")
    print(f"  Fusion Pro: {len(data['products']['fusion-pro']['versions'])} 个版本")
    print(f"\n数据来源: Archive.org (无需登录)")
    print(f"集合地址: https://archive.org/details/{ARCHIVE_ORG_COLLECTION}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
