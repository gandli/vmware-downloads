# 安全策略

## 报告漏洞

本仓库整理 VMware 官方下载链接与哈希元数据，任何**供应链完整性**问题都欢迎私下反馈：

- 📧 邮件：请在 GitHub 私信仓库所有者 [@gandli](https://github.com/gandli)
- 🔐 或通过 [GitHub Security Advisories](https://github.com/gandli/vmware-downloads/security/advisories/new) 私下报告

## 敏感场景（请立即报告）

- ⚠️ `data/vmware_downloads.json` 或 `data/checksums.txt` 中的 SHA256 与 Broadcom Support Portal 官方值**不一致**
- ⚠️ 发现某版本安装包被替换但仓库未更新哈希（build 号不变但 hash 变）
- ⚠️ archive.org 上的镜像与 Broadcom 官方哈希不匹配（`md5_mismatch` 未被 workflow 捕获）
- ⚠️ CI/CD 中存在被利用的凭据泄漏或 secret 硬编码

## 非敏感范畴（请开 Issue 而非私下）

- 版本清单缺失、日期错误、显示排序不正确、README 展示 bug —— 直接开 [Issue](https://github.com/gandli/vmware-downloads/issues/new)

## 响应时间

- **确认收到**：72 小时内
- **修复评估**：7 天内
- **披露**：修复合并后 30 天内在 [Security Advisories](https://github.com/gandli/vmware-downloads/security/advisories) 公开

## 数据源可信度

| 数据 | 来源 | 可信度 |
|:-----|:-----|:-------|
| SHA256 / MD5 / 文件大小 / 发布日期 | Broadcom Support Portal（登录抓取） | ✅ 官方权威 |
| 安装包 URL | archive.org [vmwareworkstationarchive](https://archive.org/details/vmwareworkstationarchive) | 📼 免费历史镜像 |

**校验建议**：下载安装包后务必用 `data/checksums.txt` 做 SHA256 校验，任何 `FAILED` 都视为供应链风险。
