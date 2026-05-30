# VMware 下载链接

最后更新: 2026-05-30 04:38 UTC

> **VMware Workstation Pro 和 Fusion Pro 对所有用户免费。**

## 快速安装（Windows）

### 使用 winget（推荐）

```powershell
# 安装 VMware Workstation Pro
winget install VMware.WorkstationPro

# 安装 VMware Fusion Pro（macOS）
winget install VMware.Fusion
```

### 使用 scoop

```powershell
# 添加 VMware bucket
scoop bucket add extras

# 安装 VMware Workstation Pro
scoop install vmware-workstation
```

### 使用 chocolatey

```powershell
# 安装 VMware Workstation Pro
choco install vmwareworkstation

# 安装 VMware Fusion Pro（macOS）
choco install vmwarefusion
```

## 快速下载（使用 aria2）

### 安装 aria2

```bash
# macOS
brew install aria2

# Ubuntu/Debian
sudo apt install aria2

# Windows (scoop)
scoop install aria2

# Windows (chocolatey)
choco install aria2

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
aria2c 'https://archive.org/download/vmwareworkstationarchive/26H1/VMware-Workstation-Full-26H1-25388281.exe'
```

## 下载方式

### Archive.org（推荐）

Archive.org 提供所有版本的下载，无需登录。

- [VMware 镜像集合](https://archive.org/details/vmwareworkstationarchive)
- 覆盖范围: Workstation 2.x - 26H1, Fusion 8.x - 26H1

### TechPowerUp

TechPowerUp 是可靠的第三方下载站点。

- [VMware Workstation Pro 下载页面](https://www.techpowerup.com/download/vmware-workstation-pro/)
- [VMware Fusion Pro 下载页面](https://www.techpowerup.com/download/vmware-fusion/)

## 最新版本

### VMware Workstation Pro

**版本 26H1** (Build 25388281)

| 平台 | 下载链接 |
|------|----------|
| Windows | [下载](https://archive.org/download/vmwareworkstationarchive/26H1/VMware-Workstation-Full-26H1-25388281.exe) |
| Linux | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/26H1/VMware-Workstation-Full-26H1-25388281.x86_64.bundle) |

### VMware Fusion Pro

**版本 26H1** (Build 25388279)

| 平台 | 下载链接 |
|------|----------|
| macOS | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/26H1/VMware-Fusion-26H1-25388279_universal.dmg) |

## 所有版本

### VMware Workstation Pro

| 版本 | Build | 发布日期 | Windows | Linux |
|------|-------|----------|---------|-------|
| 26H1 | 25388281 | 2026-04-15 | [下载](https://archive.org/download/vmwareworkstationarchive/26H1/VMware-Workstation-Full-26H1-25388281.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/26H1/VMware-Workstation-Full-26H1-25388281.x86_64.bundle) |
| 25H2u1 | 25219725 | 2026-02-26 | [下载](https://archive.org/download/vmwareworkstationarchive/25H2/VMware-Workstation-Full-25H2u1-25219725.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/25H2/VMware-Workstation-Full-25H2u1-25219725.x86_64.bundle) |
| 25H2 | 24995812 | 2025-10-14 | [下载](https://archive.org/download/vmwareworkstationarchive/25H2/VMware-Workstation-Full-25H2-24995812.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/25H2/VMware-Workstation-Full-25H2-24995812.x86_64.bundle) |
| 17.6.4 | 24832109 | 2025-07-15 | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.4-24832109.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-Workstation-Full-17.6.4-24832109.x86_64.bundle) |
| 17.6.3 | 24583834 | 2025-02-24 | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.3-24583834.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-Workstation-Full-17.6.3-24583834.x86_64.bundle) |
| 17.6.2 | 24409262 | 2024-12-15 | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.2-24409262.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-Workstation-Full-17.6.2-24409262.x86_64.bundle) |
| 17.6.1 | 24319023 | 2024-10-08 | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.1-24319023.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-Workstation-Full-17.6.1-24319023.x86_64.bundle) |
| 17.6.0 | 24238078 | 2024-08-28 | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.0-24238078.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-Workstation-Full-17.6.0-24238078.x86_64.bundle) |
| 17.5.2 | 23775571 | 2024-05-10 | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.5.2-23775571.exe) | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-Workstation-Full-17.5.2-23775571.x86_64.bundle) |

### VMware Fusion Pro

| 版本 | Build | 发布日期 | macOS |
|------|-------|----------|-------|
| 26H1 | 25388279 | 2026-04-15 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/26H1/VMware-Fusion-26H1-25388279_universal.dmg) |
| 25H2u1 | 25219963 | 2026-02-26 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/25H2/VMware-Fusion-25H2u1-25219963_universal.dmg) |
| 25H2 | 24995814 | 2025-10-14 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/25H2/VMware-Fusion-25H2-24995814_universal.dmg) |
| 13.6.4 | 24832108 | 2025-07-15 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.6.4-24832108_universal.dmg) |
| 13.6.3 | 24585314 | 2025-02-24 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.6.3-24585314_universal.dmg) |
| 13.6.1 | 23298819 | 2024-11-19 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.6.1-23298819_universal.dmg) |
| 13.6.0 | 23278157 | 2024-09-17 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.6.0-23278157_universal.dmg) |
| 13.5.2 | 23324145 | 2024-06-25 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.5.2-23324145_universal.dmg) |

## 文件校验

下载后请校验文件完整性：

```bash
# Linux/macOS
sha256sum -c vmware-sha256.txt

# Windows PowerShell
Get-FileHash -Algorithm SHA256 VMware-Workstation-26H1-Windows.exe
```

## VMware Tools

- 最新版本: https://packages-prod.broadcom.com/tools/releases/latest/
- 历史版本: https://packages-prod.broadcom.com/tools/frozen/

## 许可证

自 2024 年 11 月起，VMware Workstation Pro 和 Fusion Pro 对所有用户（个人、教育、商业）免费。

## License

本项目仅供学习用途。