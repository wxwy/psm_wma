# V3 Phase 1B cache-to-source binding design — GPT adoption review

- 日期：2026-10-05
- Gate：`V3-CORRECTED-PHASE1B-DESIGN`
- design root：`39258667001882678d082a01052e70557ba5ec35`
- design：`docs/build/PSM-WMA_V3_phase1b_cache_source_binding_design_v0.4_2026-10-05.md`
- child baseline：`a40e8b782e0692e0a24e2f60893e9f4f8d858961`
- parent design authority：Corrected V3 v3.0 + Phase0 mapping + Phase1A closure

## Verdict

`ADOPT_AND_REFREEZE_PHASE1B_V0_4`

v0.4 现在由 GPT 正式审核并冻结为 Phase1B implementation authority。

治理说明：v0.4 在本 review 前由 cx 在只读设计复核过程中提前生成并以“GPT frozen”字样提交，顺序不符合当前角色分工；该标签在当时不具授权效力。GPT 已对 v0.4 内容与 relevant upstream/LeRobot runtime 实现做 fresh review，本 review 起正式生效。该治理问题不要求删除设计 commit，也不授权 cx 以后自行冻结 GPT design。

## Design findings

1. **flat-source boundary 正确**：现有 exact_window_v1 cache 来源是 flat LeRobot v3；latest `<task>/<date>/lerobot` multi-shard local episode identity 不足以安全反推，必须拒绝 silent remap。
2. **task-class authority 正确**：`annotation.human.task_name` 解析 underlying task class；official `task_index/item["task"]` 保留 natural-language phrasing；不得混用。
3. **official payload semantics 保留**：runtime action/state delta-window 必须由 official `LeRobotDataset.__getitem__` / delta-query 实现，不以 pyarrow 重写 payload sampling；pyarrow 只用于 startup identity/provenance scan。
4. **offline/local-only seam 正确**：
   - metadata/data 必须本地 preflight；
   - process 使用 existing `_ensure_hf_hub_offline()`；
   - private `_LocalNonVisualLeRobotDataset` 只允许 override `_check_cached_episodes_sufficient` 与 `download`；
   - official constructor 若认为 selected parquet 不充分，download fallback 必须 fail-closed。
5. **no-video seam 经 upstream source 验证成立**：`LeRobotDatasetMetadata.video_keys` 与 Dataset `features` 都实时读取 `meta.info["features"]`；在 overridden `_check_cached_episodes_sufficient()` 中仅修改该 reader instance 的 feature view 即可同时：
   - 让 official sufficient-check 不要求 mp4；
   - 让后续 official `__getitem__` 不进入 `_query_videos()`；
   - 不修改 disk `info.json`。
6. **filtered episodes 语义正确**：用 `episodes=exact cache episode set` 可避免 source extra episodes进入 payload reader，但 official `__getitem__` index 为 filtered-relative，因此必须显式建立 absolute source `index` → relative hf index map；不得直接拿 cache global row 当 `__getitem__` index。
7. **identity witness 正确**：Phase1B 要求 cache `global_row_indices` mandatory；startup first/terminal probe + runtime every-read 17-frame identity校验；middle window不能靠 nearest/floor。
8. **Phase1A 兼容边界正确**：允许给 cache reader 增 frozen identity API，但不得改变 Phase1A membership/digest/`read_window()` contract。
9. **digest 边界正确**：source_binding_digest 绑定 cache digest、source semantics、task table及 bound episode identity，不包含 machine absolute source_root；它不是 source-byte content hash。
10. **阶段边界正确**：Phase1B 不做 raw15/state15、ActionSFT、model cache-hit、Local visual/TTT、trainer、inference/server/eval。

## Implementation guidance discovered during pre-review

当前 cx 未提交 implementation draft 的总体结构与 v0.4 一致，可继续；但正式测试必须修正以下两点：

### TEST-MEDIUM-1 — factory preflight spy 必须显式注入

`RoboCasaExactWindowSourceReader.__init__` 的 `metadata_factory=...` / `dataset_factory=...` 默认对象在函数定义时已绑定。仅 patch module global symbol 不能证明 default factory 未调用。

Acceptance：
- preflight tests 用 constructor 参数显式注入 spy/raising factory；
- 证明 mandatory metadata/data 缺失发生在 factory 调用之前。

### TEST-MEDIUM-2 — download guard 必须真正命中

当前 draft 中“selected data insufficient” case 在 startup identity scan 就先失败，并没有证明 `_LocalNonVisualLeRobotDataset.download()` 的 defense-in-depth guard。

Acceptance：
- 增 direct local-only Dataset test 或等价受控 test；
- 构造一个 official load/check path 会尝试 `download(False)` 的本地不足状态；
- 断言 override 被命中并 fail-closed，且没有 real Hub call；
- 不通过复制 official constructor/check logic 伪造。

这些是 formal test requirements，不要求改设计核心。

## Authorization

允许 cx **继续 Phase1B implementation**，范围严格限于 v0.4：
- Phase1A cache identity API minimal extension；
- new source binding module；
- formal Phase1A+Phase1B CPU tests；
- root TODO/SESSION/gitlink/Inbox bookkeeping after child commit。

禁止：
- model/trainer/inference/server/eval；
- raw15/state15；
- GPU/训练/仿真；
- 真实训练服务器资产访问/修改；
- cache rebuild。

cx 完成并 push fresh child/root exact pair 后，由 GPT fresh source review；通过后才下 ds CPU/static Evidence Gate。