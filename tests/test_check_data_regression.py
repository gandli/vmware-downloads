"""测试 scripts/check_data_regression.py —— 提交前的数据回归闸门

用临时 git 仓库跑真实 `git show HEAD:<path>` 对比，验证三种真实场景：
- 数据没变 → 放行
- 自动抓取抖动丢了下载条目 → 阻断（本次不发布）
- 破窗变量 ALLOW_REGRESSION=1 → 放行
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import check_data_regression as guard  # noqa: E402

DATA_PATH = "data/vmware_downloads.json"
META_PATH = "data/broadcom_metadata.json"


def git(*args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        check=True,
        capture_output=True,
    )


def write_json(root: Path, rel: str, payload: dict) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def downloads_doc(*, with_windows: bool = True, windows_url: str = "https://a/x") -> dict:
    downloads = {}
    if with_windows:
        downloads["windows"] = {"url": windows_url, "sha256": "abc"}
    downloads["linux"] = {"url": "", "sha256": "def"}
    return {"workstation_pro": [{"version": "26H1u1", "downloads": downloads}],
            "fusion_pro": []}


@pytest.fixture()
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    git("init", "-q")
    write_json(tmp_path, DATA_PATH, downloads_doc())
    write_json(
        tmp_path,
        META_PATH,
        {"entries": [{"product": "workstation", "release": "26H1u1",
                      "displayGroup": "WS", "files": [{"filename": "a.exe"}]}]},
    )
    git("add", "-A")
    git("commit", "-q", "-m", "baseline")
    monkeypatch.delenv(guard.BREAK_GLASS_ENV, raising=False)
    return tmp_path


def test_no_baseline_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    monkeypatch.chdir(tmp_path)
    git("init", "-q")  # 空仓库，没有任何提交
    write_json(tmp_path, DATA_PATH, downloads_doc())
    assert guard.main([]) == 0
    assert "跳过回归判定" in capsys.readouterr().out


def test_unchanged_data_passes(repo: Path, capsys):
    assert guard.main([]) == 0
    assert "数据健康检查通过" in capsys.readouterr().out


def test_lost_download_entry_blocks(repo: Path, capsys):
    """真实事故复现：windows 条目消失 → 阻断提交"""
    write_json(repo, DATA_PATH, downloads_doc(with_windows=False))
    assert guard.main([]) == 1
    out = capsys.readouterr().out
    assert "数据回归" in out
    assert "workstation/26H1u1/windows" in out


def test_degraded_url_blocks(repo: Path):
    write_json(repo, DATA_PATH, downloads_doc(windows_url=""))
    assert guard.main([]) == 1


def test_break_glass_allows(repo: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    write_json(repo, DATA_PATH, downloads_doc(with_windows=False))
    monkeypatch.setenv(guard.BREAK_GLASS_ENV, "1")
    assert guard.main([]) == 0
    assert "放行" in capsys.readouterr().out


def test_metadata_shrink_blocks(repo: Path):
    write_json(repo, DATA_PATH, downloads_doc())  # 数据本身不变
    write_json(
        repo,
        META_PATH,
        {"entries": [{"product": "workstation", "release": "26H1u1",
                      "displayGroup": "WS", "files": []}]},
    )
    assert guard.main(["--metadata"]) == 1


def test_metadata_flag_off_ignores_metadata(repo: Path):
    write_json(
        repo,
        META_PATH,
        {"entries": [{"product": "workstation", "release": "26H1u1",
                      "displayGroup": "WS", "files": []}]},
    )
    assert guard.main([]) == 0


def test_load_helpers_tolerate_garbage(repo: Path):
    # 基线 ref 不存在 / 工作区文件缺失 / JSON 坏掉 都返回 {}
    assert guard.load_baseline(DATA_PATH, base_ref="no-such-ref") == {}
    assert guard.load_current("data/missing.json") == {}
    bad = repo / "data" / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert guard.load_current("data/bad.json") == {}


def test_break_glass_values():
    import os

    for value, expected in [("1", True), ("TRUE", True), ("yes", True),
                            ("0", False), ("", False)]:
        os.environ[guard.BREAK_GLASS_ENV] = value
        try:
            assert guard.break_glass_enabled() is expected
        finally:
            del os.environ[guard.BREAK_GLASS_ENV]
