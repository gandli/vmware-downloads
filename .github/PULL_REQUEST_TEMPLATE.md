<!--
PR 描述规范 · 遵循 GitHub Docs "Helping others review your changes" 官方 5 段结构
提 PR 前必须先跑 code-review-skill 三维扫描（安全 · 性能 · 可维护性）
详见：CONTRIBUTING.md § PR 提交流程
禁止粘贴 Telegram / 微信 / 机器人对话原文
-->

## 🎯 Purpose / 动机

<!-- 一句话：这个 PR 要解决什么问题？为什么现在做？ -->

Closes #<issue>
Refs: <上游讨论 / 相关 PR>

## 📋 Overview / 改动概览

<!-- 3-7 条要点，按 [抓取/融合/渲染/CI/数据/文档/治理] 分组 -->

- **[分组]** …
- **[分组]** …
- **[分组]** …

## 🧭 Context / 上下文

<!-- 为什么选这条路？关键权衡是什么？ -->

**Blast radius:**
- [ ] 抓取逻辑（fetch_broadcom / probe_archive_org）
- [ ] 融合逻辑（collector / legacy_merger）
- [ ] 渲染逻辑（renderer / README.md）
- [ ] CI / GitHub Actions
- [ ] 数据文件（data/*.json、data/checksums.txt）
- [ ] 依赖 / 构建（pyproject.toml、requirements.txt）
- [ ] 文档 / 治理（README、CONTRIBUTING、SECURITY、PR 模板）
- [ ] 纯清理 / 重构（无行为变化）

**Trade-offs：** …
**Rejected alternatives：** …

## ✅ Verification / 验证证据

### 🔍 Code Review 结果（`code-review-skill` 三维扫描）

<!-- 强制：提 PR 前必须完成此 3×3 扫描并填表。全 0 才可合并 -->

| 维度 | 🔴 blocking | 🟡 important | 🟢 nit |
|:---|:---:|:---:|:---:|
| 🔒 安全 | 0 | 0 | 0 |
| ⚡ 性能 | 0 | 0 | 0 |
| 🛠️ 可维护性 | 0 | 0 | 0 |

<!-- 若非全 0，逐条列出：位置 → 问题 → 修复 commit SHA -->

### 🧪 自动化验证

- [ ] `pytest -q`：<N/N passed>
- [ ] `ruff check scripts/ tests/`：clean
- [ ] 覆盖率 ≥ 85%：<实测%>
- [ ] CI 全绿（Lint & Test / Secret scan / Bot review）

### 🔐 供应链检查（涉及 data/ 改动时必填）

- [ ] SHA256 来自 Broadcom Support Portal 官方元数据
- [ ] `data/checksums.txt` 与 `data/vmware_downloads.json` 一致
- [ ] 无 `md5_mismatch` 告警

### 🧍 人工复核

- [ ] 关联场景已本地跑通
- [ ] README 涉及改动时已本地重新渲染
- [ ] Workflow 改动按影响范围用 `act -j lint-and-test` / `act -j gitleaks` 跑通

## 👀 Reviewer Guidance / 给评审人的话

**建议阅读顺序：** …
**重点关注：** …
**期望反馈类型：**
- [ ] 快速通过（trivial）
- [ ] 结构 / API 建议
- [ ] 安全把关
- [ ] 性能建议

---

<!-- 可选：Rollback plan / 迁移指南 / Screenshot -->
