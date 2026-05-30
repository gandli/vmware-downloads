#!/usr/bin/env python3
"""
VMware Release Uploader
下载 VMware 安装包并上传到 GitHub Releases
"""

import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

# GitHub 仓库
REPO = "gandli/vmware-downloads"

# 要上传的版本
RELEASES = [
    {
        "tag": "workstation-26H1",
        "name": "VMware Workstation Pro 26H1",
        "files": [
            {
                "url": "https://archive.org/download/vmwareworkstationarchive/26H1/VMware-Workstation-Full-26H1-25388281.exe",
                "filename": "VMware-Workstation-Full-26H1-25388281.exe",
                "platform": "Windows",
            },
            {
                "url": "https://archive.org/download/vmwareworkstationarchive/Linux/26H1/VMware-Workstation-Full-26H1-25388281.x86_64.bundle",
                "filename": "VMware-Workstation-Full-26H1-25388281.x86_64.bundle",
                "platform": "Linux",
            },
        ],
    },
    {
        "tag": "workstation-25H2",
        "name": "VMware Workstation Pro 25H2",
        "files": [
            {
                "url": "https://archive.org/download/vmwareworkstationarchive/25H2/VMware-Workstation-Full-25H2-24995812.exe",
                "filename": "VMware-Workstation-Full-25H2-24995812.exe",
                "platform": "Windows",
            },
            {
                "url": "https://archive.org/download/vmwareworkstationarchive/Linux/25H2/VMware-Workstation-Full-25H2-24995812.x86_64.bundle",
                "filename": "VMware-Workstation-Full-25H2-24995812.x86_64.bundle",
                "platform": "Linux",
            },
        ],
    },
    {
        "tag": "fusion-26H1",
        "name": "VMware Fusion Pro 26H1",
        "files": [
            {
                "url": "https://archive.org/download/vmwareworkstationarchive/Fusion/26H1/VMware-Fusion-26H1-25388279_universal.dmg",
                "filename": "VMware-Fusion-26H1-25388279_universal.dmg",
                "platform": "macOS",
            },
        ],
    },
]


def download_file(url: str, filename: str) -> bool:
    """下载文件"""
    print(f"  下载: {filename}")
    try:
        urllib.request.urlretrieve(url, filename)
        size = os.path.getsize(filename)
        print(f"  完成: {size / 1024 / 1024:.1f} MB")
        return True
    except Exception as e:
        print(f"  失败: {e}")
        return False


def calculate_sha256(filename: str) -> str:
    """计算 SHA256"""
    sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def create_release(tag: str, name: str, files: list) -> bool:
    """创建 GitHub Release"""
    print(f"\n创建 Release: {name}")

    # 构建 release notes
    notes = f"# {name}\n\n"
    notes += "## 下载文件\n\n"
    notes += "| 文件 | 平台 | SHA256 |\n"
    notes += "|------|------|--------|\n"

    for f in files:
        if os.path.exists(f["filename"]):
            sha256 = calculate_sha256(f["filename"])
            notes += f"| {f['filename']} | {f['platform']} | `{sha256}` |\n"

    notes += "\n## 验证文件\n\n"
    notes += "```bash\n"
    notes += "# Linux/macOS\n"
    notes += "sha256sum -c checksums.txt\n\n"
    notes += "# Windows PowerShell\n"
    notes += "Get-FileHash -Algorithm SHA256 <file>\n"
    notes += "```\n"

    # 创建 release
    cmd = ["gh", "release", "create", tag, "--repo", REPO, "--title", name, "--notes", notes]

    # 添加文件
    for f in files:
        if os.path.exists(f["filename"]):
            cmd.append(f["filename"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  成功: {result.stdout.strip()}")
            return True
        else:
            print(f"  失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"  错误: {e}")
        return False


def main():
    """主函数"""
    print("VMware Release Uploader")
    print("=" * 50)

    # 创建临时目录
    tmp_dir = Path("tmp_downloads")
    tmp_dir.mkdir(exist_ok=True)

    success_count = 0
    for release in RELEASES:
        print(f"\n处理: {release['name']}")

        # 下载文件
        all_downloaded = True
        for f in release["files"]:
            filepath = tmp_dir / f["filename"]
            if not filepath.exists():
                if not download_file(f["url"], str(filepath)):
                    all_downloaded = False
                    break
            else:
                print(f"  已存在: {f['filename']}")

        # 创建 release
        if all_downloaded:
            # 切换到临时目录执行 gh 命令
            os.chdir(tmp_dir)
            if create_release(release["tag"], release["name"], release["files"]):
                success_count += 1
            os.chdir("..")

    # 清理
    print(f"\n完成: {success_count}/{len(RELEASES)} 个 Release")

    # 删除临时目录
    import shutil
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

    return 0 if success_count == len(RELEASES) else 1


if __name__ == "__main__":
    sys.exit(main())
