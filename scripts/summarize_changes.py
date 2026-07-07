#!/usr/bin/env python3
"""对比 HEAD 版和工作区版 vmware_downloads.json，摘要变化写入 stdout。

被 .github/workflows/monthly-update.yml 使用，避免 YAML 里嵌 heredoc 造成
`${{ ... }}` 双转义混乱。

对比维度：
- build 变化（次版本升级）
- sha256 变化（**供应链安全信号**：build 不变但哈希变，说明安装包被悄悄替换）
- 新增/移除版本

若所有产品线都无 workstation_pro/fusion_pro 层面变化（例如仅 broadcom_metadata.json
或 checksums.txt 变了），输出兜底提示避免 PR body 为空。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# 让 summarize_changes 可以 import vmware_lib.logs（作为 script 直接跑时）
sys.path.insert(0, str(Path(__file__).parent))
from vmware_lib.logs import get_logger  # noqa: E402

log = get_logger(__name__)


def load_head_data() -> dict:
    """拿 HEAD 版本的 vmware_downloads.json，读不到返回空 dict"""
    try:
        raw = subprocess.check_output(
            ["git", "show", "HEAD:data/vmware_downloads.json"],
            stderr=subprocess.DEVNULL,
        )
        return json.loads(raw)
    except subprocess.CalledProcessError:
        # git show 失败：文件在 HEAD 不存在（首次提交），空 dict 是合理默认
        return {}
    except OSError as e:
        # git 不可用 / 权限问题：需要显式提示
        log.warning(
            "[summarize_changes] git 调用失败 (%s): %s", type(e).__name__, e
        )
        return {}
    except ValueError as e:
        # JSON 解析失败：HEAD 版本文件损坏，静默会让 PR body 说"零变化"
        log.warning(
            "[summarize_changes] HEAD JSON 解析失败 (%s): %s", type(e).__name__, e
        )
        return {}


def versions_map(data: dict, key: str) -> dict[str, tuple[str, str]]:
    """{version: (build, sha256)} 便于对比

    sha256 参与对比是为了捕获供应链安全信号：build 相同但 hash 不同 =
    安装包被替换（可能被投毒）。
    """
    result = {}
    for v in data.get(key, []):
        version = v.get("version", "")
        build = v.get("build", "")
        # sha256 可能在顶层，也可能在 downloads.{windows,linux}.sha256 里，取第一个非空
        sha256 = v.get("sha256", "")
        if not sha256:
            downloads = v.get("downloads", {})
            if isinstance(downloads, dict):
                # dict 形态: {windows: {...}, linux: {...}}
                for platform_data in downloads.values():
                    if isinstance(platform_data, dict) and platform_data.get("sha256"):
                        sha256 = platform_data["sha256"]
                        break
            elif isinstance(downloads, list):
                # list 形态兼容
                for dl in downloads:
                    if isinstance(dl, dict) and dl.get("sha256"):
                        sha256 = dl["sha256"]
                        break
        result[version] = (build, sha256.lower() if sha256 else "")
    return result


def format_changed(v: str, old_bs: tuple[str, str], new_bs: tuple[str, str]) -> str:
    """格式化单个已变更版本，兼顾 build 和 sha256"""
    old_build, old_sha = old_bs
    new_build, new_sha = new_bs
    details = []
    if old_build != new_build:
        details.append(f"build {old_build} → {new_build}")
    if old_sha != new_sha:
        # 供应链风险信号，用醒目标记
        details.append(f"⚠️ sha256 变化 ({old_sha[:8]}… → {new_sha[:8]}…)")
    return f"- 🔄 更新: {v} ({', '.join(details)})"


def main() -> int:
    head_data = load_head_data()
    try:
        with open("data/vmware_downloads.json", encoding="utf-8") as f:
            new_data = json.load(f)
    except FileNotFoundError:
        new_data = {}

    lines = ["## 🔄 自动检测到 Broadcom 元数据变化", ""]
    total_changes = 0

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
            build, _sha = new[v]
            lines.append(f"- ➕ 新增: **{v}** (build {build})")
        for v in sorted(removed):
            lines.append(f"- ➖ 移除: {v}")
        for v in sorted(changed):
            lines.append(format_changed(v, old[v], new[v]))
        lines.append("")
        total_changes += len(added) + len(removed) + len(changed)

    # 兜底：若 vmware_downloads.json 层面无产品变化，可能是其他文件变了
    # （broadcom_metadata.json / checksums.txt / README.md 非时间戳部分）
    if total_changes == 0:
        lines.append(
            "> ℹ️ `vmware_downloads.json` 中未检测到 workstation_pro / fusion_pro "
            "层面的版本变化。可能是 `broadcom_metadata.json`、`checksums.txt` "
            "或 `README.md` 的非时间戳内容发生了变化。请查看 diff 确认。"
        )
        lines.append("")

    # GitHub Actions 环境下追加运行元数据
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if run_id and repo:
        lines += [
            "---",
            "🤖 由 [.github/workflows/monthly-update.yml]"
            "(./.github/workflows/monthly-update.yml) 自动生成",
            f"运行 ID: `{run_id}` · "
            f"[查看日志](https://github.com/{repo}/actions/runs/{run_id})",
        ]

    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
