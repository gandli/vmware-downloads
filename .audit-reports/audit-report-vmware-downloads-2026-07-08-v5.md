# 🔍 vmware-downloads · 审计白皮书 v5

**日期**：2026-07-08 · **HEAD**：`e6712ad` (v2.2.0) · **审计员**：Hermes Agent
**Skill**：fuck-my-shit-mountain (Deep Scan · full mode)
**审计工具链**：pytest+cov / ruff / bandit / grep / mypy(未装)

---

## 一、Executive Summary

| 维度 | 分数 | 评语 |
|:---:|:---:|:---|
| 🏛️ 架构 | 9.5 | vmware_lib 库/入口清晰分层，v4 加入 schema/logging 后 boundary 更硬 |
| 🔒 安全 | 9.0 | Bandit Medium × 3 (urllib 无 nosec 豁免) · Gitleaks/GitGuardian 全 pass |
| 🛡️ 稳定性 | 9.5 | `except Exception` 0 处残留 · v2-v4 三轮 pattern shadow 已治理 |
| ⚡ 性能 | 9.0 | 抓取 30+ 分钟合理 (Playwright limit) · 无性能红线 |
| 🧪 测试 | 9.0 | 205 tests · 98.33% cov (剩 4 模块 <100%) · lib 层无 IO mock 假绿 |
| 🛠️ 可维护 | 9.0 | `collect_vmware_links.py` 39 print · 未迁 logging (v3/v4 pattern shadow 第 4 轮) |
| 📜 治理 | 9.0 | dependabot/pre-commit/CODEOWNERS/SECURITY/CONTRIBUTING/PR-template 齐备 · 缺 CODE_OF_CONDUCT |

## 🏆 综合评分：**91.5 / 100 (A / 优秀)**

**技术债估算**：约 **1.5 小时**（3 P1 + 3 P2 · 全部为增量补齐，无重构风险）

**分数走势**：v1 65 → v2 79 → v3 87 → v4 89 → **v5 91.5** · 治理层进入 A 区间

---

## 二、Pattern 全景表（v1→v5）

| Pattern | v1 | v2 修 | v3 修 | v4 修 | v5 状态 |
|:---|:---:|:---:|:---:|:---:|:---|
| `except Exception` 具名化 | 5+ | 3 处 | 2 处 | 0 | ✅ 0 处残留 |
| logging 迁移（生产脚本 print 分流） | 全部 print | — | detect / summarize / (1) | fetch_broadcom | 🔴 **collect_vmware_links.py 漏网**（39 print · 未引入 logger） |
| schema 兜底测试 | — | — | 加分支未测 | 补 14 test | ✅ 100% |
| http.client.HTTPException | — | — | 加 | 补 6 test | ✅ 100% |
| lib 覆盖率 | 0 | 60% | 97% → 94%(倒退) | 98.33% | 🟡 4 模块仍 <100% |

**Pattern shadow 连续 4 轮教训**：v3 修 3 脚本 → v4 补 fetch_broadcom → v5 才发现 `collect_vmware_links.py` 从头就没引入 logger。**根因不变**：每轮修完不做「所有 scripts 是否都 import logging」的 project-wide 断言。

---

## 三、Top Risks（Fix Order）

| # | 严重 | 位置 | 问题 | 修复 | 工时 |
|:---:|:---:|:---|:---|:---|:---:|
| P1-A | 🔴 | `collect_vmware_links.py` (整文件) | 39 print 未迁 logging · pattern shadow 第 4 轮 | 引入 `from vmware_lib.logs import get_logger` · error/warning 分流到 logger.error/warning · CLI 报告 print 保留 | 25m |
| P1-B | 🔴 | 4 lib 模块 (broadcom / legacy_merger / parser / renderer) | 96-98% cov · v4 剩余长尾 | 补 4 个 targeted test 覆盖剩余分支 | 20m |
| P1-C | 🔴 | 3 处 `urllib.urlopen` (Bandit Medium B310 × 3) | 缺 `# nosec` 显式豁免 · 硬编码 URL 无 scheme 断言 | 加 `# nosec B310` 注释 + `assert URL.startswith("https://")` 双保险 | 15m |
| P2-A | 🟡 | 项目根 | CODE_OF_CONDUCT.md 缺失（治理三缺一） | 用 Contributor Covenant 2.1 模板 | 10m |
| P2-B | 🟡 | `legacy_merger.py:169` | `timeout=30` 硬编码 · 与 collector.py 不一致 | 提取 module-level `ARCHIVE_META_TIMEOUT = 30` · 允许 kwargs 覆盖 | 10m |
| P2-C | 🟡 | `pyproject.toml [dev]` | 缺 mypy + bandit（audit 工具链未固化） | 加入 dev extras · 更新 lockfile | 10m |

**P0**：无

---

## 四、详细 Issue 清单

### 🔴 P1-A · Logging Pattern Shadow 第 4 轮 · `collect_vmware_links.py`

**位置**：`scripts/collect_vmware_links.py` · 39 处 `print()` · 未 `import logging` · 未使用 `get_logger`

**证据**：
```python
# L63-73（当前）
print("=" * 60)
print("VMware 下载链接收集器 v3")
print("=" * 60)
...
print(f"  ❌ 未找到 {broadcom_path}")
print("  请先运行 scripts/fetch_broadcom.py 生成元数据。")
```

**现实失败场景**：
- CI 环境 `LOG_LEVEL=DEBUG` 想只看 error+ 时无法过滤（全走 stdout）
- 无 timestamp → 长时间跑的 monthly-update.yml 无法计时定位卡点
- 错误路径无 stderr 分流 → 触发 grep `❌` 才能提取，而非用 log level

**分类判断（沿用 v4 规则）**：
- **保留 print**（结构化 CLI 报告给人看）：横线分隔符、进度表头、最终统计
- **迁 logger**：`❌ 未找到` / `❌ 元数据校验失败` / warning 路径

**最小修复**：
```python
from vmware_lib.logs import get_logger

logger = get_logger(__name__)

# error 路径迁 logger
if not broadcom_path.exists():
    logger.error("未找到 %s", broadcom_path)
    print("  请先运行 scripts/fetch_broadcom.py 生成元数据。")  # user hint 保留
    return 1
```

**回归测试**：`tests/test_collect_vmware_links_log.py` · 3 个测试 (error/warning/info level routing)

**工时**：25m

---

### 🔴 P1-B · lib 覆盖率剩余 4 模块 <100%

| 模块 | Cov | 未覆盖行 | 分支说明 |
|:---|:---:|:---:|:---|
| `broadcom.py` | 96% | 77, 79-80 | `_parse_release_date` 非 3 段 / 未知月份 |
| `legacy_merger.py` | 95% | 75, 169-170 | `platform == "unknown"` 跳过 + 真实 urlopen |
| `parser.py` | 98% | 55 | `_platform_from_path` `Fusion/` 前缀分支 |
| `renderer.py` | 98% | 60, 74-75 | broadcom-only size 空 + collected_at 缺失 |

**证据（broadcom.py:77-80）**：
```python
month_num = _MONTHS.get(mon)
if not month_num:           # L77 · 未覆盖
    return ""               # L78
return f"{int(year):04d}-{month_num:02d}-{int(day):02d}"  # L79-80 部分
```

**现实失败场景**：Broadcom 未来改用 `Jul` 之外的月份缩写（或多语言 → `Juli`），`_parse_release_date` 返回 `""` 但没测过 → 未来变动无法通过 CI 提前发现。

**最小修复**：`tests/test_broadcom.py` / `test_legacy_merger.py` / `test_parser.py` / `test_renderer.py` 各加 1 targeted test

**工时**：20m

---

### 🔴 P1-C · Bandit Medium × 3 · urllib.urlopen 缺显式豁免

**位置**：
- `scripts/probe_archive_org.py:36`
- `scripts/vmware_lib/collector.py:36`
- `scripts/vmware_lib/legacy_merger.py:169`

**证据**：
```python
# scripts/vmware_lib/collector.py:36
req = urllib.request.Request(url, headers={"User-Agent": "vmware-downloads/2.0"})
with urllib.request.urlopen(req, timeout=timeout) as r:  # B310 Medium/High
    return json.load(r)
```

**Bandit 提示**：CWE-22 (Path Traversal / File URL Scheme Attack)

**现实失败场景**：
- Bandit 报错不等于真风险（这三处 URL 都是硬编码 `https://archive.org/...`）
- 但缺显式豁免 → 未来若 Sonarqube/Snyk/Codacy 集成 → 会在 dashboard 上一直标红
- 若未来某天 URL 变成参数（如支持自定义 archive mirror）→ 真风险出现，届时 grep `# nosec` 才能定位需要重审的位置

**最小修复**：
```python
# scripts/vmware_lib/collector.py:36
# archive.org 域硬编码，非用户输入 → path traversal 不适用
assert url.startswith(("https://archive.org/", "http://archive.org/")), \
    f"unexpected URL scheme: {url}"
with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
    return json.load(r)
```

三处同 pattern 修复 + 加 pytest 断言测试 (URL scheme 白名单)。

**工时**：15m

---

### 🟡 P2-A · CODE_OF_CONDUCT.md 缺失

**证据**：`SECURITY.md` ✅ · `CONTRIBUTING.md` ✅ · `CODE_OF_CONDUCT.md` ❌

**影响**：GitHub Community Standards 页面显示未达标（三缺一），OSS 贡献者进入时缺参考。

**最小修复**：Contributor Covenant 2.1 简体中文版模板 · 加联系邮箱

**工时**：10m

---

### 🟡 P2-B · `timeout=30` 硬编码 · 与 `collector.py` 不一致

**位置**：`scripts/vmware_lib/legacy_merger.py:169` · `scripts/probe_archive_org.py:36`

**证据**：
- `collector.py:33` · `def fetch_metadata(url=..., timeout: int = 30)` — 可参数化
- `legacy_merger.py:169` · `timeout=30` 硬编码
- `probe_archive_org.py:36` · `timeout=30` 硬编码

**修复**：提取到 `archive_common.py` 的 `ARCHIVE_META_TIMEOUT = 30`，三处引用同一常量。

**工时**：10m

---

### 🟡 P2-C · dev extras 缺 mypy / bandit

**证据**：`pyproject.toml [project.optional-dependencies].dev` 只有 pytest/pytest-cov/ruff/playwright · 未包含 mypy 和 bandit。

**影响**：v5 审计临时 `pip install bandit -q` 才能扫描 · 下次审计要重复。

**修复**：加入 dev extras + 更新 `requirements-dev.lock`。

**工时**：10m

---

## 五、Coverage Matrix

| 维度 | Confidence | 检查证据 | 排除/限制 |
|:---|:---:|:---|:---|
| 架构 | High | vmware_lib 8 模块 + 5 script 全扫 | 无 |
| 安全 | High | Bandit 全扫 + Gitleaks/GitGuardian CI 记录 | 无 |
| 稳定性 | High | `except *` 全扫 + logs.py 测试完整 | 无 |
| 性能 | Medium | 未跑 real profile · 只静态审计 | Playwright 30min 抓取实测超出 audit 时间 |
| 测试 | High | pytest --cov --report=term-missing 全跑 | 无 |
| 可维护 | High | 39 print 逐处分类 + logs 引入路径核查 | 无 |
| 治理 | High | GitHub Community Standards 逐项对表 | 无 |

---

## 六、Fix Order

依 severity + 依赖关系：

1. **P1-A · 25m** · 修 collect_vmware_links.py logging (根治 pattern shadow 第 4 轮)
2. **P1-B · 20m** · 4 lib 模块补齐测试到 100%
3. **P1-C · 15m** · 3 处 urlopen 加 nosec + scheme 断言
4. **P2-A · 10m** · CODE_OF_CONDUCT.md
5. **P2-B · 10m** · timeout 常量化
6. **P2-C · 10m** · dev extras + lockfile

**总计**：约 1.5 小时 · 预期 cov 从 98.33% → **99.5%+**，评分从 91.5 → **95+**

---

## 七、v1-v5 演进对照

| Rev | 综合分 | 主打 | 遗留 |
|:---:|:---:|:---|:---|
| v1 | 65 (D) | baseline | 5+ `except Exception` |
| v2 | 79 (C+) | 3 处 pattern shadow → 具名 | logging 全部 print |
| v3 | 87 (B+) | schema + 3 script logging + SLSA | fetch_broadcom.py 自制 log · lib cov 倒退 |
| v4 | 89 (A-) | logging pattern shadow 补 fetch_broadcom + schema/collector 100% | collect_vmware_links.py 未迁 (**未发现**) |
| **v5** | **91.5 (A)** | **collect_vmware_links.py + 剩余 cov + Bandit + CoC** | — |

---

## 八、结论

**准入门槛**：91.5 ≥ 85 · **P0 = 0** · **P1 = 3** · 全部为 skill 沉淀的 pattern 复扫产物，非新腐化。

**推荐动作**：直接进入修复循环，无需二次确认（用户允许"直接执行"）。

#audit-v5 #pattern-shadow-4th #coverage-tail #bandit-medium
