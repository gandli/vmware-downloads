#!/usr/bin/env python3
"""
VMware Download Link Collector
收集 VMware 产品的下载地址，支持 SHA 校验和 aria2 下载
使用 Broadcom CDN（通过 Cloudflare 缓存）作为首选来源
"""

import hashlib
import json
import sys
import urllib.request
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
        archive_linux = f"{archive_base}/Linux/{folder}/VMware-Workstation-Full-{version}-{build}.x86_64.bundle"
    else:
        archive_windows = f"{archive_base}/{folder}/VMware-workstation-full-{version}-{build}.exe"
        archive_linux = f"{archive_base}/{folder}/VMware-Workstation-Full-{version}-{build}.x86_64.bundle"

    # Broadcom CDN 链接（需要通过 Cloudflare 缓存访问）
    cdn_windows = f"{BROADCOM_CDN_BASE}ws/{version}/{build}/windows/core/VMware-workstation-{version}-{build}.exe.tar"
    cdn_linux = f"{BROADCOM_CDN_BASE}ws/{version}/{build}/linux/core/VMware-Workstation-{version}-{build}.x86_64.bundle.tar"

    return {
        "broadcom_cdn": {
            "windows": cdn_windows,
            "linux": cdn_linux,
        },
        "archive_org": {
            "windows": archive_windows,
            "linux": archive_linux,
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
        "broadcom_cdn": {
            "macos": cdn_macos,
        },
        "archive_org": {
            "macos": archive_macos,
        },
        "techpowerup": "https://www.techpowerup.com/download/vmware-fusion/",
    }


def collect_vmware_downloads() -> dict:
    """收集 VMware 下载链接"""
    result = {
        "collected_at": datetime.utcnow().isoformat(),
        "sources": {
            "broadcom_cdn": {
                "name": "Broadcom 官方 CDN（推荐）",
                "note": "通过 Cloudflare 缓存访问，速度最快",
                "curl_option": f"--connect-to softwareupdate-prod.broadcom.com:443:{CLOUDFLARE_CDN_HOST}:443",
            },
            "archive_org": {
                "name": "Archive.org 社区镜像",
                "note": "无需登录，社区维护",
            },
            "techpowerup": {
                "name": "TechPowerUp",
                "note": "可靠的第三方下载站点",
            },
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


def generate_aria2_configs(data: dict, output_dir: Path) -> None:
    """生成 aria2 下载配置文件"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成 Workstation Pro aria2 文件
    ws_aria2_lines = []
    for v in data["products"]["workstation-pro"]["versions"]:
        # 优先使用 Broadcom CDN
        ws_aria2_lines.append(f"# VMware Workstation Pro v{v['version']} (build {v['build']})")
        ws_aria2_lines.append(v["downloads"]["broadcom_cdn"]["windows"])
        ws_aria2_lines.append(f"  out=VMware-Workstation-{v['version']}-Windows.exe.tar")
        ws_aria2_lines.append(f"  header=Host: {CLOUDFLARE_CDN_HOST}")
        ws_aria2_lines.append("")
        ws_aria2_lines.append(v["downloads"]["broadcom_cdn"]["linux"])
        ws_aria2_lines.append(f"  out=VMware-Workstation-{v['version']}-Linux.bundle.tar")
        ws_aria2_lines.append(f"  header=Host: {CLOUDFLARE_CDN_HOST}")
        ws_aria2_lines.append("")

    ws_aria2_path = output_dir / "vmware-workstation-pro.aria2"
    with open(ws_aria2_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ws_aria2_lines))
    print(f"已生成 Workstation aria2 配置: {ws_aria2_path}")

    # 生成 Fusion Pro aria2 文件
    fusion_aria2_lines = []
    for v in data["products"]["fusion-pro"]["versions"]:
        fusion_aria2_lines.append(f"# VMware Fusion Pro v{v['version']} (build {v['build']})")
        fusion_aria2_lines.append(v["downloads"]["broadcom_cdn"]["macos"])
        fusion_aria2_lines.append(f"  out=VMware-Fusion-{v['version']}-macOS.zip.tar")
        fusion_aria2_lines.append(f"  header=Host: {CLOUDFLARE_CDN_HOST}")
        fusion_aria2_lines.append("")

    fusion_aria2_path = output_dir / "vmware-fusion-pro.aria2"
    with open(fusion_aria2_path, "w", encoding="utf-8") as f:
        f.write("\n".join(fusion_aria2_lines))
    print(f"已生成 Fusion aria2 配置: {fusion_aria2_path}")


def generate_download_scripts(data: dict, output_dir: Path) -> None:
    """生成下载脚本"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Linux/macOS 下载脚本
    sh_lines = [
        "#!/bin/bash",
        "# VMware 下载脚本（使用 aria2）",
        "",
        "# 检查 aria2 是否安装",
        "if ! command -v aria2c &> /dev/null; then",
        '    echo "错误: 未安装 aria2"',
        '    echo "请先安装 aria2: https://aria2.github.io/"',
        "    exit 1",
        "fi",
        "",
        "# 下载目录",
        'DOWNLOAD_DIR="./vmware-downloads"',
        'mkdir -p "$DOWNLOAD_DIR"',
        "",
        "# 使用 aria2 下载",
        'echo "开始下载 VMware 产品..."',
        'aria2c --dir="$DOWNLOAD_DIR" --file-allocation=none --check-integrity=true \\',
        "  --connect-timeout=30 --retry-wait=5 --max-tries=3 \\",
        "  -i vmware-workstation-pro.aria2",
        "",
        'echo "下载完成！"',
    ]

    sh_path = output_dir / "download.sh"
    with open(sh_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sh_lines))
    print(f"已生成下载脚本: {sh_path}")

    # Windows PowerShell 下载脚本
    ps1_lines = [
        "# VMware 下载脚本（使用 aria2）",
        "",
        "# 检查 aria2 是否安装",
        "if (-not (Get-Command aria2c -ErrorAction SilentlyContinue)) {",
        '    Write-Error "错误: 未安装 aria2"',
        '    Write-Host "请先安装 aria2: https://aria2.github.io/"',
        "    exit 1",
        "}",
        "",
        "# 下载目录",
        '$DOWNLOAD_DIR = ".\\vmware-downloads"',
        "New-Item -ItemType Directory -Force -Path $DOWNLOAD_DIR | Out-Null",
        "",
        "# 使用 aria2 下载",
        'Write-Host "开始下载 VMware 产品..."',
        'aria2c --dir="$DOWNLOAD_DIR" --file-allocation=none --check-integrity=true `',
        "  --connect-timeout=30 --retry-wait=5 --max-tries=3 `",
        "  -i vmware-workstation-pro.aria2",
        "",
        'Write-Host "下载完成！"',
    ]

    ps1_path = output_dir / "download.ps1"
    with open(ps1_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ps1_lines))
    print(f"已生成下载脚本: {ps1_path}")


def generate_sha256_checklist(data: dict, output_dir: Path) -> None:
    """生成 SHA256 校验清单"""
    output_dir.mkdir(parents=True, exist_ok=True)

    sha_lines = [
        "# VMware 下载文件 SHA256 校验清单",
        f"# 生成时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "#",
        "# 使用方法:",
        "# Linux/macOS: sha256sum -c vmware-sha256.txt",
        "# Windows: Get-FileHash -Algorithm SHA256 <file>",
        "",
    ]

    # Workstation Pro
    sha_lines.append("# VMware Workstation Pro")
    for v in data["products"]["workstation-pro"]["versions"]:
        sha_lines.append(f"# v{v['version']} (build {v['build']})")
        sha_lines.append(f"<sha256>  VMware-Workstation-{v['version']}-Windows.exe.tar")
        sha_lines.append(f"<sha256>  VMware-Workstation-{v['version']}-Linux.bundle.tar")
    sha_lines.append("")

    # Fusion Pro
    sha_lines.append("# VMware Fusion Pro")
    for v in data["products"]["fusion-pro"]["versions"]:
        sha_lines.append(f"# v{v['version']} (build {v['build']})")
        sha_lines.append(f"<sha256>  VMware-Fusion-{v['version']}-macOS.zip.tar")
    sha_lines.append("")

    sha_path = output_dir / "vmware-sha256.txt"
    with open(sha_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sha_lines))
    print(f"已生成 SHA256 校验清单: {sha_path}")


def generate_readme(data: dict, readme_path: Path) -> None:
    """生成 README.md"""
    lines = [
        "# VMware 下载链接",
        "",
        f"最后更新: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "> **VMware Workstation Pro 和 Fusion Pro 对所有用户免费。**",
        "",
        "## 快速下载（使用 aria2）",
        "",
        "### 安装 aria2",
        "",
        "```bash",
        "# macOS",
        "brew install aria2",
        "",
        "# Ubuntu/Debian",
        "sudo apt install aria2",
        "",
        "# Windows (winget)",
        "winget install aria2",
        "```",
        "",
        "### 下载方法",
        "",
        "```bash",
        "# 下载所有版本",
        "bash download.sh",
        "",
        "# 或使用 PowerShell",
        ".\\download.ps1",
        "",
        "# 下载单个文件",
        f"aria2c --connect-to softwareupdate-prod.broadcom.com:443:{CLOUDFLARE_CDN_HOST}:443 \\",
        "  'https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/26H1/25388281/windows/core/VMware-workstation-26H1-25388281.exe.tar'",
        "```",
        "",
        "## 下载方式",
        "",
        "### 方式一：Broadcom 官方 CDN（推荐）",
        "",
        "Broadcom 官方 CDN 通过 Cloudflare 缓存提供，下载速度最快。",
        "",
        "**使用方法（Linux/macOS curl）：**",
        "",
        "```bash",
        "# 下载 Workstation Pro（Windows）",
        f"curl -L --connect-to softwareupdate-prod.broadcom.com:443:{CLOUDFLARE_CDN_HOST}:443 \\",
        "  -o VMware-Workstation.exe.tar \\",
        f"  \"{BROADCOM_CDN_BASE}ws/26H1/25388281/windows/core/VMware-workstation-26H1-25388281.exe.tar\"",
        "",
        "# 解压 .tar 文件获得 .exe 安装包",
        "tar -xf VMware-Workstation.exe.tar",
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
        "## 文件校验",
        "",
        "下载后请校验文件完整性：",
        "",
        "```bash",
        "# Linux/macOS",
        "sha256sum -c vmware-sha256.txt",
        "",
        "# Windows PowerShell",
        "Get-FileHash -Algorithm SHA256 VMware-Workstation-26H1-Windows.exe.tar",
        "```",
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
    aria2_dir = repo_root / "aria2"

    # 保存结果
    save_to_json(data, json_path)
    generate_aria2_configs(data, aria2_dir)
    generate_download_scripts(data, aria2_dir)
    generate_sha256_checklist(data, aria2_dir)
    generate_readme(data, readme_path)

    # 打印摘要
    print("\n" + "=" * 50)
    print("收集完成！")
    print(f"  Workstation Pro: {len(data['products']['workstation-pro']['versions'])} 个版本")
    print(f"  Fusion Pro: {len(data['products']['fusion-pro']['versions'])} 个版本")
    print("\n生成的文件:")
    print(f"  - {json_path}")
    print(f"  - {readme_path}")
    print(f"  - {aria2_dir / 'vmware-workstation-pro.aria2'}")
    print(f"  - {aria2_dir / 'vmware-fusion-pro.aria2'}")
    print(f"  - {aria2_dir / 'download.sh'}")
    print(f"  - {aria2_dir / 'download.ps1'}")
    print(f"  - {aria2_dir / 'vmware-sha256.txt'}")
    print("\n下载方式:")
    print("  - Broadcom CDN: 官方 CDN（推荐，速度最快）")
    print("  - Archive.org: 社区镜像（无需登录）")
    print("  - TechPowerUp: 第三方下载站点")

    return 0


if __name__ == "__main__":
    sys.exit(main())
