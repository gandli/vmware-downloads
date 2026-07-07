# 贡献指南

感谢关注 vmware-downloads！本项目整理 VMware Workstation Pro / Fusion Pro 的官方下载链接与 SHA256 哈希，供社区免费使用。

## 项目定位

- 🎯 **元数据仓库**：仓库**不承载**任何安装包
- 🎯 **两源交叉校验**：Broadcom Support Portal（官方权威）+ archive.org（免费镜像）
- 🎯 **自动化优先**：`.github/workflows/monthly-update.yml` 每月自动抓取

## 快速开始

```bash
git clone https://github.com/gandli/vmware-downloads.git
cd vmware-downloads
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # 安装 pytest + ruff + playwright
python3 -m pytest -q             # 跑单测（应 100% 绿）
ruff check scripts/ tests/       # 代码风格检查
```

生产运行时**零外部依赖**，仅使用 Python 标准库；开发依赖仅用于测试和抓取。

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
act -j test  # 使用 .actrc 里的 catthehacker/ubuntu:act-latest 镜像
```

## 数据完整性红线

- ⚠️ **不允许**：手工编辑 `data/vmware_downloads.json` 里的 SHA256（必须来自 Broadcom 官方）
- ⚠️ **不允许**：绕过 `detect_data_changes.py` 提交空数据变更
- ⚠️ **不允许**：往仓库提交任何 `.exe` / `.bundle` / `.dmg` 二进制文件（`.gitignore` 已拦截）

## 需要帮助？

- 💬 [讨论区](https://github.com/gandli/vmware-downloads/discussions) —— 使用问题、想法
- 🐛 [Issues](https://github.com/gandli/vmware-downloads/issues) —— bug、缺失版本、显示错误
- 🔒 [Security](./SECURITY.md) —— 供应链完整性问题（私下报告）
