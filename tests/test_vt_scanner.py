"""测试 vt_scanner - VirusTotal 扫描结果解析与合并

不做真实网络调用，全部用 mock 响应验证。
"""

from __future__ import annotations

import json
import sys
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vmware_lib.vt_scanner import (
    ScanResult,
    classify_status,
    merge_into_downloads,
    parse_vt_response,
    query_hash,
)


# ============================================================
# classify_status - 状态分类逻辑
# ============================================================

def test_classify_clean_when_zero_malicious_and_suspicious():
    """malicious=0 suspicious=0 → clean"""
    assert classify_status({"malicious": 0, "suspicious": 0, "harmless": 70}) == "clean"


def test_classify_malicious_when_any_malicious():
    """malicious>0 → malicious（最高优先级）"""
    assert classify_status({"malicious": 3, "suspicious": 0}) == "malicious"
    # 即使有 suspicious 也归为 malicious
    assert classify_status({"malicious": 1, "suspicious": 5}) == "malicious"


def test_classify_suspicious_when_only_suspicious():
    """malicious=0 suspicious>0 → suspicious"""
    assert classify_status({"malicious": 0, "suspicious": 2}) == "suspicious"


def test_classify_clean_on_empty_stats():
    """空 stats（未扫描）→ clean（保守认为无威胁）"""
    assert classify_status({}) == "clean"


# ============================================================
# parse_vt_response - VT API 响应解析
# ============================================================

def test_parse_typical_clean_response():
    """典型干净响应 → status=clean + 完整字段"""
    resp = {
        "data": {
            "attributes": {
                "last_analysis_stats": {
                    "malicious": 0,
                    "suspicious": 0,
                    "harmless": 68,
                    "undetected": 2,
                    "timeout": 0,
                },
                "last_analysis_date": 1704067200,  # 2024-01-01 00:00 UTC
            }
        }
    }
    r = parse_vt_response("a" * 64, resp)
    assert r.status == "clean"
    assert r.malicious == 0
    assert r.harmless == 68
    assert r.undetected == 2
    assert r.last_analysis_date == "2024-01-01T00:00:00+00:00"
    assert r.vt_url == "https://www.virustotal.com/gui/file/" + "a" * 64


def test_parse_malicious_response():
    """恶意响应 → status=malicious"""
    resp = {
        "data": {
            "attributes": {
                "last_analysis_stats": {"malicious": 5, "suspicious": 2, "harmless": 60, "undetected": 3},
                "last_analysis_date": 1704067200,
            }
        }
    }
    r = parse_vt_response("b" * 64, resp)
    assert r.status == "malicious"
    assert r.malicious == 5
    assert r.suspicious == 2


def test_parse_missing_stats_no_crash():
    """attributes 缺 stats → 全 0，status=clean，不 crash"""
    resp = {"data": {"attributes": {}}}
    r = parse_vt_response("c" * 64, resp)
    assert r.malicious == 0
    assert r.status == "clean"
    assert r.last_analysis_date == ""


def test_parse_missing_data_key_no_crash():
    """连 data 都没有 → 优雅返回，不 crash"""
    r = parse_vt_response("d" * 64, {})
    assert r.status == "clean"  # 空 stats
    assert r.sha256 == "d" * 64


# ============================================================
# query_hash - HTTP 交互（用 mock）
# ============================================================

def _make_mock_response(status_code=200, body_dict=None):
    """构造一个 mock 的 urlopen 返回值（context manager）"""
    mock_resp = MagicMock()
    body = json.dumps(body_dict or {}).encode("utf-8")
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda self: self
    mock_resp.__exit__ = lambda *args: None
    return mock_resp


def test_query_hash_invalid_length_returns_error():
    """SHA256 长度不对 → error 状态，不发请求"""
    r = query_hash("shorthash", "any-key")
    assert r.status == "error"
    assert "length" in r.error


def test_query_hash_success():
    """200 OK + 干净结果 → ScanResult status=clean"""
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value = _make_mock_response(
            200,
            {
                "data": {
                    "attributes": {
                        "last_analysis_stats": {"malicious": 0, "harmless": 70},
                        "last_analysis_date": 1704067200,
                    }
                }
            },
        )
        r = query_hash("a" * 64, "test-key")
        assert r.status == "clean"
        assert r.harmless == 70


def test_query_hash_404_returns_unknown():
    """VT 无记录（404）→ status=unknown，不 crash"""
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.side_effect = urllib.error.HTTPError(
            url="test", code=404, msg="Not Found", hdrs=None, fp=None
        )
        r = query_hash("f" * 64, "test-key")
        assert r.status == "unknown"
        assert "VT 无记录" in r.error
        assert r.vt_url  # 仍然给个 GUI 链接方便查看


def test_query_hash_500_returns_error():
    """500 服务错误 → status=error"""
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.side_effect = urllib.error.HTTPError(
            url="test", code=500, msg="Server Error", hdrs=None, fp=None
        )
        r = query_hash("a" * 64, "test-key")
        assert r.status == "error"
        assert "500" in r.error


# ============================================================
# merge_into_downloads - 数据合并
# ============================================================

def test_merge_injects_vt_field_into_downloads():
    """扫描结果应合并到 downloads.{platform}.virustotal 字段"""
    downloads_data = {
        "workstation_pro": [
            {
                "version": "26H1",
                "build": "25388281",
                "downloads": {
                    "windows": {"sha256": "aaaa" + "a" * 60, "url": "https://..."},
                    "linux": {"sha256": "bbbb" + "b" * 60, "url": "https://..."},
                },
            }
        ]
    }
    scan_results = {
        "aaaa" + "a" * 60: ScanResult(sha256="aaaa" + "a" * 60, status="clean", harmless=70),
        "bbbb" + "b" * 60: ScanResult(sha256="bbbb" + "b" * 60, status="clean", harmless=68),
    }
    merged = merge_into_downloads(downloads_data, scan_results)
    win_vt = merged["workstation_pro"][0]["downloads"]["windows"]["virustotal"]
    assert win_vt["status"] == "clean"
    assert win_vt["harmless"] == 70


def test_merge_skips_missing_sha256():
    """downloads 里没有 sha256 → 不 crash，跳过"""
    downloads_data = {
        "workstation_pro": [
            {"downloads": {"windows": {"url": "https://..."}}}  # 无 sha256
        ]
    }
    merged = merge_into_downloads(downloads_data, {})
    assert "virustotal" not in merged["workstation_pro"][0]["downloads"]["windows"]


def test_merge_handles_case_insensitive_sha256():
    """sha256 大小写不影响匹配（归一化 lower）"""
    downloads_data = {
        "workstation_pro": [
            {"downloads": {"windows": {"sha256": "AAAA" + "A" * 60}}}
        ]
    }
    scan_results = {
        "aaaa" + "a" * 60: ScanResult(sha256="aaaa" + "a" * 60, status="clean")
    }
    merged = merge_into_downloads(downloads_data, scan_results)
    assert merged["workstation_pro"][0]["downloads"]["windows"]["virustotal"]["status"] == "clean"


def test_merge_supports_fusion_pro():
    """fusion_pro 也应被处理"""
    downloads_data = {
        "fusion_pro": [
            {"downloads": {"macos": {"sha256": "cccc" + "c" * 60}}}
        ]
    }
    scan_results = {
        "cccc" + "c" * 60: ScanResult(sha256="cccc" + "c" * 60, status="clean")
    }
    merged = merge_into_downloads(downloads_data, scan_results)
    assert "virustotal" in merged["fusion_pro"][0]["downloads"]["macos"]


# ============================================================
# ScanResult 序列化
# ============================================================

def test_scan_result_to_dict_serializable():
    """to_dict() 返回可 JSON 序列化的字典"""
    r = ScanResult(sha256="a" * 64, status="clean", harmless=70)
    d = r.to_dict()
    # 应可 json.dumps 无异常
    json.dumps(d)
    assert d["status"] == "clean"
    assert d["harmless"] == 70
