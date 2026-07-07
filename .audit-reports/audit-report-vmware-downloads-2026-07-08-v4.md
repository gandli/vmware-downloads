# 🔍 审计报告 · vmware-downloads · v4

**审计日期**：2026-07-08 (v4)
**Commit**：`76ffd0a` (main HEAD, post PR #18)
**审计员**：Hermes Agent · Skill = `fuck-my-shit-mountain`
**模式**：`full` · 简体中文 · markdown

---

## 📊 Executive Summary

| 维度 | 得分 | 等级 | 关键证据 |
|:---|:---:|:---:|:---|
| 🏗️ 架构 & 设计 | **9.5** | A+ | 10 lib 模块 SRP 清晰，`vmware_lib/{parser,collector,renderer,legacy_merger,broadcom,logs,schema}` 无循环依赖 |
| 🔒 安全 & 供应链 | **9.5** | A+ | 9 处 action 全 pin 40-char SHA · SLSA level 3 attest 已启用 · gitleaks + GitGuardian + Dependabot 三层扫描 · 0 secret leak |
| 🛡️ 稳定性 & 错误处理 | **9.5** | A+ | ✅ **0 处 `except Exception`**（v3 全清）· 0 bare except · schema fail-fast · http.client.HTTPException 兜底完整 |
| ⚡ 性能 | **9.0** | A | 6249 loc · 181 tests 0.12s · Playwright asyncio.Semaphore 限流 · urllib timeout 参数化 |
| 🧪 测试 | **8.5** | A- | 181 passed · **94% lib coverage** ↓ (v3 97%) · schema.py **80% ← 新增模块拖累** |
| 🛠️ 可维护性 | **8.0** | A- | ruff clean · 无 TODO/FIXME · **logging pattern shadow · 2 个 script 漏网**（probe_archive_org + fetch_broadcom）|
| 📖 治理 & 发布 | **9.0** | A | 5 段 PR 模板 · CHANGELOG.md · v2.1.0 tag · **缺 CODEOWNERS + pre-commit** |

**综合得分**：**8.9 / 10 (A)**（v3 的 8.7 → v4 的 8.9 = **+0.2**）
**Trend**：📈 v1 (6.5, C+) → v2 (7.9, B+) → v3 (8.7, A-) → **v4 (8.9, A)**

**推荐优先级**：修 3 个 P1 + 3 个 P2 → 项目进入 **A+ / 9.5+** 区间。

---

## 🎯 Top Risks（按优先级）

| # | 严重度 | 类别 | 位置 | 一句话 |
|:---:|:---:|:---|:---|:---|
| 1 | 🟡 P1-A | 🛠️ 可维护性 | `probe_archive_org.py` (14 print) · `fetch_broadcom.py` (11 log 调用) | **Logging pattern shadow** · v3 迁 3 个脚本走 stdlib logging，另 2 处独立出口漏网（skill v5 案例复现） |
| 2 | 🟡 P1-B | 🧪 测试 | `scripts/vmware_lib/schema.py` (80% cov, 17 行未覆盖) | **新增模块未达 lib 标准** · 项目其他 lib ≥95%，schema 拖低总覆盖率到 94% |
| 3 | 🟡 P1-C | 🛡️ 稳定性 | `scripts/vmware_lib/collector.py` (89% cov, 7 行未覆盖) | **v3 新加兜底分支未测** · L35-37/50/57-58/80 是 http.client 补丁的新路径 |
| 4 | 🟢 P2-A | 🔒 供应链 | `pyproject.toml` deps | **依赖范围锁定，无 lockfile** · `pytest>=8.0` 允许上游任意升级 |
| 5 | 🟢 P2-B | 📖 治理 | `.github/CODEOWNERS`, `.pre-commit-config.yaml` | **缺 CODEOWNERS + pre-commit** · 外部贡献者路径不完整、本地开发提交前无 ruff/pytest 门禁 |
| 6 | 🟢 P2-C | 🧪 CI | `.github/workflows/ci.yml` | **CI 单一 Python 3.11** · 无前向兼容（3.12/3.13）测试 |
| 7 | 🟢 P3-A | 🛠️ 可维护性 | `.gitignore` | **未忽略 `.coverage`** · 项目根有 53KB `.coverage` 二进制未追踪但也未忽略，未来可能被 `git add -A` 误提交 |

---

## 🔧 详细 Findings

### 🟡 P1-A · Logging Pattern Shadow · 2 个脚本漏网

**严重度**：🟡 Minor · **置信度**：**Confirmed** · **类别**：🛠️ 可维护性

#### 证据

v3 审计 P1-B 引入 `vmware_lib/logs.py` + 迁移 3 个脚本走 stdlib logging：
- ✅ `detect_data_changes.py` — 4 处 `log.warning(...)`
- ✅ `summarize_changes.py` — 2 处 `log.warning(...)`
- ✅ `collect_vmware_links.py` — 部分迁移（CLI 进度 print 保留 UX）

但**同 pattern 在另 2 个脚本独立出口漏网**：

```bash
$ rg "log\.(info|debug|warning|error)" scripts/ -c
detect_data_changes.py:4
summarize_changes.py:2
logs.py:2
# ← probe_archive_org.py: 0 处
# ← fetch_broadcom.py:    0 处
```

**1. `probe_archive_org.py` (14 处 print)** — 调研工具，模式与 `detect_data_changes.py` 同（都是 CLI 输出 + 错误告警混杂）：
```python
# L93 · 网络请求前的信息 print
print("📥 拉取 archive.org 元数据...")  # ← 可保留（CLI 进度 UX）
print(f"   共 {len(files)} 个文件")      # ← 可保留（CLI 进度 UX）
```

**2. `fetch_broadcom.py` (11 处 `log()` 调用)** — **自制 log helper 未升级**：
```python
# L57
def log(msg: str) -> None:
    print(msg, flush=True)      # ← 无 timestamp、无 level、无 stderr

# L63/183 等
log("[login] 打开登录页...")     # info 级
log(f"[{idx}/{total}] ❌ {tag} 超时")  # error 级（但和 info 走同一出口）
```

#### 现实失败场景

- **fetch_broadcom.py** 是唯一登录 Broadcom 的脚本。CI 抓取失败时排障需要：
  - **timestamp**：登录后哪一步花了 5 分钟（网络还是解析）？→ 现在无
  - **level**：过滤 error 快速定位崩溃位置 → 现在混在 info 里
  - **stderr**：与 stdout（写文件）分离 → 现在混合，无法 `2>&1` 分流
- **probe_archive_org.py** 是研究脚本，损失可控，但**保持 pattern 一致性**。

#### 最小修复

**A. `fetch_broadcom.py` 升级 log helper**（10 分钟）：

```python
# L20 加 import
from vmware_lib.logs import get_logger

_log = get_logger(__name__)

# L57 改造
def log(msg: str, level: str = "info") -> None:
    """兼容原 log(msg) 签名 + 加 level 参数供 error 出口用"""
    getattr(_log, level)(msg)

# L183 error 路径改
log(f"[{idx}/{total}] ❌ {tag} 超时", level="error")
```

**B. `probe_archive_org.py`** — **判定豁免**：调研工具，输出即 CLI report（不是错误告警），保留原样 + 加豁免注释：

```python
# scripts/probe_archive_org.py:1（顶部）
"""调研工具 · 交互式 CLI · 所有 print 均为 report 输出，不迁 logging"""
```

#### 回归测试建议

`tests/test_fetch_broadcom_log.py`（新）:
```python
def test_log_helper_maps_level_to_logger(caplog):
    from scripts.fetch_broadcom import log
    with caplog.at_level(logging.ERROR, logger="vmware.fetch_broadcom"):
        log("boom", level="error")
    assert "boom" in caplog.text
```

#### 估算工时：**20 分钟**（fetch_broadcom 迁移 + 1 测试 + probe_archive_org 加注释）

---

### 🟡 P1-B · schema.py 覆盖率 80% · 17 行未覆盖

**严重度**：🟡 Minor · **置信度**：**Confirmed** · **类别**：🧪 测试

#### 证据

```
scripts/vmware_lib/schema.py    87    17    80%   65, 67, 72, 83, 88, 113-114, 118, 122, 126-127, 131-134, 157-158, 161-164
```

项目 lib 覆盖率标准（其他模块）：`archive_common 100%` · `parser 98%` · `renderer 98%` · `broadcom 96%` · `legacy_merger 95%`。**schema.py 80% 是 lib 层最低**。

未覆盖行分类（读源码定位）：
- L65/67/72/83/88 — 顶层结构错误分支（top_keys 缺失、错类型）
- L113-114/118/122 — dl 字段错类型分支（filename 非 str、size 非 str/int）
- L126-127 — sha256 长度不等于 64 + 非 hex
- L131-134 — md5 长度校验（audit v3 CodeRabbit 加的分支）
- L157-158/161-164 — source 非法值 + 顶层 non-dict

**这些都是审计 v3 加的兜底分支，加了但没测试**。

#### 现实失败场景

Broadcom API 某天返回：
- `size: null`（不是 str 也不是 int）→ 未覆盖分支 L113
- `sha256: "not-hex-chars-here-and-more..."` (64 char 但非 hex) → 未覆盖 L126
- `source: "third-party-mirror"`（非 VALID_SOURCES）→ 未覆盖 L157

schema 校验会**通过**（因为分支没走），corrupt data 写入 `data/vmware_downloads.json`。

#### 最小修复

`tests/test_schema.py` 追加 6 个针对性测试（30 分钟）：

```python
def test_rejects_null_size():
    """size = None 应该被拒（既非 str 也非 int）"""
    data = _make_valid()
    data["workstation_pro"][0]["downloads"]["linux"]["size"] = None
    errs = validate_downloads_json(data)
    assert any("size" in e for e in errs)

def test_rejects_non_hex_sha256_of_correct_length():
    """sha256 长度 64 但含非 hex 字符（如中文/空格）应被拒"""
    data = _make_valid()
    data["workstation_pro"][0]["downloads"]["linux"]["sha256"] = "z" * 64
    errs = validate_downloads_json(data)
    assert any("sha256" in e for e in errs)

def test_rejects_unknown_source_value():
    """source 是 broadcom+archive/broadcom-only/archive-only 之外的值应被拒"""
    data = _make_valid()
    data["workstation_pro"][0]["downloads"]["linux"]["source"] = "third-party"
    errs = validate_downloads_json(data)
    assert any("source" in e for e in errs)

def test_rejects_non_dict_top_level():
    """顶层 data 不是 dict（list、str、None）应被拒"""
    errs = validate_downloads_json([{"a": 1}])  # list 不是 dict
    assert len(errs) > 0

# 类似再补 rejects_non_str_filename / rejects_md5_wrong_length
```

#### 目标：schema.py 覆盖率 80% → **≥95%**（对齐 lib 标准）

#### 估算工时：**30 分钟**

---

### 🟡 P1-C · collector.py 覆盖率 89% · v3 新加分支未测

**严重度**：🟡 Minor · **置信度**：**Confirmed** · **类别**：🛡️ 稳定性

#### 证据

```
scripts/vmware_lib/collector.py    66    7    89%   35-37, 50, 57-58, 80
```

L35-37 / 50 / 57-58 / 80 是 v3 P1-A + CodeRabbit review 加的分支（`http.client.HTTPException` 兜底、`AttributeError/TypeError/KeyError` legacy_merger 结构漂移防御）。**加了但没测**。

#### 现实失败场景

已在 v3 报告详述：Broadcom 某天返回 truncated response 触发 `IncompleteRead`，或 archive_meta 结构漂移触发 `AttributeError`。**分支加了但如果被误改回 `except Exception` 也没测试拦得住**。

#### 最小修复

`tests/test_collector.py` 追加（20 分钟）：

```python
def test_fetch_metadata_incomplete_read(monkeypatch):
    """audit v4: http.client.HTTPException 家族触发软失败"""
    import http.client
    def fake_urlopen(*args, **kwargs):
        raise http.client.IncompleteRead(b"partial", 100)
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    from vmware_lib.collector import fetch_metadata
    with pytest.raises(http.client.HTTPException):
        fetch_metadata()
```

#### 估算工时：**20 分钟**

---

### 🟢 P2-A · 依赖范围锁定 · 无 lockfile

**严重度**：🟢 Nit · **置信度**：**Confirmed** · **类别**：🔒 供应链

#### 证据

```toml
# pyproject.toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",       # ← 上游可任意升级 major
    "pytest-cov>=5.0",
    "ruff>=0.6",
    "playwright>=1.40",
]
```

CI 每次 `pip install -e ".[dev]"` 都会拿最新版。**pytest 9.0 若 breaking change**，CI 突然红。

#### 最小修复

选一：
- **A**（推荐）：`pip freeze > requirements-dev.lock` + CI 用 `pip install -r requirements-dev.lock`
- **B**：`pyproject.toml` 加严格上界 `pytest>=8.0,<9.0`

#### 估算工时：**15 分钟**

---

### 🟢 P2-B · 缺 CODEOWNERS + pre-commit

**严重度**：🟢 Nit · **置信度**：**Confirmed** · **类别**：📖 治理

#### 证据

```bash
$ ls .github/CODEOWNERS 2>&1
No such file
$ ls .pre-commit-config.yaml 2>&1
No such file
```

- 无 CODEOWNERS → PR 无自动 review 分配
- 无 pre-commit → 开发者本地可能提交 lint 失败的代码，CI 才发现

#### 最小修复

`.github/CODEOWNERS`：
```
* @gandli
```

`.pre-commit-config.yaml`（用 pin SHA）：
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: <SHA>
    hooks:
      - id: ruff
      - id: ruff-format
```

#### 估算工时：**20 分钟**

---

### 🟢 P2-C · CI 单一 Python 3.11

**严重度**：🟢 Nit · **置信度**：**Confirmed** · **类别**：🧪 CI

#### 证据

`.github/workflows/ci.yml` 只跑 Python 3.11。Python 3.12 已发布，3.13 即将发布。**无前向兼容验证**。

#### 最小修复

改 CI 加 matrix：
```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
```

#### 估算工时：**10 分钟**

---

### 🟢 P3-A · `.gitignore` 未忽略 `.coverage`

**严重度**：🟢 Nit · **置信度**：**Confirmed** · **类别**：🛠️ 可维护性

#### 证据

```bash
$ ls -la .coverage
-rw-r--r-- 53248 .coverage    # ← 53KB SQLite 数据库
$ grep coverage .gitignore
.coverage       # 只有精确匹配（旧 pytest 生成一个文件）
```

**问题**：pytest-cov 有时生成 `.coverage.HOSTNAME.PID` 变体，`.gitignore` 不匹配。且项目根 `.coverage` 未被 `.git status` 提示是 untracked（说明已被匹配到），但**对新的 `.coverage.*` 变体不生效**。

#### 最小修复

```diff
- .coverage
+ .coverage
+ .coverage.*
+ coverage.xml
```

#### 估算工时：**2 分钟**

---

## 🚀 Fix Order（建议顺序）

| # | 优先 | 修复 | 工时 | 影响 |
|:---:|:---:|:---|:---:|:---|
| 1 | P1-A | fetch_broadcom.py log helper 走 stdlib logging + probe 加豁免注释 | 20m | 🛠️ +0.5 |
| 2 | P1-B | schema.py 补 6 个测试，覆盖率 80→95%+ | 30m | 🧪 +0.5 |
| 3 | P1-C | collector.py 补 3 个测试覆盖 v3 新增分支 | 20m | 🛡️ +0.3 |
| 4 | P2-A | requirements-dev.lock + CI 用 lockfile | 15m | 🔒 +0.2 |
| 5 | P2-B | CODEOWNERS + .pre-commit-config.yaml | 20m | 📖 +0.2 |
| 6 | P2-C | CI matrix 加 3.12 + 3.13 | 10m | 🧪 +0.1 |
| 7 | P3-A | .gitignore 扩展 `.coverage.*` | 2m | 🛠️ |

**总工时：约 2 小时**

---

## ⚡ Quick Wins

- **P3-A**（2 min）：`.gitignore` 加 2 行
- **P2-C**（10 min）：CI matrix 3 行
- **P2-B**（20 min）：2 个治理文件

---

## 📈 v1 → v2 → v3 → v4 Pattern 全景

| 轮次 | 关键 pattern | 修复位置 | 遗漏（下轮暴露） |
|:---|:---|:---|:---|
| v1 | 死代码 + lint 门禁 | ruff + `probe_broadcom_full` 删除 | PR 模板不合规 |
| v2 | 供应链 pin SHA + silent swallow | 8 action pin + detect_data_changes 具名 | **`except Exception` 只修了 1/4 出口** |
| v3 | Pattern shadow (v2 遗漏 3 处) + logging + schema | P1-A/B/C 全清 4 处 except + 3 个脚本 print → logger + schema fail-fast | **logging 迁移只覆盖 3/5 脚本** |
| v4 | **Logging pattern shadow 复现** + 新增分支未测 | 本次 P1-A/B/C 补齐 2 脚本 + 覆盖率 | （待 v5 复盘） |

**教训**（登记到 skill）：
- **Pattern shadow 会连续犯 N 轮** — v3/v4 都在修 pattern shadow 的不同层：v3 修「异常处理 pattern shadow」，v4 修「logging pattern shadow」。**根因相同**：修完主路径没做 project-wide grep。
- **新增分支必须同 PR 补测试** — v3 加了 `http.client.HTTPException` / `AttributeError/TypeError/KeyError` 兜底，但只加了 P1-A 的 2 个测试，兜底分支本身没测。v4 报告发现覆盖率从 97% 掉到 94%。
- **"覆盖率下降"是 pattern shadow 的量化信号** — 每轮审计对比 lib 覆盖率，掉 3% 即触发覆盖率专项。

---

**报告文件**：`.audit-reports/audit-report-vmware-downloads-2026-07-08-v4.md`

#audit-v4 #logging-pattern-shadow #coverage-regression #vmware-downloads
