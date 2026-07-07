"""统一 logging 模块 (audit v3 · P1-B)

设计目标：
- **零外部依赖**（stdlib logging + sys.stderr）
- 支持环境变量 `LOG_LEVEL=DEBUG/INFO/WARNING/ERROR`
- 时间戳 + 模块名 + 级别，方便 CI 排障
- 全部写到 stderr，避免污染 stdout（PR body / checksums.txt 都用 stdout）

使用：
    from vmware_lib.logs import get_logger
    log = get_logger(__name__)
    log.info("拉取 archive.org metadata")
    log.error("失败: %s", err_msg)

进度提示保留 `print("[1/4] ...")` — 属于 CLI UX 而非 log。
错误 / warning / debug 一律走 logger。
"""

from __future__ import annotations

import logging
import os
import sys

_LOG_FORMAT = "[%(asctime)s] %(levelname)-7s %(name)s: %(message)s"
_LOG_DATEFMT = "%H:%M:%S"

_configured = False


def _configure_root() -> None:
    """幂等配置 root logger — 多次调用只装一个 handler"""
    global _configured
    if _configured:
        return
    root = logging.getLogger("vmware")
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATEFMT))
    root.addHandler(handler)
    # audit v3 CodeRabbit/Gemini review: LOG_LEVEL 非法值不能让脚本崩，回退 INFO
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    try:
        root.setLevel(log_level)
    except (ValueError, TypeError):
        root.setLevel(logging.INFO)
    # propagate=True 保留：pytest caplog 抓 log 依赖 root logger 传播。
    # 生产环境 root logger 默认无 handler（logging.basicConfig 未调），不会重复输出。
    root.propagate = True
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """获取带 vmware. 前缀的 logger

    传入的 name 通常是 __name__，会自动挂到 vmware.<module> 命名空间下，
    统一由 vmware root logger 控制级别与 handler。
    """
    _configure_root()
    # 把 __main__ / scripts.xxx / vmware_lib.xxx 统一挂到 vmware.<basename>
    short = name.rsplit(".", 1)[-1] if name else "root"
    return logging.getLogger(f"vmware.{short}")
