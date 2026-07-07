# 🔍 vmware-downloads 全量审计报告 · v2

**审计工具**：`fuck-my-shit-mountain` skill
**项目**：`gandli/vmware-downloads` @ `12c7baf` (main, PR #10 合并后)
**审计日期**：2026-07-08
**审计模式**：`full`（全 27 维度）
**评审语言**：简体中文
**输出格式**：Markdown

---

## 📊 Executive Summary

| 指标 | 值 |
|:---|:---|
| 项目类型 | Python 3.11 · 元数据爬虫 + 自动 README 渲染 |
| 代码规模 | 2,287 loc 源码（scripts/）+ 2,254 loc 测试（tests/），比 0.99 |
| 测试基线 | ✅ 157 passed / 0 failed, `ruff` clean, `.venv` 内 coverage **97%** |
| 依赖 | 运行时**零**外部依赖；开发依赖 pytest/pytest-cov/ruff/playwright |
| CI 状态 | Lint&Test + Secret scan + Monthly update 三 workflow 全绿 |
| **总体评分** | **7.9 / 10.0（B+）** —— 代码质量优秀，供应链 + 文档漂移是主要缺口 |

**一句话结论**：PR #10 合并后的代码本身质量非常高（97% 覆盖率、ruff 全绿、模块边界清晰），但**外围治理层**有 3 个可控的中低风险：CI action 未 pin SHA、5 处引用不存在的旧脚本名（`probe_broadcom_full.py`）、PR 模板未按刚落地的官方 5 段规范。

---

## 🗺️ Project Map

```text
vmware-downloads/
├── scripts/                         # 主逻辑（2,287 loc, Python 3.11+）
│   ├── collect_vmware_links.py      # 主入口：融合 Broadcom + archive.org
│   ├── fetch_broadcom.py            # Playwright 抓 Broadcom Portal（asyncio）
│   ├── detect_data_changes.py       # 剔除时间戳噪声后判断真实数据变化
│   ├── summarize_changes.py         # 生成月度 PR body
│   ├── probe_archive_org.py         # archive.org 调研工具
│   └── vmware_lib/                  # 核心库（1,178 loc, 覆盖率 97%）
│       ├── broadcom.py              # Broadcom 元数据加载
│       ├── collector.py             # 双源融合
│       ├── legacy_merger.py         # archive.org 历史版本合并
│       ├── renderer.py              # README/checksums 渲染（400 loc）
│       ├── parser.py                # 文件名 → 版本解析
│       ├── detail_parser.py         # HTML 详情页解析
│       └── archive_common.py        # 版本排序公用逻辑
├── tests/                           # 157 tests, 2,254 loc, coverage 97%
├── data/                            # broadcom_metadata.json (34K) + vmware_downloads.json (109K) + checksums.txt (3K)
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                   # Lint + pytest + README 同步校验
│   │   ├── monthly-update.yml       # 每月 1 号自动抓 + 开 PR
│   │   └── secret-scan.yml          # gitleaks 每周一 + 每 PR
│   ├── ISSUE_TEMPLATE/{bug_report,feature_request}.yml
│   ├── PULL_REQUEST_TEMPLATE.md     # ⚠️ 本地风格，不合新规范
│   └── dependabot.yml
├── SECURITY.md · CONTRIBUTING.md · LICENSE · README.md
├── pyproject.toml                   # 声明 requires-python >=3.11
└── requirements.txt                 # "无需外部依赖" 但项目实际用 playwright
```

**入口与边界**：
- **CI 入口**：`ci.yml` (PR/push/manual) → ruff + pytest + README drift check
- **数据流入口**：`monthly-update.yml` (cron 每月 1 号) → `fetch_broadcom.py` → `collect_vmware_links.py` → 自动开 PR
- **数据边界**：Broadcom Portal (权威 SHA256) + archive.org (镜像 URL)，两源双 MD5 交叉校验
- **敏感面**：`BROADCOM_USERNAME` / `BROADCOM_PASSWORD` (GitHub secrets, 只读用途)
- **信任面**：Playwright Chromium 从 CDN 装（每次 CI 都验证 SHA）

---

## 📋 Coverage Matrix

| 维度 | Coverage | 检查证据 | 排除 / 限制 |
|:---|:---:|:---|:---|
| 🏛️ Architecture | High | 全部 8 模块通读 · 依赖方向清晰 · SRP 好 | 无 |
| 🔒 Security | High | 全 script + workflow + SECURITY.md · gitleaks 已跑 · zero secret grep hit | 未做 fuzz |
| 🛡️ Stability | High | 7 处 `except Exception` 全部审视 · 3 处 silent swallow 标出 | 无 |
| ⚡ Performance | Medium | asyncio.Semaphore 并发合理 · legacy 复用 metadata · 未 profile | 无实际 profiler |
| 🧪 Testing | High | 157 tests, coverage 97%, tests/ 与 scripts/ 1:1 对应 | tests/ 里 `probe_broadcom_full` 幽灵引用 |
| 🛠️ Maintainability | High | ruff clean · 模块 <=400 loc · docstring 完整 | 5 处旧脚本名引用（文档漂移） |
| 🎨 Design | High | SRP · 依赖方向单一 · 双源融合抽象良好 | 无 |
| 🚀 Release | Medium | pyproject 版本 2.0.0 · 无 CHANGELOG · 无 tag/release | 未做 release |
| 📖 Documentation | Medium | README/CONTRIBUTING/SECURITY 齐 · 但引用旧脚本名 5 处 | PR 模板不合新规 |
| 📊 Observability | Low | `print()` 直接输出，无 structured log | 无关键路径需要 metrics |
| ⚙️ Configuration | High | env 变量集中、default 合理 | 无 |
| 🔐 Data Integrity | High | MD5 交叉校验 · noise-field 剔除 · checksums.txt 与 JSON 同步校验 | 无 |
| 🕵️ Privacy | Not Applicable | 无 PII，Broadcom 凭据仅 CI secret | — |
| ♿ Accessibility | Not Applicable | 无 UI | — |
| 🔗 Supply Chain | **Low** | ⚠️ CI actions 全部未 pin SHA · playwright install 从 CDN | 最主要风险面 |
| 💰 Cost | Not Applicable | 无付费 API | — |
| 🤖 AI Safety | Not Applicable | 无 LLM 使用 | — |
| 🧯 Fallback | Medium | 3 处 `except Exception: pass` 静默降级 | detect_data_changes.py |
| 🎭 Testing Authenticity | High | 157 tests 覆盖真实融合场景 + 边界 | 无 |
| 🏷️ Type Safety | Medium | `from __future__ import annotations` · 无 mypy/pyright 门禁 | 未启 strict |
| 📦 Dependency Weight | High | 运行时零依赖 · dev 仅 4 项 | 无 |
| 🎨 Code Consistency | High | ruff format clean · import 顺序统一 | 无 |
| 💬 Comment Coverage | High | 关键函数 docstring 齐 · 复杂逻辑有块注释 | 5 处 stale 引用 |
| 🔀 Concurrency | High | asyncio.Semaphore 限并发 · 无共享可变状态 | 无 |
| 🎯 Frontend State | Not Applicable | 无 UI | — |
| 🌐 Backend API | Not Applicable | 无 server | — |


