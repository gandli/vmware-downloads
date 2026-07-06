# 🎯 VMware Workstation & Fusion 下载中心

![Workstation](https://img.shields.io/badge/Workstation%20Pro-15%20versions-0071c5?style=flat-square&logo=vmware) ![Fusion](https://img.shields.io/badge/Fusion%20Pro-15%20versions-0071c5?style=flat-square&logo=vmware) ![Last Updated](https://img.shields.io/badge/updated-2026--07--06-brightgreen?style=flat-square) ![License](https://img.shields.io/github/license/gandli/vmware-downloads?style=flat-square)

> **一站式 VMware Workstation Pro & Fusion Pro 免费下载导航**  
> 📥 archive.org 免费镜像 · 🔐 Broadcom 官方 SHA256 · 🤖 每月自动更新

<sub>_Last sync: 2026-07-06 01:25 UTC_</sub>

---

## 目录

- [快速下载（最新版）](#-快速下载最新版)
- [校验完整性](#-校验完整性)
- [所有历史版本](#-所有历史版本)
- [免费使用政策](#-免费使用政策)
- [老系统兼容性](#️-老系统兼容性)
- [数据来源与说明](#-数据来源与说明)
- [贡献与反馈](#贡献与反馈)

## 🚀 快速下载（最新版）

> 直接点击文件名下载，无需登录。哈希在下方，下载后请务必[校验完整性](#-校验完整性)。

### 🪟 VMware Workstation Pro

**26H1** · Build `25388281` · 发布于 **2026-05-14**

- **Windows** — [VMware-Workstation-Full-26H1-25388281.exe](https://archive.org/download/vmwareworkstationarchive/26H1/VMware-Workstation-Full-26H1-25388281.exe) (274.34 MB · SHA256 `a0ef9087607d9cad…`)
- **Linux** — [VMware-Workstation-Full-26H1-25388281.x86_64.bundle](https://archive.org/download/vmwareworkstationarchive/Linux/26H1/VMware-Workstation-Full-26H1-25388281.x86_64.bundle) (325.03 MB · SHA256 `3f6d2501e654dbc7…`)

### 🍎 VMware Fusion Pro

**26H1** · Build `25388279` · 发布于 **2026-05-14**

- **macOS** — [VMware-Fusion-26H1-25388279_universal.dmg](https://archive.org/download/vmwareworkstationarchive/Fusion/26H1/VMware-Fusion-26H1-25388279_universal.dmg) (480.71 MB · SHA256 `c1d373aa21be2567…`)

## 🔐 校验完整性

所有 SHA256 由 **Broadcom Support Portal 官方元数据**导出，保存在：

- 📄 [`data/checksums.txt`](data/checksums.txt) — 可直接喂给 `shasum -c` / `sha256sum -c`
- 📄 [`data/vmware_downloads.json`](data/vmware_downloads.json) — 完整元数据 (size / SHA256 / MD5 / build)

把 `checksums.txt` 与下载的 `.exe`/`.bundle`/`.dmg` **放在同一目录**：

<details open>
<summary><b>🐧 Linux / 🍎 macOS</b></summary>

```bash
# Linux（GNU coreutils）
sha256sum -c checksums.txt --ignore-missing

# macOS（系统自带 shasum）
shasum -a 256 -c checksums.txt --ignore-missing
```

</details>

<details>
<summary><b>🪟 Windows PowerShell</b></summary>

```powershell
Get-Content checksums.txt | ForEach-Object {
    $h, $f = $_ -split '  ', 2
    if (-not (Test-Path $f)) { return }
    $actual = (Get-FileHash $f).Hash.ToLower()
    $ok = $actual -eq $h.ToLower()
    '{0}  {1}' -f $(if ($ok) {'OK  '} else {'FAIL'}), $f
}
```

</details>

**期望输出**：

```
VMware-workstation-full-17.6.4-24832109.exe: OK
```

> ✅ 看到 `OK` 就是**逐字节校验通过**，可以放心安装。
> ❌ 看到 `FAILED` / `WARNING` 一律**别装**，重新下载。

> 💡 `--ignore-missing` 让工具只校验当前目录已有的文件，不必下齐全部。

## 📦 所有历史版本

> **图例**：✅ Broadcom 官方数据（SHA256 权威）· 📼 archive.org 历史存档（仅 MD5/SHA1）

<details>
<summary><b>🪟 VMware Workstation Pro（15 版）</b></summary>

| 版本 | Build | 发布日期 | Windows | Linux | SHA256 | 来源 |
|:-----|:------|:---------|:--------|:------|:-------|:---:|
| 26H1 | `25388281` | 2026-05-14 | [下载](https://archive.org/download/vmwareworkstationarchive/26H1/VMware-Workstation-Full-26H1-25388281.exe) (274.34 MB) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/26H1/VMware-Workstation-Full-26H1-25388281.x86_64.bundle) (325.03 MB) | Win `a0ef9087607d9cad…` <details><summary>full</summary><code>a0ef9087607d9cad20b08139e73e41242e044ad5bd8cee141d3bad314586737f</code></details><br>Linux `3f6d2501e654dbc7…` <details><summary>full</summary><code>3f6d2501e654dbc7701a8290ff6ffcfba6c5444cd5f35f4933cd08c9499f6d84</code></details> | ✅ |
| 25H2u1 | `25219725` | 2026-02-26 | [下载](https://archive.org/download/vmwareworkstationarchive/25H2/VMware-Workstation-Full-25H2u1-25219725.exe) (278.31 MB) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/25H2/VMware-Workstation-Full-25H2u1-25219725.x86_64.bundle) (296.22 MB) | Win `b592c47756d47c93…` <details><summary>full</summary><code>b592c47756d47c932a3ce2c2b83ad3af1fa23ccc1dd1d3166a51bcc1d2bd58e0</code></details><br>Linux `721aa93c4ebcaa51…` <details><summary>full</summary><code>721aa93c4ebcaa51ac6db75ed97c7a4db10aa88110446890db1e40bfafc7566a</code></details> | ✅ |
| 25H2 | `24995812` | 2025-10-14 | [下载](https://archive.org/download/vmwareworkstationarchive/25H2/VMware-Workstation-Full-25H2-24995812.exe) (277.63 MB) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/25H2/VMware-Workstation-Full-25H2-24995812.x86_64.bundle) (295.19 MB) | Win `49ad7c2bbce854ed…` <details><summary>full</summary><code>49ad7c2bbce854ed30ed0702d1af9fc042697777dc981e087bfa7241045b0361</code></details><br>Linux `9beced8a0653c938…` <details><summary>full</summary><code>9beced8a0653c9382e9aa9917168a54bf5635e566c8cb341589d72cf14093322</code></details> | ✅ |
| 17.6.4 | `24832109` | 2025-07-15 | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.4-24832109.exe) (405.72 MB) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/17.x/VMware-Workstation-Full-17.6.4-24832109.x86_64.bundle) (339.46 MB) | Win `10fe3a36f525d88a…` <details><summary>full</summary><code>10fe3a36f525d88aa133118ab3b5a16b18da88d4aa11b14d74e4164b3fb94ba9</code></details><br>Linux `64fbfbaeacc48865…` <details><summary>full</summary><code>64fbfbaeacc48865468114362a2bbaade9110cc9e87bc3bd938396ba7f19a9bd</code></details> | ✅ |
| 17.6.3 | `24583834` | 2025-03-04 | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.3-24583834.exe) (401.43 MB) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/17.x/VMware-Workstation-Full-17.6.3-24583834.x86_64.bundle) (335.21 MB) | Win `d7c04b4dd1e6bf55…` <details><summary>full</summary><code>d7c04b4dd1e6bf551693897d4805e99c45198a830c6361d9af8267b40906857b</code></details><br>Linux `79575917728ded4c…` <details><summary>full</summary><code>79575917728ded4c6d0b89f4ab6a81be9a773c00eeb68d1d12ac0db125478ee0</code></details> | ✅ |
| 17.6.2 | `24409262` | 2024-12-17 | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.2-24409262.exe) (447.93 MB) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/17.x/VMware-Workstation-Full-17.6.2-24409262.x86_64.bundle) (372.49 MB) | Win `5e556b7fc1bd2777…` <details><summary>full</summary><code>5e556b7fc1bd27775143eea930cac68760a1b5dc9b4c089d3fc664cd8439645b</code></details><br>Linux `15536dfc5afbbcf4…` <details><summary>full</summary><code>15536dfc5afbbcf42daec10b1d9d1d6da3ca27da478938defc9c558064ff09f7</code></details> | ✅ |
| 17.6.1 | `24319023` | 2024-10-10 | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.1-24319023.exe) (447.93 MB) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/17.x/VMware-Workstation-Full-17.6.1-24319023.x86_64.bundle) (372.46 MB) | Win `f95429e395a583eb…` <details><summary>full</summary><code>f95429e395a583eb5ba91f09b040e2f8c53a5e7aa37c4c6bfcaf82115a8d3fa4</code></details><br>Linux `7b539aafa8251e7a…` <details><summary>full</summary><code>7b539aafa8251e7af3b49dc12a299b127938ef0355d3de68f616ceac3e59e016</code></details> | ✅ |
| 17.6 | `24238078` | 2024-09-03 | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.6.0-24238078.exe) (447.97 MB) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/17.x/VMware-Workstation-Full-17.6.0-24238078.x86_64.bundle) (372.46 MB) | Win `e34461ffbcb38ca7…` <details><summary>full</summary><code>e34461ffbcb38ca7baa7928f7f37575ef31129961099eae96b43a64b06462778</code></details><br>Linux `5e9e8e01278bef64…` <details><summary>full</summary><code>5e9e8e01278bef6408a360ff2f56218c2ee62854735be8d9cbe2dc61811ca0dc</code></details> | ✅ |
| 17.5.2 | `23775571` | 2024-05-14 | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.5.2-23775571.exe) (618.26 MB) | [下载](https://archive.org/download/vmwareworkstationarchive/Linux/17.x/VMware-Workstation-Full-17.5.2-23775571.x86_64.bundle) (510.58 MB) | Win `2c3a40993a450dc9…` <details><summary>full</summary><code>2c3a40993a450dc9a059563d07664fc0fb85ae398a57d22b1b4bf0e602417bf7</code></details><br>Linux `a9da5e9b785ab98c…` <details><summary>full</summary><code>a9da5e9b785ab98c6f49d1e769f6885028fd115c96e3cf0e6d22da3112b89a21</code></details> | ✅ |
| 17.5.1 | `23298084` | — | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.5.1-23298084.exe) (594.29 MB) | — | MD5 only | 📼 |
| 17.5.0 | `22583795` | — | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.5.0-22583795.exe) (571.76 MB) | — | MD5 only | 📼 |
| 17.0.2 | `21581411` | — | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.0.2-21581411.exe) (607.70 MB) | — | MD5 only | 📼 |
| 17.0.1 | `21139696` | — | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.0.1-21139696.exe) (607.72 MB) | — | MD5 only | 📼 |
| 16.2.5 | `20904516` | — | [下载](https://archive.org/download/vmwareworkstationarchive/16.x/VMware-workstation-full-16.2.5-20904516.exe) (615.58 MB) | — | MD5 only | 📼 |
| 17.0.0 | `20800274` | — | [下载](https://archive.org/download/vmwareworkstationarchive/17.x/VMware-workstation-full-17.0.0-20800274.exe) (607.88 MB) | — | MD5 only | 📼 |

</details>

<details>
<summary><b>🍎 VMware Fusion Pro（15 版）</b></summary>

| 版本 | Build | 发布日期 | macOS | SHA256 | 来源 |
|:-----|:------|:---------|:------|:-------|:---:|
| 26H1 | `25388279` | 2026-05-14 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/26H1/VMware-Fusion-26H1-25388279_universal.dmg) (480.71 MB) | `c1d373aa21be2567…` <details><summary>full</summary><code>c1d373aa21be25674e3ecc518819e255785dea9d456d8747bcb0a2a59244bdf6</code></details> | ✅ |
| 25H2u1 | `25219963` | 2026-02-26 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/25H2/VMware-Fusion-25H2u1-25219963_universal.dmg) (484.82 MB) | `bfe88fe1653e50aa…` <details><summary>full</summary><code>bfe88fe1653e50aafcaf3fce5eacb4c491d40ae5d43a5199c991caebb04b98d0</code></details> | ✅ |
| 25H2 | `24995814` | 2025-10-14 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/25H2/VMware-Fusion-25H2-24995814_universal.dmg) (484.58 MB) | `a995ebd6fded41b3…` <details><summary>full</summary><code>a995ebd6fded41b3f2da87efff6b8674d6689f4c997772810ea1a5c2ebe28c0e</code></details> | ✅ |
| 13.6.4 | `24832108` | 2025-07-15 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.6.4-24832108_universal.dmg) (530.91 MB) | `a43fd031165896bc…` <details><summary>full</summary><code>a43fd031165896bc1b7ecc61eb07b377bfc01b014c9111b08e18a6a1af121191</code></details> | ✅ |
| 13.6.3 | `24585314` | 2025-03-04 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.6.3-24585314_universal.dmg) (517.48 MB) | `4e68575577fcd731…` <details><summary>full</summary><code>4e68575577fcd7312d151d7eec8a7c4a67500b4310251bdb48151f56cfd8f44f</code></details> | ✅ |
| 13.6.2 | `24409261` | 2024-12-17 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.6.2-24409261_universal.dmg) (539.77 MB) | `13f4d4b366632895…` <details><summary>full</summary><code>13f4d4b3666328951627f717b692d563c64e5255161ef3751374eab124bd4706</code></details> | ✅ |
| 13.6.1 | `24319021` | 2024-10-10 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.6.1-24319021_universal.dmg) (539.78 MB) | `6a9faee5c0a25735…` <details><summary>full</summary><code>6a9faee5c0a2573598704a09864d6072a0685269707c186dfc8ebde4551ee5c3</code></details> | ✅ |
| 13.6 | `24238079` | 2024-09-03 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.6.0-24238079_universal.dmg) (539.77 MB) | `4b3bc6c657d6bcee…` <details><summary>full</summary><code>4b3bc6c657d6bcee6cde44f276be131cba1837b24eaf429f78c490bf2a668e7d</code></details> | ✅ |
| 13.5.2 | `23775688` | 2024-05-14 | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.5.2-23775688_universal.dmg) (750.23 MB) | `baaa201c797af8e3…` <details><summary>full</summary><code>baaa201c797af8e32a2ec3ae78c69bfedbe5c5c7960c3673885bd84e42ddfbb9</code></details> | ✅ |
| 13.5.1 | `23298085` | — | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.5.1-23298085_universal.dmg) (692.34 MB) | MD5 only | 📼 |
| 13.5.0 | `22583790` | — | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.5.0-22583790_universal.dmg) (689.40 MB) | MD5 only | 📼 |
| 13.0.1 | `21139760` | — | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.0.1-21139760_universal.dmg) (672.09 MB) | MD5 only | 📼 |
| 12.2.5 | `20904517` | — | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/12.x/VMware-Fusion-12.2.5-20904517_x86.dmg) (621.80 MB) | MD5 only | 📼 |
| 13.0.0 | `20802013` | — | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/13.x/VMware-Fusion-13.0.0-20802013_universal.dmg) (672.06 MB) | MD5 only | 📼 |
| 12.2.3 | `19436697` | — | [下载](https://archive.org/download/vmwareworkstationarchive/Fusion/12.x/VMware-Fusion-12.2.3-19436697_x86.dmg) (621.00 MB) | MD5 only | 📼 |

</details>

## 💡 免费使用政策

| 日期 | 里程碑 |
|:-----|:-------|
| **2024-05-14**（17.5.2 起） | Workstation Pro 免费供 **个人用户** |
| **2024-11-11**（17.6.2 起） | Workstation & Fusion 免费供 **所有用户**（个人 / 教育 / 商业） |

> 📖 官方公告：
> - [Desktop Hypervisor Pro Apps Now Available for Personal Use](https://blogs.vmware.com/cloud-foundation/2024/05/14/vmware-desktop-hypervisor-pro-apps-now-available-for-personal-use/)
> - [Fusion and Workstation Now Free for All Users](https://blogs.vmware.com/cloud-foundation/2024/11/11/vmware-fusion-and-workstation-are-now-free-for-all-users/)

> ⚠️ 安装时选择「个人使用」即可，**无需许可证密钥**。

## 🖥️ 老系统兼容性

| 操作系统 | 最终支持的 Workstation 版本 |
|:---------|:---------------------------|
| Windows 7 | 15.5.7 |
| Windows XP / 32 位 | 10.0.7 |

## 📖 数据来源与说明

### 数据溯源

- **SHA256 / MD5 / 文件大小 / 发布日期**
  Broadcom Support Portal（登录抓取，官方权威）
  - [Workstation Pro Downloads](https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro&freeDownloads=true)
  - [Fusion Pro Downloads](https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Fusion%20Pro&freeDownloads=true)
- **安装包 URL**
  archive.org [vmwareworkstationarchive 集合](https://archive.org/details/vmwareworkstationarchive)（免费，无需登录）

### 自动化

- 🤖 每月首日 06:00 UTC 自动抓取最新版本并开 PR ([workflow](.github/workflows/monthly-update.yml))
- 🧪 TDD 保护：143 个单测覆盖抓取 / 合并 / 渲染全链路
- 📁 仓库不承载任何安装包，仅提供**整理好的元数据** + **archive.org 公开镜像链接**

## 贡献与反馈

发现某版本下载失效？欢迎 [开 Issue](https://github.com/gandli/vmware-downloads/issues/new) 或 [提 PR](https://github.com/gandli/vmware-downloads/compare) 🙏

---

<sub>本仓库仅提供元数据整理服务。VMware / Workstation / Fusion 是 Broadcom Inc. 的注册商标。</sub>
