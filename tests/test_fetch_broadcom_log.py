"""audit v4 · P1-A · fetch_broadcom.log() 双出口回归测试

保护 log() 从自制 print helper 升级到 stdlib logging 后：
- info 级默认 → vmware.fetch_broadcom logger info
- error 级参数 → vmware.fetch_broadcom logger error
- print 出口保留（Playwright 抓取要 stdout 实时刷进度）
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.fixture
def fetch_broadcom_module():
    """import fetch_broadcom（避免 Playwright side-effect）"""
    import fetch_broadcom
    return fetch_broadcom


def test_log_default_info_level(fetch_broadcom_module, caplog, capsys):
    """log(msg) 默认走 info level + print 到 stdout（CI 进度用）"""
    with caplog.at_level(logging.INFO, logger="vmware.fetch_broadcom"):
        fetch_broadcom_module.log("[login] 开始")
    assert "[login] 开始" in caplog.text
    assert "INFO" in caplog.text or any(
        r.levelname == "INFO" for r in caplog.records
    )
    # 双出口：stdout 也要有
    captured = capsys.readouterr()
    assert "[login] 开始" in captured.out


def test_log_error_level_routed(fetch_broadcom_module, caplog, capsys):
    """log(msg, level='error') 走 ERROR level（排障用）"""
    with caplog.at_level(logging.ERROR, logger="vmware.fetch_broadcom"):
        fetch_broadcom_module.log("[1/10] ❌ boom", level="error")
    assert "[1/10] ❌ boom" in caplog.text
    assert any(r.levelname == "ERROR" for r in caplog.records)
    # print 出口也保留
    captured = capsys.readouterr()
    assert "❌ boom" in captured.out


def test_log_uses_vmware_namespace(fetch_broadcom_module, caplog):
    """logger 命名遵循 vmware.<module> 规范"""
    with caplog.at_level(logging.INFO, logger="vmware.fetch_broadcom"):
        fetch_broadcom_module.log("ping")
    assert any(
        r.name == "vmware.fetch_broadcom" for r in caplog.records
    ), f"logger name mismatch, got: {[r.name for r in caplog.records]}"
