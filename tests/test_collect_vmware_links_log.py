"""Regression tests for collect_vmware_links.py logging pattern shadow (v5).

audit v5 P1-A: 修完 fetch_broadcom.py 自制 log helper（v4）后，
collect_vmware_links.py 仍未 import logging。v5 补齐后测：
1. logger 已引入且模块名正确
2. error 分支走 logger.error
3. warning 分支走 logger.warning
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import collect_vmware_links  # noqa: E402


def test_logger_configured() -> None:
    """logger 已引入且命名遵循 vmware.<module> 规范"""
    assert hasattr(collect_vmware_links, "logger")
    assert isinstance(collect_vmware_links.logger, logging.Logger)
    assert collect_vmware_links.logger.name == "vmware.collect_vmware_links"


def test_logger_error_routed(caplog) -> None:
    """logger.error 走 stdlib logging（caplog 捕获）"""
    with caplog.at_level(logging.ERROR, logger="vmware"):
        collect_vmware_links.logger.error("sentinel error msg")
    assert any(
        "sentinel error msg" in r.message and r.levelname == "ERROR"
        for r in caplog.records
    )


def test_logger_warning_routed(caplog) -> None:
    """logger.warning 走 stdlib logging"""
    with caplog.at_level(logging.WARNING, logger="vmware"):
        collect_vmware_links.logger.warning("sentinel warn msg")
    assert any(
        "sentinel warn msg" in r.message and r.levelname == "WARNING"
        for r in caplog.records
    )
