# 贡献指南

感谢关注 vmware-downloads！本项目整理 VMware Workstation Pro / Fusion Pro 的官方下载链接与 SHA256 哈希，供社区免费使用。

## 项目定位

- 🎯 **元数据仓库**：仓库**不承载**任何安装包
- 🎯 **两源交叉校验**：Broadcom Support Portal（官方权威）+ archive.org（免费镜像）
- 🎯 **自动化优先**：`.github/workflows/monthly-update.yml` 每月自动抓取

## 快速开始

> ⚠️ **Python 版本要求**：本项目 `pyproject.toml` 声明 `requires-python = ">=3.11"`，CI 也跑 3.11。
> macOS 系统自带 python 3.9.x 无法通过 `pytest` — 请先安装 3.11+：
> ```bash
> brew install python@3.11
> python3.11 -m venv .venv        # 关键：显式用 3.11
> ```

```bash
git clone https://github.com/gandli/vmware-downloads.git
cd vmware-downloads
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # 安装 pytest + ruff + playwright
python3 -m pytest -q             # 跑单测（应 100% 绿）
ruff check scripts/ tests/       # 代码风格检查
```

生产运行时**零外部依赖**，仅使用 Python 标准库；开发依赖仅用于测试和抓取。

### 日志级别（audit v3 引入）

所有脚本通过 `LOG_LEVEL` 环境变量控制日志级别：

```bash
LOG_LEVEL=DEBUG python -m scripts.detect_data_changes    # 详细模式（调试）
LOG_LEVEL=WARNING python -m scripts.collect_vmware_links # 只看警告及以上
```

默认 `INFO`。日志走 **stderr**，`stdout` 保留给结构化输出（PR body / checksums.txt）。

## 开发工作流

### 1. TDD 强制流程（RED → GREEN → REFACTOR）

- 修改任何 `scripts/vmware_lib/` 代码前，**先写测试**
- 测试放 `tests/`，覆盖新增分支
- `pytest -q` 全绿才可提 PR

### 2. Ruff 门禁

```bash
ruff check scripts/ tests/  # 必须全绿
ruff format scripts/ tests/  # 建议
```

### 3. 分支规范

```bash
git checkout -b feat/xxx        # 功能
git checkout -b fix/xxx         # 修 bug
git checkout -b chore/xxx       # 构建 / CI / 依赖
git checkout -b docs/xxx        # 文档
```

### 4. Commit 规范

采用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
feat(scope): 简短描述
fix(scope): 简短描述
chore: 简短描述
docs: 简短描述
```

**scope 常用值**：`legacy` / `broadcom` / `renderer` / `ci` / `readme` / `sort`

### 5. PR 检查表

- [ ] `pytest -q` 全绿
- [ ] `ruff check scripts/ tests/` 无错误
- [ ] 新增功能包含单测
- [ ] 若改动数据结构，同步更新 `README.md`（不要手改 README，跑 `scripts/collect_vmware_links.py` 重新渲染）
- [ ] PR 描述说明**动机 + 影响面**，附 diff summary

## 常见任务

### 本地重新生成 README + checksums

```bash
python3 -c "
import json, sys
sys.path.insert(0, 'scripts')
from vmware_lib.renderer import render_readme, render_checksums
data = json.load(open('data/vmware_downloads.json'))
open('README.md', 'w').write(render_readme(data))
open('data/checksums.txt', 'w').write(render_checksums(data))
"
```

### 手动抓取 Broadcom 元数据

需要 Broadcom Support Portal 账号（详见 `scripts/fetch_broadcom.py` 顶部注释）。

### 使用 act 本地跑 CI

```bash
brew install act
act -j lint-and-test    # 使用 .actrc 里的 catthehacker/ubuntu:act-latest 镜像
act -j gitleaks         # 单独跑 secret scan
```

`.actrc` 已配好 `--container-architecture linux/amd64` 与镜像，M 系列 Mac 也能跑。

## PR 提交流程（强制）

本仓库遵循 **GitHub Docs 官方 5 段 PR 描述结构** + **每个 PR 必先跑 `code-review-skill` 三维扫描**。

### 1. 提 PR 前必做（3×3 扫描）

用 Hermes Agent 加载 `code-review-skill` 对本次 diff 做扫描，输出下面这张表贴到 PR 描述：

| 维度 | 🔴 blocking | 🟡 important | 🟢 nit |
|:---|:---:|:---:|:---:|
| 🔒 安全 | 0 | 0 | 0 |
| ⚡ 性能 | 0 | 0 | 0 |
| 🛠️ 可维护性 | 0 | 0 | 0 |

**门禁**：🔴 blocking > 0 → 追加 commit 修完再开 PR；🟡 important > 0 → 本 PR 修或开跟随 issue。

### 2. PR 描述结构（5 段）

按 `.github/PULL_REQUEST_TEMPLATE.md` 已内嵌的 5 段填写：**Purpose / Overview / Context / Verification / Reviewer Guidance**。禁止：

- ❌ 粘贴 Telegram / 微信 / 机器人对话原文
- ❌ 大段 stack trace（贴 CI run 链接 + 1-2 行摘要）
- ❌ >400 行 diff 不做拆分（须在 Context 段声明分片计划）

### 3. 合并门禁

- CI 全绿（Lint & Test / Secret scan）
- Gitleaks / CodeRabbit / GitGuardian 等 bot **blocking = 0**
- README 与 data JSON 同步（`Verify README is in sync` step 通过）

## 数据完整性红线

- ⚠️ **不允许**：手工编辑 `data/vmware_downloads.json` 里的 SHA256（必须来自 Broadcom 官方）
- ⚠️ **不允许**：绕过 `detect_data_changes.py` 提交空数据变更
- ⚠️ **不允许**：往仓库提交任何 `.exe` / `.bundle` / `.dmg` 二进制文件（`.gitignore` 已拦截）

## 需要帮助？

- 💬 [讨论区](https://github.com/gandli/vmware-downloads/discussions) —— 使用问题、想法
- 🐛 [Issues](https://github.com/gandli/vmware-downloads/issues) —— bug、缺失版本、显示错误
- 🔒 [Security](./SECURITY.md) —— 供应链完整性问题（私下报告）
