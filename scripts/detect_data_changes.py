#!/usr/bin/env python3
"""检测 data/ 里是否有真实的数据变化（忽略时间戳字段）。

被 .github/workflows/monthly-update.yml 使用：
- 每次运行 fetch_broadcom.py 都会更新 collected_at / elapsed_sec 时间戳，
  导致原生 `git diff` 认为"每次都有变化"，触发无意义的空 PR。
- 本脚本剔除这些噪声字段后再对比，只在真实数据变化时返回退出码 0（有变化）。

用法（GitHub Actions 环境）：
    if python scripts/detect_data_changes.py; then
      echo "changed=true" >> $GITHUB_OUTPUT
    else
      echo "changed=false" >> $GITHUB_OUTPUT
    fi

退出码：
    0 - 有真实变化
    1 - 无变化（或只有噪声字段变化）
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

# 这些字段每次运行都变，但不代表数据本身变化，对比时剔除
NOISE_FIELDS = {
    "collected_at",   # ISO 时间戳
    "elapsed_sec",    # 抓取耗时
    "worker_count",   # BROADCOM_WORKERS 环境变量决定，与数据本身无关
    "duration_sec",   # fetch_broadcom 另一个耗时字段
}


def strip_noise(obj):
    """递归剔除噪声字段，返回一份新 dict"""
    if isinstance(obj, dict):
        return {k: strip_noise(v) for k, v in obj.items() if k not in NOISE_FIELDS}
    if isinstance(obj, list):
        return [strip_noise(v) for v in obj]
    return obj


def load_head_json(path: str) -> dict:
    """拿 HEAD 版的 JSON。文件不存在（首次提交）→ 返回空 dict。

    其他错误（权限/仓库损坏/JSON 损坏）**记录到 stderr 后返回空 dict** —— 静默吞
    会让 has_real_json_change 恒 True，与本脚本"避免空 PR"的初衷相反。
    """
    try:
        raw = subprocess.check_output(
            ["git", "show", f"HEAD:{path}"],
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        # 首次提交或该路径在 HEAD 不存在 —— 正常情况，不报警
        return {}
    except OSError as e:
        print(f"⚠️  load_head_json({path}) 调用 git 失败: {e}", file=sys.stderr)
        return {}

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"⚠️  load_head_json({path}) JSON 解析失败: {e}", file=sys.stderr)
        return {}


def load_work_json(path: str) -> dict:
    """拿工作区当前 JSON。文件不存在 → {}；解析错误 → 记录后 {}"""
    if not Path(path).exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"⚠️  load_work_json({path}) 失败: {e}", file=sys.stderr)
        return {}


def has_real_json_change(path: str) -> bool:
    """对比 HEAD 版 vs 工作区版，剔除噪声字段后是否仍有差异"""
    head = strip_noise(load_head_json(path))
    work = strip_noise(load_work_json(path))
    return head != work


def has_readme_change() -> bool:
    """README.md 除时间戳行外是否有变化"""
    try:
        head = subprocess.check_output(
            ["git", "show", "HEAD:README.md"],
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", errors="ignore")
    except subprocess.CalledProcessError:
        # HEAD 里没有 README（首次提交）—— 视为"从无到有"，返回空对比即可
        head = ""
    except OSError as e:
        print(f"⚠️  has_readme_change 调用 git 失败: {e}", file=sys.stderr)
        head = ""

    try:
        with open("README.md", encoding="utf-8") as f:
            work = f.read()
    except FileNotFoundError:
        work = ""

    def strip_ts(text: str) -> str:
        """删除"最后更新: YYYY-MM-DD HH:MM UTC"这一行

        用正则匹配日期格式而非硬编码前缀，避免文案/语言调整时误判。
        """
        # 匹配任意包含 YYYY-MM-DD HH:MM UTC 时间戳的整行
        ts_line = re.compile(
            r"^.*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s*UTC.*$",
            re.MULTILINE,
        )
        return ts_line.sub("", text)

    return strip_ts(head) != strip_ts(work)


def main() -> int:
    changed = False

    if has_real_json_change("data/vmware_downloads.json"):
        print("🆕 data/vmware_downloads.json: 有真实数据变化")
        changed = True

    if has_real_json_change("data/broadcom_metadata.json"):
        print("🆕 data/broadcom_metadata.json: 有真实数据变化")
        changed = True

    # checksums.txt 是纯 SHA256 列表，直接 git diff 对比即可（无时间戳）
    try:
        subprocess.check_output(
            ["git", "diff", "--quiet", "HEAD", "--", "data/checksums.txt"],
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print("🆕 data/checksums.txt: 有变化")
        changed = True

    if has_readme_change():
        print("🆕 README.md: 有非时间戳变化")
        changed = True

    if changed:
        return 0
    else:
        print("✅ 无真实数据变化，仅时间戳被刷新")
        return 1


if __name__ == "__main__":
    sys.exit(main())
