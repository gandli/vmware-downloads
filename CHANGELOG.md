# Changelog

All notable changes to this project will be documented in this file.

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) · 版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/).

## [Unreleased]

### Added
- 🆕 **`data/checksums.sha1.txt`** — SHA1 兜底校验清单（191 条 · 100% 覆盖），弥补 archive.org 老版本无 SHA256 的空缺
- 🆕 **`render_sha1_checksums()`** — 新渲染函数生成 `sha1sum -c` 兼容文件
- 🆕 **`_hash_display()` 统一哈希展示** — 优先 SHA256，缺失时 fallback 到 SHA1（明示 algo 标签）
- ✅ **+5 renderer 测试**（tests/test_renderer.py）

### Changed
- 🛠️ **README 表格所有 "MD5 only" 显示 → SHA1 兜底**（164 处老版本全部有可用校验值）
- 🛠️ **README 校验章节文案** — 说明 SHA256 (Broadcom 主线) + SHA1 (archive.org 历史) 双清单及原因
- 🛠️ **`collect_vmware_links.py` 主流程** — 增加 `checksums.sha1.txt` 出口

### Rationale
- **VMware 官网 SHA256 已无法回填**：Broadcom 2023 收购后下架老版本 support 页面，Customer Connect SPA 无 Wayback 缓存，old-VMware.com Release Notes 不含 sha256
- **SHA1 密码学强度弱于 SHA256**，但用于**下载完整性校验（防传输损坏 + 官方镜像投毒）足够**
- **archive.org 官方 metadata 提供 sha1（201/202 覆盖）**，直接使用无需下载算

## [2.3.0] - 2026-07-08 (audit v5)

### Added
- 🆕 **`CODE_OF_CONDUCT.md`** — Contributor Covenant 2.1 简体中文版（GitHub Community Standards 治理层三缺一补齐）
- ✅ **`tests/test_collect_vmware_links_log.py`** — 3 测试保护 collector CLI 的 logger 引入（audit v5 P1-A）
- ✅ **4 lib 模块覆盖率补齐到 100%** — broadcom / legacy_merger / parser / renderer（audit v5 P1-B · 8 新测试）
- ✅ **URL scheme 白名单断言 + 测试** — `fetch_metadata` 拒 `file://` / `ftp://` 等 scheme（audit v5 P1-C · 3 新测试）
- 🆕 **`ARCHIVE_META_TIMEOUT` 模块常量** — `archive_common.py` 提取 timeout 常量避免多处硬编码（audit v5 P2-B）
- 🆕 **dev extras 加入 bandit + mypy** — 审计工具链纳入 lockfile，下次审计无需现装（audit v5 P2-C）

### Changed
- 🛠️ **Logging pattern shadow 第 4 轮根治（audit v5 P1-A）** — v3/v4 已迁 4 个脚本，v5 才发现 `collect_vmware_links.py` 从头未 `import logging`：
  - 引入 `from vmware_lib.logs import get_logger` · 5 处 error/warning print 迁 logger.error/warning
  - CLI 结构化报告 print 保留（给人看的进度/表头）· error/warning 双出口（logger + user hint）
- 🔒 **Bandit B310 三处 urllib.urlopen 显式豁免（audit v5 P1-C）** — 加 `# nosec B310` 注释：
  - `scripts/vmware_lib/collector.py:41` · 加 URL scheme 白名单 assert
  - `scripts/vmware_lib/legacy_merger.py:172` · nosec + 使用 ARCHIVE_META_TIMEOUT 常量
  - `scripts/probe_archive_org.py:37` · nosec + 使用 ARCHIVE_META_TIMEOUT 常量
- 🛠️ **legacy_merger `timeout=30` 硬编码 → 常量引用（audit v5 P2-B）** — 三处 timeout 统一走 `ARCHIVE_META_TIMEOUT`

### Fixed
- 🐛 **legacy_merger 死代码 `platform == "unknown"` 分支** — `is_installer` 已限定 `.exe/.bundle/.dmg`，`detect_platform` 恰好识别这三种 → 不可达。加 `pragma: no cover` 保留防御性检查用于未来扩展

### Audit
- 📊 **v5 综合评分 91.5/100 (A)** — v1 65 → v2 79 → v3 87 → v4 89 → **v5 91.5**
- 📊 **lib cov 从 98.33% → 100.00%**（4 模块补齐 + 2 处 pragma 豁免）
- 📊 **Bandit Medium 3 → 0** · Low 稳定 11（subprocess 全 hardcode 参数无风险）
- 📊 **测试数 205 → 221**（+16 targeted test）

## [2.2.0] - 2026-07-08 (audit v4)

### Added
- 🆕 **`.pre-commit-config.yaml`** — 本地提交前门禁（ruff + trailing whitespace + yaml/toml lint）
- 🆕 **`.github/CODEOWNERS`** — PR review 自动分配给 @gandli
- 🆕 **`requirements-dev.lock`** — pip freeze 生成的精确版本 lockfile，CI 用它保证复现
- ✅ **schema.py 单元测试补齐** — 14 个新测试覆盖顶层类型 / filename / sha256 / md5 / size / build / downloads / source 等所有 v3 加的兜底分支
- ✅ **collector.py 单元测试补齐** — 6 个新测试覆盖 v3 P1-A 加的 http.client.HTTPException + `size` 类型兜底 + basename 冲突分支
- ✅ **`tests/test_fetch_broadcom_log.py`** — 3 个测试保护 log() 双出口（stdout + stdlib logging）

### Changed
- 🛠️ **Logging pattern shadow 补齐（audit v4 P1-A）** — v3 迁 3 脚本走 stdlib logging，v4 补齐第 4 处：
  - `scripts/fetch_broadcom.py:57` · 自制 `log()` 升级到 stdlib logging + 保留 print 双出口（Playwright 抓取进度实时刷新）
  - `scripts/fetch_broadcom.py:198,205` · error 出口显式 `level="error"`（timestamp/level/stderr 分流）
  - `scripts/probe_archive_org.py` · 加豁免注释（纯调研 CLI 报告不迁）
- 🔒 **依赖版本上界锁定（audit v4 P2-A）** — `pyproject.toml`：pytest/pytest-cov/ruff/playwright 都加严格上界，避免上游 major 升级 breaking CI
- 🧪 **CI 前向兼容矩阵（audit v4 P2-C）** — `.github/workflows/ci.yml`：Python 3.11 → **3.11 + 3.12 + 3.13 matrix**
- 🧪 **CI 用 lockfile 安装** — `pip install -r requirements-dev.lock` 保证 CI 与本地版本一致
- 🧪 **cov 门禁抬高** — `--cov-fail-under=85` → `--cov-fail-under=95`（新覆盖率 98.33%）

### Fixed
- 🛠️ **`.gitignore` 扩展** — 增加 `.coverage.*` + `coverage.xml`（pytest-cov 部分场景生成的变体）

### Test Coverage
- **v3**: 94.11% (schema 80% / collector 89% 拖累)
- **v4**: **98.33%** ✅（schema 100% · collector 100%）
- 单测数量：181 → **205**（+24 tests）

## [2.1.0] - 2026-07-08 (audit v3)

### Added
- 🆕 **`scripts/vmware_lib/logs.py`** — 统一 stdlib logging 模块（零依赖）
  - `LOG_LEVEL` 环境变量控制级别（DEBUG/INFO/WARNING/ERROR）
  - 日志走 stderr，stdout 保留给结构化输出
  - 完整单元测试 (`tests/test_logs.py`, 4 tests)
- 🆕 **`scripts/vmware_lib/schema.py`** — JSON schema 契约校验器（零依赖）
  - `validate_downloads_json()` 检查 sha256/url/size/source 格式
  - 主入口 `collect_vmware_links.py` 集成 fail-fast（写文件前校验）
  - 完整单元测试 (`tests/test_schema.py`, 11 tests 含真数据回归)
- 🆕 **SLSA build provenance** — `actions/attest-build-provenance@v4.1.1`
  - `monthly-update.yml` 每次发布 attestation
  - 用户可 `gh attestation verify data/vmware_downloads.json --repo gandli/vmware-downloads`
- 🆕 **`CHANGELOG.md`** — 遵循 Keep a Changelog 规范

### Changed
- 🛡️ **修复 3 处 pattern shadow · `except Exception`** — v2 只修 detect_data_changes，v3 补齐：
  - `scripts/summarize_changes.py:32` → 具名捕获 `subprocess.CalledProcessError` / `OSError` / `ValueError`
  - `scripts/collect_vmware_links.py:89` → `(OSError, ValueError, RuntimeError, json.JSONDecodeError)`
  - `scripts/collect_vmware_links.py:167` → `(ImportError, OSError, ValueError, RuntimeError)`
  - `scripts/fetch_broadcom.py:186` → `(PWError, OSError, ValueError, json.JSONDecodeError)`
- 🛠️ **error / warning 路径 print → logging** — `detect_data_changes.py` + `summarize_changes.py` 全迁移
- 📖 **CONTRIBUTING.md** — 加 Python 3.11 版本要求提示 + LOG_LEVEL 使用说明

### Security
- 🔒 SLSA level 3 attestation → 用户可验证 `data/*.json` 来源
- 🔒 schema 校验 → Broadcom API 静默改字段将被 fail-fast 拦截

### Tests
- **179 passed** / 97% coverage（v2 是 162 passed）
- 新增 4 类回归测试：logs (4) · schema (11) · summarize logging (2) · pattern shadow

## [2.0.0] - 2026-07-07 (audit v2)

### Added
- 治理三件套：`SECURITY.md` / `CONTRIBUTING.md` / `.github/dependabot.yml`
- 官方 5 段 GitHub Docs PR body 模板
- `code-review-skill` 3×3 强制门禁（🔒安全 · ⚡性能 · 🛠️可维护性 × 🔴/🟡/🟢）
- 8 处 GitHub Actions 全部 pin 40-char SHA + tag 注释
- Node 24 runtime 迁移（Actions 5 major bump）

### Changed
- **`detect_data_changes.py`** 3 处 `except Exception` → 具名异常 + stderr
- `.github/workflows/ci.yml` 加 `persist-credentials: false`
- 162 passed / ruff clean

## [1.0.0] - 2026-07-06 (audit v1)

### Added
- 初版审计：删除死代码 `probe_broadcom_full.py`
- 引入 ruff + pytest 门禁
- 融合逻辑重构为 `scripts/vmware_lib/` 5 模块

---

[Unreleased]: https://github.com/gandli/vmware-downloads/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/gandli/vmware-downloads/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/gandli/vmware-downloads/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/gandli/vmware-downloads/releases/tag/v1.0.0
