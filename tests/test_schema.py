"""audit v3 · P1-C · schema validator 单元测试"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from vmware_lib.schema import validate_downloads_json  # noqa: E402


def _make_valid_dl():
    return {
        "filename": "VMware-Workstation-Full-17.5.0-22583795.exe",
        "size": "603.03 MB",
        "sha256": "a" * 64,
        "md5": "b" * 32,
        "url": "https://archive.org/download/x/y.exe",
        "source": "broadcom+archive",
    }


def _make_valid_entry():
    return {
        "version": "17.5.0",
        "build": "22583795",
        "downloads": {"windows": _make_valid_dl()},
    }


def _make_valid_data():
    return {
        "collected_at": "2026-07-08T00:00:00Z",
        "workstation_pro": [_make_valid_entry()],
        "fusion_pro": [],
    }


def test_valid_data_passes():
    assert validate_downloads_json(_make_valid_data()) == []


def test_rejects_non_dict_root():
    errs = validate_downloads_json([])
    assert errs and "应为 dict" in errs[0]


def test_missing_top_keys():
    errs = validate_downloads_json({"collected_at": "x"})
    assert any("缺失必需字段" in e for e in errs)


def test_rejects_malformed_sha256():
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"]["windows"]["sha256"] = "abc"  # 长度不对
    errs = validate_downloads_json(data)
    assert any("sha256" in e and "64 位" in e for e in errs)


def test_empty_sha256_allowed():
    """archive.org 未镜像的版本 sha256 可以为空 —— 不算错"""
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"]["windows"]["sha256"] = ""
    assert validate_downloads_json(data) == []


def test_rejects_malformed_size():
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"]["windows"]["size"] = "603 大小"
    errs = validate_downloads_json(data)
    assert any("size" in e for e in errs)


def test_rejects_non_http_url():
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"]["windows"]["url"] = "ftp://example.com/x"
    errs = validate_downloads_json(data)
    assert any("url" in e for e in errs)


def test_source_optional_but_validated_if_present():
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"]["windows"]["source"] = "unknown-source"
    errs = validate_downloads_json(data)
    assert any("source" in e and "未识别" in e for e in errs)


def test_source_missing_is_allowed():
    """archive.org 老版本没 source 字段 —— 不算错"""
    data = _make_valid_data()
    del data["workstation_pro"][0]["downloads"]["windows"]["source"]
    assert validate_downloads_json(data) == []


def test_real_data_passes():
    """回归：真产品 data/vmware_downloads.json 必须过校验"""
    import json
    repo = Path(__file__).parent.parent
    with open(repo / "data" / "vmware_downloads.json") as f:
        data = json.load(f)
    errs = validate_downloads_json(data)
    assert errs == [], f"真数据违反 schema: {errs[:5]}"


def test_broadcom_api_field_rename_would_be_caught():
    """回归场景 · Broadcom API 把 sha256 改名为 SHA-256 → 必须报错"""
    data = _make_valid_data()
    dl = data["workstation_pro"][0]["downloads"]["windows"]
    del dl["sha256"]  # 老字段没了 → 但 sha256 已改为可选，不再必错
    # 但 filename 是必需的 —— 用 filename 缺失作为契约违规样本
    dl2 = _make_valid_dl()
    del dl2["filename"]
    data["fusion_pro"] = [
        {"version": "13.5", "build": "22583795", "downloads": {"mac": dl2}}
    ]
    errs = validate_downloads_json(data)
    assert any("filename" in e or "缺失必需字段" in e for e in errs)


def test_rejects_non_string_md5_types():
    """CodeRabbit/Gemini review · v3: md5 = None/0/False 等非 str 值必须报错"""
    data = _make_valid_data()
    dl = data["workstation_pro"][0]["downloads"]["windows"]
    for bad in (None, 0, False, 123, []):
        dl["md5"] = bad
        errs = validate_downloads_json(data)
        assert any(".md5:" in e and "应为字符串" in e for e in errs), (
            f"未拒绝 md5={bad!r}"
        )


# ============================================================
# audit v4 · P1-B · 补齐 schema.py 未覆盖分支
# ============================================================


def test_rejects_missing_required_dl_keys():
    """L57-60: dl 缺 filename/size/url → 早退返回，不再检查后续字段"""
    data = _make_valid_data()
    del data["workstation_pro"][0]["downloads"]["windows"]["url"]
    errs = validate_downloads_json(data)
    assert any("缺失必需字段" in e and "url" in e for e in errs)


def test_rejects_non_string_filename():
    """L64: filename 是 None/int → 类型错"""
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"]["windows"]["filename"] = None
    errs = validate_downloads_json(data)
    assert any("filename" in e and "应为非空字符串" in e for e in errs)


def test_rejects_filename_with_illegal_chars():
    """L66-67: filename 含 shell 特殊字符 (空格/;/&)"""
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"]["windows"]["filename"] = "bad; rm -rf.exe"
    errs = validate_downloads_json(data)
    assert any("filename" in e and "非法字符" in e for e in errs)


def test_rejects_non_string_sha256():
    """L71-72: sha256 是 None（不是 str）"""
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"]["windows"]["sha256"] = None
    errs = validate_downloads_json(data)
    assert any("sha256" in e and "应为字符串" in e for e in errs)


def test_rejects_non_hex_sha256():
    """L73-76: sha256 长度对但含非 hex 字符 → 潜在数据污染"""
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"]["windows"]["sha256"] = "z" * 64
    errs = validate_downloads_json(data)
    assert any("sha256" in e and ("64 位 hex" in e or "hex" in e) for e in errs)


def test_rejects_non_string_md5():
    """L80-81: md5 非 str → 类型错"""
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"]["windows"]["md5"] = 12345
    errs = validate_downloads_json(data)
    assert any("md5" in e and "应为字符串" in e for e in errs)


def test_rejects_malformed_md5():
    """L82-83: md5 长度不对（非 32 hex）"""
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"]["windows"]["md5"] = "abc"
    errs = validate_downloads_json(data)
    assert any("md5" in e for e in errs)


def test_rejects_non_string_size():
    """L87-88: size 是 int（不是 str，如 Broadcom API 改字段类型）"""
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"]["windows"]["size"] = 274000000
    errs = validate_downloads_json(data)
    assert any("size" in e and "非空字符串" in e for e in errs)


def test_rejects_missing_entry_keys():
    """L112-114: entry 缺 version/build/downloads → 早退"""
    data = _make_valid_data()
    del data["workstation_pro"][0]["build"]
    errs = validate_downloads_json(data)
    assert any("缺失必需字段" in e and "build" in e for e in errs)


def test_rejects_non_string_version():
    """L117-118: version 非 str"""
    data = _make_valid_data()
    data["workstation_pro"][0]["version"] = 175
    errs = validate_downloads_json(data)
    assert any("version" in e for e in errs)


def test_rejects_non_string_build():
    """L121-122: build 非 str"""
    data = _make_valid_data()
    data["workstation_pro"][0]["build"] = 22583795
    errs = validate_downloads_json(data)
    assert any("build" in e for e in errs)


def test_rejects_non_dict_downloads():
    """L125-127: downloads 是 list（Broadcom 改结构）"""
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"] = ["a", "b"]
    errs = validate_downloads_json(data)
    assert any("downloads" in e and "dict" in e for e in errs)


def test_rejects_non_dict_download_entry():
    """L131-134: 单个 platform 下载 entry 是 str（不是 dict）"""
    data = _make_valid_data()
    data["workstation_pro"][0]["downloads"] = {"windows": "not-a-dict"}
    errs = validate_downloads_json(data)
    assert any("windows" in e and "dict" in e for e in errs)


def test_rejects_non_list_products():
    """L157-158: workstation_pro 不是 list（是 dict）"""
    data = _make_valid_data()
    data["workstation_pro"] = {"a": 1}
    errs = validate_downloads_json(data)
    assert any("workstation_pro" in e and "list" in e for e in errs)


def test_rejects_non_dict_entry_in_list():
    """L161-164: workstation_pro list 里的 entry 是 str（不是 dict）"""
    data = _make_valid_data()
    data["workstation_pro"] = ["not-a-dict"]
    errs = validate_downloads_json(data)
    assert any("workstation_pro[0]" in e and "dict" in e for e in errs)
