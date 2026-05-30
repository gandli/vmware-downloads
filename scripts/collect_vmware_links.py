#!/usr/bin/env python3
"""
VMware Download Link Collector
收集 VMware 产品的下载地址
使用 Cloudflare CDN 缓存和 Archive.org 作为来源
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Archive.org 集合地址
ARCHIVE_ORG_COLLECTION = "vmwareworkstationarchive"

# Broadcom CDN 配置（通过 Cloudflare 缓存访问）
BROADCOM_CDN_BASE = "https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/"
CLOUDFLARE_CDN_HOST = "softwareupdate-prod.broadcom.com.cdn.cloudflare.net"

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
        if "u" in version:
            return version.split("u")[0]
        return version
    major = version.split(".")[0]
    return f"{major}.x"


def generate_workstation_downloads(version: str, build: str) -> dict:
    """生成 Workstation 下载链接"""
    folder = get_archive_org_folder(version)
    archive_base = f"https://archive.org/download/{ARCHIVE_ORG_COLLECTION}"

    # Archive.org 链接
    if version.startswith("25H") or version.startswith("26H"):
        archive_windows = f"{archive_base}/{folder}/VMware-Workstation-Full-{version}-{build}.exe"
        archive_linux = f"{archive_base}/{folder}/VMware-Workstation-Full-{version}-{build}.x86_64.bundle"
    else:
        archive_windows = f"{archive_base}/{folder}/VMware-workstation-full-{version}-{build}.exe"
        archive_linux = f"{archive_base}/{folder}/VMware-Workstation-Full-{version}-{build}.x86_64.bundle"

    # Broadcom CDN 链接（需要通过 Cloudflare 缓存访问）
    cdn_windows = f"{BROADCOM_CDN_BASE}ws/{version}/{build}/windows/core/VMware-workstation-{version}-{build}.exe.tar"
    cdn_linux = f"{BROADCOM_CDN_BASE}ws/{version}/{build}/linux/core/VMware-Workstation-{version}-{build}.x86_64.bundle.tar"

    return {
        "archive_org": {
            "windows": archive_windows,
            "linux": archive_linux,
        },
        "broadcom_cdn": {
            "windows": cdn_windows,
            "linux": cdn_linux,
        },
        "techpowerup": "https://www.techpowerup.com/download/vmware-workstation-pro/",
    }


def generate_fusion_downloads(version: str, build: str) -> dict:
    """生成 Fusion 下载链接"""
    folder = get_archive_org_folder(version)
    archive_base = f"https://archive.org/download/{ARCHIVE_ORG_COLLECTION}"

    archive_macos = f"{archive_base}/Fusion/{folder}/VMware-Fusion-{version}-{build}_universal.dmg"

    # Broadcom CDN 链接
    cdn_macos = f"{BROADCOM_CDN_BASE}fusion/{version}/{build}/universal/core/com.vmware.fusion.zip.tar"

    return {
        "archive_org": {
            "macos": archive_macos,
        },
        "broadcom_cdn": {
            "macos": cdn_macos,
        },
        "techpowerup": "https://www.techpowerup.com/download/vmware-fusion/",
    }


def collect_vmware_downloads() -> dict:
    """收集 VMware 下载链接"""
    result = {
        "collected_at": datetime.utcnow().isoformat(),
        "sources": {
            "broadcom_cdn": "Broadcom 官方 CDN（通过 Cloudflare 缓存访问）",
            "archive_org": "Archive.org 社区镜像（无需登录）",
            "techpowerup": "TechPowerUp 第三方下载站点",
        },
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
        "# VMware 下载链接",
        "",
        f"最后更新: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "> **VMware Workstation Pro 和 Fusion Pro 对所有用户免费。**",
        "",
        "## 下载方式",
        "",
        "### 方式一：Broadcom 官方 CDN（推荐）",
        "",
        "Broadcom 官方 CDN 通过 Cloudflare 缓存提供，下载速度最快。",
        "",
        "**使用方法（Linux/macOS）：**",
        "",
        "```bash",
        "# 下载 Workstation Pro（Windows）",
        f"curl -L --connect-to softwareupdate-prod.broadcom.com:443:{CLOUDFLARE_CDN_HOST}:443 \\",
        "  -o VMware-Workstation.exe.tar \\",
        f"  \"{BROADCOM_CDN_BASE}ws/26H1/25388281/windows/core/VMware-workstation-26H1-25388281.exe.tar\"",
        "",
        "# 解压 .tar 文件获得 .exe 安装包",
        "tar -xf VMware-Workstation.exe.tar",
        "",
        "# 下载 Workstation Pro（Linux）",
        f"curl -L --connect-to softwareupdate-prod.broadcom.com:443:{CLOUDFLARE_CDN_HOST}:443 \\",
        "  -o VMware-Workstation.bundle.tar \\",
        f"  \"{BROADCOM_CDN_BASE}ws/26H1/25388281/linux/core/VMware-Workstation-26H1-25388281.x86_64.bundle.tar\"",
        "",
        "# 解压",
        "tar -xf VMware-Workstation.bundle.tar",
        "```",
        "",
        "**使用方法（Windows PowerShell）：**",
        "",
        "```powershell",
        "# 修改 hosts 文件（需要管理员权限）",
        "# 在 C:\\Windows\\System32\\drivers\\etc\\hosts 添加：",
        "# softwareupdate-prod.broadcom.com.cdn.cloudflare.net softwareupdate-prod.broadcom.com",
        "",
        "# 然后直接下载",
        f"Invoke-WebRequest -Uri \"{BROADCOM_CDN_BASE}ws/26H1/25388281/windows/core/VMware-workstation-26H1-25388281.exe.tar\" -OutFile VMware-Workstation.tar",
        "",
        "# 解压",
        "tar -xf VMware-Workstation.tar",
        "```",
        "",
        "### 方式二：TechPowerUp",
        "",
        "TechPowerUp 是可靠的第三方下载站点。",
        "",
        "- [VMware Workstation Pro 下载页面](https://www.techpowerup.com/download/vmware-workstation-pro/)",
        "- [VMware Fusion Pro 下载页面](https://www.techpowerup.com/download/vmware-fusion/)",
        "",
        "### 方式三：Archive.org 镜像",
        "",
        "Archive.org 提供历史版本的镜像，无需登录。",
        "",
        f"- [VMware 镜像集合](https://archive.org/details/{ARCHIVE_ORG_COLLECTION})",
        "",
    ]

    # 最新版本快速下载
    latest_ws = data["products"]["workstation-pro"]["versions"][0]
    latest_fusion = data["products"]["fusion-pro"]["versions"][0]

    lines.extend([
        "## 最新版本",
        "",
        "### VMware Workstation Pro",
        "",
        f"**版本 {latest_ws['version']}** (Build {latest_ws['build']})",
        "",
        "| 平台 | Broadcom CDN | Archive.org |",
        "|------|--------------|-------------|",
        f"| Windows | [CDN]({latest_ws['downloads']['broadcom_cdn']['windows']}) | [下载]({latest_ws['downloads']['archive_org']['windows']}) |",
        f"| Linux | [CDN]({latest_ws['downloads']['broadcom_cdn']['linux']}) | [下载]({latest_ws['downloads']['archive_org']['linux']}) |",
        "",
        "### VMware Fusion Pro",
        "",
        f"**版本 {latest_fusion['version']}** (Build {latest_fusion['build']})",
        "",
        "| 平台 | Broadcom CDN | Archive.org |",
        "|------|--------------|-------------|",
        f"| macOS | [CDN]({latest_fusion['downloads']['broadcom_cdn']['macos']}) | [下载]({latest_fusion['downloads']['archive_org']['macos']}) |",
        "",
    ])

    # 所有版本
    lines.extend([
        "## 所有版本",
        "",
        "### VMware Workstation Pro",
        "",
        "| 版本 | Build | 发布日期 | Windows (CDN) | Linux (CDN) | Windows (Archive) | Linux (Archive) |",
        "|------|-------|----------|---------------|-------------|-------------------|-----------------|",
    ])

    for v in data["products"]["workstation-pro"]["versions"]:
        lines.append(
            f"| {v['version']} | {v['build']} | {v['release_date']} | "
            f"[CDN]({v['downloads']['broadcom_cdn']['windows']}) | "
            f"[CDN]({v['downloads']['broadcom_cdn']['linux']}) | "
            f"[下载]({v['downloads']['archive_org']['windows']}) | "
            f"[下载]({v['downloads']['archive_org']['linux']}) |"
        )

    lines.extend([
        "",
        "### VMware Fusion Pro",
        "",
        "| 版本 | Build | 发布日期 | macOS (CDN) | macOS (Archive) |",
        "|------|-------|----------|-------------|-----------------|",
    ])

    for v in data["products"]["fusion-pro"]["versions"]:
        lines.append(
            f"| {v['version']} | {v['build']} | {v['release_date']} | "
            f"[CDN]({v['downloads']['broadcom_cdn']['macos']}) | "
            f"[下载]({v['downloads']['archive_org']['macos']}) |"
        )

    lines.extend([
        "",
        "## CDN 访问说明",
        "",
        "Broadcom 官方 CDN (`softwareupdate-prod.broadcom.com`) 的 DNS 已被移除，",
        "但可以通过 Cloudflare 边缘缓存访问：",
        "",
        "### Linux/macOS",
        "",
        "使用 `curl --connect-to` 参数：",
        "",
        "```bash",
        f"curl --connect-to softwareupdate-prod.broadcom.com:443:{CLOUDFLARE_CDN_HOST}:443 <URL>",
        "```",
        "",
        "### Windows",
        "",
        "修改 `C:\\Windows\\System32\\drivers\\etc\\hosts` 文件，添加：",
        "",
        "```",
        f"{CLOUDFLARE_CDN_HOST} softwareupdate-prod.broadcom.com",
        "```",
        "",
        "然后直接使用 CDN 链接下载。",
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
    print("VMware 下载链接收集器")
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
    print("\n下载来源:")
    print("  - Broadcom CDN: 官方 CDN（通过 Cloudflare 缓存访问）")
    print("  - Archive.org: 社区维护的镜像（无需登录）")
    print("  - TechPowerUp: 第三方下载站点")

    return 0


if __name__ == "__main__":
    sys.exit(main())
