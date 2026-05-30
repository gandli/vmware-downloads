# VMware 下载链接

最后更新: 2026-05-30 03:12 UTC

> **VMware Workstation Pro 和 Fusion Pro 对所有用户免费。**

## 快速下载（使用 aria2）

### 安装 aria2

```bash
# macOS
brew install aria2

# Ubuntu/Debian
sudo apt install aria2

# Windows (winget)
winget install aria2
```

### 下载方法

```bash
# 下载所有版本
bash download.sh

# 或使用 PowerShell
.\download.ps1

# 下载单个文件
aria2c --connect-to softwareupdate-prod.broadcom.com:443:softwareupdate-prod.broadcom.com.cdn.cloudflare.net:443 \
  'https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/26H1/25388281/windows/core/VMware-workstation-26H1-25388281.exe.tar'
```

## 下载方式

### 方式一：Broadcom 官方 CDN（推荐）

Broadcom 官方 CDN 通过 Cloudflare 缓存提供，下载速度最快。

**使用方法（Linux/macOS curl）：**

```bash
# 下载 Workstation Pro（Windows）
curl -L --connect-to softwareupdate-prod.broadcom.com:443:softwareupdate-prod.broadcom.com.cdn.cloudflare.net:443 \
  -o VMware-Workstation.exe.tar \
  "https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/26H1/25388281/windows/core/VMware-workstation-26H1-25388281.exe.tar"

# 解压 .tar 文件获得 .exe 安装包
tar -xf VMware-Workstation.exe.tar
```

### 方式二：TechPowerUp

TechPowerUp 是可靠的第三方下载站点。

- [VMware Workstation Pro 下载页面](https://www.techpowerup.com/download/vmware-workstation-pro/)
- [VMware Fusion Pro 下载页面](https://www.techpowerup.com/download/vmware-fusion/)

### 方式三：Archive.org 镜像

Archive.org 提供历史版本的镜像，无需登录。

- [VMware 镜像集合](https://archive.org/details/vmwareworkstationarchive)

## 最新版本

### VMware Workstation Pro

**版本 26H1** (Build 25388281)

| 平台 | Broadcom CDN | Archive.org |
|------|--------------|-------------|
| Windows | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/26H1/25388281/windows/core/VMware-workstation-26H1-25388281.exe.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/26H1/VMware-Workstation-Full-26H1-25388281.exe) |
| Linux | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/26H1/25388281/linux/core/VMware-Workstation-26H1-25388281.x86_64.bundle.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/26H1/VMware-Workstation-Full-26H1-25388281.x86_64.bundle) |

### VMware Fusion Pro

**版本 26H1** (Build 25388279)

| 平台 | Broadcom CDN | Archive.org |
|------|--------------|-------------|
| macOS | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/fusion/26H1/25388279/universal/core/com.vmware.fusion.zip.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/26H1/VMware-Fusion-26H1-25388279_universal.dmg) |

## 所有版本

### VMware Workstation Pro

| 版本 | Build | 发布日期 | Windows (CDN) | Linux (CDN) | Windows (Archive) | Linux (Archive) |
|------|-------|----------|---------------|-------------|-------------------|-----------------|
| 26H1 | 25388281 | 2026-04-15 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/26H1/25388281/windows/core/VMware-workstation-26H1-25388281.exe.tar) | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/26H1/25388281/linux/core/VMware-Workstation-26H1-25388281.x86_64.bundle.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/26H1/VMware-Workstation-Full-26H1-25388281.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/26H1/VMware-Workstation-Full-26H1-25388281.x86_64.bundle) |
| 25H2u1 | 25219725 | 2026-02-26 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/25H2u1/25219725/windows/core/VMware-workstation-25H2u1-25219725.exe.tar) | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/25H2u1/25219725/linux/core/VMware-Workstation-25H2u1-25219725.x86_64.bundle.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/25H2/VMware-Workstation-Full-25H2u1-25219725.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/25H2/VMware-Workstation-Full-25H2u1-25219725.x86_64.bundle) |
| 25H2 | 24995812 | 2025-10-14 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/25H2/24995812/windows/core/VMware-workstation-25H2-24995812.exe.tar) | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/25H2/24995812/linux/core/VMware-Workstation-25H2-24995812.x86_64.bundle.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/25H2/VMware-Workstation-Full-25H2-24995812.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/25H2/VMware-Workstation-Full-25H2-24995812.x86_64.bundle) |
| 17.6.4 | 24832109 | 2025-07-15 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/17.6.4/24832109/windows/core/VMware-workstation-17.6.4-24832109.exe.tar) | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/17.6.4/24832109/linux/core/VMware-Workstation-17.6.4-24832109.x86_64.bundle.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.4-24832109.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-Workstation-Full-17.6.4-24832109.x86_64.bundle) |
| 17.6.3 | 24583834 | 2025-02-24 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/17.6.3/24583834/windows/core/VMware-workstation-17.6.3-24583834.exe.tar) | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/17.6.3/24583834/linux/core/VMware-Workstation-17.6.3-24583834.x86_64.bundle.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.3-24583834.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-Workstation-Full-17.6.3-24583834.x86_64.bundle) |
| 17.6.2 | 24409262 | 2024-12-15 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/17.6.2/24409262/windows/core/VMware-workstation-17.6.2-24409262.exe.tar) | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/17.6.2/24409262/linux/core/VMware-Workstation-17.6.2-24409262.x86_64.bundle.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.2-24409262.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-Workstation-Full-17.6.2-24409262.x86_64.bundle) |
| 17.6.1 | 24319023 | 2024-10-08 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/17.6.1/24319023/windows/core/VMware-workstation-17.6.1-24319023.exe.tar) | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/17.6.1/24319023/linux/core/VMware-Workstation-17.6.1-24319023.x86_64.bundle.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.1-24319023.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-Workstation-Full-17.6.1-24319023.x86_64.bundle) |
| 17.6.0 | 24238078 | 2024-08-28 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/17.6.0/24238078/windows/core/VMware-workstation-17.6.0-24238078.exe.tar) | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/17.6.0/24238078/linux/core/VMware-Workstation-17.6.0-24238078.x86_64.bundle.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.0-24238078.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-Workstation-Full-17.6.0-24238078.x86_64.bundle) |
| 17.5.2 | 23775571 | 2024-05-10 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/17.5.2/23775571/windows/core/VMware-workstation-17.5.2-23775571.exe.tar) | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/ws/17.5.2/23775571/linux/core/VMware-Workstation-17.5.2-23775571.x86_64.bundle.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.5.2-23775571.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-Workstation-Full-17.5.2-23775571.x86_64.bundle) |

### VMware Fusion Pro

| 版本 | Build | 发布日期 | macOS (CDN) | macOS (Archive) |
|------|-------|----------|-------------|-----------------|
| 26H1 | 25388279 | 2026-04-15 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/fusion/26H1/25388279/universal/core/com.vmware.fusion.zip.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/26H1/VMware-Fusion-26H1-25388279_universal.dmg) |
| 25H2u1 | 25219963 | 2026-02-26 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/fusion/25H2u1/25219963/universal/core/com.vmware.fusion.zip.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/25H2/VMware-Fusion-25H2u1-25219963_universal.dmg) |
| 25H2 | 24995814 | 2025-10-14 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/fusion/25H2/24995814/universal/core/com.vmware.fusion.zip.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/25H2/VMware-Fusion-25H2-24995814_universal.dmg) |
| 13.6.4 | 24832108 | 2025-07-15 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/fusion/13.6.4/24832108/universal/core/com.vmware.fusion.zip.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.6.4-24832108_universal.dmg) |
| 13.6.3 | 24585314 | 2025-02-24 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/fusion/13.6.3/24585314/universal/core/com.vmware.fusion.zip.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.6.3-24585314_universal.dmg) |
| 13.6.1 | 23298819 | 2024-11-19 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/fusion/13.6.1/23298819/universal/core/com.vmware.fusion.zip.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.6.1-23298819_universal.dmg) |
| 13.6.0 | 23278157 | 2024-09-17 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/fusion/13.6.0/23278157/universal/core/com.vmware.fusion.zip.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.6.0-23278157_universal.dmg) |
| 13.5.2 | 23324145 | 2024-06-25 | [CDN](https://softwareupdate-prod.broadcom.com/cds/vmw-desktop/fusion/13.5.2/23324145/universal/core/com.vmware.fusion.zip.tar) | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.5.2-23324145_universal.dmg) |

## 文件校验

下载后请校验文件完整性：

```bash
# Linux/macOS
sha256sum -c vmware-sha256.txt

# Windows PowerShell
Get-FileHash -Algorithm SHA256 VMware-Workstation-26H1-Windows.exe.tar
```

## CDN 访问说明

Broadcom 官方 CDN (`softwareupdate-prod.broadcom.com`) 的 DNS 已被移除，
但可以通过 Cloudflare 边缘缓存访问：

### Linux/macOS

使用 `curl --connect-to` 参数：

```bash
curl --connect-to softwareupdate-prod.broadcom.com:443:softwareupdate-prod.broadcom.com.cdn.cloudflare.net:443 <URL>
```

### Windows

修改 `C:\Windows\System32\drivers\etc\hosts` 文件，添加：

```
softwareupdate-prod.broadcom.com.cdn.cloudflare.net softwareupdate-prod.broadcom.com
```

然后直接使用 CDN 链接下载。

## VMware Tools

- 最新版本: https://packages-prod.broadcom.com/tools/releases/latest/
- 历史版本: https://packages-prod.broadcom.com/tools/frozen/

## 许可证

自 2024 年 11 月起，VMware Workstation Pro 和 Fusion Pro 对所有用户（个人、教育、商业）免费。

## License

本项目仅供学习用途。