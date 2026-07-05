#!/usr/bin/env python3
"""对已 dump 的 HTML 重新提取（不重跑 Playwright）"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from probe_broadcom_full import parse_detail_table

DUMP = Path("probe_output/full")
files = sorted(DUMP.glob("detail_*.html"))
print(f"处理 {len(files)} 个 dump 文件\n")

# 从 detail_NN_tag.html 恢复 subFamily / release / servicePk
old_json = json.loads((DUMP / "broadcom_official.json").read_text(encoding="utf-8"))
entries = old_json["entries"]

updated = []
total_files, with_sha256, with_md5 = 0, 0, 0

for idx, entry in enumerate(entries, 1):
    # 找对应 HTML
    tag = f"{entry['subFamily']}_{entry['release']}".replace(" ", "_").replace("/", "_")
    tag = re.sub(r"[^A-Za-z0-9_.-]", "", tag)
    matches = list(DUMP.glob(f"detail_{idx:02d}_*.html"))
    if not matches:
        print(f"[{idx:02d}] ⚠️  无 HTML dump")
        entry["files"] = []
        updated.append(entry)
        continue

    html = matches[0].read_text(encoding="utf-8")
    files_data = parse_detail_table(html)
    entry["files"] = files_data
    total_files += len(files_data)

    for f in files_data:
        if f["sha256"]:
            with_sha256 += 1
        if f["md5"]:
            with_md5 += 1
        marker = "✅" if f["sha256"] else "⚠️"
        print(
            f"[{idx:02d}] {marker} {f['filename']} ({f['size']}) build={f['build']} sha256={f['sha256'][:16]}... md5={f['md5'][:12]}..."
        )

    updated.append(entry)

# 写回
result = dict(old_json)
result["entries"] = updated
result["total_files"] = total_files
(DUMP / "broadcom_official.json").write_text(
    json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
)

print(f"\n{'=' * 60}")
print(f"总文件: {total_files}")
print(
    f"SHA256 覆盖: {with_sha256}/{total_files} ({100 * with_sha256 // total_files if total_files else 0}%)"
)
print(
    f"MD5 覆盖:    {with_md5}/{total_files} ({100 * with_md5 // total_files if total_files else 0}%)"
)
