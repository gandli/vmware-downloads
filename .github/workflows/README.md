# GitHub Actions 工作流说明

## `monthly-update.yml` — 月度自动抓取 Broadcom 元数据

### 触发时机
- **定时**: 每月 1 号 UTC 06:00（北京时间 14:00）
- **手动**: Actions 页面点 "Run workflow"

### 为什么按月？
根据 `data/vmware_downloads.json` 里 2024-05 至今 9 次发布记录：
- 平均发布间隔 **91 天**（约 3 个月）
- 最短 37 天，最长 135 天
- 月度频率覆盖率 **100%**（每月跑必抓到潜在新版）

### 工作流步骤
1. checkout 代码
2. 装 Python 3.11 + Playwright + pytest
3. 缓存 Playwright Chromium（约 15s 加速）
4. 跑单元测试（**59 tests 必须绿**）
5. 登录 Broadcom Support Portal，API 拦截抓取全部元数据
6. 融合 archive.org 索引，生成 README + checksums.txt
7. 有数据变化 → 自动开 PR（`auto/monthly-update` 分支）
8. 无变化 → 静默跳过

### 需要配置的 Secrets
在 https://github.com/gandli/vmware-downloads/settings/secrets/actions 添加：

| Secret Name | 内容 |
|-------------|------|
| `BROADCOM_USERNAME` | Broadcom Support Portal 用户名 |
| `BROADCOM_PASSWORD` | Broadcom Support Portal 密码 |

> ⚠️ **强烈建议**用 Broadcom 专用只读账号（如支持），避免主账号凭证长期挂在 CI。

### 输出
若检测到变化，PR body 会摘要：
- ➕ 新增版本
- ➖ 移除版本
- 🔄 build 号更新

### 风控风险
GitHub Actions runner 位于 Azure/AWS 段，可能被 Broadcom WAF 标记：
- **若首次运行失败**：查看日志，若见 CAPTCHA/风控，切换到自托管 runner
- **若账号被封**：立即换密码 + 撤销 CI secrets + 短期停用 workflow

### 手动触发测试
```bash
gh workflow run monthly-update.yml
gh run watch  # 观察日志
```
