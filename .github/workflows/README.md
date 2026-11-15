# GitHub Actions 工作流说明

设计原则：**跑起来就不需要人管**。数据的每一次自动更新都必须先过健康检查才允许
提交；抓取抖动一律降级为"本次不更新"，绝不把退化发布出去；真出问题自动开 issue，
下次跑通自动关。

## 全景

| 工作流 | 触发 | 作用 |
|--------|------|------|
| `data-update.yml` | 每周一 06:00 UTC + 手动 | 抓 Broadcom 元数据 → 融合 archive.org → 渲染 → 健康检查 → 提交 main |
| `ci.yml` | push / PR / 手动 | ruff + mypy + bandit + pytest（覆盖率 ≥95%）+ README/数据同步校验 |
| `dependabot-auto-merge.yml` | Dependabot PR | 自动批准并开启 auto-merge，CI 绿了自动合并 |
| `codeql.yml` / `secret-scan.yml` / `release-please.yml` | 各自定时或 push | 静态扫描 / 密钥扫描 / 版本发布 |

## `data-update.yml` — 无人值守的数据更新

### 触发时机
- **定时**：每周一 UTC 06:00（北京时间 14:00，Broadcom 美西上班后）
- **手动**：Actions 页面 "Run workflow"；可勾选 `force_metadata`

### 为什么改成周频
2024-05 至 2026-05 共 9 次发布，平均间隔 91 天。周频并不为抢速度，而是为了两件事：

1. 新版发布后最多 7 天就能被发现（月频最长要等 30 天）；
2. **GitHub 会在仓库连续 60 天无提交后自动停用 schedule**。月频一旦连续两次
   "无变化"或失败，流水线就静默死掉。周频 + 心跳提交让这条规则永远打不到。

### 五道闸门（任何一道不放行都不发布）

| # | 闸门 | 位置 | 拦什么 |
|---|------|------|--------|
| 1 | 单元测试 | `pytest -q` | 代码回归 |
| 2 | 元数据收缩保护 | `fetch_broadcom.py` 退出码 3 | Portal 某个 detail 页抓空（同版本文件数变少）、列表页整页丢失 |
| 3 | 采集重试 | 工作流循环 3 次 | archive.org metadata 抖动 |
| 4 | 提交前回归防护 | `check_data_regression.py` | 下载条目消失、直链退化成"需登录"、版本整体消失 |
| 5 | Schema 校验 | `collect_vmware_links.py` | 字段结构漂移 |

闸门 2 命中时不会中断流水线：`fetch_broadcom.py` **保留上一版元数据**、把可疑结果
写到 `data/broadcom_metadata.rejected.json`（已在 .gitignore），渲染继续用旧元数据，
线上数据不退化。

闸门 4 命中时流水线判失败：`data/` 回滚到 HEAD，**本次不发布任何新数据**，
并自动开 issue。

### 自动恢复 vs 需要人看

| 情况 | 结果 |
|------|------|
| 某周 Portal 少返 detail 页 | 闸门 2 拦下，用旧元数据继续跑，不提交 → 下周自动再试 |
| archive.org metadata 抖动 | 闸门 3 重试最多 3 次 |
| push 失败 | 自动 rebase + 重试 3 次 |
| 连续 3 周只有时间戳变化 | 心跳提交一次 `collected_at`（`--heartbeat-days 21`），README 的抓取时间保持诚实 |
| 3 次重试后仍数据退化 / 登录失败 / Schema 失败 | **自动开 issue**「数据更新流水线失败（自动创建，勿改标题）」并附运行链接；下次成功自动关闭 |
| 上游真的撤下老版本 | 属正常收缩，闸门 2 只拦"同版本文件数下降"和"大面积版本消失（>30% 且 ≥2 个）" |

### 需要配置的 Secrets
https://github.com/gandli/vmware-downloads/settings/secrets/actions

| Secret | 内容 |
|--------|------|
| `BROADCOM_USERNAME` | Broadcom Support Portal 用户名 |
| `BROADCOM_PASSWORD` | Broadcom Support Portal 密码 |

> 建议用 Broadcom 专用只读账号，避免主账号凭证长期挂在 CI。

### 罕见的人工介入（破窗）

只有两种场景需要人：

```bash
# 1. 上游真实下架，但闸门 2 误判（罕见）
Actions → Data Update → Run workflow → 勾选 force_metadata
# 等价于本地： BROADCOM_ALLOW_SHRINK=1 python scripts/fetch_broadcom.py

# 2. 确认某次"条目消失"是合理的，允许提交
ALLOW_REGRESSION=1 python scripts/check_data_regression.py --metadata
```

两者都会留下痕迹：`BROADCOM_ALLOW_SHRINK` 的结果照常落库；`ALLOW_REGRESSION`
要求你在 commit message 里写明原因。

### 本地复现

```bash
python scripts/check_data_regression.py --metadata   # 单独跑数据健康检查
python scripts/detect_data_changes.py --heartbeat-days 21
gh workflow run data-update.yml && gh run watch
```

### 风控风险
GitHub Actions runner 位于 Azure/AWS 段，可能被 Broadcom WAF 标记。若 issue 里反复
出现登录失败/CAPTCHA，切到自托管 runner（改 `runs-on`）；若账号被封，立即换密码、
撤销 CI secrets、停用 workflow。
