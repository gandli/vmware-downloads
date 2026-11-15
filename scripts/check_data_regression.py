#!/usr/bin/env python3
"""提交前数据回归防护 —— 无人值守流水线的安全阀。

把工作区里待提交的 ``data/*.json`` 与基线版（默认 HEAD）对比，命中任一条就
拒绝提交：

- 下载条目消失（上一版有、这一版没有）
- 可下载链接退化成"需登录 Broadcom 官网"
- 某版本整体消失
- Broadcom 元数据文件数异常收缩（detail 页抓空 / 大面积抓取失败）

被 ``.github/workflows/data-update.yml`` 调用。它的存在意义是：抓取抖动
（Portal 少返一页、archive.org metadata 不完整）不能让线上数据退化。宁可
本次不更新，也不能把"少了链接"的结果发布出去。

用法：
    python scripts/check_data_regression.py
    python scripts/check_data_regression.py --metadata
    ALLOW_REGRESSION=1 python scripts/check_data_regression.py   # 破窗，需在 commit 里说明

退出码：
    0 - 数据健康（或已显式破窗）
    1 - 检测到回归
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vmware_lib.health import compare, metadata_regressions, regressions  # noqa: E402
from vmware_lib.logs import get_logger  # noqa: E402

log = get_logger(__name__)

BREAK_GLASS_ENV = "ALLOW_REGRESSION"
BREAK_GLASS_VALUES = {"1", "true", "yes"}


def load_baseline(path: str, base_ref: str = "HEAD") -> dict:
    """取基线版 JSON（默认 HEAD）。文件不存在或读不出来 → 空 dict（视为无基线）"""
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{base_ref}:{path}"],
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        # 首次提交 / 基线里没有这个路径 —— 正常情况
        return {}
    except OSError as e:
        log.warning("load_baseline(%s) 调用 git 失败: %s", path, e)
        return {}
    try:
        return json.loads(raw)
    except ValueError as e:
        log.warning("load_baseline(%s) JSON 解析失败: %s", path, e)
        return {}


def load_current(path: str) -> dict:
    """取工作区当前 JSON。文件不存在 → 空 dict"""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        log.warning("load_current(%s) 失败: %s", path, e)
        return {}


def break_glass_enabled() -> bool:
    return os.environ.get(BREAK_GLASS_ENV, "").strip().lower() in BREAK_GLASS_VALUES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data", default="data/vmware_downloads.json", help="下载清单 JSON 路径"
    )
    parser.add_argument(
        "--metadata",
        action="store_true",
        help="同时检查 data/broadcom_metadata.json 是否异常收缩",
    )
    parser.add_argument(
        "--base-ref", default="HEAD", help="基线 git ref（默认 HEAD）"
    )
    args = parser.parse_args(argv)

    old = load_baseline(args.data, args.base_ref)
    new = load_current(args.data)

    reasons: list[str] = []
    if not old:
        print(f"ℹ️  基线 {args.base_ref}:{args.data} 不存在，跳过回归判定（首次生成）")
    else:
        diff = compare(old, new)
        print(
            f"📊 对比 {args.base_ref} → 工作区："
            f"新增 {len(diff['added'])} 条，丢失 {len(diff['lost'])} 条，"
            f"链接退化 {len(diff['degraded'])} 条"
        )
        for item in diff["added"]:
            print(f"   ➕ {item}")
        reasons += regressions(old, new)

    if args.metadata:
        old_meta_path = "data/broadcom_metadata.json"
        old_meta = load_baseline(old_meta_path, args.base_ref)
        new_meta = load_current(old_meta_path)
        if old_meta:
            reasons += metadata_regressions(old_meta, new_meta)

    if not reasons:
        print("✅ 数据健康检查通过")
        return 0

    print(f"❌ 数据回归：{len(reasons)} 处（已阻断提交）", flush=True)
    for reason in reasons:
        print(f"   - {reason}", flush=True)

    if break_glass_enabled():
        print(
            f"⚠️  {BREAK_GLASS_ENV}=1 已设置，放行。"
            f"请确认这是上游真实下架，并在 commit message 里写明原因。",
            flush=True,
        )
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
