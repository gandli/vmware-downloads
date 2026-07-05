#!/usr/bin/env python3
"""对比 HEAD 版和工作区版 vmware_downloads.json，摘要变化写入 stdout。

被 .github/workflows/monthly-update.yml 使用，避免 YAML 里嵌 heredoc 造成
`${{ ... }}` 双转义混乱。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys


def load_head_data() -> dict:
    """拿 HEAD 版本的 vmware_downloads.json，读不到返回空 dict"""
    try:
        raw = subprocess.check_output(
            ["git", "show", "HEAD:data/vmware_downloads.json"],
            stderr=subprocess.DEVNULL,
        )
        return json.loads(raw)
    except Exception:
        return {}


def versions_map(data: dict, key: str) -> dict[str, str]:
    """{version: build} 便于对比"""
    return {v["version"]: v.get("build", "") for v in data.get(key, [])}


def main() -> int:
    head_data = load_head_data()
    with open("data/vmware_downloads.json", encoding="utf-8") as f:
        new_data = json.load(f)

    lines = ["## 🔄 自动检测到 Broadcom 元数据变化", ""]

    for key, label in [
        ("workstation_pro", "Workstation Pro"),
        ("fusion_pro", "Fusion Pro"),
    ]:
        old = versions_map(head_data, key)
        new = versions_map(new_data, key)
        added = set(new) - set(old)
        removed = set(old) - set(new)
        changed = {v for v in old.keys() & new.keys() if old[v] != new[v]}

        if not (added or removed or changed):
            continue

        lines.append(f"### {label}")
        for v in sorted(added):
            lines.append(f"- ➕ 新增: **{v}** (build {new[v]})")
        for v in sorted(removed):
            lines.append(f"- ➖ 移除: {v}")
        for v in sorted(changed):
            lines.append(f"- 🔄 更新: {v} (build {old[v]} → {new[v]})")
        lines.append("")

    # GitHub Actions 环境下追加运行元数据
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if run_id and repo:
        lines += [
            "---",
            "🤖 由 [.github/workflows/monthly-update.yml](./.github/workflows/monthly-update.yml) 自动生成",
            f"运行 ID: `{run_id}` · [查看日志](https://github.com/{repo}/actions/runs/{run_id})",
        ]

    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
