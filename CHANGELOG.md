# Changelog

All notable changes to this project will be documented in this file.

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) · 版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/).

## [Unreleased]

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
