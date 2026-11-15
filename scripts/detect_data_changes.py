#!/usr/bin/env python3
"""检测 data/ 里是否有真实的数据变化（忽略时间戳字段）。

被 .github/workflows/monthly-update.yml 使用：
- 每次运行 fetch_broadcom.py 都会更新 collected_at / elapsed_sec 时间戳，
  导致原生 `git diff` 认为"每次都有变化"，触发无意义的空 PR。
- 本脚本剔除这些噪声字段后再对比，只在真实数据变化时返回退出码 0（有变化）。

用法（GitHub Actions 环境）：
    if python scripts/detect_data_changes.py --heartbeat-days 21; then
      echo "changed=true" >> $GITHUB_OUTPUT
    else
      echo "changed=false" >> $GITHUB_OUTPUT
    fi

心跳（--heartbeat-days N）：无人值守的 schedule 会被 GitHub 在仓库连续 60 天
无提交后自动停用。周频流水线在 Broadcom 不发版时可以连续两三个月只刷新时间戳
而零提交，正好撞上这条规则。传入 --heartbeat-days N 后，若"只剩时间戳变化"
且距最后一次提交已 ≥ N 天，就当成一次真实变化让流水线提交：
README 的"数据抓取时间"保持诚实，schedule 也永不停摆。

退出码：
    0 - 有真实变化（含心跳到期）
    1 - 无变化（或只有噪声字段变化）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# 让 detect_data_changes 可以 import vmware_lib.logs（作为 script 直接跑时）
sys.path.insert(0, str(Path(__file__).parent))
from vmware_lib.logs import get_logger  # noqa: E402

log = get_logger(__name__)

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
        log.warning("load_head_json(%s) 调用 git 失败: %s", path, e)
        return {}

    try:
        return json.loads(raw)
    except ValueError as e:
        # json.JSONDecodeError 与 UnicodeDecodeError 都继承 ValueError，
        # 一网打尽（bytes 解码失败也算 JSON 解析失败）
        log.warning("load_head_json(%s) JSON 解析失败: %s", path, e)
        return {}


def load_work_json(path: str) -> dict:
    """拿工作区当前 JSON。文件不存在 → {}；解析错误 → 记录后 {}"""
    if not Path(path).exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        # ValueError 覆盖 JSONDecodeError + UnicodeDecodeError（文件编码坏）
        log.warning("load_work_json(%s) 失败: %s", path, e)
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
        log.warning("has_readme_change 调用 git 失败: %s", e)
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


def has_checksums_change() -> bool:
    """checksums.txt 是纯 SHA256 列表，直接 git diff 对比即可（无时间戳）"""
    try:
        subprocess.check_output(
            ["git", "diff", "--quiet", "HEAD", "--", "data/checksums.txt"],
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        # 非 0：有差异，或者根本不是一个 git 仓库（报 CalledProcessError 并不合理，
        # 但旧行为就是当成“有变化”，保守起见保持）
        return True
    return False


def last_commit_age_days() -> float | None:
    """距最后一次提交过去了多少天。拿不到（非 git 仓库/命令失败）→ None"""
    try:
        raw = subprocess.check_output(
            ["git", "log", "-1", "--format=%ct"],
            stderr=subprocess.DEVNULL,
        )
        return (time.time() - int(raw.decode("utf-8", errors="ignore").strip())) / 86400
    except (subprocess.CalledProcessError, OSError, ValueError) as e:
        log.warning("last_commit_age_days 失败: %s", e)
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--heartbeat-days",
        type=int,
        default=int(os.environ.get("HEARTBEAT_DAYS", "0") or 0),
        help="连续 N 天无提交时，仅时间戳变化也提交一次（0=关闭心跳）",
    )
    args = parser.parse_args(argv)
    changed = False

    if has_real_json_change("data/vmware_downloads.json"):
        print("🆕 data/vmware_downloads.json: 有真实数据变化")
        changed = True

    if has_real_json_change("data/broadcom_metadata.json"):
        print("🆕 data/broadcom_metadata.json: 有真实数据变化")
        changed = True

    # checksums.txt 是纯 SHA256 列表，直接 git diff 对比即可（无时间戳）
    if has_checksums_change():
        print("🆕 data/checksums.txt: 有变化")
        changed = True

    if has_readme_change():
        print("🆕 README.md: 有非时间戳变化")
        changed = True

    if changed:
        return 0

    if args.heartbeat_days > 0:
        age = last_commit_age_days()
        if age is not None and age >= args.heartbeat_days:
            print(
                f"🫀 距上次提交 {age:.1f} 天（阈值 {args.heartbeat_days} 天）："
                f"提交时间戳刷新，保持 README 诚实 & schedule 不被 GitHub 停用"
            )
            return 0

    print("✅ 无真实数据变化，仅时间戳被刷新")
    return 1


if __name__ == "__main__":
    sys.exit(main())
