# 架构说明 · vmware-downloads

本文档面向贡献者，说明数据如何从上游源流经脚本，最终生成 README 与校验清单。

## 数据流总览

```text
┌─────────────────────┐     ┌──────────────────────┐
│ Broadcom Support     │     │ archive.org          │
│ Portal (官方)        │     │ (历史镜像)           │
│ SHA256 / MD5 / build │     │ 可下载 URL / SHA1    │
└──────────┬──────────┘     └───────────┬──────────┘
           │                            │
   fetch_broadcom.py            fetch_metadata()
   (Playwright 登录抓取)        (collector.py, urllib)
           │                            │
           ▼                            ▼
  data/broadcom_metadata.json    archive.org metadata
           │                            │
           └────────────┬───────────────┘
                        ▼
           collect_vmware_links.py (主流程)
             1. 加载 Broadcom 元数据
             2. 加载 archive.org 索引
             3. 融合（官方 SHA256 主 + 镜像 URL 辅）
             4. 生成产物
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
 data/vmware_        data/            README.md
 downloads.json    checksums*.txt   (renderer.py)
```

## 关键模块（`scripts/vmware_lib/`）

| 模块 | 职责 |
|---|---|
| `broadcom.py` | 解析 Broadcom 元数据 → 下载条目（跳过无 SHA256） |
| `collector.py` | 拉 archive.org metadata（`fetch_metadata`，URL scheme 白名单校验）+ 建 filename 索引 |
| `legacy_merger.py` | 融合 Broadcom + archive.org 历史版本 |
| `parser.py` / `detail_parser.py` | 文件名解析（版本 / build / 平台）|
| `schema.py` | 写入前最小契约校验（`validate_downloads_json`）|
| `renderer.py` | 纯函数生成 README / checksums.txt / checksums.sha1.txt |
| `archive_common.py` | 共享常量（`ARCHIVE_META_TIMEOUT`）与工具 |
| `logs.py` | 统一 stdlib logging（stderr，`LOG_LEVEL` 可配）|

## 入口脚本（`scripts/`）

| 脚本 | 用途 | 网络/IO |
|---|---|---|
| `fetch_broadcom.py` | Playwright 登录 Broadcom 抓元数据 | 浏览器 + 凭据（env var）|
| `collect_vmware_links.py` | 主流程：融合 + 生成产物 | archive.org（`--dry-run` 可离线）|
| `detect_data_changes.py` | 检测数据是否有真实变化（非时间戳）| git |
| `summarize_changes.py` | 生成变更摘要（PR body 用）| git |
| `probe_archive_org.py` | 调研工具：探查 archive.org 版本清单 | archive.org |

## 设计约束

- **生产运行时零外部依赖**：`scripts/vmware_lib/` 与除 `fetch_broadcom.py`（需 Playwright）外的入口脚本仅用标准库（urllib / json / pathlib / dataclasses / asyncio）。
- **不打包**：刻意不设 `build-system` / `[project.scripts]`，直接 `python scripts/x.py` 运行，保持零安装门槛。
- **README 自动生成**：任何 README 改动必须改 `renderer.py` 再重新生成，CI 有 `Verify README is in sync` 门禁，手改会挂。
- **凭据只走环境变量**：`BROADCOM_USERNAME` / `BROADCOM_PASSWORD`，绝不硬编码。

## CI 质量门（`.github/workflows/ci.yml`）

Python 3.11 / 3.12 / 3.13 矩阵，每次 PR 与 push 到 main：

1. `ruff check scripts/ tests/`
2. `mypy scripts/vmware_lib`（零错误）
3. `bandit -r scripts/vmware_lib`（零 High/Medium/Low）
4. `pytest --cov --cov-fail-under=95`（库代码 100% 覆盖）
5. `Verify README is in sync`（README + checksums 与数据一致）
