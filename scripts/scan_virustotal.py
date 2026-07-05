#!/usr/bin/env python3
"""VirusTotal 扫描 CLI

从 data/vmware_downloads.json 收集所有 sha256，用 VT API 逐个查询扫描结果，
写入 data/virustotal_scan.json 并合并到 vmware_downloads.json。

用法：
    python scripts/scan_virustotal.py

环境变量：
    VT_API_KEY - VirusTotal API 密钥（必需）
    VT_DRY_RUN - 若设置为 "1"，只打印哈希列表不发请求（调试用）

设计特点：
- 无 API key 时优雅降级：打印警告并 exit 0（不阻断 workflow）
- 尊重 VT 免费限流（4 req/min）：每次请求间 sleep 16s
- 结果落盘 virustotal_scan.json，供 renderer 展示
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vmware_lib.vt_scanner import merge_into_downloads, scan_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


DATA_DIR = Path(__file__).parent.parent / "data"
DOWNLOADS_JSON = DATA_DIR / "vmware_downloads.json"
VT_JSON = DATA_DIR / "virustotal_scan.json"


def collect_all_sha256(data: dict) -> list[str]:
    """从 vmware_downloads.json 抽取所有唯一 SHA256"""
    seen = set()
    result = []
    for key in ("workstation_pro", "fusion_pro"):
        for entry in data.get(key, []):
            for platform, dl in entry.get("downloads", {}).items():
                if isinstance(dl, dict):
                    sha = (dl.get("sha256") or "").strip().lower()
                    if sha and len(sha) == 64 and sha not in seen:
                        seen.add(sha)
                        result.append(sha)
    return result


def main() -> int:
    api_key = os.environ.get("VT_API_KEY", "").strip()
    if not api_key:
        logger.warning("⚠️  VT_API_KEY 未设置，跳过 VirusTotal 扫描")
        logger.info("提示：在 GitHub Secrets 添加 VT_API_KEY 后重跑")
        return 0

    if not DOWNLOADS_JSON.exists():
        logger.error(f"❌ {DOWNLOADS_JSON} 不存在，请先运行 fetch_broadcom.py")
        return 1

    downloads = json.loads(DOWNLOADS_JSON.read_text(encoding="utf-8"))
    all_hashes = collect_all_sha256(downloads)
    logger.info(f"📋 从 vmware_downloads.json 收集到 {len(all_hashes)} 个唯一 SHA256")

    if os.environ.get("VT_DRY_RUN") == "1":
        logger.info("🧪 DRY_RUN 模式，只打印哈希不请求：")
        for i, h in enumerate(all_hashes, 1):
            print(f"  [{i:2d}] {h}")
        return 0

    if not all_hashes:
        logger.warning("没有 SHA256 需要查询，退出")
        return 0

    # 查询
    logger.info(f"🔍 开始 VT 查询（预估 {len(all_hashes) * 16 // 60} 分钟，遵守 4 req/min）")
    results = scan_all(all_hashes, api_key)

    # 统计
    stats = {"clean": 0, "malicious": 0, "suspicious": 0, "unknown": 0, "error": 0}
    for r in results.values():
        stats[r.status] = stats.get(r.status, 0) + 1
    logger.info(
        f"✅ 完成：clean={stats['clean']} malicious={stats['malicious']} "
        f"suspicious={stats['suspicious']} unknown={stats['unknown']} error={stats['error']}"
    )

    # 落盘 virustotal_scan.json
    vt_data = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "total_hashes": len(all_hashes),
        "summary": stats,
        "scans": {sha: r.to_dict() for sha, r in results.items()},
    }
    VT_JSON.write_text(json.dumps(vt_data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"💾 已写入 {VT_JSON}")

    # 合并到 vmware_downloads.json
    merged = merge_into_downloads(downloads, results)
    DOWNLOADS_JSON.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info(f"🔗 已合并 VT 结果到 {DOWNLOADS_JSON}")

    # 恶意样本告警
    if stats["malicious"] > 0 or stats["suspicious"] > 0:
        logger.error(
            f"🚨 发现 {stats['malicious']} 恶意 + {stats['suspicious']} 可疑样本！"
            f"请查看 {VT_JSON.name}"
        )
        return 2  # 非零 exit，workflow 可捕获

    return 0


if __name__ == "__main__":
    sys.exit(main())
