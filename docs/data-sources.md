# 📖 数据来源与说明

## 数据溯源

- **SHA256 / MD5 / 文件大小 / 发布日期**
  Broadcom Support Portal（登录抓取，官方权威）
  - [Workstation Pro Downloads](https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Workstation%20Pro&freeDownloads=true)
  - [Fusion Pro Downloads](https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Fusion%20Pro&freeDownloads=true)
- **安装包 URL**
  archive.org [vmwareworkstationarchive 集合](https://archive.org/details/vmwareworkstationarchive)（免费，无需登录）

## 自动化

- 🤖 每月首日 06:00 UTC 自动抓取最新版本并开 PR ([workflow](../.github/workflows/monthly-update.yml))
- 🧪 TDD 保护：单元测试覆盖抓取 / 合并 / 渲染全链路
- 📁 仓库不承载任何安装包，仅提供**整理好的元数据** + **archive.org 公开镜像链接**

## 贡献与反馈

发现某版本下载失效？欢迎 [开 Issue](https://github.com/gandli/vmware-downloads/issues/new) 或 [提 PR](https://github.com/gandli/vmware-downloads/compare) 🙏
