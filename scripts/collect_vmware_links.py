#!/usr/bin/env python3
"""VMware 下载链接收集器 v3

Broadcom Support Portal 为**权威主数据源**，提供官方 SHA256/MD5/发布日期。
archive.org metadata 提供可下载镜像 URL（Broadcom 直链需登录，无法给公众用）。

数据流：
    1. 读 data/broadcom_metadata.json（由 scripts/fetch_broadcom.py 生成）
    2. 拉 archive.org metadata（或本地 --dry-run）
    3. 按 filename 融合 → grouped 结构（与旧 renderer 兼容）
    4. 渲染 JSON / checksums.txt / README.md

用法：
    python scripts/collect_vmware_links.py
    python scripts/collect_vmware_links.py --dry-run <archive_metadata.json>
    python scripts/collect_vmware_links.py --broadcom-metadata data/xxx.json
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vmware_lib.broadcom import build_download_entries, load_broadcom_metadata
from vmware_lib.collector import (
    build_archive_filename_index,
    fetch_metadata,
    merge_broadcom_with_archive,
)
from vmware_lib.renderer import render_checksums, render_readme
from vmware_lib.schema import validate_downloads_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        metavar="METADATA_JSON",
        help="使用本地 archive.org metadata JSON，不发起网络请求",
    )
    parser.add_argument(
        "--broadcom-metadata",
        default=None,
        help="Broadcom 元数据 JSON 路径（默认 data/broadcom_metadata.json）",
    )
    parser.add_argument("--output-dir", default=None, help="输出目录（默认为仓库根）")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    output_dir = Path(args.output_dir) if args.output_dir else repo_root
    data_dir = output_dir / "data"
    broadcom_path = Path(
        args.broadcom_metadata or (data_dir / "broadcom_metadata.json")
    )

    print("=" * 60)
    print("VMware 下载链接收集器 v3")
    print("  主数据源: Broadcom Support Portal (官方 SHA256/MD5)")
    print("  辅助源:   archive.org (可下载镜像 URL)")
    print("=" * 60)

    # 1. 加载 Broadcom 官方元数据
    print(f"\n[1/4] 加载 Broadcom 元数据: {broadcom_path.name}")
    if not broadcom_path.exists():
        print(f"  ❌ 未找到 {broadcom_path}")
        print("  请先运行 scripts/fetch_broadcom.py 生成元数据。")
        return 2
    versions = load_broadcom_metadata(broadcom_path)
    broadcom_entries = build_download_entries(versions, skip_incomplete=True)
    ws_bc = len(broadcom_entries.get("workstation", []))
    fu_bc = len(broadcom_entries.get("fusion", []))
    print(f"  ✓ Workstation {ws_bc} 条, Fusion {fu_bc} 条（跳过无 SHA256 条目）")

    # 2. 拉 archive.org metadata
    print("\n[2/4] 加载 archive.org 镜像索引")
    if args.dry_run:
        print(f"  [dry-run] 从本地读取: {args.dry_run}")
        with open(args.dry_run, encoding="utf-8") as f:
            archive_metadata = json.load(f)
    else:
        print("  拉取网络 metadata...")
        try:
            archive_metadata = fetch_metadata()
        except (
            OSError,
            ValueError,
            RuntimeError,
            json.JSONDecodeError,
            http.client.HTTPException,
        ) as e:
            # 覆盖：urlopen OSError、JSON 解析、archive API 结构漂移、
            # http.client 家族异常（IncompleteRead / BadStatusLine / RemoteDisconnected）
            # audit v3 CodeRabbit review: 补 http.client.HTTPException 兜底
            print(f"  ❌ 拉取 archive.org metadata 失败: {type(e).__name__}: {e}")
            print("     可尝试：--dry-run <本地 metadata.json> 使用离线缓存")
            return 1
    archive_index = build_archive_filename_index(archive_metadata)
    print(f"  ✓ archive.org 索引: {len(archive_index)} 个文件")

    # 3. 融合
    print("\n[3/4] 融合两源")
    merged = merge_broadcom_with_archive(broadcom_entries, archive_index)
    ws_count = len(merged.get("workstation", []))
    fusion_count = len(merged.get("fusion", []))

    # 统计融合情况
    stats = {"broadcom+archive": 0, "broadcom-only": 0, "md5_mismatch": 0}
    for _prod, items in merged.items():
        for item in items:
            for _plat, dl in item["downloads"].items():
                stats[dl["source"]] = stats.get(dl["source"], 0) + 1
                if dl.get("md5_mismatch"):
                    stats["md5_mismatch"] += 1

    print(f"  ✓ Workstation {ws_count} 版本, Fusion {fusion_count} 版本")
    print(f"  ✓ 双源匹配:      {stats['broadcom+archive']}")
    print(f"  ⚠️  仅 Broadcom:  {stats['broadcom-only']}  (archive.org 未镜像)")
    if stats["md5_mismatch"]:
        print(f"  🚨 MD5 不匹配:   {stats['md5_mismatch']}  (可能投毒！)")

    # 4. 构造 JSON + 写文件
    result = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "primary": {
                "broadcom": "https://support.broadcom.com/group/ecx/productdownloads",
                "note": "Official SHA256/MD5/release dates from Broadcom Support Portal",
            },
            "mirror": {
                "archive_org": "https://archive.org/details/vmwareworkstationarchive",
                "note": "Free downloadable copies (may lag behind Broadcom by days-weeks)",
            },
        },
        "stats": stats,
        "workstation_pro": merged.get("workstation", []),
        "fusion_pro": merged.get("fusion", []),
    }

    # 4.5 追加 archive.org 独有的历史老版本（补齐到 TOP_N 版）
    print("\n[3.5/4] 追加 archive.org 历史版本（Broadcom Portal 已下架）")
    try:
        from vmware_lib.legacy_merger import fetch_and_merge as legacy_fetch_and_merge

        # 默认全量（archive.org 全部历史）；LEGACY_TOP_N 可限制上限
        top_n_env = os.environ.get("LEGACY_TOP_N", "").strip()
        if top_n_env:
            try:
                top_n = int(top_n_env)
            except ValueError:
                print(
                    f"⚠️  LEGACY_TOP_N={top_n_env!r} 不是合法整数，回退到全量模式",
                    flush=True,
                )
                top_n = None
        else:
            top_n = None
        before_ws = len(result["workstation_pro"])
        before_fu = len(result["fusion_pro"])

        # 复用已加载的 archive_metadata（不发起第二次网络请求）
        result = legacy_fetch_and_merge(
            result, top_n=top_n, archive_meta=archive_metadata
        )
        after_ws = len(result["workstation_pro"])
        after_fu = len(result["fusion_pro"])
        print(
            f"  ✓ Workstation: +{after_ws - before_ws} 历史版 (共 {after_ws}), "
            f"Fusion: +{after_fu - before_fu} 历史版 (共 {after_fu})"
        )
    except (
        ImportError,
        OSError,
        ValueError,
        RuntimeError,
        AttributeError,
        TypeError,
        KeyError,
    ) as e:
        # ImportError: legacy_merger 模块加载失败（不影响主输出）
        # OSError: 网络问题
        # ValueError / RuntimeError: legacy 数据解析异常
        # AttributeError / TypeError / KeyError: audit v3 CodeRabbit review：
        #   fetch_and_merge 对 archive_meta/files/name 结构漂移不做防御性检查，
        #   任何结构漂移都软失败，而不是崩掉整个脚本
        print(f"  ⚠️  跳过历史版本追加: {type(e).__name__}: {e}")

    ws_count = len(result["workstation_pro"])
    fusion_count = len(result["fusion_pro"])

    # audit v3 · P1-C · schema fail-fast：产品输出前做契约校验，
    # 防止 Broadcom API 静默改字段/字段类型导致下游 checksums.txt 也被牵连坏掉
    print("\n[4/4] Schema 校验 + 写文件")
    schema_errs = validate_downloads_json(result)
    if schema_errs:
        print(f"  ❌ Schema 校验失败：{len(schema_errs)} 处违规", flush=True)
        for err in schema_errs[:10]:
            print(f"     - {err}", flush=True)
        if len(schema_errs) > 10:
            print(f"     ... 另有 {len(schema_errs) - 10} 处", flush=True)
        return 2  # 非 0 阻止写坏数据
    print("  ✓ Schema 校验通过")

    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ 写到 {output_dir}")

    json_path = data_dir / "vmware_downloads.json"
    json_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  ✓ {json_path.relative_to(output_dir)}")

    checksums_path = data_dir / "checksums.txt"
    checksums_path.write_text(render_checksums(result), encoding="utf-8")
    print(f"  ✓ {checksums_path.relative_to(output_dir)}")

    readme_path = output_dir / "README.md"
    readme_path.write_text(render_readme(result), encoding="utf-8")
    print(f"  ✓ {readme_path.relative_to(output_dir)}")

    # 汇总
    print()
    print("完成:")
    print(f"  Workstation Pro: {ws_count} 版本")
    print(f"  Fusion Pro:      {fusion_count} 版本")
    if result["workstation_pro"]:
        print(f"  最新 Workstation: {result['workstation_pro'][0]['version']}")
    if result["fusion_pro"]:
        print(f"  最新 Fusion:      {result['fusion_pro'][0]['version']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
