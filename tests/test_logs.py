"""audit v3 · P1-B · logs 模块单元测试"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vmware_lib.logs import get_logger  # noqa: E402


def test_get_logger_returns_vmware_prefixed_logger():
    log = get_logger("scripts.detect_data_changes")
    # basename 提取（vmware.detect_data_changes）
    assert log.name == "vmware.detect_data_changes"


def test_get_logger_writes_warning_to_stderr(caplog):
    log = get_logger("test_logs_a")
    with caplog.at_level(logging.WARNING, logger="vmware.test_logs_a"):
        log.warning("boom %s", 42)
    assert any("boom 42" in r.getMessage() for r in caplog.records)


def test_get_logger_is_idempotent():
    """多次调用 get_logger 只装一个 handler，避免重复输出"""
    log_a = get_logger("test_logs_idem")
    log_b = get_logger("test_logs_idem")
    assert log_a is log_b
    # root logger vmware 只有 1 个 handler
    root = logging.getLogger("vmware")
    assert len(root.handlers) == 1


def test_logger_dunder_main_name_handling():
    """__main__ 作为 name 时也要归到 vmware.__main__"""
    log = get_logger("__main__")
    assert log.name == "vmware.__main__"
