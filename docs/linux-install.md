# 🐧 Linux 安装 `.bundle`

VMware 官方 Linux 安装包是自解压 shell 脚本（`.bundle`），不是 rpm/deb。安装、卸载都用同一个二进制。

## 前置：内核头文件

VMware 会在安装过程中编译 `vmmon` / `vmnet` 两个内核模块。必须先装匹配当前内核的 header：

<details open>
<summary><b>Debian / Ubuntu</b></summary>

```bash
sudo apt update
sudo apt install -y build-essential linux-headers-$(uname -r)
```

</details>

<details>
<summary><b>Fedora / RHEL / Rocky / AlmaLinux</b></summary>

```bash
sudo dnf install -y gcc make kernel-devel kernel-headers
# kernel-devel 会拉取匹配运行内核的版本; 若内核刚升级过, 先 reboot 再装
```

</details>

<details>
<summary><b>Arch / Manjaro</b></summary>

```bash
sudo pacman -S --needed base-devel linux-headers
# 若用 linux-lts 内核，装 linux-lts-headers
```

</details>

<details>
<summary><b>openSUSE / SLES</b></summary>

```bash
sudo zypper install -y kernel-syms gcc make
# kernel-syms 自动匹配当前内核变体 (default / preempt / ...) 的开发包
```

</details>

## 安装

```bash
# 0. 拉校验清单到安装包同目录（一次性）
curl -LO https://raw.githubusercontent.com/gandli/vmware-downloads/main/data/checksums.txt

# 1. 校验完整性
sha256sum -c checksums.txt --ignore-missing

# 2. 加执行权限
chmod +x VMware-Workstation-Full-*.x86_64.bundle

# 3. 运行安装器 (需 root)
sudo ./VMware-Workstation-Full-*.x86_64.bundle

# 或静默安装 (不弹 GUI, 自动接受 EULA)
sudo ./VMware-Workstation-Full-*.x86_64.bundle --console --required --eulas-agreed
```

首次启动 `vmware` 命令时会触发模块编译。如果编译失败（新内核常见），装社区维护的补丁：

```bash
git clone https://github.com/mkubecek/vmware-host-modules.git
cd vmware-host-modules
git checkout workstation-17.6.4  # 换成你装的版本 tag
make
sudo make install
sudo systemctl restart vmware
```

## 卸载

```bash
# 列出已安装组件
vmware-installer -l

# 卸载 Workstation (组件名一般是 vmware-workstation)
sudo vmware-installer -u vmware-workstation
```

## 常见坑

| 现象 | 原因 | 处理 |
|:-----|:-----|:-----|
| `Unable to find kernel headers` | header 版本对不上当前 `uname -r` | 内核刚升级过没重启; 或装 `linux-headers-$(uname -r)` |
| 首次启动卡在 `Compiling modules...` | 新内核 API 不兼容旧 VMware | 装 [mkubecek/vmware-host-modules](https://github.com/mkubecek/vmware-host-modules) 补丁 |
| `SecureBoot` 报错模块签名 | 内核开了 lockdown | 关 SecureBoot, 或用 `mokutil` 给编出的模块签名 |
| Wayland 下窗口异常 | VMware GUI 走 X11 | 命令行 `env GDK_BACKEND=x11 vmware` 启动 |

> 官方安装文档：[VMware · Installing Workstation Pro on Linux](https://docs.vmware.com/en/VMware-Workstation-Pro/17.0/com.vmware.ws.using.doc/GUID-832D3ABB-DE30-4BED-9A36-2E0154F0A2ED.html)
