## 动机 / Why

<!-- 这个 PR 解决什么问题？关联 Issue / Discussion / 上下文 -->

## 改动 / What

<!-- 关键改动列表 -->
- 
- 
- 

## 影响面 / Blast radius

<!-- 打勾所有适用项 -->
- [ ] 抓取逻辑（fetch_broadcom / probe_archive_org）
- [ ] 融合逻辑（collector / legacy_merger）
- [ ] 渲染逻辑（renderer / README.md）
- [ ] CI / GitHub Actions
- [ ] 数据文件（data/*.json、data/checksums.txt）
- [ ] 依赖 / 构建（pyproject.toml、requirements）
- [ ] 文档 / 治理（README、CONTRIBUTING、SECURITY）
- [ ] 仅仅是清理 / 重构（无行为变化）

## 验证 / Verification

<!-- 附命令输出或截图 -->
- [ ] `pytest -q` 全绿
- [ ] `ruff check scripts/ tests/` 无错
- [ ] 涉及 README 改动时已本地重新渲染
- [ ] 若为 workflow 改动，用 `act` 本地跑通

## 供应链检查（若涉及 data/ 改动）

- [ ] SHA256 来自 Broadcom Support Portal 官方元数据
- [ ] `data/checksums.txt` 与 `data/vmware_downloads.json` 一致
- [ ] 无 `md5_mismatch` 告警

## 其他备注 / Notes
