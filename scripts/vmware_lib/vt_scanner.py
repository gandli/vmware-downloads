"""VirusTotal 扫描结果查询器

用 SHA256 哈希查 VirusTotal v3 API，获取该文件的历史扫描结果。
不下载/上传任何安装包，只查已有的哈希 → Broadcom EULA 合规 + VT 免费额度足够。

API 文档：https://docs.virustotal.com/reference/file-info
免费限流：500 req/day, 4 req/min（我们 27 个哈希 × 2 平台 ≈ 54 次，2 分钟够）

设计原则：
- 无 key 时优雅降级（不 crash，跳过 VT 步骤）
- 命中 404（VT 无记录）时返回 status="unknown" 而非报错
- 每次请求间 sleep 16s 保守遵守 4 req/min 限制
- 失败重试：3 次，指数退避
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

VT_API_URL = "https://www.virustotal.com/api/v3/files/{sha256}"
VT_GUI_URL = "https://www.virustotal.com/gui/file/{sha256}"
RATE_LIMIT_SLEEP = 16  # 4 req/min → 15s + 1s buffer
MAX_RETRIES = 3


@dataclass
class ScanResult:
    """单个哈希的扫描结果摘要"""

    sha256: str
    status: str  # "clean" | "malicious" | "suspicious" | "unknown" | "error"
    malicious: int = 0
    suspicious: int = 0
    harmless: int = 0
    undetected: int = 0
    last_analysis_date: str = ""
    vt_url: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "malicious": self.malicious,
            "suspicious": self.suspicious,
            "harmless": self.harmless,
            "undetected": self.undetected,
            "last_analysis_date": self.last_analysis_date,
            "vt_url": self.vt_url,
            "error": self.error,
        }


def classify_status(stats: dict) -> str:
    """根据 last_analysis_stats 分类为 clean/suspicious/malicious"""
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    if malicious > 0:
        return "malicious"
    if suspicious > 0:
        return "suspicious"
    return "clean"


def parse_vt_response(sha256: str, response_json: dict) -> ScanResult:
    """将 VT v3 API JSON 响应解析为 ScanResult

    结构（简化）：
      {
        "data": {
          "attributes": {
            "last_analysis_stats": {"malicious": 0, "suspicious": 0, "harmless": 70, "undetected": 2, "timeout": 0},
            "last_analysis_date": 1704000000  (epoch seconds)
          }
        }
      }
    """
    attrs = response_json.get("data", {}).get("attributes", {})
    stats = attrs.get("last_analysis_stats", {})
    ts = attrs.get("last_analysis_date", 0)

    last_analysis_iso = ""
    if ts:
        from datetime import datetime, timezone
        last_analysis_iso = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    return ScanResult(
        sha256=sha256,
        status=classify_status(stats),
        malicious=stats.get("malicious", 0),
        suspicious=stats.get("suspicious", 0),
        harmless=stats.get("harmless", 0),
        undetected=stats.get("undetected", 0),
        last_analysis_date=last_analysis_iso,
        vt_url=VT_GUI_URL.format(sha256=sha256),
    )


def query_hash(sha256: str, api_key: str, timeout: int = 30) -> ScanResult:
    """查询单个 SHA256 的 VT 扫描结果

    返回：
      - status="clean" 无威胁
      - status="suspicious" 疑似
      - status="malicious" 恶意
      - status="unknown" VT 无记录（新版本刚发）
      - status="error" API 错误（网络/限流/key 错等）
    """
    if not sha256 or len(sha256) != 64:
        return ScanResult(sha256=sha256, status="error", error="invalid sha256 length")

    url = VT_API_URL.format(sha256=sha256)
    req = urllib.request.Request(url, headers={"x-apikey": api_key})

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return parse_vt_response(sha256, data)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # VT 从未见过这个哈希（新版本）
                return ScanResult(
                    sha256=sha256,
                    status="unknown",
                    vt_url=VT_GUI_URL.format(sha256=sha256),
                    error="VT 无记录",
                )
            if e.code == 429:
                # 限流，指数退避
                wait = RATE_LIMIT_SLEEP * (2 ** (attempt - 1))
                logger.warning(f"VT 429 限流，等待 {wait}s 后重试（{attempt}/{MAX_RETRIES}）")
                time.sleep(wait)
                continue
            return ScanResult(sha256=sha256, status="error", error=f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            if attempt == MAX_RETRIES:
                return ScanResult(sha256=sha256, status="error", error=f"URLError: {e.reason}")
            time.sleep(RATE_LIMIT_SLEEP)
        except (json.JSONDecodeError, KeyError) as e:
            return ScanResult(sha256=sha256, status="error", error=f"parse error: {e}")

    return ScanResult(sha256=sha256, status="error", error="max retries exceeded")


def scan_all(sha256_list: list[str], api_key: str, sleep_between: int = RATE_LIMIT_SLEEP) -> dict[str, ScanResult]:
    """批量查询，遵守 VT 限流"""
    results = {}
    total = len(sha256_list)
    for idx, sha in enumerate(sha256_list, 1):
        logger.info(f"[{idx}/{total}] VT 查询 {sha[:16]}...")
        results[sha] = query_hash(sha, api_key)
        if idx < total:
            time.sleep(sleep_between)
    return results


def merge_into_downloads(
    downloads_data: dict, scan_results: dict[str, ScanResult]
) -> dict:
    """把 VT 扫描结果合并到 vmware_downloads.json 结构里

    对每个 workstation_pro / fusion_pro 条目的 downloads.{windows,linux,macos}.sha256
    查 scan_results，把结果注入到该 download 对象的 virustotal 字段。
    """
    for key in ("workstation_pro", "fusion_pro"):
        for entry in downloads_data.get(key, []):
            for platform, dl in entry.get("downloads", {}).items():
                if not isinstance(dl, dict):
                    continue
                sha = dl.get("sha256", "").lower()
                if sha and sha in scan_results:
                    dl["virustotal"] = scan_results[sha].to_dict()
    return downloads_data
