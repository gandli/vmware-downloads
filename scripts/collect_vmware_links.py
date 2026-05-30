#!/usr/bin/env python3
"""
VMware Link Collector
从 Broadcom 官方获取 SHA256，从 Archive.org 获取直链
"""

import hashlib
import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

# Archive.org 集合地址
ARCHIVE_ORG_COLLECTION = "vmwareworkstationarchive"

# Broadcom 官方下载页面
BROADCOM_URLS = {
    "workstation_pro": "https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro&freeDownloads=true",
    "fusion_pro": "https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Fusion%20Pro&freeDownloads=true",
}

# 版本信息
# SHA256 来源：
# - Broadcom 官方下载页面（通过浏览器获取）
# - Chocolatey 包管理器 (community.chocolatey.org)
# - GitHub 社区 (201853910/VMwareWorkstation)
# - TechPowerUp 下载页面
VERSIONS = {
    "workstation": {
        "26H1": {
            "build": "25388281",
            "date": "2026-04-15",
            "sha256": {
                "windows": "a0ef9087607d9cad20b08139e73e41242e044ad5bd8cee141d3bad314586737f",
                "linux": "3f6d2501e654dbc7701a8290ff6ffcfba6c5444cd5f35f4933cd08c9499f6d84",
            },
        },
        "25H2": {
            "build": "24995812",
            "date": "2025-10-14",
            "sha256": {
                "windows": "49ad7c2bbce854ed30ed0702d1af9fc042697777dc981e087bfa7241045b0361",
                "linux": "9beced8a0653c9382e9aa9917168a54bf5635e566c8cb341589d72cf14093322",
            },
        },
        "17.6.4": {
            "build": "24832109",
            "date": "2025-07-15",
            "sha256": {
                "windows": "10fe3a36f525d88aa133118ab3b5a16b18da88d4aa11b14d74e4164b3fb94ba9",
                "linux": "64fbfbaeacc48865468114362a2bbaade9110cc9e87bc3bd938396ba7f19a9bd",
            },
        },
        "17.6.3": {
            "build": "24583834",
            "date": "2025-02-24",
            "sha256": {
                "windows": "2e87994dd2580bc006a0b96ef089f500a718d05c3302d78bd9c85df4439cf67c",
                "linux": "85ca2c19a13b0d85b121a5f737408c3d7f96dae7cde7cb5f5bbfa4f582fdeef3",
            },
        },
        "17.6.2": {
            "build": "24409262",
            "date": "2024-12-15",
            "sha256": {
                "windows": "d0f62805019d1ca5a1d5bafdf4d030dd782bd17abecea0662a5197563825ec8b",
                "linux": "15536dfc5afbbcf42daec10b1d9d1d6da3ca27da478938defc9c558064ff09f7",
            },
        },
    },
    "fusion": {
        "26H1": {
            "build": "25388279",
            "date": "2026-04-15",
            "sha256": {
                "macos": "c1d373aa21be25674e3ecc518819e255785dea9d456d8747bcb0a2a59244bdf6",
            },
        },
        "13.6.4": {
            "build": "24832108",
            "date": "2025-07-15",
            "sha256": {
                "macos": "a43fd031165896bc1b7ecc61eb07b377bfc01b014c9111b08e18a6a1af121191",
            },
        },
    },
}


def get_archive_org_folder(version: str) -> str:
    """获取 Archive.org 文件夹名"""
    if version.startswith("25H") or version.startswith("26H"):
        if "u" in version:
            return version.split("u")[0]
        return version
    return f"{version.split('.')[0]}.x"


def generate_links(product: str, version: str, build: str) -> dict:
    """生成下载链接"""
    base = f"https://archive.org/download/{ARCHIVE_ORG_COLLECTION}"
    folder = get_archive_org_folder(version)

    if product == "workstation":
        if version.startswith("25H") or version.startswith("26H"):
            win = f"{base}/{folder}/VMware-Workstation-Full-{version}-{build}.exe"
            linux = f"{base}/Linux/{folder}/VMware-Workstation-Full-{version}-{build}.x86_64.bundle"
        else:
            win = f"{base}/{folder}/VMware-workstation-full-{version}-{build}.exe"
            linux = f"{base}/Linux/{folder}/VMware-Workstation-Full-{version}-{build}.x86_64.bundle"
        return {"windows": win, "linux": linux}
    else:
        macos = f"{base}/Fusion/{folder}/VMware-Fusion-{version}-{build}_universal.dmg"
        return {"macos": macos}


def verify_link(url: str, timeout: int = 30, retries: int = 3) -> tuple[bool, str]:
    """验证链接可访问性（带重试）"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, method='GET')
            req.add_header('Range', 'bytes=0-0')
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status in (200, 206):
                    size = response.headers.get("Content-Length", "N/A")
                    content_range = response.headers.get("Content-Range", "")
                    if content_range and '/' in content_range:
                        size = content_range.split('/')[-1]
                    if size != "N/A":
                        size_mb = f"{int(size) / 1024 / 1024:.1f} MB"
                    else:
                        size_mb = "N/A"
                    return True, size_mb
                if attempt < retries - 1:
                    continue
                return False, f"HTTP {response.status}"
        except Exception as e:
            if attempt < retries - 1:
                continue
            return False, str(e)
    return False, "Max retries exceeded"


def calculate_sha256_from_url(url: str, timeout: int = 300) -> str | None:
    """从 URL 下载完整文件并计算 SHA256"""
    try:
        sha256 = hashlib.sha256()
        with urllib.request.urlopen(url, timeout=timeout) as response:
            total = 0
            for chunk in iter(lambda: response.read(8192), b''):
                sha256.update(chunk)
                total += len(chunk)
                # 每 10MB 打印进度
                if total % (10 * 1024 * 1024) < 8192:
                    print(f"    已下载: {total / 1024 / 1024:.1f} MB", end='\r')
        print(f"    已下载: {total / 1024 / 1024:.1f} MB")
        return sha256.hexdigest()
    except Exception as e:
        print(f"    计算 SHA256 失败: {e}")
        return None


def collect_downloads() -> dict:
    """收集下载链接"""
    result = {
        "collected_at": datetime.utcnow().isoformat(),
        "official": BROADCOM_URLS,
        "archive_org": f"https://archive.org/details/{ARCHIVE_ORG_COLLECTION}",
        "workstation_pro": [],
        "fusion_pro": [],
    }

    # 收集 Workstation
    print("收集 VMware Workstation Pro...")
    for version, info in VERSIONS["workstation"].items():
        links = generate_links("workstation", version, info["build"])

        # 验证链接
        print(f"  v{version} (build {info['build']}):")
        verified_links = {}
        sha256_values = dict(info["sha256"])
        for platform, url in links.items():
            ok, size = verify_link(url)
            if ok:
                verified_links[platform] = {"url": url, "size": size}
                print(f"    [OK] {platform}: {size}")
                # 如果 SHA256 缺失，自动计算
                if not sha256_values.get(platform):
                    print(f"    计算 {platform} SHA256...")
                    sha256 = calculate_sha256_from_url(url)
                    if sha256:
                        sha256_values[platform] = sha256
                        print(f"    [OK] SHA256: {sha256[:16]}...")
            else:
                print(f"    [FAIL] {platform}: {size}")

        result["workstation_pro"].append({
            "version": version,
            "build": info["build"],
            "date": info["date"],
            "downloads": verified_links,
            "sha256": sha256_values,
        })

    # 收集 Fusion
    print("\n收集 VMware Fusion Pro...")
    for version, info in VERSIONS["fusion"].items():
        links = generate_links("fusion", version, info["build"])

        print(f"  v{version} (build {info['build']}):")
        verified_links = {}
        sha256_values = dict(info["sha256"])
        for platform, url in links.items():
            ok, size = verify_link(url)
            if ok:
                verified_links[platform] = {"url": url, "size": size}
                print(f"    [OK] {platform}: {size}")
                # 如果 SHA256 缺失，自动计算
                if not sha256_values.get(platform):
                    print(f"    计算 {platform} SHA256...")
                    sha256 = calculate_sha256_from_url(url)
                    if sha256:
                        sha256_values[platform] = sha256
                        print(f"    [OK] SHA256: {sha256[:16]}...")
            else:
                print(f"    [FAIL] {platform}: {size}")

        result["fusion_pro"].append({
            "version": version,
            "build": info["build"],
            "date": info["date"],
            "downloads": verified_links,
            "sha256": sha256_values,
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
        "> **所有链接均可直接下载，无需登录。**",
        "",
        "## 快速下载",
        "",
        "### VMware Workstation Pro",
        "",
        f"**{ws_latest['version']}** (Build {ws_latest['build']})",
        "",
    ]

    # Workstation 下载链接
    for platform, info in ws_latest["downloads"].items():
        sha256 = ws_latest["sha256"].get(platform, "")
        sha_str = f" | SHA256: `{sha256[:16]}...`" if sha256 else ""
        lines.append(f"- **{platform.title()}**: [{info['url']}]({info['url']}) ({info['size']}{sha_str})")

    lines.extend([
        "",
        "### VMware Fusion Pro",
        "",
        f"**{fusion_latest['version']}** (Build {fusion_latest['build']})",
        "",
    ])

    # Fusion 下载链接
    for platform, info in fusion_latest["downloads"].items():
        sha256 = fusion_latest["sha256"].get(platform, "")
        sha_str = f" | SHA256: `{sha256[:16]}...`" if sha256 else ""
        lines.append(f"- **{platform.title()}**: [{info['url']}]({info['url']}) ({info['size']}{sha_str})")

    # 所有版本表格（包含 SHA256）
    lines.extend([
        "",
        "## 所有版本",
        "",
        "### VMware Workstation Pro",
        "",
        "| 版本 | Build | 日期 | Windows | Windows SHA256 | Linux | Linux SHA256 |",
        "|------|-------|------|---------|----------------|-------|--------------|",
    ])

    for v in data["workstation_pro"]:
        win = v["downloads"].get("windows", {})
        linux = v["downloads"].get("linux", {})
        win_sha = v["sha256"].get("windows", "")
        linux_sha = v["sha256"].get("linux", "")
        win_link = f"[下载]({win['url']}) ({win['size']})" if win else "N/A"
        linux_link = f"[下载]({linux['url']}) ({linux['size']})" if linux else "N/A"
        win_sha_str = f"`{win_sha[:16]}...`" if win_sha else "N/A"
        linux_sha_str = f"`{linux_sha[:16]}...`" if linux_sha else "N/A"
        lines.append(f"| {v['version']} | {v['build']} | {v['date']} | {win_link} | {win_sha_str} | {linux_link} | {linux_sha_str} |")

    lines.extend([
        "",
        "### VMware Fusion Pro",
        "",
        "| 版本 | Build | 日期 | macOS | SHA256 |",
        "|------|-------|------|-------|--------|",
    ])

    for v in data["fusion_pro"]:
        macos = v["downloads"].get("macos", {})
        macos_sha = v["sha256"].get("macos", "")
        macos_link = f"[下载]({macos['url']}) ({macos['size']})" if macos else "N/A"
        macos_sha_str = f"`{macos_sha[:16]}...`" if macos_sha else "N/A"
        lines.append(f"| {v['version']} | {v['build']} | {v['date']} | {macos_link} | {macos_sha_str} |")

    lines.extend([
        "",
        "## 完整 SHA256 校验值",
        "",
        "```",
    ])

    for v in data["workstation_pro"]:
        for platform, sha in v["sha256"].items():
            if sha:
                filename = f"VMware-Workstation-Full-{v['version']}-{v['build']}"
                if platform == "windows":
                    filename += ".exe"
                else:
                    filename += ".x86_64.bundle"
                lines.append(f"{sha}  {filename}")

    for v in data["fusion_pro"]:
        for platform, sha in v["sha256"].items():
            if sha:
                filename = f"VMware-Fusion-{v['version']}-{v['build']}_universal.dmg"
                lines.append(f"{sha}  {filename}")

    lines.append("```")

    lines.extend([
        "",
        "## 验证文件",
        "",
        "```bash",
        "# Linux/macOS",
        "sha256sum -c checksums.txt",
        "",
        "# Windows PowerShell",
        "Get-FileHash -Algorithm SHA256 <file>",
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
    print("=" * 50)

    data = collect_downloads()

    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    save_json(data, repo_root / "data" / "vmware_downloads.json")
    generate_readme(data, repo_root / "README.md")

    print(f"\n收集完成！")
    print(f"  Workstation Pro: {len(data['workstation_pro'])} 个版本")
    print(f"  Fusion Pro: {len(data['fusion_pro'])} 个版本")

    return 0


if __name__ == "__main__":
    sys.exit(main())
