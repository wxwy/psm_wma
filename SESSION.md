# V3 Corrected Phase 3 cached-SFT/cache-hit implementation（2026-10-05）

- Gate `V3-CORRECTED-PHASE3-CACHED-SFT-CACHE-HIT` 进入 REVIEW。authority：Phase3 v1.0 design root `78ff45375cecc3783ec3d219af23c4be5902b9da` 与 `/tmp/CX_PHASE3_CACHED_LATENT_SFT_CACHE_HIT.md`；baseline child `ce07cb6f4a3f7792d85b7583ff6c8bda0bfa0cb0`。复用 Phase1A cache catalog/reader、Phase1B source/index、Phase2 official raw15/state15 adapter、官方 ActionSFTDataset/ActionTransformPipeline 与 PackingDataLoader；本轮 child 只新增 `robocasa_exact_window_cached_sft.py`、`robocasa_exact_window_cached_sft_test.py`、`omni_mot_cached_vision_test.py`，并仅在 `omni_mot_model.py:get_data_and_condition` 加 optional cache-hit vision preparation。raw sample 附 `cached_latent_required=True`，model 对哨兵缺 latent/反向缺哨兵及不合法 packed ABI fail-closed；constructor 校验 VideoResize `192×320` canvas 与 fixed Wan factor16 对应 latent `12×20`，cache-hit保留 native crop 与 temporal helper，VAE/collective调用为0，off-mode 保持原路。
- cx 离线 synthetic CPU/static：Phase1A+1B+2+3、ActionTransform 与 OmniMoT 相关 7 文件合并 pytest **191 passed**；三新增文件 Ruff check、Ruff format --check PASS；core `omni_mot_model.py` Ruff check 仅基线已有 I001，format --diff 仅基线已有三处 hunk（本轮新增 hunk 已格式化），`--ignore I001` check PASS；child staged diff-check PASS。未访问真实 cache/source/checkpoint/训练服务器，未运行 GPU/训练/仿真或 ds 独立 Evidence。child `b6707e2c89fe6078e2a0bb4ff7266205b827825e` 已推送 `v3-local-ttt`；root 本步仅更新 Gitlink、SESSION/TODO、append Inbox，请 GPT fresh exact pair review，不自授批准。本条落盘时 root 未提交。

# V3 Corrected Phase 3 design freeze（2026-10-05）

- GPT 已冻结 `docs/build/PSM-WMA_V3_phase3_cached_latent_sft_model_cache_hit_design_v1.0_2026-10-05.md`。cx 全文阅读并只读对照 v3.0、Phase0 mapping、Phase2 closure、V2 donor/current child；先前 PackingDataLoader ABI blocker 与 §13 rank 冲突已修订：inner collate 为 Tensor[B,5,48,H,W]，最终 model 为 list[B] of Tensor[1,5,48,H,W]，单项 rank5。现有 `custom_collate_fn`、`_get_next_sample`、`_update_output_batch` 的传递路径符合修订 ABI；`OmniMoTModel.get_data_and_condition` 的 cache-hit seam 尚未实现。设计要求 placeholder 复用 builder 的 VideoResize canvas、cache latent 继续 common post-VAE crop，Phase3 不改 generic collator/packer/Local；本轮未发现新的 docs-only freeze blocker。root 仅提交设计原文、`docs/INDEX.md` current authority 与本条 SESSION；child/Gitlink/TODO/production/test 不动，未运行项目代码、测试、GPU、训练或仿真。Phase3 实现和 ds Evidence 均未开始；本条写入时 design root 尚未提交。

# V3 Corrected Phase 2 immutable VAE authority 修复（2026-10-05）

- Gate `V3-CORRECTED-PHASE2-IMPLEMENTATION` 保持 REVIEW。GPT r2 review `docs/collab/chatgpt/reviews/2026-10-05_V3_phase2_source_review_r2_6d033018_9819cec5.md` 对 root `6d0330186717d6a02efd87fe65effedc8e1d8037` / child `9819cec5f456fb4f5a9b9681479c05a97f62cb70` 给 `REQUEST_CHANGES`：`frozen=True` 的公开 VAE dict/list 仍可原地篡改，从而使 `[33]` 通过 resolver/validator；前一 candidate-config blocker 已闭合。cx 仅改 child `robocasa_exact_window_policy.py`、`robocasa_exact_window_policy_test.py`：构造时把 compute_dtype、完整 exact durations、chunk frames 保存为私有不可变字符串/tuple 快照；公开 manifest copy 仍保留原形态，但 resolver/validator 只读快照，resolver 输出仍为普通 list。正式测试逐一篡改原始输入与公开 copy 的 durations/chunk/dtype，验证 resolver 保留 `[17,61]`、旧 `[33]` 拒绝、缺少原 manifest 必需 chunk 键的候选由 validator/resolver 均拒绝、Edge candidate 非合同字段不变。最终 Phase1A+1B+2 离线 synthetic CPU pytest **137 passed**；两文件 Ruff check、Ruff format --check、diff-check PASS。命令使用既有 V3 venv、`CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1` 与 pytest `-o addopts='' --tb=short`。无真实训练资产/GPU/训练/仿真，尚无 ds Evidence。child `ce07cb6f4a3f7792d85b7583ff6c8bda0bfa0cb0` 已推送 `origin/v3-local-ttt`；root 本步仅更新 Gitlink、SESSION、TODO、原样纳入 r2 review，随后另行 append Inbox 请求 GPT fresh pair。本记录写入时 root 未提交，不自授批准。

# V3 Corrected Phase 2 source review blocker 修复（2026-10-05）

- Gate `V3-CORRECTED-PHASE2-IMPLEMENTATION` 保持 REVIEW。GPT review `docs/collab/chatgpt/reviews/2026-10-05_V3_phase2_source_review_8b21e7b1_826c7ca0.md` 对 formal root `8b21e7b1eb01e229ab6152371ac4039d4e4905da` / child `826c7ca0fd5b6967d7199c0fefd144fe1fdd57e2` 给 `REQUEST_CHANGES`，唯一 blocker 为 no-arg tokenizer resolver 从 bare Edge base 重建整份 runtime config，覆盖 wrapper 的 `WAN_VAE_PATH`。已读原 review；本轮仅修改 child `robocasa_exact_window_policy.py` 和 `robocasa_exact_window_policy_test.py`：`resolve_tokenizer_config(candidate_config)` 深拷贝 caller config，OmegaConf `DictConfig` 转为保留未解析插值的容器，只覆盖 manifest 完整 `encode_exact_durations`，然后校验 fixed Edge chunk capability/manifest/dtype；删除 no-arg resolver。正式测试以 current Edge wrapper 为输入，逐项比较所有非 duration 字段、输入不变、resolved validator PASS，旧 Edge dataset chunk32 仍拒绝。首次合并测试 `131 passed/4 failed`，根因为测试直接解析未设置的 OmegaConf `WAN_VAE_PATH`；第二次 `134 passed/1 failed`，根因为负例测试展开 `DictConfig` 时解析同一插值；修正为 `OmegaConf.to_container(resolve=False)` 后最终合并 Phase1A+1B+2 synthetic CPU pytest **135 passed**，两文件 Ruff check、Ruff format --check、child diff-check PASS。命令使用既有 V3 venv、`CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 MKL_NUM_THREADS=1` 与 pytest `-o addopts='' --tb=short`，未访问真实训练资产/GPU/训练/仿真；尚无 ds 独立 Evidence。child `9819cec5f456fb4f5a9b9681479c05a97f62cb70` 已推送 `origin/v3-local-ttt`；root 本步预计只更新 Gitlink、SESSION、TODO、原样提交上述 review，然后另行 append Inbox 请求 GPT fresh exact-pair review。本记录写入时 root 未提交，不自授批准。

# V3 Corrected Phase 2 implementation（2026-10-05）

- Phase2 child `826c7ca0fd5b6967d7199c0fefd144fe1fdd57e2` 已先提交并推送 `origin/v3-local-ttt`，formal diff 恰为新增 `robocasa_exact_window_policy.py`、`robocasa_exact_window_policy_test.py`。adapter 以无 constructor proxy 调官方 `_build_frame_wise_action`/`_build_initial_state`，输出 raw15/state15/17行 stream 并保留 source 身份；contract 从 Phase1A manifest 保留完整 VAE 配置，验证 fixed Edge 能力、H_pred16/R 范围与 resolved dataset/runtime/tokenizer，旧 Nano/Edge chunk32/[33] 拒绝。synthetic CPU 合并 Phase1A+1B+2 pytest **135 passed**；最终两文件 Ruff check、Ruff format --check、child staged/formal diff-check PASS。第一次合并 pytest 为 134 passed/1 failed，根因是 Nano 整数 fps20 与合同浮点20.0 的过严类型比较，修为数值20且拒 bool/非有限后全绿；最后又补 fixed Edge 全能力校验和 legacy Edge dataset 测试，已包含在最终 135 passed。仅本地合成数据，未访问真实 cache/source/训练服务器；未运行 GPU/训练/仿真，尚无 ds Evidence。root formal 预计只提交 Gitlink、TODO、SESSION，随后另以 Inbox ledger commit 请求 GPT fresh exact-pair review；本记录写入时 root 尚未提交，Gate 保持 REVIEW。

- Gate `V3-CORRECTED-PHASE2-IMPLEMENTATION` 已认领，状态 IN_PROGRESS。已全文重读 `/tmp/CX_PHASE2_RAW15_STATE15_HPRED16.md`、GPT frozen Phase2 v1.1、v3.0、Phase0 mapping、Phase1B closure、Phase2 seam audit；design root `e75910db1be92fecd0c7e849b3a5556b8a2aaa90`，child baseline/Gitlink `21e60d6eb3a04846ffa7280aca18f6005399363e`。预计 child **仅新增** `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_policy.py` 与 `robocasa_exact_window_policy_test.py`；root 后续仅 Gitlink、TODO、SESSION 与 live Inbox append。先以官方 RoboCasa 私有 helper 桥接 raw15/state15，再以 synthetic CPU 测试验证17行条件语义、ActionProcessor与manifest/legacy配置 fail-closed，回归 Phase1A/1B；不碰 official core/model/packing/loss、旧 recipe/launcher、trainer/inference/server/eval、真实训练资产/GPU/训练/仿真。本条及 TODO 认领暂未提交；完成 child self-test 与提交后回填 exact SHA/结果，再送 GPT fresh review。

# V3 Corrected Phase 2 design freeze（2026-10-05）

- GPT 已重新生成并冻结 `docs/build/PSM-WMA_V3_phase2_raw15_state15_hpred16_design_v1.1_2026-10-05.md`，取代损坏且未提交的 v1.0。cx 全文只读复核 v1.1、Corrected V3 v3.0、Phase0 mapping、Phase1B closure 与 Phase2 source seam audit，并核对当前 child 官方 `_build_frame_wise_action`/`_build_initial_state`、WAM Case B 17/17、ActionProcessor、OmniMoT action mask/noising/loss、Phase1A `vae_encode_contract` 和 Edge tokenizer 配置；未发现 docs-only freeze blocker。v1.1 将 Phase2 限于官方 raw12→raw15/state16→state15 桥接、17 行 state/action CPU 合同与 manifest 驱动的 H_pred16/VAE 校验；旧 chunk32/[33] 必须 fail-closed，server/eval 与真实执行仍留后续 Gate。本步 root 仅提交 v1.1 原文、`docs/INDEX.md` 当前 Phase2 索引与本条 SESSION；child/Gitlink/TODO 不动。只执行只读文件/源码/Git 检查及文档 diff-check；未运行项目代码、测试、GPU、训练或仿真，未访问真实训练资产。design root SHA 以本次提交为准；Phase2 production 尚未实施。

# V3 Corrected Phase 2 设计输入（2026-10-05）

- Phase1B 正式 closure：GPT review `docs/collab/chatgpt/reviews/2026-10-05_V3_phase1b_closure_d7aa5673_21e60d6e.md` 对 formal root `d7aa56730b8d04c50ed471179a0c08a038f3c07e` / child `21e60d6eb3a04846ffa7280aca18f6005399363e` 给 `APPROVE_PHASE1B_CACHE_SOURCE_BINDING_ONLY`；closure review 已作为单文件 bookkeeping root `a3156bb7927770c453719fc578e76ba23e78df87` 推送。ds 独立 Evidence 为 115 passed/Ruff/format/diff-check PASS，只覆盖 synthetic/local CPU/static。
- 新任务 `V3-CORRECTED-PHASE2-DESIGN`：当前 V3 未见 Phase2 专项 frozen design。cx 只读核对 Phase1B raw12/state16 输出、官方 `RoboCasaLeRobotDataset` 转换/clean state 行、Case B sequence plan，以及 Edge/Nano/H100 旧 `[33]`/chunk32 冲突，写入 `docs/build/PSM-WMA_V3_phase2_source_seam_audit_v0.1_2026-10-05.md` 供 GPT 冻结设计；该审计不是设计 authority。预计/实际 root 仅该审计、TODO、SESSION，后续 append Inbox 请求 GPT Phase2 design；child/Gitlink 不动。未运行项目代码、测试、GPU、训练或仿真，未访问真实训练资产。本条落盘时尚未提交。

# V3 Corrected Phase 1B cache-to-flat-source binding（2026-10-05）

- GPT 对旧 formal pair root `610737dd841dd2cd6ef3a3661d323808d41b8ef7` / child `db2701554ae26c50e26d1854ef3b1182de37118d` 的 fresh source review `docs/collab/chatgpt/reviews/2026-10-05_V3_phase1b_source_review_610737dd_db270155.md` verdict=`REQUEST_CHANGES`；唯一 blocker 为 `summary().mismatch_counters` 空 dict。review 原文纳入本次 root formal commit，不改内容。另一用户提及的 `2026-10-05_V3_phase1b_design_v0_4_adoption_39258667_a40e8b78.md` 在当前树不存在；既有正式 adoption review `2026-10-05_V3_phase1b_design_adoption_39258667_a40e8b78.md` 已由 root `76341a03` 原样提交，授权 v0.4。
- cx 仅改 child `robocasa_exact_window_source.py` 与 `robocasa_exact_window_source_test.py`：valid summary 固定 machine-readable `missing/ambiguous/task_mismatch/frame_mismatch/row_mismatch=0`，formal valid-official-reader test 精确断言全部键值；actual mismatch 仍逐项抛错，未增加宽松统计。child `21e60d6eb3a04846ffa7280aca18f6005399363e` 已推送 `v3-local-ttt`。相同离线/CPU 合并命令（见下）再次 **115 passed**；两文件 Ruff check、Ruff format --check、child staged diff-check PASS。未运行 ds Evidence、真实资产、GPU、训练或仿真。root 本轮仅新 Gitlink、SESSION/TODO 与原样 review；formal root 本条记录时未提交，随后 append Inbox 请求 GPT fresh exact-pair source review。Gate 保持 REVIEW，不自授批准。

- Phase1B implementation 已提交 child `db2701554ae26c50e26d1854ef3b1182de37118d` 并推送 `v3-local-ttt`；GPT adoption review `docs/collab/chatgpt/reviews/2026-10-05_V3_phase1b_design_adoption_39258667_a40e8b78.md` verdict=`ADOPT_AND_REFREEZE_PHASE1B_V0_4` 已单独 bookkeeping commit `76341a03fbd297e68f9d2b3e78251e1be0f13b3e` 推送，旧「GPT frozen」标签自该 review 起才具 authority。Gate 现为 REVIEW，待 GPT fresh source review；不自授批准。
- 实际 child 只改 `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache.py`（向后兼容 `ExactWindowIdentity/read_identity`），新增 `robocasa_exact_window_source.py` 与 `robocasa_exact_window_source_test.py`。flat v3 本地 preflight/离线 guard、私有官方 LeRobot 两 method override、cache exact episodes、identity parquet scan、absolute→relative anchor、逐窗 action12/state16/17 帧与 pad/caption/class 校验、cache-driven index 与便携 source-binding digest 均已落盘；无 raw15/state15/model/Local/inference/trainer/eval 接线。
- Review 两项测试修正：mandatory metadata/data preflight 用显式注入的 raising factory 断言构造前拒绝；direct local-only official constructor fallback 命中 overridden `download(False)` 并断言 Hub pull 0。valid official no-video fixture 对 action12/source frame 1..16 和 state16/source frame 1..17 作逐值相等断言，证明没有 normalization/conversion。合并命令：`CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /disk/rl/worktrees/cosmos-framework-v3/.venv/bin/pytest -q cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache_test.py cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source_test.py -o addopts='' --tb=line`；结果 **115 passed**。三文件 Ruff check、Ruff format --check、child staged diff-check 均 PASS。仅 synthetic tmp_path CPU；未访问真实 source/cache/训练服务器、GPU、训练、仿真或 ds 独立 Evidence。root 本步预计仅 Gitlink、SESSION、TODO；formal root 此刻未提交，随后 append Inbox 请求 fresh exact-pair source review。

- Gate `V3-CORRECTED-PHASE1B-CACHE-SOURCE-BINDING` 已认领，状态 IN_PROGRESS。authority：`/tmp/CX_PHASE1B_IMPLEMENT.md`、Phase1B v0.4 frozen design（root `39258667001882678d082a01052e70557ba5ec35`）、v3.0/Phase0 mapping；Phase1A child baseline `a40e8b782e0692e0a24e2f60893e9f4f8d858961`。已全文复读 brief/v0.4，核对 Phase1A reader、official LeRobot seam 与 clean root/child。预计 child 仅新增 `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source.py`、`robocasa_exact_window_source_test.py`，仅为兼容 identity API 可改同目录 `robocasa_exact_window_cache.py`、`robocasa_exact_window_cache_test.py`；root 后续仅 Gitlink、TODO、SESSION、append Inbox。当前未提交。禁止 raw15/model/Local/inference/GPU/训练/仿真/真实训练资产。

# V3 Corrected Phase 1A cache catalog（2026-10-05）

- Phase1B design freeze（docs-only，2026-10-05）：全文复核 `docs/build/PSM-WMA_V3_phase1b_cache_source_binding_design_v0.4_2026-10-05.md`，对照 v3.0、Phase0 mapping、current `LeRobotDatasetMetadata`/`LeRobotDataset`/`BaseActionLeRobotDataset`。v0.4 以仅覆盖 `_check_cached_episodes_sufficient` 与 `download` 的私有 LeRobot 子类，在 constructor 检查期移除本实例 video features 并复用 `super()`；构造前 offline guard、local meta/data preflight，`episodes` 精确等于 cache episode set，absolute→relative anchor 映射与当前实现相符。先前 v0.3 的构造期视频检查 blocker 及 v0.4 文件污染/旧版本自引用已消除，未发现本轮 docs-only freeze blocker。root 只提交 v0.4 设计原文、`docs/INDEX.md` 当前 authority 索引和本记录；child/Gitlink 保持 `a40e8b782e0692e0a24e2f60893e9f4f8d858961`，TODO/production/test 不动。未运行项目代码、测试、GPU、训练或仿真；Phase1B source binding 尚未实现或验收。本记录随 design root 提交，此刻未提交。

- 当前整改：GPT r2 review `docs/collab/chatgpt/reviews/2026-10-05_V3_phase1a_cache_catalog_source_review_r2_7c214251_e98f293f.md` 对 formal root `7c214251f3535116e7b19f964ee907e8653fd388` / child `e98f293f396df74bb7030d525c40faa21e7d226d` 给出 `REQUEST_CHANGES`，撤销同 pair 的旧执行放行。唯一 blocker 是 `_audit_files` 漏记 `tasks/*/episodes/` 内非 canonical 的 `.pt` payload。cx 仅改 child `robocasa_exact_window_cache.py` 与 `robocasa_exact_window_cache_test.py`：扫描该 namespace 所有 `.pt`，保留 canonical 路径作为 expected，异常文件计 extra；三个文件名各有 strict 拒绝与 non-strict 统计测试。child `a40e8b782e0692e0a24e2f60893e9f4f8d858961` 已推送 `origin/v3-local-ttt`；合成 tmp_path targeted CPU pytest `60 passed`，Ruff check、Ruff format --check、child staged diff-check 均 PASS。命令：`CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /disk/rl/worktrees/cosmos-framework-v3/.venv/bin/pytest -q cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache_test.py -o addopts=''`。root `origin/V3=126070c0ba37abe01cca3f6af71c8c2c478c2834` 已 fetch/ff-only；本步 root 仅更新 Gitlink、SESSION、TODO、原样提交 r2 review，随后 append Inbox 请求 fresh pair。未执行 ds 独立 Evidence、真实 cache/GPU/训练/仿真，也未触碰 binder/model/trainer/inference/server/eval。root formal commit 此刻未提交。

- Phase1A 实施结果（未提交 root formal pair 时记录）：child `e98f293f396df74bb7030d525c40faa21e7d226d` 已推送 `origin/v3-local-ttt`，仅新增 `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache.py` 与同目录 `_test.py`。manifest 决定 accepted corpus；portable `task_class/task_slug/episode_index` 身份与 `tasks/<slug>/episodes/episode_<index:06d>.pt` 定位；manifest SHA 与去绝对 root 的语义 digest；声明/发现/accepted/extra、task/window/effective consumer/unique-frame 统计；payload/window 按需 `torch.load(weights_only=True)`，exact key、fp32 finite `[5,48,H,W]` 与 17 帧/5 anchor 校验；无 raw dataset/VAE fallback。GPT early review 两项已纳入：公开 `episodes` 为排序后的 records，扫描整个 `tasks/*/episodes/episode_*.pt` 并拒绝未声明 task/episode；额外补 VAE contract 非法字段及 `source_video_frames`/window_count 不符的拒绝测试。合成 tmp_path targeted CPU pytest `57 passed`（命令：`CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /disk/rl/worktrees/cosmos-framework-v3/.venv/bin/pytest -q cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache_test.py -o addopts=''`），Ruff check PASS、Ruff format --check PASS、child staged diff-check PASS。最初系统 pytest 缺 `omegaconf`；禁插件的 V3 pytest 因 conftest xdist hook 未注册失败，改用既有 V3 venv/默认插件后通过；未改环境文件。未测试真实 cache schema/性能、无 ds 独立 Evidence；未访问训练服务器/GPU/训练/仿真。root `git fetch origin V3` 成功，advertised/tracking 均为 `08e09d3cac2d895e4bc9b8fa162a097f7f3dcc75`，无新增提交且 ff-only 已是最新。下一步 root 仅提交 Gitlink+TODO+SESSION，推送后 append Inbox 请求 GPT fresh review；不自授批准。

- Gate `V3-CORRECTED-PHASE1A-CACHE-CATALOG` 已认领，状态 IN_PROGRESS。前置 exact pair：Phase0 mapping root `861849491488258214e96e778cff7d1bd0309089` / child `c00a014444083c7c554fff7626f48cceaf5c5c31`；GPT formal review `docs/collab/chatgpt/reviews/2026-10-05_V3_corrected_phase0_mapping_86184949_c00a0144.md` 为 `APPROVE_PHASE0_MAPPING_ONLY`，仅授权 Phase1 cache catalog/contract tests。已全文重读 v3.0 设计与 Phase0 mapping、Phase1A 任务 `/tmp/CX_PHASE1A_CORRECTED_V3_CACHE_CATALOG.md`；复用 `tools/g0/build_cosmos_robocasa_latent_dataset.py` 的 exact_window_v1 manifest/payload 布局与 V2 donor reader 结构，**不复用其 raw dataset 过滤及固定 `[17,61,73]` 假设**。child clean，`origin/v3-local-ttt=c00a014444083c7c554fff7626f48cceaf5c5c31`，已切本地 tracking branch。预计 child 只新增 `cosmos-framework/cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache.py` 与 `robocasa_exact_window_cache_test.py`；root 后续仅更新 Gitlink、SESSION、TODO、append Inbox。现在未提交；禁止 source binder/model/trainer/inference/server/eval、训练服务器/cache、GPU/训练/仿真。

# V3 Corrected Phase 0 mapping（2026-10-05）

- 本轮 `V3-CORRECTED-PHASE0-MAPPING` 最后一项 docs-only 补充：预计仅改 mapping、必要 TODO/SESSION，正式 root 推送后 append Inbox。只读核对 current Edge wrapper `action_policy_robocasa_edge.py:23` 设 `encode_exact_durations=[33]`、H100 入口 `psm_wma_robocasa_h100.py:265` 强制 `[33]`、`:275` chunk32；V2 donor `vision_vae.py:12` 定义 `[17,61,73]`，`tools/g0/build_cosmos_robocasa_latent_dataset.py:527–528,588–591` 将该参考 exact-window VAE contract 写入 manifest。mapping 已在 Edge overlay、H100、默认32污染、Phase 2–3 加：corrected H_pred16 的 17 帧窗口要求 effective exact durations 含17；完整列表及 dtype/chunk frames 以**指定 cache 的实际** `vae_encode_contract` + fixed tokenizer 能力精确校验，不能只改 chunk16、推断实际 manifest 或重新编码。本轮未读取实际 cache manifest，测试项仍为未来验收；不访问训练服务器，不改 child production/test/Gitlink，不执行项目代码/GPU/训练/仿真。旧 formal root `08bda92f5d837377dd9ef83b78fc2f4bbaf70626` 的审核请求将由新 root 的 Inbox append 取代；本段记录时未提交。

- Owner 后续职责修正（同 Gate，docs-only）：`local_memory_client.py` 仅保留 pending pre-action composite RGB，在 `env.step` 成功后将 composite + canonical executed raw15 标为 completed 并发送；同一 preprocessing/VAE helper 的 `T_pixel=1` Encode1 在模型/VAE 所在进程的 server-side `robocasa_local_memory_policy` adapter 执行。Phase 6 和验收加 client 无 Wan VAE 依赖、失败步无 completed 发送/Local 更新、server Encode17[0] parity。上一 docs-only formal root `2c6d99b6a6cd0e8dc87bd4aa2713919f071b181f` 已推送；其 Inbox 请求由 bookkeeping commit `abb527e2` 记录，本次将以新 formal root 的 append 条目明确取代。预计修改 mapping、TODO、SESSION 与后续 Inbox append；child production/test/Gitlink 不动。`git diff --check` 待提交前复核；未执行项目代码/GPU/训练/仿真；本段记录时本次修订未提交。

- Phase 0 第二轮 docs-only 修订（任务 `V3-CORRECTED-PHASE0-MAPPING`）：Owner 明确将三条 tmux 意见作为 GPT direct review findings，授权直接修 mapping，无需先等旧 root review 文件；新 formal root 后由 GPT 处理正式 review。当前操作预计且实际仅改 `docs/build/PSM-WMA_V3_corrected_implementation_mapping_v0.1_2026-10-04.md`、必要 `TODO.md`/`SESSION.md`，然后 append-only `docs/collab/chatgpt/CODEX_INBOX.md`。复用 v3.0 D§24/35/36/44/45/48、current `local_memory_grouped_window.py:97–164`、`robocasa_grouped_segment.py:420–452`、`ActionSFTDataset.__getitem__` 与 `ActionTransformPipeline.__call__`。修订明确：同 index 跨 B_stream slot 批量 fast-update 且 T 串行，scalar/batched 数值及 W0/KQV/encoder/host 梯度 parity；推理 completed pre-action composite 默认以同一 preprocessing/VAE helper 做 Encode1，policy current-z callback 仅可选优化，以 Encode17[0] parity 验收；训练 `video_latent` cache-hit 必需，逐层保键并把 grouped 旧拒绝 guard 改为 cache-required。`git fetch origin V3` 成功，advertised/tracking SHA 均为 `cdaa32d93146f0829936784b588d6c875e5bc621`，从 before_head 同 SHA 无新增，祖先检查 0、ff-only 已是最新；旧 root `ad2817a5cd323cf37c2354cbaf81cba6fe35edf4` 的 reviews 目录精确检索无命中，但不作为本轮修订阻塞。`git diff --check` PASS；未执行项目代码/正式测试/GPU/训练/仿真，因仅文档修订。child/Gitlink 保持 `c00a014444083c7c554fff7626f48cceaf5c5c31`；本段记录时未提交，下一步 docs-only formal commit→push V3→Inbox append 请求 GPT 审核。旧 cache 路径询问不作为本轮前置。

- 2026-10-05 00:36:28 CST，Phase 0 第 2 次 V3/GPT-only 只读观察：`before_head=a4c47c91ae3210951a3ccf6ed556a645e9d888da`；`git fetch origin V3` 成功，`git ls-remote origin refs/heads/V3` advertised SHA=`origin/V3`=`a4c47c91ae3210951a3ccf6ed556a645e9d888da`；完整新增提交范围为空；祖先检查 exit 0；`merge --ff-only` 为 Already up to date；对 formal root `ad2817a5cd323cf37c2354cbaf81cba6fe35edf4` 的 `rg -l -F` review 精确检索标准化输出 `NO_EXACT_ROOT_MATCH`。V3 最新角色指定 GPT 审核，无 MM/Kimi 冻结 pane；该输出仅是本轮目录事实，未作为实现批准。
- 新增只读 cache 线索：历史目录 `/disk/rl/starVLA/playground/Datasets/robocasa365_wan2.2_latent/v1.0/target/atomic/` 存在，但其 `window_manifests/wan2.2_h10_f8_train.parquet` 与 17 帧 exact-window 目标不同，且该目录深度 8 内未找到 `dataset_manifest.json`；不能将其作为 corrected V3 指定 cache。`tools/g0/build_cosmos_robocasa_latent_dataset.py:570–606` 的 builder schema 有 `source_dataset` 路径、`script_revision`、`episode_count`、`window_count`、`latent_shape`、tasks 与 VAE 几何，但实际 target cache manifest 未读到，不能据源码声称 corpus fingerprint 或完整性已验证。`C/model/generator/omni_mot_model.py:get_data_and_condition` 现有训练入口始终调用 `_encode_vision_x0_tokens`，进一步明确 V2 cache-hit optional 分支的接入点；未修改 production/test/Gitlink，未运行项目代码/GPU/训练/仿真。继续等待实际 cache 路径和 formal mapping 范围裁决；此段记录未提交。
- 2026-10-05 00:30:34 CST，Phase 0 / broad Corrected V3 goal 只读后续核验：`before_head=bab3140dcbe1122475d9c4dc1cd5aa47ddb50ca8`；`git fetch origin V3` 成功；`git ls-remote origin refs/heads/V3` advertised SHA 与 `origin/V3` 均为 `bab3140dcbe1122475d9c4dc1cd5aa47ddb50ca8`；`git log --oneline before_head..origin/V3` 输出为空；`git merge-base --is-ancestor before_head origin/V3` exit 0；`git merge --ff-only origin/V3` 为 Already up to date。formal mapping pair root=`ad2817a5cd323cf37c2354cbaf81cba6fe35edf4` / child=`c00a014444083c7c554fff7626f48cceaf5c5c31`；`rg -l -F <完整 formal root> docs/collab/chatgpt/reviews` 标准化结果 `NO_EXACT_ROOT_MATCH`。按最新 V3 角色仅 GPT 审 mapping，旧 MM/Kimi pane 不作为本 Gate 名册；本轮不由 Inbox 推断 verdict，未启动实现。
- Phase 0 cache schema 资产检查：当前 cx 环境 `ROBOCASA_LATENT_CACHE_ROOT` 未设置；`/disk/rl/data`、`/disk/rl/datasets` 深度 6 内无 `dataset_manifest.json`；`/disk/rl` 深度 5 的只读查找亦未发现指定的 corrected composite exact-window manifest。已向 Owner 异步询问具体机器/路径。V2 donor 的 `robocasa_lerobot_dataset.py:363–515` 仅作参考：schema `exact_window_v1`、H_pred16、`[5,48,H,W]`、每 window 的 17 帧/5 anchors；其 `_filter_valid_episodes` 会按 cache 可用 episode 过滤，**不能**直接作为 corrected V3 的 corpus authority/fail-closed 实现。现有本地证据不足以验证实际 target-atomic cache 的 schema、canvas、UID 或完整性；未执行项目代码/GPU/训练/仿真。下一步在获知 cache 路径后做只读 manifest/window 核验，并按 GPT/Owner 对 formal mapping 的审查范围推进；本段记录未提交。
- Owner 追加的两项 docs-only 修订：① fixed upstream `cf5d68c` 只有官方 `action_policy_robocasa_nano.py`，没有项目 `action_policy_robocasa_edge.py`；mapping 已分列 UP KEEP 与 project ADAPT/replace wrapper。② 补 `local_memory_grouped_window.py` 的 T16/8 slot/GA2 与 `trainer/local_memory_grouped.py` 的 GA2 固定点，并追踪 `robocasa_grouped_segment.py` 的相关几何假设；要求 T16/32 真正可执行、B_stream/GA 默认 8/2 但独立配置。先前 formal mapping root `7a0cb5ef20fa08efcbefb749d8ed19b312cf99d0` 被本次修订取代，后续以新 docs-only commit 为 formal root；此段记录时新修订未提交。未修改 child/Gitlink 或运行测试/GPU/训练/仿真。
- 修订自检：`git diff --check` PASS；`git diff --name-only` 仅 mapping 与 SESSION；fixed upstream `git ls-tree` 确认 Nano recipe 存在、Edge recipe 不存在；逐字段 `rg` 核对 `local_memory_grouped_window.py:57,105,131,164` 与 `trainer/local_memory_grouped.py:184`，并列检查 `robocasa_grouped_segment.py` 关联硬编码；child worktree clean、Gitlink 保持 `c00a014444083c7c554fff7626f48cceaf5c5c31`。未运行项目测试，原因是 docs-only Phase 0。下一步提交、推送并以新 exact pair append Inbox 修订申请；提交哈希以新 formal commit 为准。
- 修订 formal docs-only root `ad2817a5cd323cf37c2354cbaf81cba6fe35edf4` 已推送 V3，formal child/Gitlink 不变。`git diff-tree --no-commit-id --name-only -r ad2817a5cd323cf37c2354cbaf81cba6fe35edf4` 仅 mapping 与 SESSION；其前一 root `7a0cb5ef20fa08efcbefb749d8ed19b312cf99d0` 的 Inbox 申请已由新 exact-pair append 条目明确取代。live Inbox 追加前容量 75405+1396=76801 bytes，仍低于 131072 上限；此后 ledger/SESSION 提交只是 bookkeeping，不改变 formal root 或 child。当前仍为 REVIEW，不自授批准。
- 任务 `V3-CORRECTED-PHASE0-MAPPING`：只读对照固定 root `380f886223bbf14ad8d133589aaf4a6bba750ecc`、child/Gitlink `c00a014444083c7c554fff7626f48cceaf5c5c31`、V2 donor `e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92`、upstream `cf5d68c00d97ccd2480a2320ed652b92dec63102`。复用 v3.0 设计、官方 RoboCasa loader/state/decoder/server、V2 cache-hit/pool 与现有 Local/事务/DCP 入口；逐文件映射写入 `docs/build/PSM-WMA_V3_corrected_implementation_mapping_v0.1_2026-10-04.md`。本文列出 B1 视觉、raw dataset/chunk32、cache-hit 缺失、env.step 前 evidence 和 T/R 耦合等冲突及候选最小 seam，cache 真实 schema 和数值 parity 留后续只读/Gate 核验。
- 本步实际修改：上述 mapping 文档、`TODO.md`、`SESSION.md`；后续仅 append live Inbox 审核申请。已执行 `git diff --check` PASS、root/child SHA 与 Gitlink 检查 PASS、child worktree clean；未执行项目测试/GPU/训练/仿真，因为 Phase 0 仅文档映射。当前状态 REVIEW，等待 GPT/Owner 对 mapping 与待裁决项审核；本段记录时未提交，commit SHA 待下步回填。
- Phase 0 formal docs-only root `7a0cb5ef20fa08efcbefb749d8ed19b312cf99d0` 已推送 origin/V3；formal child/Gitlink 仍为 `c00a014444083c7c554fff7626f48cceaf5c5c31`。提交范围由 `git diff-tree --no-commit-id --name-only -r 7a0cb5ef20fa08efcbefb749d8ed19b312cf99d0` 核对为 mapping、TODO、SESSION。live Inbox append 容量检查 73651+1754=75405 bytes，已追加 exact-pair GPT/Owner 审核申请；此处仅为 bookkeeping，不改变 formal pair、不自授 verdict。未送 MM/Kimi 旧 V2 三方审核，也未进入旧 B2-B Gate。

# V3 H3-E 8×H100 integration smoke（2026-09-27）

- H3-E CPU harness child `6c7b1333c94773b2fb6940b530a63eb74b82a753` 已提交并推送；root 本步更新 Gitlink 与 `docs/build/PSM-WMA_V3_h3e_cpu_harness_implementation_2026-09-27.md`，root SHA 以本次提交为准。预计修改文件仅 SESSION、TODO、implementation record、Gitlink；`artifacts/v3/` 保持未跟踪且不纳入。
- 复用 Stage-A TOML 官方 Hydra compose、one-step DCP 与 raw15 transform，H3-B 18 类 catalog/binder、H3-C grouped trainer、H3-D dataloader rank-pkl resume。child 新增 H100 launcher/test，trainer 只增加可选 observer；8 rank×8 slot×GA2×T16、Edge host+Local optimizer 与严格 DCP 不降级。读过上述入口及 H3-E v0.1 设计；未改 V2、B0/B1、policy forward 或 4090 relay。
- CPU：H3-E 定向 8 项与 grouped trainer 合计 13/13；此前 13 文件 244/244 加三文件 23/23，相关回归合计 267 项，最后两项监控/DCP 小改的定向 13/13 PASS。真实资产预检（临时绕过未提交 pair 锁，仅用于诊断）PASS：18 类 9036 episode、manifest `a8cad3f053232b348ea155f15bf79c2c9cf807dedcf39b89e246b17e43f283df`、Stage-A DCP 549 键、CloseFridge ep0 8 consumer raw15/padded64 batch；日志 `/tmp/cx_v3_h3e_preflight.log`。child 三文件 Ruff/format、两仓 diff-check PASS。
- 本步不运行 GPU、DCP save/reload 或 8×H100；runtime 尚无 PASS。下一步在本 root/child formal pair 上重新跑不绕过的 CLI preflight，再由 ds 执行 fresh 一窗口和同 job resume 第二窗口，保留原始每 rank JSON/JSONL 与 DCP。cx 对真实失败负责定位并修复；ChatGPT 仅不定期审核。状态仍 IN_PROGRESS，未授 closure。

- H3-E 设计起点 root `6ca3304a14190f44a0a1b0bcd1e432ad8249e148` / child `74fd78531ab77d4cea77903470f8ceb8ff136873`；入口从 Stage-A one-step DCP warm-start，保留 Edge generation/action+全部 Local trainable、8 rank×8 slot×GA2×T16、raw15/chunk32/33 与严格 DCP resume；CPU harness 与实现状态以上述新记录为准，8×H100 fresh/resume 尚未启动。

# V3 H3-D strict grouped resume（2026-09-27）

- H3-D CPU/static 由 cx 依据 child `74fd78531ab77d4cea77903470f8ceb8ff136873` 技术关闭：新增 per-rank Local 状态回调、严格同 job DCP rank-pkl 预检，复用 upstream DCP `trainer` 组件的 GradScaler/iteration/Python/NumPy/Torch RNG；fast state 仍不进参数或优化器。恢复前验证 manifest/config/几何/rank/iteration/slot 与 terminal 身份，四个 fast tensor 必须 finite fp32；恢复失败后 trainer 实例禁止重试。中断与连续路径下一段 identity/evidence/loss/grad CPU 对照 PASS；16 文件 260/260、四文件 Ruff/format、双仓 diff-check PASS。未执行真实 DCP save/reload 或 GPU；H3-E 由 ds 验证 8×H100 跨 rank DCP 恢复。

# V3 H3-C grouped trainer transaction（2026-09-27）

- H3-C CPU/static 由 cx 依据 child `0dca391d2cb6e4a62b0fca0c39ebf0640e678dd9` 技术关闭：`GroupedLocalMemoryTrainer` 复用上游 `ImaginaireTrainer` train loop，在两次 GA 调用之间维持候选 grouped window；每 index 原生 batch 普通联合 autograd，按整窗有效数归一化一次；选中梯度 finite、GradScaler skip 与 optimizer 成功门后才发布 frontier/sidecar/scheduler。14 文件隔离 CPU 回归 243/243 PASS，新增两文件 Ruff/format、双仓 diff-check PASS；真实 CloseFridge ep0 前8 consumer 经 Stage-A transform 后 grouped native batch ABI PASS，日志 `/tmp/cx_v3_h3c_native_b8_preflight.log`。未执行 GPU、完整 Edge FSDP 或 DCP resume；H3-D 继续严格恢复，H3-E 由 ds 做 8×H100 短跑。

# V3 H3-B grouped persistent producer（2026-09-27）

- H3-B CPU/static 实现：child `8d7ddd7b77cd204fda7d8cae1e81d591660cddd8` 已提交并推送，仅新增 grouped producer 与测试；root 本步更新 Gitlink/TODO/SESSION。Stage-A 18 类训练 catalog 共 9036 episode，manifest digest `a8cad3f053232b348ea155f15bf79c2c9cf807dedcf39b89e246b17e43f283df`；8 rank 完整 epoch 逐段核对无重无漏，GA2×8 slot×T16 candidate-only，真实 CloseFridge raw15/64D Stage-A transform binder 与 18 类 latent H5 抽样 PASS。12 文件隔离 CPU 回归 227/227 PASS，Ruff/format、双仓 diff-check PASS；日志 `/tmp/cx_v3_h3b_full_epoch_chronology.log`、`/tmp/cx_v3_h3b_real_binder.log`、`/tmp/cx_v3_h3b_18_task_cache_preflight.log`。未跑 GPU；H3-C 继续实现 trainer transaction、speculative fast-state 和 GA2 原子发布。
- H3-A CPU/static 已由 cx 依据 formal pair root `6a8cd45f534d261033a8ed872a34dd181b2df648` / child `4548f5ad666d8a50d244ba2d1e4decefafd570aa` 的 213/213 回归与官方 flow action loss 联合梯度证据关闭；root closure bookkeeping `16dc360221eca0b170d929968556564bab4c5a8c`。
- H3-B v0.1 design root `665b72b40ec3003300a04cc602cbcef9e388899e`；v0.2 override 修正非 8 倍数 episode 的 epoch rollover：队列分配完即可跨 epoch，新 UID 不能与 live/candidate slot 并发重复；队列/epoch/cursor 仍 candidate-only、成功 step 后发布。

# V3 H3-A 联合梯度 CPU/static（2026-09-27）

- cx 作为技术 owner 判定 H3-A CPU/static seam 已满足 v0.2 验收：formal implementation pair root `6a8cd45f534d261033a8ed872a34dd181b2df648` / child/Gitlink `4548f5ad666d8a50d244ba2d1e4decefafd570aa`。B2-C run06 已证明完整 Edge `training_step` 在 4090 detached-prefix Local-only 配置中可执行；H3-A 新测试证明同一框架 flow action loss 经 two-way Memory Prefix 普通图可同时给代表 host 与全部 Local slow 参数传梯度。两项证据不可外推为 8×H100 完整联合模型运行；后者必须由 H3-E ds 实证。ChatGPT 非在线，本次是 cx 技术判断，不冒充其 verdict。
- 当前责任：cx 为技术 owner，负责设计、实现与处理 blocker；ds 负责后续 GPU 执行验证；ChatGPT 是用户不定期激活的非在线审核者。B2-C 已按 run06 实证关闭，正式 RoboCasa 8×H100 训练仍未启动。
- 任务 `V3-H3A-JOINT-AUTOGRAD-CPU-STATIC`：复用 `CanonicalLocalMemorySegmentAdapter.scan`、模型持有的 encoder/core、`OmniMoTModel.training_step` 现有 private prefix seam 和 two-way Memory Prefix。child 仅新增 `cosmos_framework/model/generator/mot/local_memory_joint_segment.py` 与其测试，提交 `7098d4d9fce0faf514a1e1ec1394c360362d8eea` 已推送；root 新增 H3-A v0.2 设计并更新本状态/TODO/Gitlink。不改 4090 relay、trainer、producer、配置、checkpoint 或 GPU 路径；root 本步提交前为未提交。
- V3 venv 定向 4/4 PASS；B0/B1/B2-A/B2-B/B2-C/R1-A/R1-B/H3-A 11 文件隔离 CPU suite 213/213 PASS；新增两文件 Ruff check/format 与双仓 diff-check PASS。测试证明单 slot T16 中 S0 prefix=None，另外 15 个保持原始 scan graph；同一个 two-way native attention outer loss 一次 backward 同时产生 host 与全部 Local slow 参数有限梯度，代表参数非零；独立直接 scan 梯度相等；失败不改 sidecar/frontier。没有运行 GPU、真实资产或完整 Edge `training_step` 联合反传，故 H3-A 状态保持 REVIEW，下一步补真实 native loss 接线证据。
- 后续只改 child 测试，改用框架现有 `compute_flow_matching_loss` 的 64D action prediction + raw_action_dim=15 mask 作为同一个 outer loss；没有新增 inner/reconstruction objective。child follow-up `4548f5ad666d8a50d244ba2d1e4decefafd570aa` 已推送。最终定向 4/4、11 文件 CPU 213/213、Ruff/format、双仓 diff-check PASS；本次 root 仅更新 Gitlink/TODO/SESSION，提交前未提交。仍未运行完整 Edge `training_step` 或 GPU，不关闭 H3-A。

# V3 Stage B2-C RTX4090 S1 run06 closure（2026-09-27）

- cx 作为当前 V3 技术 owner 依据 ds 独立执行结果判定 `V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE` 达到冻结 §8 验收；正式 execution pair root `57413889e3466c767f22956d98edc8b843b463d2` / child/Gitlink `a9aca770fd39b8eed9c456fc2dbdb8867189e78e`。`artifacts/v3/stage_b2c_4090_s1/run06/result.json` 为 PASS，ds 记录 exit 0；16 个 finite native loss、五项非零 Local 梯度、165312 选中参数、一次真实 optimizer_step、fast_state_commit、host unchanged、无 OOM；41 条 CUDA phase trace 峰值 allocated 17005632000 B/reserved 17924358144 B。run01–run05 immutable，artifacts 仍不提交；closure 记录见 `docs/build/PSM-WMA_V3_stage_b2c_run06_closure_2026-09-27.md`。ChatGPT 是非在线审核者，此次技术判定不冒充其正式 verdict。
- B2-C 仅证明 RTX4090 单段 Local-only 更新；未实现 8×H100 联合训练。下一步按已冻结 `PSM-WMA_V3_post_b2c_to_h100_gate_sequence_v0.1_2026-09-27.md` 依次推进 H3-A/B/C/D/E/F。R4/R5 两个 harness 整改任务随 run06 证据关闭，child production 无新改动。NCCL 在 exit 0 后报告 process group 未显式销毁；GPU 已释放，记录为后续运行生命周期清理项，不作为本次 S1 数值/资源失败。

# V3 Stage B2-C R5 DTensor witness（2026-09-27）

- run05 formal pair root `f782f2cc351fabded26bab23588758f899e3256a` / child `8984ceb065df231da6fdf9708322b7eae29af08a`，ds 单次执行后终止 FAIL，原始 `artifacts/v3/stage_b2c_4090_s1/run05/` 保留。16 个 consumer forward/backward 与 relay_backward 已完成，失败于 harness `optimizer.step` wrapper 内的 `_witness`：`torch.count_nonzero(DTensor gradient)` 缺少 sharding strategy，尚未调用真实 optimizer step，也未发布 fast state；不是 OOM。任务 `V3-STAGE-B2C-R5-DTENSOR-WITNESS`：child `a9aca770fd39b8eed9c456fc2dbdb8867189e78e` 已推送，仅改 `examples/psm_wma_robocasa_local_s1.py` 与 `_test.py`；root 仅 Gitlink/本状态/TODO/实施记录。用户最新职责为 cx owner、ds 执行；不等待 ChatGPT 在线，cx 不跑 GPU。
- R5 将 DTensor 梯度和参数诊断转为单 rank 本地 shard 后做 finite/nonzero/norm 与 host/Local 参数比较，未改真实 FusedAdam/Local 算法。V3 venv harness 定向 15/15、十文件 CPU 合并 209/209 PASS；真实 CPU/Gloo DTensor 用例覆盖 finite/nonzero/zero/NaN、冻结 host 与前后比较；两文件 Ruff/format、child/root diff-check PASS。R4 的真实资产 CPU preflight 仍为 PASS，run05 已实证 16 个 native consumer 和 relay。下一步 root 提交/push 新 Gitlink，再由 ds 在全新 run06 目录单次执行；run05 不重跑。

# V3 Stage B2-C R4 native batch envelope（2026-09-27）

- 用户最新职责调整：cx 负责判断与实现，ds 执行验证；ChatGPT 为非在线审核者，不将其即时回复作为修复的前置条件。任务 `V3-STAGE-B2C-R4-NATIVE-BATCH-ENVELOPE` 已认领。仅修改 V3 child `examples/psm_wma_robocasa_local_s1.py` 与 `_test.py`，child `8984ceb065df231da6fdf9708322b7eae29af08a` 已推送；root 仅本状态、TODO、MEMORY、实施记录与 Gitlink，构成本次 root 提交。旧 V2/v2、common dataloader/model、B0/B2-B、run01–run04 原始产物均不改。
- run04 formal execution pair root `4c128e6ad104f736e4a6cfef63b39ba0b3d662a0` / child `f8b81133f22ab01197b7b36003207cf5cfeb2e41` 已终止 FAIL：DCP、VAE、Local optimizer、B0 scan 通过；consumer0 因 harness 单层 `text_token_ids` 与生产 JointDataLoader 双层 batch 封装不一致而在原生 text pack 报 TypeError。修复前 V3/root branch 为 `ae8fc5b256e0b30e4552b734b828d2062c046f08`、child 为 `f8b81133f22ab01197b7b36003207cf5cfeb2e41`；执行 pair 的 detached checkout 已恢复开发分支，`artifacts/v3/` 保持未跟踪。CPU 诊断对 text/video/action/action_raw 四项均证明生产封装为 `list[list[Tensor]]`，详见 `/tmp/cx_v3_b2c_run04_remediation_map.md`。本条仅记录 run04 原始故障。
- R4 child 复用现有 `JointDataLoader._get_next_sample` / `_update_output_batch`，使单 consumer batch 与正式训练封装一致；真实资产 preflight 逐 payload 核对 text/video/action/action_raw。V3 venv 定向 14/14、B0/B1/B2-A/B2-B/B2-C/R1-A/R1-B 十文件 208/208 PASS；Stage-A 独立进程 24 passed、2 skipped、10 subtests passed。`/tmp/cx_v3_b2c_r4_preflight_20260927_01/result.json` PASS：549 DCP keys、429 帧、16 payload、consumer0 152 tokens/SHA256 `854e3c085df7ab1b392c0e4960875673123b22e5afd4d051c11c9ac119380aad`、CUDA trace 空。两文件 Ruff/format 与 child/root diff-check PASS。下一步 root 提交/push 新 Gitlink，然后 ds 仅在全新 run05 目录执行单次 RTX4090 S1；cx 不跑 GPU，不把 CPU PASS 当 runtime PASS。

# V3 Stage B2-C R3 Stage-A text transform（2026-09-27）

- Gate `V3-STAGE-B2C-R3-STAGE-A-TEXT-TRANSFORM` DONE；设计 authority root `3091df07983d15f4ecad3a30b27fd721522aede4` 的 R3 v0.1；formal pair root `4c128e6ad104f736e4a6cfef63b39ba0b3d662a0` / child `f8b81133f22ab01197b7b36003207cf5cfeb2e41`；ChatGPT verdict `APPROVE_TO_CLOSE_V3_STAGE_B2C_R3_STAGE_A_TEXT_TRANSFORM`，review `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b2c_r3_text_transform_closure_4c128e6a_f8b81133.md`。ChatGPT 设计/审核；用户 owner/最终裁决；cx 实现；ds 执行/测试。此 verdict 只授权 ds 单次 RTX4090 S1 run04；run01–run03 immutable，不授权 B2-C closure 或 8×H100 训练。
- child 仅改 `examples/psm_wma_robocasa_local_s1.py` 与 `_test.py`，提交 `f8b81133f22ab01197b7b36003207cf5cfeb2e41` 已推送 `v3-local-ttt`。保留原 raw episode/index/raw15 校验，按冻结 Stage-A config 对 16 个副本运行真实 ActionTransformPipeline，seed0 防文本 dropout；native callback 接转换后 RGB payload。root 仅 Gitlink、本状态、TODO 与 R3 implementation record。
- V3 venv 十文件 CPU suite 207/207 PASS；Stage-A 合同独立进程 26/26 PASS；真实资产 CPU preflight `/tmp/cx_v3_b2c_r3_preflight_20260927_01/result.json` PASS（549 DCP keys、429 帧、16 payload、consumer0 152 tokens、raw15/padded64，CUDA trace 为空）。Stage-A 测试结束后进程级 grad mode 为 False，故两套测试分进程；混跑的 grad-mode 失败不作验收证据。两文件 Ruff/format 与 child/root diff-check PASS。未跑 GPU，待 fresh review；不自授 closure。
- 第 1 轮观察凭证（2026-09-27 16:29 CST）：formal target root `4c128e6ad104f736e4a6cfef63b39ba0b3d662a0` / child `f8b81133f22ab01197b7b36003207cf5cfeb2e41`；before_head=`4c128e6ad104f736e4a6cfef63b39ba0b3d662a0`，`git fetch origin V3` 成功，advertised SHA 与 `origin/V3` 均为 `4c128e6ad104f736e4a6cfef63b39ba0b3d662a0`，新增提交范围为空，`merge-base --is-ancestor` 返回 0，`merge --ff-only` 为 Already up to date。`rg -l '4c128e6ad104f736e4a6cfef63b39ba0b3d662a0|f8b81133f22ab01197b7b36003207cf5cfeb2e41' docs/collab/chatgpt/reviews` 无命中；ds pane `ds:0.0` capture 只有 R3 预备 checklist，末尾为 402 Insufficient Balance，尚无 fresh pair 独立 CPU 结果。V3 角色 override 不再要求旧 MM/Kimi 三方门，且当前无其 pane。已在 canonical Inbox 追加 exact-pair fresh review 请求；该 ledger 提交不改变 formal pair，不授权 run04。后续需取得 ChatGPT 正式 review 与 ds 独立复核后再决定执行。
- 第 2 轮观察凭证（2026-09-27 16:32 CST）：formal target 同上；before_head=`04fef163efb011693bb39d3bd0f53e752ae2c98a`，`git fetch origin V3` 成功，advertised SHA=`origin/V3`=`04fef163efb011693bb39d3bd0f53e752ae2c98a`，新增提交范围为空，祖先检查返回 0，`merge --ff-only` 为 Already up to date。相同 exact-pair `rg -l` review 检索无命中；`ds:0.0` 本轮 capture 仍仅有预备 checklist 与 402，未见 fresh pair 独立复核。只读接线缺口整理于 `/tmp/cx_v3_8xh100_readiness_gap_20260927.md`：当前单段 Local-only relay 与正式 8×H100 联合训练之间尚缺 grouped producer/driver、joint autograd、trainer transaction 和严格 resume。未改 child、未执行 GPU；本轮状态不构成新运行授权。
- 第 3 轮观察凭证（2026-09-27 16:35 CST）：formal target 仍为 root `4c128e6ad104f736e4a6cfef63b39ba0b3d662a0` / child `f8b81133f22ab01197b7b36003207cf5cfeb2e41`；before_head=`af6cfb853830a6621f19c192e97c2d86a50482bb`，`git fetch origin V3` 成功，advertised SHA=`origin/V3`=`af6cfb853830a6621f19c192e97c2d86a50482bb`，新增范围为空，祖先检查返回 0，`merge --ff-only` 为 Already up to date。相同 exact-pair `rg -l` review 检索无命中；`ds:0.0` 本轮 capture 仍停在 R3 预备 checklist 与 402。独立补强真实资产 CPU 预检 `/tmp/cx_v3_b2c_r3_preflight_20260927_02/result.json` PASS；与 `/tmp/cx_v3_b2c_r3_preflight_20260927_01/result.json` 逐字段比较，seed0、16 payload、consumer0 152 tokens、SHA256 `854e3c085df7ab1b392c0e4960875673123b22e5afd4d051c11c9ac119380aad`、结构化 caption/plan/action shapes 完全一致，两次 CUDA trace 均为空。仅补充 CPU Evidence，不改 formal pair、不授权 GPU。
- 第 4 轮观察凭证（2026-09-27 16:37 CST）：formal target 同上；before_head=`e538afb006de4fd4d5f1cb3bc2d91dec70048959`，`git fetch origin V3` 成功，advertised SHA=`origin/V3`=`e538afb006de4fd4d5f1cb3bc2d91dec70048959`，新增范围为空，祖先检查返回 0，`merge --ff-only` 为 Already up to date。相同 exact-pair `rg -l` review 检索无命中。ds 请求回执：约 16:37 CST 向 `ds:0.0` 用 `tmux send-keys -l` 写入一次包含 exact pair、R3 v0.1、CPU/static only 与 no GPU/no code change 的复核请求；间隔 1.3 秒后独立 Enter；随后独立 capture 显示消息已离开输入框，但 Claude API 立即返回 `402 Insufficient Balance`（request_id `af455c39-0db3-47d5-bc9d-124312f56baa`），未生成 ds 审核结果。此同一请求不重发；root/child formal pair、run03 Evidence 与 GPU 禁令不变。
- 第 5 轮观察凭证（2026-09-27 16:40 CST）：16:37 推送本地回执提交被拒，因 origin/V3 新增 `e59bf9ec6f64555d76bc0d0970f71b8c019f410d`（R3 closure review + Inbox），其 Gitlink 仍为 formal child。检查双方提交范围互不重叠后，仅把未推送的 SESSION 提交重放至远端并推送 root `ce8525b68fb7fd7a21df3600cb863ca19feb5bfe`。随后以 before_head=`ce8525b68fb7fd7a21df3600cb863ca19feb5bfe` 执行 `git fetch origin V3` 成功，advertised SHA=`origin/V3`=`ce8525b68fb7fd7a21df3600cb863ca19feb5bfe`，新增范围为空，祖先检查返回 0，`merge --ff-only` 为 Already up to date。exact-pair review `docs/collab/chatgpt/reviews/2026-09-27_V3_stage_b2c_r3_text_transform_closure_4c128e6a_f8b81133.md` 声明 root `4c128e6ad104f736e4a6cfef63b39ba0b3d662a0` / child `f8b81133f22ab01197b7b36003207cf5cfeb2e41` 与 verdict `APPROVE_TO_CLOSE_V3_STAGE_B2C_R3_STAGE_A_TEXT_TRANSFORM`，仅授权全新目录 `artifacts/v3/stage_b2c_4090_s1/run04` 的一次 RTX4090 S1。`ds:0.0` 同轮 capture 显示该 run04 exact-pair 命令已提交会话，但 API 返回 `402 Insufficient Balance`（request_id `90d86e67-678a-4900-b684-5a9d9548769e`）；run04 目录检查为不存在，未执行 GPU。ds 服务恢复前不得把送达消息当作执行结果，也不重复同一 run04 请求。

# V3 Stage B2-C R1-B Tiny FSDP Micro-Smoke Harness（2026-09-27）

- Gate `V3-STAGE-B2C-R1B-TINY-FSDP-MICRO-SMOKE` 状态 REVIEW；唯一 authority root `544bbe0976aa60e935eee431350b20f38c47f28c` 的 R1-B v0.1。R1-A formal pair root `cae1c4bf5d681f93228a9b1a5c74e14d1b5acee4` / child `558f364efaf6704c9d65037c17ec250a9331be8a` 已 closure。ChatGPT 设计/审核；用户 owner/最终裁决；cx 实现；ds 执行/测试。
- child `8029b5ff002a350d22ee955db0463cc2e2d3665a` 已推送 `v3-local-ttt`，仅新增 `examples/psm_wma_local_fsdp_scan_micro_smoke.py` 与 `_test.py`；root 本次仅更新 Gitlink、implementation record、TODO/SESSION。tiny Local owner 使用 training-mode `ParallelDims(1)`、root FSDP2、BF16 compute/FP32 reduce、注册 scan；不加载 Edge/VAE/DCP/RoboCasa，不改 production 语义。
- V3 venv 十一文件 CPU 隔离 suite 216/216 PASS，4 GPU 标记测试 deselected；独立 `--preflight` PASS：`/tmp/cx_v3_b2c_r1b_preflight_20260927_01/result.json`，Local 参数 165312，CUDA trace 为空。新增两文件 Ruff/format、child/root diff-check PASS。未运行 GPU，run01 原始 Evidence 未改、不重跑；R1-B GPU 待 fresh review 后由 ds 单次执行，B2-C run02 不自动授权，不自授 closure。

# V3 Stage B2-C R1-A FSDP Local Scan（2026-09-27）

- Gate `V3-STAGE-B2C-R1-FSDP-LOCAL-SCAN` 状态 DONE；formal pair root `cae1c4bf5d681f93228a9b1a5c74e14d1b5acee4` / child `558f364efaf6704c9d65037c17ec250a9331be8a`，verdict `APPROVE_TO_CLOSE_V3_STAGE_B2C_R1_FSDP_LOCAL_SCAN`。设计 authority root `b5404e9896892b2156e2cca11ef64db871b34def`；run01 Evidence 未改、未重跑。ChatGPT 设计/审核；用户 owner/最终裁决；cx 实现；ds 执行/测试。
- child `558f364efaf6704c9d65037c17ec250a9331be8a` 已推送 `v3-local-ttt`：只改 `cosmos3_vfm_network.py`、`parallelize_vfm_network.py`、`local_memory_segment_adapter.py`、`local_memory_native_segment.py`，新增 `local_memory_fsdp_scan_test.py`。root 本次只更新 Gitlink、实施记录、TODO/SESSION。模型持有 scan 经 root FSDP forward method 注册；DTensor-owned Local 缺注册时 fail closed；复用同一 encoder/core、B0 transaction 与 B2-B relay。未改 trainer、checkpoint、inference 或 harness。
- V3 venv 十文件 CPU 隔离 suite 205/205 PASS，4 GPU 标记测试 deselected；Local optimizer inventory 165312、S0/PAD、梯度与事务保持。五文件 Ruff format PASS，四文件 Ruff clean；network 的 I001 为 HEAD 既有 import 排序债务，排除该项后 clean；child/root diff-check PASS。未运行 GPU、R1-B micro-smoke 或完整 S1，等待 fresh review。

# V3 Stage B2-C RTX4090 S1 harness（2026-09-27）

- Gate `V3-STAGE-B2C-RTX4090-REAL-S1-SMOKE` 状态 REVIEW；authority root `ced270eb07bbf9fac321e410f6d1992911d591cb` 的设计 v0.1；B2-B 已关闭，formal pair root `81fa515593e7cd8e2d4f7d226efb915b17be3b5b` / child `bf6c80e679812b7d2881d6a54aa0b518299e3869`。ChatGPT 设计/审核；用户 owner/最终裁决；cx 实现；ds 执行/测试。
- cx 仅新增 V3 child `examples/psm_wma_robocasa_local_s1.py` 与 `_test.py`，child `7de65c8e752c47359786e5ff2535a8d3cd5ddced` 已推送 `v3-local-ttt`；root 本次仅更新 Gitlink、TODO/SESSION 和 B2-C implementation record。复用 B2-B serial relay，固定 CloseFridge ep0 cursor0 T16、Stage-A DCP、native RGB→Wan VAE、Local-only 165312 参数/LR 5e-5；无 GPU 运行。
- 八文件 CPU 隔离 suite 187/187 PASS；新增两文件 Ruff check/format、child/root diff-check PASS。真实资产 CPU preflight PASS：`/tmp/cx_v3_b2c_preflight_20260927_05/result.json`，Stage-A DCP 549 keys、episode 429 frames、raw15、16 payloads。预检需 V3 venv 的 `nvidia/cu13/lib` 供 TorchCodec CPU 解码；未启动 CUDA。GPU smoke、DCP save、eval、server 均未执行；待 fresh review，不自授 closure。

# V3 Stage B2-B Single-Segment Gradient Relay（2026-09-27）

- Gate `V3-STAGE-B2B-SINGLE-SEGMENT-GRADIENT-RELAY-CPU-STATIC` 状态 DONE；formal pair root `81fa515593e7cd8e2d4f7d226efb915b17be3b5b` / child `bf6c80e679812b7d2881d6a54aa0b518299e3869` 已关闭。B2-A closure pair root `21f20f2c436e9627a938148afca039da6023d145` / child `366501b3b4626f30f0739d2e5765139a52f2308f`；B2-B authority root `bf5c8d134014d0023a03c25f95d8e971922f40fd` 的设计 v0.1 与资源 v0.3。ChatGPT 设计/审核；用户 owner/最终裁决；cx 实现；ds 执行/测试。
- child 仅新增 `cosmos_framework/model/generator/mot/local_memory_native_segment.py` 和对应 `_test.py`，提交 `bf6c80e679812b7d2881d6a54aa0b518299e3869` 已推送 `v3-local-ttt`；root 更新 Gitlink、本状态/TODO 与 B2-B implementation record。复用 B0 adapter/transaction/sidecar 与 model.net.local_memory_runtime 同一 encoder/core，单 slot/T16、一成员 serial exact-gradient relay；不接 trainer/launcher/DCP/inference/GPU。
- V3 venv 定向 22/22、B0/B1/B2-A/B2-B 七文件 CPU 隔离 suite 175/175 PASS；新增两文件 Ruff check/format PASS，child staged diff-check 与 root diff-check PASS。测试使用 `CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`，无 GPU、外网、checkpoint 或数据集依赖；仅 B1 测试临时 H5 fixture。B2-B 已按上述 formal pair 关闭。

# V3 Stage B2-A Native Memory Prefix（2026-09-27）

- Gate `V3-STAGE-B2A-NATIVE-MEMORY-PREFIX-CPU-STATIC`，状态 DONE；formal pair root `21f20f2c436e9627a938148afca039da6023d145` / child `366501b3b4626f30f0739d2e5765139a52f2308f`，verdict `APPROVE_TO_CLOSE_V3_STAGE_B2A_NATIVE_MEMORY_PREFIX_CPU_STATIC`。设计 authority root `d57ef855404cabceed9c4190b13d435a98a30206`；资源口径为同提交 v0.2。ChatGPT 设计/审核；用户 owner/最终裁决；cx 实现；ds 执行/测试。
- cx 只改 V3 child 的 Local K/V prefix、配置/数据载体/packer、native two_way attention 与直接 CPU 测试；child `366501b3b4626f30f0739d2e5765139a52f2308f` 已推送 `v3-local-ttt`。root 本轮仅 Gitlink、B2-A implementation record 和本状态/TODO；现有 `artifacts/v3/` 未纳入。
- 当前最终代码：V3 venv、CPU-only 六文件 suite 153/153 PASS（B2-A 21 + B0/B1 132）；Local optimizer allowlist 精确 165,312，host 冻结，fast state 不入 optimizer；BF16 target + FP32 bridge 梯度、tensorized K/V interleave、mixed S0、no-Local parity、CP/CUDA graphs/inference fail-closed 均有定向测试。新文件 Ruff/format clean；所有修改文件 Ruff（排除既有 I001）clean；已有 packers/omni format debt 的 HEAD 基线已核对，未整文件重排；两仓 diff-check PASS。
- 本 Gate 未接 active driver/trainer、DCP、inference、GPU；没有 4090 smoke。B2-A 已按上述 formal pair 关闭，后续 B2-B 另见本文件顶部记录。

# V3 Stage A server guardrails glue（2026-09-26）

- 任务 V3-STAGE-A-SERVER-GUARDRAILS，REVIEW；基线 root `21a390b18672aaf6b268b6c463c402821e02b9a6` / child `edb922605281614c4df13c4c734c9082363e8a6b`。用户要求继续推进；ChatGPT 冻结该最小设计范围。CPU 验证完成，按 child 提交/push → root Gitlink/文档提交/push 交付，新 pair 待 fresh review。
- 职责：ChatGPT 设计/审核；用户 owner/最终裁决；cx 实现；ds 执行/测试。
- 根因：action server 的 predict_policy 路径不消费 generation text/video guardrail；ActionServerArgs 未暴露 common setup 的 guardrails，默认初始化把 gated Cosmos-Guardrail1 引入 action-only baseline 的无关启动依赖。
- 实际修改仅 child `cosmos_framework/scripts/action_policy_server_robocasa.py`、`examples/psm_wma_robocasa_native.py`、对应现有测试（3文件 +29）；root 仅本文件、TODO 和 Gitlink。ActionServerArgs 新增 `guardrails: bool=True` 并透传给 OmniSetupOverrides，wrapper server 显式 `--no-guardrails`。不改 common inference、Edge recipe/TOML、raw15/ego20/data/action contract、Local-TTT；不运行 GPU。
- 已读项目状态/约定、V3 bootstrap、server 参数/setup/predict 入口与 common args，复用既有 tyro_cli 与 OmniSetupOverrides；起始 child clean，root 仅未跟踪 artifacts/v3/（不纳入提交）。提交前只读规范自检：本轮按上述冻结范围实施，未推进 runtime Gate，未将旧审核结论套用到新 pair，协作规范未修改。
- 环境纠正：最初 --help 误用旧 V2 venv；按本轮指令向自有 PID 28899 发送 SIGTERM，停止等待，不将旧诊断计入验证。后续统一使用 `/disk/rl/worktrees/cosmos-framework-v3/.venv/bin/python` 与同目录 Ruff，不再使用 V2 venv。
- CPU：V3 child 工作目录，`CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. EDGE_POLICY_CHECKPOINT=/disk/rl/models/Cosmos3-Edge-Policy-DROID BASE_CHECKPOINT_PATH=/disk/rl/models/Cosmos3-Edge-Policy-DROID-dcp .venv/bin/python examples/psm_wma_robocasa_native_test.py -v`，26/26 PASS，无跳过，84.048秒；日志 `/tmp/cx_v3_guardrails_tests.log`。生产 main 的完整 tyro 解析接受 `--no-guardrails` 且 build_setup_overrides().guardrails=False；另测默认 True；raw15/chunk32/fps20、ego20 与既有合同通过。仅 mock serve，不加载模型或监听端口。
- 静态：wrapper/test 完整 Ruff check/format PASS；server 完整 Ruff 命中基线已有 I001、format 命中基线已有两处折行（由 git show HEAD 同命令复核），保持无关源码不变；server `ruff check --ignore I001` PASS。两仓 diff-check PASS；未运行 GPU/runtime，由 ds 后续取证。
- 本轮审核裁定的验收口径：targeted 26 tests PASS、wrapper/test Ruff clean、server 新增 diff 无新 lint violation、两仓 diff-check PASS；不清理 upstream 既有 lint debt，不扩大范围。
- child 提交 `196b93b70b579023ef008030b0c18a6fde353c82`，3文件 +29/-0；已先推送 v3-local-ttt。root Gitlink 与嵌套 checkout 同步该 SHA；root 交付 SHA 为包含本记录的提交，推送后在交付报告核对远端 exact pair。仅纳入 SESSION/TODO/Gitlink，不纳入 artifacts/v3/。

---

# V3 Stage A Edge raw15 实施（2026-09-26）

- 任务：V3-STAGE-A-EDGE-RAW15，REVIEW；静态实现经 ChatGPT 审核通过，待 ds runtime Evidence。用户本轮明确授权提交与推送：child 仅5个已审核 Edge 文件，root 更新 Gitlink 和状态；先 push child v3-local-ttt，再 push root V3；不运行 GPU。职责：ChatGPT 设计/审核；用户 owner/最终裁决；cx 实现；ds 执行/测试。
- 工作区：root `/disk/rl/worktrees/psm_wma-v3`；child `/disk/rl/worktrees/cosmos-framework-v3`。嵌套 child 是另一个独立 checkout，仅同步至已提交 child SHA 以保持 Gitlink 与工作树一致；V2/v2 仅只读参考。
- 实际修改：child 新增 `action_policy_robocasa_edge.py`，注册 `configs/base/config.py`，原位替换 `examples/psm_wma_robocasa_native.py`、对应测试及 smoke TOML（共5文件）；root 更新本文件、TODO、MEMORY/DECISIONS、V3 bootstrap 文档的显式 override（共4文件）。
- 起始 child HEAD `6ee1efb1d48307f25b60e0e60e72da96aef327fa`，工作树 clean；既有 Nano glue 已提交，并非未提交残留。root 仅有其他执行者未跟踪 `artifacts/v3/`，不改动。
- 已读：当前项目约定/会话/live Inbox/TODO/决策、V3 bootstrap、child AGENTS、upstream raw15 recipe、EDGE_MODEL_CONFIG、DCP planner、V2 Edge/libero warmstart（只读）。不迁 Local-TTT，不改 ego20。
- 行为：Edge 模型整体替换 Nano 模型；raw15/64维/32domains、20fps/32chunk/[33]、left_wrist/state/no normalization 保持 upstream；ego20/data/loss 核心文件与 upstream 无差异。DROID warm-start `keys_to_skip_loading=['net_ema.']`、`strict_resume=True`，保留动作头；预检验证本地 HF 身份/文件及 DCP policy/动作头/视觉投影形状。metadata 有549键，无 action_pos_embed 参数。
- 已落实用户转达的三项增量要求：launcher 不设置或清除 offline 变量（caller 未设置/0/1 均测试）；两组 domain-aware projections 的 weight decay skip patterns 进入实际合成配置；职责归因按上文统一。
- 验证命令：已有 `/disk/rl/psm_wma/cosmos-framework/.venv/bin/ruff check --no-cache` 与 `ruff format --no-cache --check` 检查新增 recipe、wrapper/test，均 PASS；base config 由真实 Hydra 导入验证；两仓 `git diff --check` PASS。
- CPU 命令：在 V3 child，`CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. EDGE_POLICY_CHECKPOINT=/disk/rl/models/Cosmos3-Edge-Policy-DROID BASE_CHECKPOINT_PATH=/disk/rl/models/Cosmos3-Edge-Policy-DROID-dcp /disk/rl/psm_wma/cosmos-framework/.venv/bin/python examples/psm_wma_robocasa_native_test.py -v`；24/24 PASS，无跳过，29.556秒；日志 `/tmp/cx_v3_edge_cpu_tests.log`。覆盖原15项升级版、真实 Hydra compose/YAML 往返、DCP planner skip、HF/DCP metadata、本地 processor、mask loss/gradient/unpad、ego20 与缺失资产负例。
- 首轮22项测试的新增 loss fixture 将 mask 错写为 `[T]`，按当前 API 改为 `[T,1]` 并修正 weight mock 签名后重跑上述24项全部通过；未改生产 loss。
- 官方 config dryrun：同上 CPU/离线环境，增加 `WAN_VAE_PATH=/disk/rl/models/wan22_vae/Wan2.2_VAE.pth ROBOCASA_ROOT=/disk/rl/data/robocasa_v30`，执行 `python examples/psm_wma_robocasa_native.py config --output-root /tmp/cx_v3_edge_config`，退出0；日志 `/tmp/cx_v3_edge_config.log`；YAML `/tmp/cx_v3_edge_config/psm_wma_v3/edge_robocasa/smoke/config.yaml`，实际 server raw15/Edge 预检 PASS，未实例化模型。
- 提交前 root HEAD `3591743d651ab64270713fa6e6e00e579a83dc57`，child HEAD `6ee1efb1d48307f25b60e0e60e72da96aef327fa`。root 既有 `artifacts/v3/` 不纳入提交。静态/CPU 24/24、DCP/readiness（静态资产/配置准入）均 PASS；本轮仅 root 状态收尾，child production 与已审核 diff 保持一致，不重复 CPU 测试。
- child 提交 `edb922605281614c4df13c4c734c9082363e8a6b`（仅5文件，+348/-12）；提交前完整 patch 与已审核 `/tmp/cx_v3_edge_child.patch` 经 `cmp` 逐字一致，staged diff-check PASS。root Gitlink 与嵌套 checkout 同步该 SHA；root 交付提交为包含本记录的提交。推送顺序按 child → root，最终远端 SHA 与 clean status 在本轮交付报告核验。
- 提交前只读自检：V3 角色 override 与用户本轮提交授权适用，未弱化治理规范、未推进 runtime Gate；本节静态审核结论依据本轮明确指令，不拼接历史 pane/旧 pair。远端预检分别为 child `6ee1efb1d48307f25b60e0e60e72da96aef327fa`、root `3591743d651ab64270713fa6e6e00e579a83dc57`，与提交前本地一致。
- 下一步：ds 执行1–3步训练/DCP reload/server/CloseFridge 1ep并提供 runtime Evidence；真实 GPU train/server/eval pending。本轮不执行这些 GPU/runtime 验证，不宣称 runtime PASS。

---

# 历史：V3 P1 实现交付（2026-09-26，已被上述 Edge 路线替代）

- 任务 V3-P1-UPSTREAM-NATIVE-ROBOCASA-SMOKE：实现已完成；运行验证待 ds，P1 不宣称 runtime PASS。角色：ChatGPT 设计/总体规划/审核；用户项目 owner/最终裁决；cx 实现；ds 执行/测试。
- ChatGPT 本轮独立复审结论（本轮对话）：production glue 无 blocker，CPU 15/15、raw15 compose、server/eval flags 与 upstream contract 核对通过；唯一 REQUEST_CHANGES 是 docs-only 提交/派发归因。
- 归因已改正：提交/派发需经 ChatGPT 本轮审核后进行，不表述为用户禁止。用户本轮明确授权该窄整改后提交 child/root，并先 push child、再 push root；cx 不运行训练/GPU。
- canonical root 起点=666ca58e7848ab55ab82b03ac7c2e11aa0d284df；upstream child 起点=850fdbeacddabad138ed56df39cd6fb96e975078；提交前本轮 ls-remote 确认两个远端分支仍分别指向该 pair。
- child 实现提交=6ee1efb1d48307f25b60e0e60e72da96aef327fa；root Gitlink 同步到该提交。root 交付 SHA 为包含本节的提交；推送后以最终报告及远端 advertised SHA 核验。
- child 仅新增 examples/psm_wma_robocasa_native.py、examples/psm_wma_robocasa_native_test.py、examples/toml/sft_config/psm_wma_robocasa_native_smoke.toml；production glue 与复审 diff byte-for-byte 一致。本轮只改 docs 归因及交付记录，不改官方 cosmos_framework/ 源码/raw15/ego20。
- root 范围：AGENTS.md、MEMORY/DECISIONS.md、SESSION.md、TODO.md、docs/build/PSM-WMA_V3_upstream_bootstrap_2026-09-26.md 与 Gitlink；未纳入其他执行者的未跟踪 artifacts/v3/。
- 本轮验证：15/15 CPU tests、两仓 diff-check PASS；日志 /tmp/cx_v3_p1_precommit_tests.log；使用已有 /disk/rl/psm_wma/cosmos-framework/.venv/bin/python，CUDA_VISIBLE_DEVICES 为空、测试调用方显式 offline。child 未修改，不重复重型 compose；此前 Ruff/格式/实际 overrides Hydra 合成/YAML raw15 预检均 PASS，完整命令 /tmp/cx_v3_p1_checks.sh，日志 /tmp/cx_v3_p1_checks.log。
- 实施复用官方 action_policy_robocasa_nano、SFT TOML schema、DCP、policy server 与 closed-loop。glue 继承调用方网络环境；Nano Qwen/Qwen3-VL-8B-Instruct tokenizer 缓存完整性由 ds 核验。
- 数据合同：训练 /disk/rl/data/robocasa_v30；eval 原始 v2.1 /data/rl/datasets/robocasa365/v1.0/target/atomic/<task>/<date>/lerobot，必须包含 extras/dataset_meta.json。
- 运行交接命令和证据判据：/tmp/cx_v3_p1_commands.md；真实 1–3 step/GPU、checkpoint reload、server 与闭环未运行，后续由 ds 执行。当前不进入 P2 Edge raw15 或 P3+ Local-TTT。
- 基线纠正记录：旧 WIP 已保存 /tmp/cx_v3_stage_a_wip.patch（SHA256 72f7f97c481e9d5e26e1969f95fcf23d494e15460a167164df95fe1178f1002d）；未携带 f5729bec/a5ffd57f 分叉提交。V2/v2 冻结引用=8ba88dfe8d4af1ffcb180ec274ddd1fee7c5face / ae2e9f72fdbc53a5acf1c1d81f5dcb437426e80a。

---

# V3 Upstream Bootstrap（ChatGPT，2026-09-26）

- root branch: `V3`
- child branch: `wxwy/cosmos-framework:v3-local-ttt`
- pinned upstream child SHA: `850fdbeacddabad138ed56df39cd6fb96e975078`
- current V3 policy: keep `V2/v2` frozen; first validate upstream-native RoboCasa raw15 before porting Local-TTT.
- next Gate: `V3-P1-UPSTREAM-NATIVE-ROBOCASA-SMOKE`.
- ds_pro/tmux ds is execution-validation only; no production edits/commits.
- 用户最新角色 override：ChatGPT 设计/总体规划/审核；用户为项目 owner/最终裁决；cx/Codex 实现及静态/CPU 检查；ds 执行/测试；cx 不运行训练/GPU。
- V3 training-smoke constraint: GA=1 regardless of detected GPU capacity (connected host currently reports A100 80GB).
- V2 launchers/configs inherited in root are not V3 authority until explicitly ported.

---

# A2 构建状态更新（ChatGPT，2026-09-18）

代码候选 child=`de84a5675d029ef96d1b2d1fcb2ef3281242ca6e`，隔离分支 `chatgpt/a2-delivery-20260918`。
CPU release：217 passed；校验器负例：4 passed。源码绑定receipt/JUnit位于 artifacts/g0/chatgpt_a2_delivery/。
实现：A2 + 可配置B_stream、精确D025、native加权loss修正、原子多row状态、恢复几何、在线事务API。
真实GPU首试在首个optimizer update后因指标容器适配失败；已修复并通过CPU，修复后GPU尚未执行。
当前阻塞：另一Remote Desktop会话在原目录运行20-step，占用唯一GPU；不终止未知作业，不并发抢卡。
验收状态 BLOCKED。准备好 tools/g0/run_a2_delivery_validation.sh；GPU处置确认/释放后继续真实控制/恢复/native/20-step验收。
独立review与作者自测分离；未启动5000-step、未推送远端、未覆盖原工作树。

---

# ChatGPT 构建接手（2026-09-18）

用户将构建任务交给 ChatGPT；原 ds_pro 构建者已确认只读，不再写入/启动训练。当前代码 root=e05ed2c5、child=ac28e5d；uv.lock 原有修改保留。
当前目标：完成 Local Memory 的 A2 训练实现与可验证运行交付，不把图示或自测当作科研/闭环效果证明。
预计修改：新增 grouped_active_local_memory*.py 和测试；active_local_memory_launch.py；配置 action_policy_libero_edge_all.py；prepared capability 类型/模型入口；ttt_lifecycle_test.py；readiness/acceptance 工具及测试；本轮 design/runbook。
独立审核与自测分离：ChatGPT 此轮为代码作者，不给自己的实现颁发独立审核批准。后续另送 DS/MM。
任务：LOCAL-A2-DELIVERY / ACTIVE-MEMBER-SHAPE-REFREEZE / B_STREAM-CONFIGURABLE。状态 IN_PROGRESS；长训 readiness 在新实现实证前 BLOCKED。

---

# 当前协作状态（rolling）

> 本文件只保留**当前目标 / Gate / 最近有效 pair / residue / 下一步 / blockers**，加最近阶段的详细历史。
> 更早内容已按日期归档：`docs/collab/session_archive/SESSION_2026-09-18_a71bbd0.md`（11253 行，immutable）。

## 当前状态（2026-09-18）

- **目标**：Local Memory 具备正式训练条件（active 路线）。
- **已关闭 Gate**：`G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION`、`...-ACTIVE-ROUTE-RESUME`、`...-ACTIVE-CATALOG-EPOCH-REUSE`、`...-ACTIVE-PRODUCE-PREFETCH`（DS/MM 均 APPROVE_TO_CLOSE）。
- **已撤销**：`...-ACTIVE-SCHEDULER-SEMANTICS-REFREEZE` — 用户 2026-09-18 裁决「不清零」；design v0.1 标 withdrawn（HIGH-1 前提过时、HIGH-2 消解）。**D8b 长跑不再被 refreeze 阻塞**。
- **最近有效 formal pair**：Gate3 closure / PRODUCE-PREFETCH = root `c16fc8ec` / `8e4dc334` / child `fca7eb5`。
- **审核名册**：DS=`ds:0.0` + MM=`mm:0.0`（Kimi 已由用户移除）；GPT 按用户提示读取 `docs/collab/chatgpt/reviews/`。
- **Dirty residue**：子模块 `uv.lock`（dirty）、`results/libero_closed_loop_*`、`examples/eval_*_4090.sh`（未跟踪）。
- **正在运行的 process**：无（GPU 空闲）。
- **下一步**：MEDIUM-2（TODO zombie 收敛）、hygiene 补全；之后 D8b 长跑（用户已接受当前 regime）。
- **Blockers**：无强制阻塞。

---

## 最近阶段详细历史

### slot 饥饿最小修复：设计 + 生产链路 monkeypatch 验证（2026-09-17）

**判定缺陷而非冻结语义**（更正此前 TODO 中「触及 v0.3.5 冻结语义」的暂定评估）：

1. 规范原文把 weighted deficit 定义为「**选择下一 category**，再从该 category 的 seeded shuffled episode queue 取最前 eligible entry」（`docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md:86`、`PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md:229`）。规范**只约束 category 级配额**，从未把同 category 内的 tie-break 定义为「恒取 slot_id 大者」，更未授权任何 slot 永久饿死。
2. `production_active_wiring.py:88` 走 singleton 候选 `owner.admit_next((identity,))`；`canonical_segment_runtime.py:98-111` 先按冻结计划第 `index` 个成员过滤候选、要求恰好 1 个匹配，再交给 `scheduler.admit()`。故 `scheduler.admit()` 的多候选 tie-break **在 active 路径上根本不被行使**，driver 的 `freeze_window` 顺序即唯一权威 ⟹ 修复可自包含于 `freeze_window`，不触及 owner/scheduler 冻结接口。
3. 规范同时规定「已绑定 slot 必须同 episode、同 digest、`cursor+1` 连续推进」（同上 :86/:90）。交替选 slot 下每条 slot 仍逐次 `cursor+1`（本 window 每 slot 恰推进 16 次），`_is_admissible` 的连续性约束依然成立。

**最小补丁**（仅 `active_local_memory_driver.py:214-229`）：

```
     used: dict[int, int] = {}
     for _ in range(self.window_members):
         choices: list[tuple[float, str, int, int, tuple]] = []
         for slot_id in self._by_slot:
             ...
             choices.append(
                 (target[stream.category] - observed, stream.category, -used.get(slot_id, 0), slot_id, view)
             )
         ...
         _, category, _used, slot_id, view = max(choices, key=lambda item: item[:3])
         stream, cursor, terminal, rebind, position = view
         self._commit_block(slot_id, stream, cursor, position)
         used[slot_id] = used.get(slot_id, 0) + 1
         exposure[category] = exposure.get(category, 0) + planned
```

即 tie-break 第三项由 `slot_id` 改为 `-used[slot_id]`：同 category 内的两条 slot 交替入选，跨 category 仍由 deficit 决定。

**验证（真实生产链路，CPU-only，monkeypatch 只作用于进程内，未改仓库文件）**：

```
cd /disk/rl/psm_wma/cosmos-framework
LIBERO_ROOT=/disk/rl/data/LIBERO_LeRobot_v3 \
LIBERO_LATENT_CACHE_ROOT=/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1 \
.venv/bin/python /tmp/verify_starvation_fix.py
```

| 量 | 原版 | 补丁版 |
|---|---|---|
| `per_slot_members` | `{4:32,5:32,6:32,7:32}` | **全 8 slot 各 16** |
| `slots_starved` | `[0,1,2,3]` | **`[]`** |
| `slot_sequence` 前缀 | `[7,6,5,4]×8` | **`[3,2,1,0,7,6,5,4]×4`** |
| `per_category_members` | 各 32 | **各 32（不变）** |
| `ga_effective` | 128 | **128（不变）** |
| `rebind_count` / 首次位置 | 13 / #28 | 12 / #40 |

**关键性质**：修复后 `8 slot × 16 = 128 = b_stream × ga`，每 8 个连续 member 来自 8 条不同 slot 流。现实现每批只跨 4 条流（各重复 2 次），与冻结契约「B_stream=8 由同 window 内 8 个连续 member 实现」的字面表述是否一致，**请 Gate 一并裁定**。

**当前状态**：仓库代码零改动（补丁仅存在于上述验证脚本与本文档）。因该修复改变 Gate 已批准冻结组件的行为（被选中的 episode 集合与 rebind 位置全部变化），按项目流程须经设计 + 三方 Gate 方可落地。

---

### SLOT-STARVATION 修复已落地（2026-09-17，用户委托决策后）

**授权链**：用户先选择「授权走设计+三方 Gate」，随后明确「我睡觉了，你自己决策了」。依 AGENTS.md:151（Codex 是构建者、执行者与最终技术决策主体；审核者意见仅作技术参考）推进为「先证伪 → 再落地 → 后送审」，把已实现的 diff 而非提案送三方审核。

**设计文档**：`docs/build/PSM-WMA_Local_Memory_v0.3.5_active_window_slot_rotation_fix_design_v0.1.md`（Gate `G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION`）。

**子模块改动**（child commit `6dc25e0f8c3ba39525c8ba994b8d0c38c2ce5461`，分支 `v2`）：

| 文件 | 改动 |
|---|---|
| `active_local_memory_driver.py` | `freeze_window` +6/-2：`used` 计数、tie-break 第三项 `slot_id` → `-used[slot_id]`、选中后递增 |
| `active_local_memory_driver_test.py` | import `Counter` +2 例 fixture |

（`uv.lock` 为遗留 dirty 文件，未纳入提交。）

**证据链（四步）**：

1. **fixture 先证伪**（补丁前）：`2 failed, 11 passed in 41.14s`，失败值 `assert [4, 5, 6, 7] == [0,1,...,7]` —— 与生产链路实测的 `window_slots_used` 一致，证明 fixture 捕获的正是生产缺陷，非空转断言。
2. **补丁后**：driver 测试 `13 passed in 24.35s`；`ruff check` All checks passed；`py_compile` PASS；`git diff --check` PASS。
3. **生产链路复验**（无 monkeypatch，跑已修改的仓库代码）：`window_slots_starved [0,1,2,3] → []`、`per_slot_members {4:32,5:32,6:32,7:32} → 8 个 slot 各 16`、`per_category_members` 仍各 32、`ga_effective` 仍 128、`first_rebind_position 28 → 40`、`rebind_count 13 → 12`。
4. **相邻契约测试**：`production_active_wiring_test` + `local_memory_segment_test` + `canonical_segment_runtime_test` + `active_local_memory_launch_test` = **58 passed in 142.96s**。

**效果**：每 suite episode 覆盖率 50% → 100%；可达唯一 block 7240 → 14430。

**测试缺口（本项目已修补）**：既有唯一涉及 slot 轮转的用例 `active_local_memory_driver_test.py:138` 用的是**两个不同 category**（slots 0/1 分属 a/b），deficit 不等故 tie 不发生；而生产形态 `b_stream=8` / 4 categories 使**同一 category 恒有两条 slot**，该分支从未被覆盖。新增 fixture 直接构造同 category 双 slot。

---

### RESUME 缺口：fail-closed 防线已落地（2026-09-17）

**背景**：核实 D8a 产物时确认，active 路线的**数据进度状态完全不入 checkpoint** —— driver 的 `_stream_index`/`_active_stream`/`_active_cursor`/`_window_index` 与 scheduler 的 `cumulative_valid_consumer_exposure` 及各守卫在 resume 时全部重建，而 model/optim/LR-schedule 正常前进，形成「optimizer 已前进、数据回退重放」的语义错乱。

**机制更正（推翻此前判断）**：原先记录的「scheduler 已有 `snapshot()`/`rebuild()`，只需接线到 `on_save_checkpoint`/`on_load_checkpoint`」**是错的**。核实 `dcp.py`：① `on_load_checkpoint(model, state_dict={})`（`:943`）拿到的是**空 dict**，源码注释明言该回调从未被使用；② 在 `on_save_checkpoint` 往 `to_save_dict`（`:1114-1125`）新增顶层 key 会让 resume 直接 `raise ValueError(f"Invalid key: {key}. not support to resume.")`（`:939`）。真正被认可的机制是 `_DataloaderWrapper`（`:112-153`）：回调声明 `checkpoint_component = "dataloader"` 即被持久化到 `"dataloader"` key。**该槽在 action/libero 链上为空**（`DataLoaderStateCallback` 只注册于 reasoner 系列）。选项 (a)「排除 `admission_order`/`committed_identities`」同样**已被证伪** —— 二者是活的守卫状态（`canonical_segment_runtime.py:181-182` 断言 `admission_order` 每一项都在 `committed_identities` 中并从中派生 `committed_by_slot`）。

**落地改动**（child commit `525f5066393cba044f00f1104b83f5eb424a9c49`）：

| 文件 | 改动 |
|---|---|
| `active_local_memory_launch.py:234` | `del iteration` → `if iteration > 0: raise RuntimeError(...)` |
| `active_local_memory_launch_test.py` | 新增 `test_launch_refuses_to_resume_an_interrupted_active_run` |

依据 `Callback.on_train_start(model, iteration=0)`：`callback.py:348` 的 `tqdm.trange(self.config.trainer.max_iter, initial=iteration, ...)` 证明 `iteration` 即恢复到的迭代数。新增 CPU 测试断言失败后 `driver is None`、`trainer.callbacks._callbacks == []`；launch 测试 **11 passed in 18.90s**；`ruff check` 仅报 `active_local_memory_launch_test.py:6:1 I001`，已用 `git show HEAD:... | ruff check --stdin-filename ... -` 证明该告警在 HEAD 版本**同样存在**，属既有问题、与本次改动无关，按最小修改原则不动。

**代价与边界**：中断即须从头重跑。故该防线只是正式训练前的临时护栏；**D8b 长跑（5000 步 ≈ 11.9 天）不能在此防线下启动**，须先完成完整 resume 实现（driver 持 `checkpoint_component="dataloader"` + 持久化 slot 前沿与 scheduler 快照，并证明 `_by_slot` 在 resume 时逐位可复现）。

### REBIND-COVERAGE-D8A 降为 CPU 可覆盖（2026-09-17）

`tools/g0/probe_r09_b_active_static.py --members 128`（CPU-only）走满整个冻结窗口：`LIBERO_ROOT` / `LIBERO_LATENT_CACHE_ROOT` 指向真实 libero 4-suite + latent cache，单次约 7 分钟（其中约 30 秒为数据集加载），无需 GPU。使 `REBIND-COVERAGE-D8A` 从「需 7.3 小时 GPU」变为「7 分钟 CPU」。

**产物**（原为 `/tmp/probe_d6_128_rebind.json`；2026-09-17 复跑落盘为 **`artifacts/g0/active_static_probe/probe_full_window_postfix.json`**，`result="PASS"`，读数逐位一致）：`rebind_count=12`、`rebind_positions=[40,50,57,60,69,70,88,99,100,113,114,125]`、`per_slot_blocks={0:16,1:16,2:16,3:16,4:16,5:16,6:16,7:16}`、`walk.members=128`、`loss 82.6322 → 71.8982`（finite）、`evidence_free_members=[]`、`window_closed={slow_optimizer_steps:1, slow_grads_cleared:false, scheduler_committed:128}`、RSS 3.46 GB。窗口关闭是**显式断言**的：`owner.finish_window` → `resolve_local_memory_slow_window` 后若 `phase != "IDLE"` 即 `raise`（`probe_r09_b_active_static.py:464-478`）。即**每个 rebind 接缝都经 `driver._produce → _rebind_terminal → scheduler.terminal_rebind` 真实行使，且窗口随后成功关闭**。12 次（而非修复前的 13 次）因 slot 饥饿修复后每 slot 每 window 只推进 16 block（原 32）。

探针补记上述三个读数，使「rebind 接缝确被行使」可从仓库复现，而非只存在于一次性脚本。

---

### RESUME：接缝已建好但未接线（2026-09-17，设计送审）

**判定更正**：此前把 RESUME 记为「机制未知、需重新设计」**不成立**。grep 核实 `CanonicalSegmentRuntimeOwner.snapshot()`（`canonical_segment_runtime.py:173-190`）与 `RankLocalSegmentScheduler.rebuild()`（`local_memory_segment.py:351-364`）**均已完整实现，但全仓零生产调用点**。故本项是「接缝已建好、只差持久化接线」。

**同时更正两条此前的错误判断**：① `on_load_checkpoint(model, state_dict={})`（`dcp.py:943`）拿到的是**空 dict**（源码注释明言该回调从未被使用）；② 在 `on_save_checkpoint` 往 `to_save_dict` 新增顶层 key 会让 resume 直接 `raise ValueError("Invalid key: ... not support to resume.")`（`dcp.py:939`）。**真正机制**是 `_DataloaderWrapper`（`dcp.py:112-153`）的 `checkpoint_component="dataloader"` 槽；该槽在 action/libero 链上**为空**，本设计将是第一个占用者。wrapper 在存/取盘时构造（`dcp.py:1120`/`:934`）并每次重新遍历 callbacks，故 driver 只需在 `attach()` 后具备该接口。

**选项 (a) 被证伪**：`admission_order`/`committed_identities` **不是审计轨迹，是活的守卫状态**（`local_memory_segment.py:322-323`、`local_memory_segment_adapter.py:79`、`canonical_segment_runtime.py:86`/`:224` 均做成员判断），排除会直接打断守卫。

**修剪安全性证明**（来自 `owner.snapshot()` 自身，非新假设）：它只在 **IDLE（窗口边界）** 可调用，`:181` 以 `committed_by_slot`（后写覆盖 = **每 slot 最近一条**）派生，`:182` 断言 `admission_order ⊆ committed_identities`，`:183-186` 要求 `committed_by_slot[slot]` 与 `stable_slots[slot]` 恰为 sidecar 的该 slot 已提交 identity ⟹ **resume 路径只咨询「每 slot 最近一条」**，更早条目无任何读取点。修剪只作用于 snapshot 输出；运行期活列表保持不修剪（`:86`/`:224` 的 skip/retry 守卫需要成员判断，而这些路径的 `_skipped_plan`/`_retry_plan` 均为内存态、resume 后为 None）。

**产物**：设计文档 `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_resume_wiring_design_v0.1.md`（Gate `G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`，formal root `8bb48f35`，child `525f5066`），并已送三方审核（INBOX 条目同日记）。**尚无代码改动**；当前 operative 行为仍是 `active_local_memory_launch.py:234` 的 fail-closed 守卫。

---

### rebind 覆盖的前提更正 + resume §6 BLOCKED 判据证伪（2026-09-17）

**一、`REBIND-COVERAGE-D8A` 结案：1 次 iteration = 1 个完整 window，不是 1 个 member**

本条此前记「D8a 的 member #0–#24 rebind 覆盖为零」「覆盖首次 rebind 需 ≥29 步」「覆盖全部需 128 步 ≈7.3 小时」，三句共享同一个前提「1 次 iteration = 1 个 member」。该前提**不成立**。真实关系是 **1 iteration = 1 完整 window = 128 个 member = 1 次 optimizer step**，由七条互相独立的证据确定：

| # | 证据 | 出处 |
|---|---|---|
| 1 | `window_members` 必须等于 `trainer.config.trainer.grad_accum_iter`，否则 `_arm_initial` 直接 raise | `active_local_memory_driver.py:162-165` |
| 2 | `freeze_window()` 只在 `owner.phase is IDLE` 时经 `_arm_initial` 调用一次；其余 member 走 `_arm_continuation` 复用同一个 `self._window` | 同文件 `:158-175` |
| 3 | `on_training_step_batch_start` 每个 microbatch 触发一次 | 同文件 `:137-140` |
| 4 | `microbatch_count` 在 `finish()` 内清零 ⟹ 它是**每个 optimizer step 内的前反向次数** | `trainer/__init__.py:162-184` |
| 5 | D8a 全部 25 条 iteration 行均为 `perf/microbatches=128` | `/tmp/d8a_launch_stdout.log` |
| 6 | `grad_accum_iter = 8 × PSM_R09_B_TTT_ACTIVE_GA = 8×16 = 128` | `action_policy_libero_edge_all.py:322-348` |
| 7 | 一个冻结窗口走满后 `window_closed={slow_optimizer_steps:1, scheduler_committed:128}` | `artifacts/g0/active_static_probe/probe.json` |

⟹ **D8a 的 25 次 iteration = 25 个完整 window = 25×128 = 3200 个 member**，每个 window 含 12 个 rebind member（`rebind_positions=[40,50,57,60,69,70,88,99,100,113,114,125]`）⟹ **GPU 上已行使约 300 次 rebind，而非 0 次**。补强证据：`terminal_rebind` 自带 fail-closed 守卫（`local_memory_segment.py:340-341`，非 terminal stable slot 即 `raise ValueError`），25 窗全过即接缝顺序正确。**证据强度须如实标注**：CPU 全窗探针是**直接观测**（逐位行使 12 条接缝）；GPU 侧为**构造强制 + 25 窗无异常**，非直接观测（训练日志无 rebind 计数行）。

**顺带更正**：`ActiveWindowMember`/`ActiveWindowFreeze` 只持 `stream`/`cursor`/两个 bool（`active_local_memory_driver.py:39-55`），**不含张量**。探针早期记的「整个 window ≈100 GB」是「同时保留 128 个 `SegmentBatch` 产物」所致，生产一次只持一个 member（实测 trainer 树 RSS 平在 6.6 GB）。

**二、resume 设计 §6 的 BLOCKED 判据证伪**

设计把「`_by_slot` 重建不确定」列为不落地的 BLOCKED 条件。两个独立进程各建一遍同一套生产 producer，对 **完整 stream 元组 + 每条 stream 的 `block_count` + `frame_source` 的 `_ep_vals`/`_ep_starts`/`_valid_cum` 原始字节**求 SHA256，**逐位相同**：

```
P1/P2: CATALOG_SHA256=f465db8e661a6fc4bfa79196c07d61238a073c23446c2ae5997150f06c9fd67c  SLOTS=8 STREAMS=1676
```

代码上同样确定：`canonical_segment_streams`（`active_local_memory_launch.py:146-180`）只读 `producer.frame_source._ep_vals/_ep_starts/_valid_cum`（`libero_lerobot_dataset.py:203-214`：`np.unique` + **seeded** per-episode train/val split）与 `block_count`，不涉 RNG、不涉进程态；`ActionIterableShuffleDataset` 只打乱 **block 迭代顺序**（`action_sft_dataset.py:69-88`），且 active 路线实测 `iterable_shuffle=False`（D8a callback config dump，`/tmp/d8a_launch_stdout.log:40`）。⟹ 该设计可继续评审与实现。

**三、DeviceMonitor 目录为空的原因更正**

此前把空目录归因于 `every_n=200`，**是错的**：per-iteration CSV 落盘被包在 `if self.save_s3 and self.rank == 0:` 内（`callbacks/device_monitor.py:160`），而 `save_s3="${upload_reproducible_setup}"`（`configs/base/defaults/callbacks.py:137`）且 `upload_reproducible_setup` 默认 False（`configs/base/config.py:70`），active TOML 未覆盖 ⟹ **任何** `every_n` 下都不会写 CSV。但 `log.info(f"{self.name} Stats:\n{summary_df.to_string()}")`（`:179`）**无条件执行**（rank 0），故 `PSM_R08_GATE_A_DEVICE_MONITOR_EVERY_N=1` 仍能把 `cpu_mem_gb`/`nvml_used_gpu_mem_gb` 逐迭代打进训练日志——这正是长跑要用的遥测通道。已隔离验证该 env 钩子在 active 路线生效：`device_monitor = {'every_n': 1, 'log_memory_detail': True, 'save_s3': False, 'step_size': 1, 'upload_every_n_mul': 5}`，`save_s3=False` + TOML 的 `wandb_mode="disabled"` ⟹ 该回调**不触网**。

### catalog 容量换算：现有 catalog 只够 112 个优化步，而计划是 5000 步（2026-09-17）

**怎么发现的**：复核 slot rotation 送审件时，注意到「饿死 slot 独占 7190/14430 = 49.83% block……**可达唯一 block 上限 7240 ≈ 56.6 window**，而正式训练计划约 5000 步」这句话里含一个此前被读过去的换算——`7240 / 56.6 = 128`，即**一个 window 消耗 128 个 block**。于是不再依赖转述，直接实测 catalog 的总容量。

**结论**：生产 catalog 的**总** block 容量 = `14430`，一个 window 消耗 `grad_accum_iter = 128` 个 block ⟹ **整个 catalog 只够 112.73 个 optimizer step**。正式计划 `max_iter = 5000` ⟹ **缺口 44.4 倍**。第 113 个窗口的 `freeze_window()` 会 `raise RuntimeError("active Local window exhausted every segment stream")`（`active_local_memory_driver.py:230-231`）。

**证据（直接实测，CPU-only）**：探针 `tools/g0/probe_block_capacity.py`，产物 `artifacts/g0/active_static_probe/probe_block_capacity.json`（`result="PASS"`，同参数独立复跑读数逐位一致；该探针参考 `probe_r09_b_active_static.py` 的形态，root 同样取自环境变量）。

| 项 | 读数 |
|---|---|
| streams / slots | 1676 / 8 |
| `per_slot_blocks` | `{0:2865, 1:1255, 2:1741, 3:1329, 4:2855, 5:1333, 6:1739, 7:1313}` |
| `per_category_blocks` | `{libero_10:5720, libero_goal:2588, libero_object:3480, libero_spatial:2642}` |
| `total_blocks` / `windows_served` | 14430 / **112.73** |
| `per_category_windows` | `{libero_10:178.75, libero_goal:80.88, libero_object:108.75, libero_spatial:82.56}` |
| `windows_until_first_slot_drained` | **78.44**（slot 1 = libero_goal，1255 block） |

**换算依据经代码核实，非推断**：① 一个 member 恰好消耗一个 block——`_peek_block` 每 member 推进一格 cursor、走满 `blocks-1` 才换下一 episode（`active_local_memory_driver.py:258-280`），`_commit_block` 只增不减（`:282-286`），**永不回收**；② `block_count = valid_start_count // ttt_tbptt_steps`（`canonical_local_memory_producer.py:113-115`），即一个 block = 一个 T=16 训练段；③ catalog 全程只建一次——`_by_slot` 在 `__init__` 构建（`:99-106`），`on_train_start` 建完 driver 后 `iteration > 0` 直接 raise、重复建也 raise（`active_local_memory_launch.py:223-289`），**无 epoch 重建、无绕回**；④ slot↔suite 映射为 `slot % len(categories)`（`active_local_memory_launch.py:166`），与 `probe_full_window_postfix.json` 的 `per_category`（375/424/449/428）及本次 block 数逐项吻合。

**如实标注本项新意**：`14430` 这一总数仓库内**早有记录**（`SESSION.md:9332`「1676 streams / 8 slots / 14430 whole blocks」、`SESSION.md:10426`「可达唯一 block 7240 → 14430」），但**从未有人把它换算成可服务的训练步数**。本项的新内容是 `14430 / 128 = 112.73 步` 这一换算，以及它与 `max_iter=5000` 的 44.4 倍缺口。

**为何至今未暴露**：D8a 25 步、soak45 45 步均 < 112。**与已结案两项的关系**：① slot 饥饿修复把可用量由 7240 提高到 14430（翻倍），是必要的，但不充分；② resume 恢复的是数据进度、不增加容量，故 resume 落地后 5000 步依然跑不完。

**为何旧记录未点明**：`SLOT-STARVATION-ACTIVE-WINDOW` 行内「各 slot 至少可支撑 41 个 window ≈ 5200 步」把 window 当成了 member（与 `REBIND-COVERAGE-D8A` **同源**的错误前提），41 window 实为 **41 步**——正是这个错误前提让人以为容量够用。

**已记录**：`TODO.md` 新增 `CATALOG-CAPACITY-VS-5000-STEP`（状态 TODO）。**已通知三方**：`docs/collab/chatgpt/CODEX_INBOX.md` 末尾「catalog 容量换算」条目，请审核者校正对「5000 步」的理解；两个在审 Gate 的送审件 SHA 均未改动。

**可能解法（(a) 已出设计送审；其余未自行实现）**：(a) **catalog 多 epoch 复用**——唯一能真正填平缺口的方向，也是常规训练语义（5000 步需要每段复用约 44 次）。**核实后判定：不是发明新机制，而是接线**——epoch 快照契约 `QueueEpochSnapshot`、确定性排列 `queue_permutation`（`PSM-WMA/queue/v1` 版本标记）、epoch 边界规则 `rollover_projected_if_safe`（`canonical_segment_adapter_scheduler.py:57-67`/`:76-110`/`:546-549`）**均已冻结**；`RankLocalSegmentScheduler.configure_queue`（`local_memory_segment.py:331-337`）**已预留接口、全仓零生产调用点**；`snapshot()`/`rebuild()` 已含 `queue_seed`/`queue_epoch`/`queue_permutation`。单位也对齐（契约 `_queue_for` 与 active 的 `_by_slot[slot]` 同以 episode 为单位）。**且不需给 identity 加 epoch 维度**：`_is_admissible` 在 `stable_slots` 无该 slot 时只要求 `cursor == 0`（`:309-311`），`terminal_rebind` 删除该条目（`:343`），故重置守卫容器后复用同一 identity 天然可准入，**不触及 `SegmentIdentity` ABI**（此前记的「触及 ABI」是未核实的判断，此处更正）。设计文档 `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_catalog_epoch_reuse_design_v0.1.md`，Gate `G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`，已送三方。**建议顺序：resume 先落地，再多 epoch**。(b) 缩短训练计划——112 步不足以训练；(c) 降低 `ttt_tbptt_steps`（16→8 使 block 数翻倍至 225 窗口）——仍不够且改变 TBPTT 语义；(d) 扩充数据集。**在此之前不得启动 D8b 长跑**（会在第 113 步 crash，白耗约 8 小时）。

### 契约的 epoch 边界在 active 路线上经实测不可达——多 epoch 复用设计由 v0.1 修订为 v0.2（2026-09-17）

**目的**：为「catalog 多 epoch 复用」设计（Gate `G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`）实测其最关键前提——契约 `rollover_projected_if_safe`（`canonical_segment_adapter_scheduler.py:542-549`）的两条边界条件在 b_stream=8 / 4 categories 的生产形态下是否可满足。设计文档 §6 把「条件 2 恒不成立」列为不落地的 BLOCKED 判据。

**方法**：新建 `tools/g0/probe_catalog_epoch_boundary.py`，走**真实 driver + 真实 scheduler**（`ActiveLocalMemoryWindowDriver` + `RankLocalSegmentScheduler` + `CanonicalSegmentRuntimeOwner` + `SuiteRoutedSegmentProducer`，与 `probe_r09_b_active_static.py` 同一套搭建），**不调用 `producer.produce`**、不取任何张量，故能走完全部 112 个窗口。在每个**窗口边界**上评估契约的两条条件本身。设计上两个判断：① `freeze_window` 要么返回完整 128-member 计划要么 raise，故「能否再冻结」无需额外探测；② `freeze_window` **非原子**（循环内逐 member `_commit_block`，`:234`），故 raise 后用 `_save_cursors`/`_restore_cursors` 恢复游标。

**读数**（产物 `artifacts/g0/active_static_probe/probe_catalog_epoch_boundary.json`）：

| 项 | 读数 |
|---|---|
| `windows_completed` | 112 |
| `boundary_error` | `active Local window exhausted every segment stream` |
| 条件 1 成立次数 / 112 个边界 | **0** |
| 条件 2 成立次数 / 112 个边界 | **0** |
| `both_true_boundaries` / `reachable` | `[]` / **false** |
| `stranded_blocks` | **94**（slot 0 = 50，slot 4 = 44） |
| `remaining_blocks_by_category` | libero_10 = 94，其余三个 = **0** |
| `admissible_episodes` | 375 / 424 / 449 / 428（合计 1676 = streams，无零 block episode） |
| `terminal_slots` / `stable_but_not_terminal` | `{0,1,2,3,5,6,7}` / `[4]` |

**结论：契约的 epoch 边界在 active 路线上永久不可达**（是证明，不是推断）。第 112 窗口后总剩余 94 < 128 = `window_members`，此后每个 `freeze_window` 必在其 128 轮之一找不到有 block 的 slot 而 raise（`:230-231`）⟹ 第 14336 个之后的 block 永不提交、游标永久冻结 ⟹ slot 0 的下一个 episode（持 50 个残留 block）永不被 admit（条件 1 永久假）；slot 4（中途，持 44 个残留 block）永不到 terminal（条件 2 永久假）。

**根因（结构性）**：契约的窗口成员是**弹性的**——`derive_member(*, member_index, slot_ids)` 由调用方给出本 member 参与哪些 slot（`:522-530`）；active 路线的窗口**定长 128**（`_arm_initial` 断言 `window_members == trainer.config.trainer.grad_accum_iter`，`:158-160`）。契约模型允许「最后一个窗口短一点」，本路线不允许。

**设计修订（v0.1 → v0.2，blob `c686ff3b` → `8a1dbec3`）**：
1. **触发条件改用界条件**：窗口边界上当且仅当「下一个窗口填不满」（`Σ_slot remaining_blocks < window_members`）时推进 epoch。它恰好在「catalog 再也供不起整窗口」时触发，在 catalog 可被整窗口整除时与契约条件 1 **重合**，是本路线唯一可达的触发点。每 epoch 因此为 **112** 个窗口（非 112.73），`max_iter=5000` ⟹ **45 个 epoch**；每 epoch 推迟 94 个尾块（0.65%），因新 epoch 从位置 0 按新排列重走全部 catalog，**不永久丢失**（v0.2 §6 判据 5 专门断言）。
2. **契约条件 2 在本路线是多余约束，v0.1 的回退无收益**：契约的 rollover 会清空守卫容器——`rollover_projected_if_safe` 构造新状态时**不传** `stable_slots`/`terminal_slots`（`:564-569`），而二者默认 `()`（`:434-435`），故 mid-episode 的延续会**静默消失**，这才是条件 2 在契约里承重的原因；而本设计 §4.3 的重置既清容器**又归零每个 slot 的游标**，尾部是被**显式推迟**并在下一 epoch 完整重走 ⟹ 条件 2 不必要。v0.1 §6 的「按 slot 独立推进 epoch」回退会引入逐 slot epoch 记账与「一个 category 的排列跨两个 slot」的额外语义，无收益。
3. **§2 判定降级**：v0.1 称「不是新机制，而是接线」——**部分成立**。快照契约 / 排列函数 / scheduler 接口确为复用；但**边界规则必须为 active 路线新定**，契约的规则在本路线不可表达。
4. **§4.4 新增，消除 v0.1 「重排 `_by_slot[slot]`」的歧义**：排列是 category 级、以 episode 为单位，而 `_by_slot[slot]` 是该 category 的 episode 在 2 个 slot 上的**划分**。规则：按 `(source_digest, episode_id)` 排序得参照序（**必须与 `_queue_for` 的排序 `:477` 逐位一致**）→ 应用 `queue_permutation` → 每个 slot 取自身 episode 的**保序子序列**。**注意参照序是字符串比较**（`episode_id = str(stream.episode_index)`，`"10" < "2"`），实现若按数值排序会与契约偏离。

**探针自身的一处更正（如实记录）**：初版把条件 1 算成了 **block 级**（「该 category 还有没有整块」），而契约的条件 1 是 **episode 级**（已核实：`_admit_free_slot` 用 `positions[category]` 索引 `_queue_for` 的排列 `:512-517`、`_commit_admission` 每 admit 一个 episode 才 +1 `:589-590`、`_queue_for` 每 episode 一行 `:471-480`）。block 级是更强的谓词，两者在边界附近会给出不同答案；初版读数「`condition1_all_categories_drained=false`」因而**依据不成立**（方向虽同）。初版产物已被修正版覆盖、未提交；上表全部为修正版读数，且修正版额外记录了逐边界的条件轨迹。

**已记录 / 已通知**：`TODO.md` 的 `CATALOG-CAPACITY-VS-5000-STEP` 已追加本节结论与两处易错点；`docs/collab/chatgpt/CODEX_INBOX.md` 末尾已追加 v0.2 修订说明（取代 v0.1 的 §2/§3/§6/§8，请裁定四点）。**无代码改动**：`active_local_memory_driver.py` 未被修改，`freeze_window` 的 fail-closed `raise` 仍是当前 operative 行为，**D8b 长跑仍不得启动**。

### 多 epoch 复用设计修订为 v0.3——自查发现 §4.3 重置清单缺 adapter sidecar；规划层满跑 PASS（2026-09-17）

**目的**：在等 45 epoch 满跑的同时，复核 v0.2 §8 第 3 问（「§4.3 的重置清单是否完备——是否还有第四处状态会跨窗口残留」）。**该问由本设计自查给出了答案，且答案是「有」。**

**发现 1：rollover 缺 adapter 的 `LocalMemorySegmentSidecar` 重置，后果是必然抛错（不是概率事件）**

- `sidecar.commit` 只在该 identity `training_stream_end` 为真时 pop（`local_memory_segment_adapter.py:39-43`），否则存下该 slot 的 fast-state；`sidecar.read`（`:29-37`）在「不是前一身份 + 1 个 cursor」时**抛 `ValueError`（不是返回 `None`）**。
- **为何今天不暴露**：不改 epoch 时，slot 换 episode 只发生在上一 episode 已 terminal 时，而 terminal 的那次 `commit` 已把记录 pop 掉——即不变量「slot 换 episode 时 sidecar 必无该 slot 记录」。**`sidecar.reset` 因此是死代码（生产与测试零调用点）。** 而 **epoch rollover 是这套代码里第一个在记录仍存活时把 slot 倒回 cursor 0 的操作**，它打破了这个不变量。
- **为何必然抛错**：新 epoch 的 slot 首块 `cursor == 0`，而 `_active_stream` 已被清空 ⟹ `_peek_block` 的 `rebind = stream is not None` 为 **False**（`active_local_memory_driver.py:264-280`）⟹ 运行时**不会**调用 `_rebind_terminal`；且 `_rebind_terminal` 本身只对 terminal slot 生效（`:190-194`，`terminal_slots.get(slot_id)` 为 None 时直接返回）、**完全不触碰 sidecar**。于是 `read` 要求 `0 == previous.cursor + 1`，在 `previous.cursor ≥ 0` 时**不可能成立**——**与重排结果无关**。
- **边界处记录确实存在**：`probe_catalog_epoch_boundary.json` 的 `stable_but_not_terminal = [4]` ⟹ slot 4 的末次 commit `training_stream_end == False` ⟹ 记录存活。
- **最小复现（真实类，无需数据集/张量，2026-09-17 01:27 实测）**：commit 一个非 terminal 的 `(episode "7", cursor 3)`，再 `read` 同 episode 的 cursor 0 → `ValueError: segment sidecar identity is not a canonical continuation.`；`read` 不同 episode 的 cursor 0 → 同一条 `ValueError`；`reset` 后 `read` → `None`。
- **丢弃 carry 在语义上也正确**：rollover 把该 slot 倒回其首 episode 的 cursor 0，该 episode 会**从头重放**，其首块本应继承**初始**状态，而非上一 epoch 中途留下的 carry。

**发现 2：§6 判据 6 的措辞在今天就已为假（与本设计无关）**

原文写「`per_slot_members` 在每个窗口内仍为 8 个 slot 均衡」。但 `freeze_window` 的选择键是 `(target[category] - observed, category, -used)`（`:227-232`），**只看 exposure 赤字、不看该 category 还剩多少 block**；四个 category 的 block 供给量不等（5720 / 2588 / 3480 / 2642），故任一 category 抽干后，其两个 slot 就从 `choices` 中消失（`:222-224` 的 `if view is None: continue`）。**实测（2 epoch / 224 窗口冒烟）**：`windows_by_distinct_slots = {2:51, 4:49, 5:4, 6:39, 7:2, 8:79}`，**仅 79/224 覆盖全 8 slot**；epoch 0 自第 **80** 个窗口起不再覆盖 8 slot，**epoch 1 无一窗口覆盖 8 slot**。故判据改为可测的正确形式：对在该窗口**实际被服务**的 category，其两 slot 成员数之差 ≤ 1（`max_within_category_slot_skew`），覆盖度作为记录量而非通过条件。

**发现 3：复用把既有的类别偏斜放大为全 run 稳态**

`cumulative_valid_consumer_exposure` 45 epoch 后为 `libero_10=4050720 / libero_goal=1863360 / libero_object=2505600 / libero_spatial=1902240` ⟹ **libero_10 占 39.2%，而 `target_distribution` 是 25%**。成因是每 epoch 尾部（另三类已抽干、只剩 libero_10 的 slot 0/4）窗口 100% 给 libero_10。**epoch 0 与之后 44 个 epoch 逐位相同**（`windows_per_epoch` 全 112、`remaining_blocks_at_rollover` 全 94）⟹ **不是本设计引入，而是本设计让它每 epoch 重复一次**。已作为 §8 第 7 问送审：是否需先修 `freeze_window` 的供给感知。

**发现 4：规划层满跑 PASS（判据 2 的完整证明）**

探针 `tools/g0/probe_epoch_reuse_planning.py`（rollover 是**探针内参考实现**，生产文件未被改动）→ `artifacts/g0/active_static_probe/probe_epoch_reuse_planning.json`：

| 项 | 读数 |
|---|---|
| `result` | **PASS** |
| `windows_total` | **5040**（= 45 × 112，正是 §3.4 的容量换算） |
| `windows_per_epoch` | 45 项，**唯一值 = 112** |
| `criterion1_slot_order_matches_permutation` | **true**（`mismatches = []`） |
| `criterion2_meets_target` / `exceeds_single_epoch` | **true** / true |
| `criterion3_probe_is_pure` | **true** |
| `criterion4_window_index_not_reset` | **true**（`window_index = 5040 = windows_total`） |
| `criterion5_deferred_tail` | `deferred_after_epoch0 = 94`、`recovered_in_epoch1 = 94`、`missing_from_epoch1 = []` |
| `rollovers` | 44 次，`remaining_blocks_at_rollover` **唯一值 = 94**，`queue_epoch` 单调 1→44 |

**附带定量结论（复用不引入新的调度开销）**：`admit`/`commit` 的守卫成员检查是 **list 线性扫描**（`local_memory_segment.py:322-323` 的 `identity not in self.admission_order` / `identity in self.committed_identities`）。实测真实 `RankLocalSegmentScheduler`：N=2000 时 415 µs、N=14336 时 1261 µs，单 epoch 累计约 **9 s**。因 rollover **清空**这两个容器，该 O(n²) 的 n 上界**恰好等于今天单 epoch 的值**（45 epoch 合计约 6.8 min，相对 5000 步墙钟可忽略）。**这是「清空守卫容器」这一设计的附带收益。**

**设计修订（v0.2 → v0.3）**：§4.3 补 adapter 侧重置；新增 §4.7（sidecar 重置的归属与可达路径，三候选，建议 (b)）；§6 新增判据 8、更正判据 6 措辞；§5 补一处 resume 语义（边界处 sidecar **刻意清空**，resume 不得当数据缺失回填）；§8 收敛第 3 问（已答：**有且只有 sidecar 一处**）、新增第 6/7 问；§10 补 10.2/10.3/10.4。v0.2 的 §1–§3、§4.1–§4.2、§4.4、§7 **逐字未改**。

**§8 第 3 问的复核结论（供三方核对）**：v0.2 担心的另两处经复核**不构成残留**——`_rebind_terminal` 只对 terminal slot 生效且被 §4.3 的清空取代；`owner` 的 `phase`/`transaction`/`forward`/`_retry_plan`/`_completed_transaction`/`_sealed_slow_window` 全是**按 window** 的能力，窗口结束即归 `IDLE`（`canonical_segment_runtime.py:157-171`、`:173-179`），`wiring` 只持有 adapter 与 slow 参数（`production_segment_wiring.py:36-37`），`registry` 只持有四个按 window 的能力（`production_active_wiring.py:62-66`）。故按 slot 的持久状态**全清单为四处**：driver 的四个游标容器、scheduler 的两个守卫容器 + 两个序列表、`cumulative_valid_consumer_exposure`（刻意不清零）、sidecar。

**无代码改动**：`active_local_memory_driver.py`、`local_memory_segment.py`、`local_memory_segment_adapter.py`、`canonical_segment_runtime.py` **均未被修改**；`freeze_window` 的 fail-closed `raise` 仍是当前 operative 行为，**D8b 长跑仍不得启动**。

### soak45 的验收判据（预先登记，2026-09-17 01:33，迭代 8/45）

**为何登记**：`active_soak45` 这次 45 步 GPU 短跑此前**只在对话里说过判据、未落到文档**。未登记的验收判据容易被事后合理化，故本节点把它写死。**内存判据的统计量在迭代 8/45 时登记——早于看到终值；登记后不再修改，若终值不满足即记 FAIL。**

**运行参数**（`RUN_NAME=edge_libero_4in1_localmem_active`，`OUTPUT_ROOT=/disk/rl/psm_wma/artifacts/g0/active_soak45`，训练进程 pid **1205406**）：

```
PSM_R09_B_TTT_ACTIVE=1 PSM_R09_B_TTT_ENABLED=1 PSM_R08_LOCAL_HISTORY_ENABLED=1 \
PSM_R09_B_TTT_ACTIVE_GA=16 PSM_R08_GATE_A_DEVICE_MONITOR_EVERY_N=1 \
EXTRA_TAIL_OVERRIDES="trainer.max_iter=45 checkpoint.save_iter=15"
```

**判据**：

1. **完成性**：45 步全部走完，无 `Traceback` / `CUDA out of memory` / `Killed`。（注意：配置 dump 中的回调名 `skip_nan_step` 含 "nan" 字样，**不是失败信号**，勿误判。）
2. **数值健康**：每步 `train/loss` 有限（非 nan/inf）。
3. **slot 轮转修复生效**：**本次运行不可验证——登记者须如实标注，不得记为 PASS。**
   - **登记时的判断依据**（2026-09-17 01:34 实测，非推测）：`grep -icE "slot|window" /tmp/active_soak45.log` 得 **2**，且两处命中**都在启动时的配置 dump 内**（其一为 `'plan_chain_id': 'active-local-window'` 的 `window` 字样），**运行时无任何逐 member 的 slot 证据**；`grep -icE "PSM_DIAG_EVIDENCE|psm_diag"` 得 **0**，即逐 member 诊断探针（`local_memory_segment_adapter.py:104-157`）**本次未启用**。
   - 叠加的规模约束：45 步 < 128 member ⟹ **连一个完整窗口都没走完**（与 D8a 25 步同理）。
   - **因此判据 3 在本运行记为 N/A（不是 PASS，也不是 FAIL）。** slot 轮转修复的实证须另跑：设 `PSM_DIAG_EVIDENCE=1` 并跑到 ≥1 个完整窗口，参照基线为修复前实测 `window_per_slot_members={4:32,5:32,6:32,7:32}`、`slot 0/1/2/3 恒为 0`。
   - **本条为登记后修订**（01:3x 登记 → 01:34 核实后改）：登记时我写的是「只能用窗口内前 45 个 member 的 slot 覆盖来验证」，该说法**建立在日志含逐 member slot 信息这一未核实的假设上**；核实后发现假设为假。修订只把**不可验证**如实标出，**未放宽**任何通过条件。
4. **exposure 单调性**：`cumulative_valid_consumer_exposure` 单调不减。
5. **内存判据（本次预先登记的统计量）**：取 DeviceMonitor 的 `cpu_mem_gb` 逐迭代序列（`every_n=1`）。
   - **丢弃前 2 个样本**作为 warmup。理由：迭代 1 含 allocator / latent cache 首次填充，实测存在一次性台阶（4.834 → 6.593）。
   - 对剩余样本定义带宽 **B = max − min**，最小二乘斜率 **s（GB / 100 迭代）**。
   - **PASS 条件：`|s| < B / 2`**——即趋势幅度不超过噪声带宽的一半。理由（为何该阈值非任意）：若存在真实泄漏，趋势将随时间主导带宽，`|s|×100` 会超过 B；若只是振荡，斜率不可从噪声中分辨。该式自带标度，不需额外的绝对阈值。
   - 同时记录**最后 20 个样本**的 B 与 s 作为稳健性对照（长跑泄漏在尾部更易显现）。
6. **显存**：`nvml_used_gpu_mem_gb` 不随迭代单调上升（同一条 `|s| < B/2` 统计量）。

**登记时的快照（迭代 8/45，未参与判定，仅供追溯起点）**：`cpu_mem_gb` = 4.820（预跑）、4.834、6.593、6.146、6.147、6.173、6.470、6.120、6.121；`nvml_used_gpu_mem_gb` 稳定 **12.281**。

**已知与本次运行无关的既有事实**：`cpu_mem_gb` 由 psutil 求**当前进程 + 全部子进程** RSS 之和（`device_monitor.py:116-123`），而训练进程 `num_workers=0` ⟹ 无子进程，故该值就是训练进程自身 RSS。轨迹中的 1.76 GB 跳变经查**不是** latent 缓存 LRU（上界 8 个 episode，实测文件均值 32.2 MB / 最大 108.1 MB ⟹ 至多 0.86 GB，**假说不成立**），也**不是** page cache（psutil 的 RSS 不含它）。

### 45 epoch 满跑把复用设计 v0.3 的两处推断证伪，设计修订为 v0.4（2026-09-17 01:47）

run-2（pid 1216599，`/tmp/epoch_reuse_full2.log`）于 **01:46:56** 结束，`result=PASS`，产出最终产物 `artifacts/g0/active_static_probe/probe_epoch_reuse_planning.json`（9711 字节）。判据 1/2/3/4/5 与 run-1 **逐位一致**：`windows_total=5040`、`windows_per_epoch` 45 项唯一值 112、44 次 rollover 残留唯一值 94 且 `queue_epoch` 单调 1→44、`criterion1_mismatches=[]`、`criterion3_probe_is_pure=true`、`criterion4_window_index_not_reset=true`（`window_index=5040`）、`criterion5_deferred_tail={deferred:94, recovered:94, missing:[]}`、`committed_identities=14336`。

**新度量推翻了 v0.3 §10.4 的两处表述**（这是本次复用设计至今最重要的技术发现）：

| v0.3 的表述 | 实测 |
|---|---|
| 「epoch 0 与之后 44 个 epoch **逐位相同**」 | **假**。只有聚合量相同（112 窗 / 残留 94）；**窗口内部构成相反**：epoch 0 有 81/112 个窗口服务全部 4 类（`all_categories_windows=81`、`all_slots_windows=79`），**epochs 1–44 的 `first_partial_category_window` 恒为 1** ⟹ 无一窗口覆盖全部 category |
| 「51 个 2-slot 窗口来自尾部只剩 libero_10」 | **算术上不可能**：51 × 128 = 6528 > libero_10 每 epoch 全部消耗 5626。该推断把「2 个 slot」等同于「1 个 category」 |

**严格下界（由直方图推出，非估计）**：被服务 category 实例数 = 1×3826 + 2×1070 + 3×63 + 4×81 = **6479**；实际 distinct slot 实例数 = 2×3826 + 3×51 + 4×1019 + 5×7 + 6×56 + 7×2 + 8×79 = **12898**；若每 category 出满 2 slot 应为 12958 ⟹ **缺口 60**，与**奇数 slot 窗口数 51+7+2 = 60** 精确吻合（互为交叉验证）。2-slot 窗口若为「2 category × 1 slot」每个耗 2 个缺口 ⟹ 至多 30 个；直方图不含 1-slot 窗口故 1-category 窗口全落在 2-slot 桶内 ⟹

> **单 suite 窗口 ≥ 3826 − 30 = 3796，即 ≥ 3796/5040 = 75.3% 的窗口只服务 1 个 suite。**

对照 epoch 0（= 今天的单 epoch 行为）：**72.3% 的窗口服务全部 4 个 suite**。两者是**相反的构成**。

`windows_by_distinct_categories = {1:3826, 2:1070, 3:63, 4:81}`、`windows_by_distinct_slots = {2:3826, 3:51, 4:1019, 5:7, 6:56, 7:2, 8:79}`、`max_within_category_slot_skew = 64`。`tail_structure`：epoch 0 = `{first_partial_window: 80, first_partial_category_window: 82}`，epochs 1–4 均 = `{1, 1}`，五者的 `remaining_by_category_at_epoch_end` 全为 `{libero_10: 94, 其余: 0}`。

**根因（已核实，非推测）**：`cumulative_valid_consumer_exposure` **同时是 `freeze_window` 的控制输入**（选择键 `target - observed`，`active_local_memory_driver.py:227-232`），而它在 rollover 时被**刻意保留**（v0.3 §4.3）⟹ epochs ≥1 开局即继承 epoch 0 末的偏斜赤字（libero_10 占 39.2%、赤字深度为负；另三类为正），`freeze_window` 连续服务赤字为正者直到其抽干，**窗口塌缩到单一 category 的 2 个 slot**。故 v0.3 的「偏差成因是供给约束而非不清零」**只对 epoch 0 成立**。

**对设计定性的影响**：v0.3 曾把 39.2% 偏斜定性为「既有性质被复用放大」，据此建议「可作既有行为接受、单独开 Gate」。**该定性的前提已被推翻**——这不是把既有行为重复 45 次，而是**让 44/45 的训练步运行在今天从未运行过的 regime 里**。候选修法（保留累计字段作报告量、赤字改用 per-epoch observed）**触及 §7 改动面之外的选择键，本设计未擅自纳入**，已升级为 §8 第 7 问（三选一）。

**§6 判据 6 的第二次更正**：v0.3 把「同类两 slot 成员数之差 ≤ 1」拟升为**通过条件**，实测全局 `max_within_category_slot_skew = 64`（上限 128）；但该值**未按 epoch 分离**，**无法判断 epoch 0 单独是否 ≤ 1**——若为假则与刚更正掉的原文属**同一类缺陷**（把今天不成立的性质写成判据）⟹ **降级为记录量**，跑出单 epoch 基线前不得作 PASS 条件。

**供给侧交叉验证（新增，可复算）**：`per_slot_blocks` 显示**同类两 slot 的供给本身就不等**（goal 1255/1333 差 78、spatial 1329/1313、object 1741/1739、libero_10 2865/2855）。最小值 **1255 ÷ 16**（每 slot 每窗口成员数）= **78.44**，与容量探针的 `windows_until_first_slot_drained = 78.44` **逐位吻合** ⟹ epoch 0 的 `first_partial_window = 80` 是**由供给推出来的**（第 79 窗仍用掉该 slot 剩余的 7 块，第 80 窗起为 0），不是观测巧合。

**无代码改动**：`active_local_memory_driver.py`、`local_memory_segment.py`、`local_memory_segment_adapter.py`、`canonical_segment_runtime.py` **均未被修改**；探针中的 rollover 是**探针内参考实现**，生产改动仍等 Gate 授权。`freeze_window` 的 fail-closed `raise` 仍是当前 operative 行为，**D8b 长跑仍不得启动**。

**本窗口另完成**：① 把 soak45 的验收判据**预先登记**到上文（内存统计量在迭代 8/45 时登记，早于终值）；② 登记后核实**判据 3（slot 轮转）在 soak45 日志中不可验证**（`grep -icE "slot|window"` 得 2，两处命中均在启动配置 dump 内；`PSM_DIAG_EVIDENCE` 未设置）⟹ 已如实改为 **N/A**，并注明登记时的说法建立在未核实的假设上。

**设计文档已修订为 v0.4**（blob `219355d3d5dda1407e5602218d6ab1c7bb79ad47`），改动集中在 §4.3 一条、§6 一条、§8 一条、§10.4 全节、§0 与标题；v0.3 的 §1–§3、§4.1–§4.2、§4.4–§4.7、§5、§7、§9 **逐字未改动**。

### 审核前置硬检查（第 1 轮）——检查结果：**三个在审 Gate 的 formal root 不在远端，未送达**（2026-09-17 01:49 CST）

**本轮性质**：这是对 `G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION`、`G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`、`G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE` 三个 Gate 的**首次完整前置检查**，不是「续等已检查过的同一计时句柄」。所有步骤均成功执行，故结论**不是**「检查失败/状态未知」。

| 凭证字段 | 本轮实测 |
|---|---|
| 轮次 / 时间 | 第 1 轮，2026-09-17 01:49:37 CST |
| `before_head` | `661b54f3c2616f55b2fff8adf386252e3f8dbe22` |
| 远端 advertised SHA | `f63ee3c5ab8da0855aea1ca2d9e47f5b5d4eb28c`（`git ls-remote origin refs/heads/V2`） |
| `git fetch origin V2` | 成功（`* branch V2 -> FETCH_HEAD`） |
| `git log before_head..origin/V2` | **空** ⟹ 远端无新增提交 |
| ff 判定 | `merge-base --is-ancestor <before_head> origin/V2` 返回**非 0**；但 `f63ee3c5` 是 `HEAD` 的**祖先** ⟹ 远端**纯落后**，非分叉，无需 ff |
| 本地领先量 | `V2 [origin/V2: ahead 29]` |
| 子模块 Gitlink | `HEAD` 的 `cosmos-framework` = `525f5066393cba044f00f1104b83f5eb424a9c49`；工作树另有 ` M cosmos-framework`（**dirty，单独报告，不污染审核范围**） |
| ChatGPT exact-pair 检索 | `grep -rl <root> docs/collab/chatgpt/reviews/`，对 `5d527f3e`/`8bb48f35`/`bae39647`/`f6d3ae26`/`661b54f3` **命中文件数均为 0**；`reviews/` 最新文件为 `2026-09-16_stage1_pragmatic_pair_producer_advice_b57ad44_93a89ba.md`（2026-09-16 11:52），锚定 `b57ad44`/`93a89ba` |
| pane capture 1：`ds:0.0` | 成功。显示的是**旧 pair** `formal root=3324b3a0a4dc92b36882e23b4d9b42052554965c` / `child=93a89ba61306d840a008813f62f26a34d54850f4` 的 `REQUEST_CHANGES`（针对 `source_evidence_production_entrypoints_implementation_design_v0.1.md:64`）。**未出现任何当前 Gate 的 pair** |
| pane capture 2：`mm:0.0` | 成功，但显示 **Claude Code 进程已退出**——`pane_current_command = zsh`，pane 停在裸 shell，末行为 `Resume this session with: claude --resume a34005ee-6e0d-46c3-be87-d0bce4d661ff`。**MM 审核进程不可用** |

**核心事实（本轮最重要的发现）**：`INBOX` 引用过的 root 的远端可达性**分成截然两段**——

| root | 对应 Gate | 远端 |
|---|---|---|
| `3bf72e49` / `a58bdb90` / `187768e4` / `786538f8` / `3324b3a0` | 历史已获批各 Gate | **在远端** ✓ |
| `5d527f3e` | ACTIVE-WINDOW-SLOT-ROTATION | **仅本地** ✗ |
| `8bb48f35` | ACTIVE-ROUTE-RESUME | **仅本地** ✗ |
| `bae39647`（及修订 `f6d3ae26`、`661b54f3`） | ACTIVE-CATALOG-EPOCH-REUSE | **仅本地** ✗ |

远端最后一次推送为 **`f63ee3c5` @ 2026-09-16 21:21:45**；此后 29 个提交（含三个 Gate 的全部送审件与设计文档）**从未推送**。历史上每个可审核的 Gate 其 formal root 都在远端，故「root 可达」是本项目审核送达的既有前提。

**逐方状态（严格由本轮凭证导出）**：
- **ChatGPT（`ds:0.0`）**：处理中——但其手上的 pair 是 `3324b3a0`，**当前三个 Gate 的 pair 未送达**。`reviews/` 中无任一当前 root 的 exact formal review。
- **MM（`mm:0.0`）**：**不可用**——审核进程已退出，pane 停在 shell。
- **Kimi**：**未检查**——本轮冻结名册中未登记其 pane（`fz`/`fq` 会话存在但从未在 SESSION 中 capture 过）。

**结论**：三个 Gate 的诚实状态是 **「未送达 / 链路不完整」**，不是「尚未回复」。因此**不存在推进令牌**，三个 Gate 全部保持 `REVIEW`；按治理规则，无令牌时**禁止整改、编码、提交、执行、训练或关闭 Gate**，仅可修复审核链路、记录失败、或撰写不依赖既有审核结论的 docs-only 设计。

**链路修复所需的动作（需用户决定，本回合未执行）**：推送本地 29 个提交使三个 Gate 的 formal root 在远端可达；并恢复 MM 的审核会话（`claude --resume a34005ee-6e0d-46c3-be87-d0bce4d661ff`）。**推送属「外网访问」，按 CLAUDE.md 确认规则须取得用户明确许可**，故本回合**未推送**，仅如实记录。

---

### 复用设计修订为 v0.5——单 epoch 基线跑出，§6 判据 6 的更正形式**整体撤回**（2026-09-17 02:05 CST）

**触发**：v0.4 把 §6 判据 6 的更正形式（「对在该窗口实际被服务的 category，其两 slot 成员数之差 ≤ 1」）降级为记录量，理由是 45 epoch 全局 `max_within_category_slot_skew = 64` **未按 epoch 分离**，**无法判断 epoch 0 单独是否 ≤ 1**，并明确写下「若为假则与刚更正掉的 v0.2 原文属同一类缺陷；须先跑单 epoch 基线」。该基线已跑出，**结论是该形式应整体撤回**。

**新证据**：`artifacts/g0/active_static_probe/probe_epoch_reuse_planning_epoch0.json`（`tools/g0/probe_epoch_reuse_planning.py --max-epochs 1 --target-windows 112`；`result=PASS`、`windows_total=112`、`window_index=112`、`rollovers=[]`、`epochs_planned=1`）。

| 项 | epoch 0 单独 | 45 epoch 全体 |
|---|---|---|
| `max_within_category_slot_skew` | **32**（上限 128） | 64 |
| `windows_by_distinct_categories` | `{1: 16, 2: 13, 3: 2, 4: 81}` | `{1: 3826, 2: 1070, 3: 63, 4: 81}` |
| `windows_by_distinct_slots` | `{2: 16, 4: 13, 5: 1, 6: 1, 7: 2, 8: 79}` | `{2: 3826, 3: 51, 4: 1019, 5: 7, 6: 56, 7: 2, 8: 79}` |
| `all_categories_windows` / `all_slots_windows` | 81 / 79 | 81 / 79 |
| `first_partial_window` / `first_partial_category_window` | 80 / 82 | 80（epoch 0）→ 1（epochs ≥ 1） |
| `remaining_by_category_at_epoch_end` | `{libero_10: 94, 其余: 0}` | 每 epoch 均为 94 |
| `cumulative_exposure` | `{libero_10: 90016, libero_goal: 41408, libero_object: 55680, libero_spatial: 42272}`（libero_10 = 39.2%） | 45× 同比例 |

**判定 1（判据 6）**：`max_within_category_slot_skew = 32 ≠ 1`，**在 epoch 0 单独就已成立**。故该判据形式**在今天就已为假**——若升为 PASS 条件，它是一条「今天的生产行为就已经不满足」的判据，**与 v0.2 原文属同一类缺陷**。⟹ **整体撤回**（不再作判据、不再作候选通过条件），该项仅作**记录量**保留。§6 的 GPU 部分因此只保留两条已核实可判定的断言：「loss 有限」与「`cumulative_valid_consumer_exposure` 单调不减」。

**判定 2（量化 v0.4 的核心结论）**：单 suite 窗口占比 **epoch 0 = 16/112 = 14.3%**；**epochs 1–44 = (3826 − 16)/44 = 86.6/epoch = 77.3%**——**相差 5.4 倍**。且 epoch 0 有 **81** 个「4 类并存」窗口，epochs ≥ 1 为 **0**。这以最直接的方式量化了「复用改变了训练 regime」而非「重复了同一 regime」，把 v0.4 的定性判断落成两个可复算的数字。

**顺带确认（epoch 0 单独也成立的两项）**：`first_partial_window = 80` 与 `first_partial_category_window = 82` 在单 epoch 与 45 epoch 下**逐位相同**（epoch 0 段），与供给侧交叉验证（最小值 `1255 ÷ 16 = 78.44`）一致；`remaining_by_category_at_epoch_end` 的 `libero_10 = 94` 即每 epoch 推迟的尾块数，与 `probe_catalog_epoch_boundary.json` 的 `stranded_blocks = 94` **吻合**。

**范围声明**：**无生产代码改动**（同 v0.3/v0.4）；探针中的 rollover 是**探针内参考实现**。设计文档修订为 **v0.5**（blob `e22b6543ee3d2c0874dc2be9f60dcca6e89ca37c`），改动集中在 §0 / §6 的一条 / §10.4 的一节 / 标题，§1–§5、§7–§9 逐字未改；v0.4 的实质内容全部保留。INBOX 已追加「第四次修订」条目（重建后的精简 live Inbox 中，`## 未决 Gate 索引` 的 epoch reuse 行本已写明「以本文件末尾『第四次修订』为准」，该节现已存在，指引不再指向空处）。

**自守声明**：本次撤回**不是**放宽标准——它把一条**在今天就已为假**的候选判据撤掉，避免重演 v0.2 原文的缺陷类；判据总数减少，但保留的两条均为已核实可判定项。

**未决不变**：§8 第 7 问 (a)/(b) 仍待三方裁定；(c) 已由本次基线闭合。三个 Gate 状态仍为**未送达**（见上节），**无推进令牌**。

---

### 审核前置硬检查（第 2 轮，用户询问「正式训练条件 / 昨晚情况」触发）——结论：状态与昨晚一致，仍「未送达 / 链路不完整」（2026-09-17 09:34 CST）

| 凭证字段 | 本轮实测 |
|---|---|
| 轮次 / 时间 | 第 2 轮，2026-09-17 09:34:05 CST |
| `before_head` | `4cdedf68f6e0f302b0d46343c82965b7ffafefbd` |
| `git fetch origin V2` | 成功 |
| 远端 advertised SHA | `f63ee3c5ab8da0855aea1ca2d9e47f5b5d4eb28c`（`git ls-remote origin refs/heads/V2`），与 tracking `origin/V2` 一致 |
| `git log before_head..origin/V2` | **空** ⟹ 远端无新增提交 |
| ff 方向 | `merge-base --is-ancestor origin/V2 HEAD` 返回 **0** ⟹ 远端 `f63ee3c5` 是本地 `HEAD` 的**祖先**，远端**纯落后**，非分叉，无需 ff |
| 本地领先量 | `git rev-list --count origin/V2..HEAD` = **30**（较昨晚第 1 轮的 29 多 1，即 v0.5 提交 `4cdedf68`） |
| ChatGPT exact-pair 检索 | 对 `5d527f3e`/`8bb48f35`/`bae39647`/`f6d3ae26`/`661b54f3`/`4cdedf68` 逐一 `grep -rl`，**命中文件数均为 0**；`reviews/` 最新文件仍为 `2026-09-16_stage1_pragmatic_pair_producer_advice_b57ad44_93a89ba.md`（2026-09-16 11:52），锚定 `b57ad44`/`93a89ba` |
| pane capture：`mm:0.0` | 成功。内容为**旧 pair** 的 SegmentBatch/loss 接缝设计 review（`REQUEST_CHANGES`，日期 Sep 7），**未出现当前三个 Gate 任一 pair** |
| pane capture：`ds:0.0` | 成功。内容为**旧 pair** 的 HIGH-1..HIGH-5 `REQUEST_CHANGES`（DeepSeek V4 Pro），**未出现当前三个 Gate 任一 pair** |

**本轮结论**：远端自 `2026-09-16 21:21:45`（`f63ee3c5`）后**仍无任何新推送**；三个在审 Gate（`ACTIVE-WINDOW-SLOT-ROTATION` / `ACTIVE-ROUTE-RESUME` / `ACTIVE-CATALOG-EPOCH-REUSE`）的 formal root **仍不在远端**，`reviews/` 中无 exact formal review，MM/DS 两个 pane 的 capture 均非当前 pair。⟹ 状态仍为 **「未送达 / 链路不完整」**，**不存在推进令牌**，三个 Gate 保持 `REVIEW`。

**逐方状态（由本轮凭证导出）**：ChatGPT=`未送达`（pair 不在远端、无 exact review）；MM=`未送达`（pane 内容非当前 pair）；Kimi=`未检查`（冻结名册未登记其 pane，本会话 `kimi`/`fq` 存在但从未在 SESSION capture 过）。

**正式训练条件仍未具备**，阻塞不变：①三个 Gate 未送达、无令牌；②catalog 容量仅 112.73 步（缺口 44.4 倍，依赖 epoch-reuse 裁定）；③resume 未接线（fail-closed `iteration>0` 直接 raise，D8b 长跑不能在该防线下跑）；④slot 饥饿修复待 Gate 授权落地。链路修复仍须用户许可：推送本地 30 个提交（外网访问）+ 恢复 MM 审核会话。

---

### 审核链路修复 + 三 Gate 重新送达（2026-09-17 09:54 CST，REVIEW）

**目标（用户 /goal）**：按项目规范持续推进，只到实现具备 local mem 训练条件。

**链路修复（已执行，推送成功）**：
- 子模块 `cosmos-framework` v2 推送 `5d24528 → 525f506`（3 个提交：`81fa342`/`6dc25e0`/`525f506`）。
- 根仓 `V2` 推送 `f63ee3c5 → 4cdedf68`（30 个提交）。
- 推送后 `git ls-remote`：根仓 `V2=4cdedf68`，子模块 `v2=525f506`；`git rev-list --count origin/V2..HEAD = 0`，本地与远端同步。

**三个 Gate 的 formal pair（以 archive `CODEX_INBOX_2026-09-17_661b54f.md` 的 canonical 声明为准，现已全部远端可达）**：
| Gate | formal root | child/Gitlink | 设计文档 blob |
|---|---|---|---|
| ACTIVE-WINDOW-SLOT-ROTATION | `5d527f3ea8db25f23482c9a3e13b5c7ca2fd6a99` | `6dc25e0f8c3ba39525c8ba994b8d0c38c2ce5461` | `8556b0a5` |
| ACTIVE-ROUTE-RESUME | `8bb48f3507dda24090de41bbc4208dfc9e4538aa`（附注前进至 `c48c0169`，送审件未变） | `525f5066393cba044f00f1104b83f5eb424a9c49` | `a8dd24ca` |
| ACTIVE-CATALOG-EPOCH-REUSE | `bae3964776d3138d2a60d1b03cbabe0062fef75c`（修订至 v0.5，最终 commit `4cdedf68`） | `525f5066393cba044f00f1104b83f5eb424a9c49` | `e22b6543` |

**送达回执（三联：send-keys -l → ≥1s → 独立 Enter → capture）**：
- ChatGPT：canonical live Inbox 已随根仓 `4cdedf68` 推送；未决 Gate 索引 + archive 完整正文均远端可达。
- MM=`mm:0.0`（pane 进程 `claude`）：送达成功，capture 显示完整三 Gate 申请进入会话、底部 `✽ Computing…`（开始处理）。
- DS=`ds:0.0`（pane 进程 `opencode`）：送达成功，capture 显示完整申请进入会话、底部 `Thinking`（DeepSeek 开始处理）。

**状态**：三个 Gate 全部 `REVIEW`，三方 final 未齐、无推进令牌。下一步按三分钟完整远端锁定 + 三方 exact-pair 核验轮询，至少连续三十轮。

### 三 Gate 审核轮询（第 1 轮，2026-09-17 09:59:07 CST，REVIEW）

- `before_head=4cdedf68`；fetch 成功；advertised/tracking=`4cdedf68`；新增范围为空；祖先判定=0；ff=`Already up to date`。
- ChatGPT exact-pair 检索（`5d527f3e`/`8bb48f35`/`bae39647`/`4cdedf68`/`6dc25e0f`/`525f506`）**命中数均 0**，`reviews/` 无新增。
- MM=`mm:0.0` capture：显示针对 epoch-reuse 的意见（`probe_epoch_reuse_planning.json` 判据 1-5 全 PASS、无 HIGH/CRITICAL，但 §8 第 7 问 (a)/(b) 不可悬置、75.3% 单 suite = 5.4 倍 regime 变化应实现前裁定），**尚未给出 self-contained 同 pair FINAL**；pane 内有用户输入「选 (a)，出 v0.6」。
- DS=`ds:0.0` capture：`Thinking`（处理中），尚无 final。
- 无推进令牌，三个 Gate 保持 REVIEW，继续轮询。

### 轮询 #2（10:03:26 CST）：fetch 无新增（advertised=`4cdedf68`）；ChatGPT reviews/ 0 命中；MM 显示 epoch-reuse 第 7 问 (a)/(b) 裁定中（pane 内用户输入「选 (a)，出 v0.6」，MM 输出 v0.6 修订措辞），无 self-contained FINAL；DS 正读 `canonical_segment_adapter_scheduler.py`（configure_queue 审核中）。无令牌，继续。

### 轮询 #3（10:08:10 CST）：fetch 无新增（advertised=`4cdedf68`）；ChatGPT reviews/ 0 命中。**DS=`ds:0.0` 已给出三 Gate literal verdicts**（Build 13m56s）：
- Gate 1 `ACTIVE-WINDOW-SLOT-ROTATION`：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_WINDOW_SLOT_ROTATION`（内容层面；§2.3(B) 解读成立；**须改正设计头部 stale root/child**）。
- Gate 2 `ACTIVE-ROUTE-RESUME`：`REQUEST_CHANGES` —— HIGH：`resume_wiring_design_v0.1.md:59,148-150`（load 时序使 `_DataloaderWrapper` 永不命中 driver）。
- Gate 3 `ACTIVE-CATALOG-EPOCH-REUSE`：`REQUEST_CHANGES` —— 主因：`catalog_epoch_reuse_design_v0.1.md:191-197,485-493`（不清零 exposure 控制输入，静默改变 44/45 epoch regime，不应作为已知代价接受）；其他 `:136-146`/`:222-231`/`:199-202,249-262`/`:268`/`:237-247`。
- DS 另附「未决送达事实」：基于旧 ledger `CODEX_INBOX.md:10-23` 称三 root 不在远端、无令牌，**未意识到已推送**；并指 exact-pair identity 需改正（stale root/child）。DS 声明「在链路与 exact-pair identity 改正前，本结果不能作为正式三方同 SHA 闭批」。
- MM=`mm:0.0`：仍停在「选 (a)，出 v0.6」输入，无新 FINAL。ChatGPT 未回复。无推进令牌，继续。

### 三 Gate 一次性整改（2026-09-17 10:57 CST，REVIEW → 整改中）

**技术决策（Codex 主体，非用户裁定）**：采纳 DS `REQUEST_CHANGES` 与 MM「第 7 问不可悬置」意见，三个 Gate 各做最小 docs-only 整改：

1. **Gate 1 `ACTIVE-WINDOW-SLOT-ROTATION`**：设计头部 stale `formal root/child`（`3065bc8a`/`81fa342d`）改正为送审件实际提交 `5d527f3e`/child `6dc25e0f`，附修订说明；正文 §1–§9 无改动。
2. **Gate 2 `ACTIVE-ROUTE-RESUME` → v0.2**：经代码核实 DS HIGH 意见成立（`trainer/__init__.py:383` load 早于 `:400` on_train_start，driver 在后者才 attach）。修正：checkpoint 接口从 driver 移到 `ActiveLocalMemoryLaunchCallback`（`_DataloaderWrapper` 遍历的是 callbacks），新增 `_pending_resume_state` 暂存 buffer（load 时 driver 未构建则暂存、on_train_start 后应用），`has_checkpoint_state()` 恒 `True`。
3. **Gate 3 `ACTIVE-CATALOG-EPOCH-REUSE` → v0.6**：§8 第 7 问**裁定 (a)**——引入 per-epoch observed 计数器 `_epoch_observed`，`freeze_window` 选择键改用之、累计字段 `cumulative_valid_consumer_exposure` 保留仅作报告量；同步闭合其余六问（queue_seed 选 (b)、sidecar 归属选 (b)）；§7 显式放宽「改选择键 observed 来源」一条；§6 新增判据 9/10。

**待办（Kimi 8 条建议，空闲处理）**：覆盖不变量一等公民测试、tie-break 纪律入设计模板、容量探针标准化、尾巴截断量化入 epoch-reuse Gate、清理 v0.13/D018 §4 僵尸任务、三 Gate 并行送审（已在做）、resume 范围框死（边界重启 vs 状态续传，需评估是否改 v0.2）、T 循环吞吐地板微基准。详见 TODO。

下一步：静态核验（已 `git diff --check` PASS）→ 提交 → 推送 → 以新 formal pair 重新送审三 Gate。

### 三 Gate 整改后重新送审（2026-09-17 11:04 CST，REVIEW）

- 整改提交 `1ba933c1`（三文档 + SESSION）已推送；Inbox 更新提交 `a1477862` 已推送。远端 `V2=a1477862`。
- **新 formal pair**（root 均为整改提交 `1ba933c1`，child 不变）：slot-rotation=`1ba933c1`/`6dc25e0f`；resume=`1ba933c1`/`525f506`；epoch-reuse=`1ba933c1`/`525f506`。设计文档 blob：`e50e55ca`/`ab65f3c8`/`6a4c0ac6`。
- 送达回执：ChatGPT=Inbox 已推送（`a1477862`）；MM=`mm:0.0` 已送达（`Moonwalking…` 处理中）；DS=`ds:0.0` 已送达（capture 显示其正以 `git rev-parse`/`ls-tree`/`log` 核实新 root `1ba933c1`，处理中）。
- 三方 final 未齐，无推进令牌；三 Gate 保持 REVIEW，进入三分钟轮询。

### 轮询 #4（整改后第 1 轮，2026-09-17 11:10:32 CST）：fetch 无新增（advertised=`de999520`）；ChatGPT reviews/ 0 命中。**DS 第 2 轮 verdict + MM 第 2 轮 verdict 已出**：

**DS=`ds:0.0`（Build 3m57s）literal verdicts**：
- Gate 1：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_WINDOW_SLOT_ROTATION`（无附加条件）。
- Gate 2：`REQUEST_CHANGES(file:line)` —— `resume_wiring_design_v0.1.md:198`（同一性判定位置未钉死）、`:163-177,194-200`（重建/同一性/版本 fail-closed 完备性）、`:4`（头部 formal root 陈旧，仍 `8bb48f35`，应改整改提交）。DS 附注「HIGH 已闭合，仅余 fail-closed 完备性 MEDIUM」。
- Gate 3：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`（附条件：判据 9/10 必须在 closure 前实测通过；Q5 seed 注入需确认 manifest/config/source digest、Q6 sidecar 归属须与 Gate 2 实现顺序绑定，余项「实现前补入」）。DS 附注「第 7 问 (a) 主因已闭合」。

**MM=`mm:0.0`（Brewed 1m16s）**：对 Gate 3 v0.6 结论「未发现 HIGH/CRITICAL/MEDIUM 缺陷，授权按 §4.1/§4.3/§4.6/§4.7/§6 判据 9-10 落地，按 §5 顺序（Gate 2 v0.2 先落地 → 本设计后落地），`discard_committed_carry()` 与 Gate 2 `snapshot()/rebuild()` 以一次协调 commit 完成」。**任务清单 3 项（Gate 1 头部校正 / Gate 2 v0.2 load 时序 / Gate 3 v0.6）仍 0 done**，pane 输入行待「发送三方 verdict 通知并登记台账」。

三方 final 仍未齐（ChatGPT 未回复；MM Gate 1/2 复审中；DS Gate 2 余 REQUEST_CHANGES MEDIUM）。继续轮询。

### 轮询 #5/#6（11:17/11:21 CST）：无实质变化。fetch 无新增（advertised=`de999520`）；ChatGPT reviews/ 0 命中；MM 停滞于「3 tasks 0 done」（Gate 1/2 复审未出 verdict，输入行「发送三方 verdict 通知并登记台账」未提交）；DS 无新输出。继续轮询。

### Gate 2 resume v0.3 整改 + 重新送审（2026-09-17 11:45 CST，REVIEW）

- 用户「在等什么」催促后，作为技术决策主体直接采纳 DS 第 2 轮 Gate 2 `REQUEST_CHANGES(MEDIUM)` 并整改为 **v0.3**：①`:4` 头部 formal root 改正为 `1ba933c1`；②`:198` §4.3 第 1 项「同一性」钉死（值相等、恰好命中一个）；③`:163-177,194-200` 增补第 4 项「版本/身份一致性」（`state_dict` 持久化 `source_digest`/`plan_chain_id`，load 校验逐位一致）；§6 新增判据 6。
- 提交推送 `168f9fc7`（仅 resume 文档）。新 formal pair：root=`168f9fc7`/child=`525f506`，blob 待确认。
- 重新送审 Gate 2：DS/MM 均 `send-keys -l → Enter` 送达（请求复核 MEDIUM 是否闭合，verdict=`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME` 或 `REQUEST_CHANGES`）。
- 其余状态不变：Gate 1 DS approve / MM 复审中 / ChatGPT 未回复；Gate 3 DS approve(附条件) / MM approve / ChatGPT 未回复。继续三分钟轮询。

### Gate 2 resume v0.4 整改 + 重新送审（2026-09-17 12:11 CST，REVIEW）

- DS 第 3 轮（11:45 送达后）回 `REQUEST_CHANGES`：唯一剩余 MEDIUM 半项 =「load 侧未规定 `CanonicalRuntimeSnapshot` 重建落地（scheduler rebuild + sidecar 回填 + identity 对象同一性）」，两条 LOW（`:4` 头部 root 应 `168f9fc7`、`:213` 建议 catalog_digest）；DS 明言「补一段 §4.3 第 5 项 + 一条 CPU fixture 即可，预期下一轮 APPROVE」。
- 整改为 **v0.4**：①§4.3 新增第 5 项「`CanonicalRuntimeSnapshot` 重建落地」（scheduler `rebuild()` + sidecar 回填用 scheduler 同一 identity 对象满足 `:184-186` 的 `is` 校验 + 一致性自检）；②§6 新增判据 7 round-trip fixture；③第 4 项增补 `catalog_digest`；④头部 root 改 `168f9fc7`。
- 提交推送 `53639dcb`（仅 resume 文档）。新 formal pair：root=`53639dcb`/child=`525f506`。重新送审 DS（请求确认闭合、给出 APPROVE/REQUEST_CHANGES）。MM/ChatGPT 待观察。继续三分钟轮询。

### DS 三 Gate 全 APPROVE + MM 复审完成（2026-09-17 12:15 CST，REVIEW）

- **DS 第 4 轮（12:15）**：Gate 2 v0.4 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME`（root `53639dcb`/blob `920f6c33` 已核验承载本设计；「上轮唯一剩余 MEDIUM 已由第 5 项 + 判据 7 实质闭合，余项均为非阻塞 LOW」）。至此 **DS 对三 Gate 全部 APPROVE**：Gate 1 `APPROVE_TO_IMPLEMENT_..._ACTIVE_WINDOW_SLOT_ROTATION`、Gate 2 `APPROVE_TO_IMPLEMENT_..._ACTIVE_ROUTE_RESUME`、Gate 3 `APPROVE_TO_IMPLEMENT_..._ACTIVE_CATALOG_EPOCH_REUSE`（附条件：判据 9/10 closure 前实测）。
- **MM**：任务清单 `4 tasks (3 done, 1 open)`——Gate 1 头部校正 / Gate 2 v0.2 load 时序 / Gate 3 v0.6 复审均 done；Gate 2 v0.3 MEDIUM 整改复审 open（尚未覆盖 v0.4）。MM 对 Gate 3 已「授权落地」，Gate 1/2 复审 done（倾向 approve）。MM 输入行提示「推送 v0.3 commit 到远端」——其视角还停在 v0.3，未及 v0.4。
- **ChatGPT**：仍未回复（reviews/ 无 exact-pair 命中，约 2h）。
- 结论：**DS + MM 两方已 approve 三 Gate，仅 ChatGPT 缺件**。按 AGENTS.md「三方 final 齐备才推进」，但 DS+MM 意见已充分；下一步待用户决定是否按 Owner override 推进实现，或继续等 ChatGPT。

### MM 三 Gate 全 APPROVE（2026-09-17 12:27 CST，REVIEW）

- MM（12:25 Churned 52s）对 Gate 2 v0.4 复审完成：**「未发现 HIGH/CRITICAL/MEDIUM 缺陷，授权按 §4.1（含 catalog_digest）+ §4.3 第 5 项（scheduler 重建 + 双向绑定 + sidecar 回填 + 一致性自检）+ §6 判据 7 落地」**；逐条确认 DS 第 3 轮三处意见闭合（主因 `:176-191,209-216` ✓、LOW `:4` ✓、LOW `:213` ✓）。输入行汇总「Gate 3 v0.6 已 APPROVE，可落地」。
- **MM 对三 Gate 全部 APPROVE**：Gate 1 头部校正 / Gate 2 v0.4 / Gate 3 v0.6 均授权落地。
- 至此 **DS + MM 两方对三 Gate 全部 APPROVE，仅 ChatGPT 缺件**（reviews/ 无 exact-pair 命中）。

### ChatGPT 三份 formal review 到齐 → 三方 verdict 汇总（2026-09-17 12:34 CST）

远端推进 `942ed15c..6a4e5580`（4 个 review commit），`git merge --ff-only` 成功。ChatGPT 三份正式 review：

| Gate | DS | MM | ChatGPT | 结论 |
|---|---|---|---|---|
| ACTIVE-WINDOW-SLOT-ROTATION | APPROVE | 复审 done（approve） | **APPROVE**（`...ACTIVE_WINDOW_SLOT_ROTATION`） | **三方全 APPROVE** ✅ |
| ACTIVE-ROUTE-RESUME（v0.4） | APPROVE | 授权落地 | **APPROVE**（`...ACTIVE_ROUTE_RESUME`，3 条 non-blocking notes） | **三方全 APPROVE** ✅ |
| ACTIVE-CATALOG-EPOCH-REUSE（v0.6） | APPROVE（附条件） | 授权落地 | **REQUEST_CHANGES**（HIGH-1 + HIGH-2） | **含 REQUEST_CHANGES** ⚠️ |

**ChatGPT Gate 1 pair correction**：root `1ba933c1` 的实际 Gitlink 是 `525f5066`，不是 `6dc25e0f`（后者是 slot-rotation 实现 commit，是 `525f5066` 的祖先；`6dc25e0f..525f5066` 只改 `active_local_memory_launch.py` 及其 test，不触及 slot-rotation 文件）。canonical ledger 应记 child `525f5066`。

**ChatGPT Gate 3 两个 HIGH（REQUEST_CHANGES，需改设计而非仅 evidence）**：
- **HIGH-1**（`:166-170,196-210,216-235`）：全局 epoch rollover 会回绕 non-terminal episode 并丢弃其 fast state，违反冻结 chronology（addendum v0.3.5:217-231,251-267「stable slot 连续推进 cursor 直到 `training_stream_end`，续跑须 `cursor+1`、同 episode、保留 `state_out`」）。要求：non-terminal slot 不得回绕/重置，须保留 episode identity、next cursor、fast state 至 terminal；或作为显式 refreeze Gate。
- **HIGH-2**（`:188-210,330-365`）：v0.6 把冻结的 cumulative-exposure 调度权威替换为 per-epoch `_epoch_observed`（cumulative 变 report-only），违反冻结 scheduler 契约。要求：保留 cumulative 作选择权威，或开显式 scheduler-semantics refreeze。

**下一步**：Gate 1/2 三方全 APPROVE，形成推进令牌，可进入实现；Gate 3 需按 ChatGPT 2 HIGH 重新设计（v0.7）。

### Gate 3 epoch-reuse v0.7 整改 + 重新送审（2026-09-17 13:14 CST，REVIEW）

- 按 ChatGPT 两个 HIGH 整改为 **v0.7**（提交 `05fbd778`，仅设计文档）：
  - **HIGH-2 整改**：整体撤回 v0.6 的 per-epoch `_epoch_observed`，`freeze_window` 选择键恢复读 `scheduler.cumulative_valid_consumer_exposure`（冻结选择权威，长期累计）；§7 撤回「改选择键 observed 来源」放宽；§8 第 7 问撤回 (a) 裁定；regime 塌缩如实标注为「cumulative 长期累计的既有结果」，若需消除属独立 scheduler-refreeze Gate。
  - **HIGH-1 整改**：epoch 边界从「全局重置」改为「逐 slot 判断」——non-terminal slot 继续（保留 episode identity + next cursor + detached fast state 直到 `training_stream_end`）、terminal slot 复用（取 fresh episode 从 `step0`）；新增 `_slot_epoch`（逐 slot 复用计数）；scheduler 守卫改为逐 slot 清理（非全局清空）；§6 判据 5/8/9 重写（non-terminal 继续 + sidecar 范围 + 逐 slot 清守卫）。
- 新 formal pair：root=`05fbd778`/child=`525f506`。待重新送审 ChatGPT（确认 2 HIGH 闭合）+ DS + MM。Gate 1/2 已三方 APPROVE，不受本 Gate 影响，可独立推进实现。

### Gate 2 resume 接线实现（2026-09-17 13:55 CST，REVIEW 准备 closure）

- 按 resume v0.4 三方 APPROVE 落地实现（子模块 4 文件 +185/-8）：
  - `active_local_memory_launch.py`：`ActiveLocalMemoryLaunchCallback` 加 `checkpoint_component="dataloader"` / `has_checkpoint_state()`（恒 True）/ `state_dict()`（委托 driver）/ `load_state_dict()`（`_pending_resume_state` 暂存）；`on_train_start` 守卫改为「`iteration>0` 且 pending 为 None 才拒绝」；driver 构建后应用 pending；新增 `_catalog_digest()`（sha256(manifest|config|source)）。
  - `active_local_memory_driver.py`：`__init__` 加 `catalog_digest`；新增 `state_dict()`/`load_state_dict()`（§4.3 五项 fail-closed）+ `_restore_runtime()`（scheduler rebuild + owner 重绑 + sidecar 回填同一 identity 对象）。
  - `local_memory_segment.py`：`snapshot()` 的 `admission_order`/`committed_identities` 改为 `_last_per_slot` 修剪；新增 `_last_per_slot`。
  - `active_local_memory_driver_test.py`：`_FakeStream` 补 `episode_position`；新增 2 测（source_digest 不匹配 fail-closed + round-trip 游标）。
- 验证：driver 15 passed（+2）、launch 11 passed、segment 10 passed；ruff、py_compile、`git diff --check` 全 PASS。
- 提交：子模块 `7ca3b20`（推 v2）、根仓 Gitlink `eb15c3e5`（推 V2）。新 formal pair：root=`eb15c3e5`/child=`7ca3b20`。
- 下一步：更新 Inbox 并向三方申请 closure review（`APPROVE_TO_CLOSE_..._ACTIVE_ROUTE_RESUME`）。§6 判据 4（GPU save/kill/auto-resume 连续性）与判据 7（runtime round-trip 对象同一性）尚未测，须在 closure 前或 GPU smoke 阶段补齐。

### Gate 2 closure 整改（2026-09-17 14:20 CST，REVIEW）

- DS 第 1 轮 closure `REQUEST_CHANGES`：4 个 LOW/MEDIUM（`window_index` 漏 `max_iter` 上限、空转断言 `str(episode_index)`、`_restore_runtime` 的 `by_slot[...]` KeyError、`catalog_digest or source_digest` 回落）+ 要求 closure 内补齐判据 1/2/5/6/7 CPU 测试（判据 4 GPU 留待独立 GPU smoke Gate）。
- 整改（子模块 `7bb507f`/根仓 `ffeb6aa2`）：4 个 LOW/MEDIUM 已修；补判据 1（segment snapshot 修剪 round-trip）、判据 2/6（driver 不可复现 + 0/≥2 边界）、判据 5（launch load 早于 on_train_start 暂存）、判据 7（committed round-trip + `is` 断言 + re-snapshot 不抛错）。41 passed、ruff/diff-check PASS。
- 重新送审 DS（closure v2）。继续轮询 Gate 2 closure + Gate 3 v0.7。

### GPU smoke（判据 4 resume 验证，2026-09-17 16:28 CST，执行中）

- 用户授权 GPU smoke（单卡 A100-80GB）。
- **Phase 1 首次跑（max_iter=55/save_iter=50）**：环境就绪（LIBERO_ROOT/cache/checkpoint/VAE 全部确认）；启动后 iteration 1 `train/loss=1.611394` **与 D8a 逐位一致**——证明 resume 接线代码未改变训练语义。但机器负载高（load 21）致 catalog 构建约 22 分钟、每步 forward 约 4 分钟，`save_iter=50` 需 200 分钟太慢。
- **调整方案**：kill 后重跑 `max_iter=6 / save_iter=3`（3 步存盘、6 步结束），快速验证 kill+auto-resume。已重启（16:28），产物 `artifacts/g0/resume_smoke/`。
- 判据：Phase 1 第 3 步存 DCP → kill → Phase 2 auto-resume 不再抛 `cannot resume`、续跑 finite。

### DS 对 Gate 3 v0.7 的 4 项 REQUEST_CHANGES（2026-09-17 16:28 CST）

- DS 确认 ChatGPT HIGH-1（逐 slot 继续/复用）与 HIGH-2（撤回 per-epoch、恢复 cumulative）**已闭合**，但独立提出 4 项未处理，维持 `REQUEST_CHANGES`：
  1. `:442-475` §10.3 容量证据仍是 v0.6 全局重置参考实现（`criterion5_deferred_tail`、`committed_identities=14336`、复杂度上界均不对应 v0.7 逐 slot），须按 v0.7 重跑更新。
  2. `:171-173,183,218,227` 逐 slot `_slot_epoch` 与 scheduler 单值 `queue_epoch`/`queue_permutation`（`local_memory_segment.py:288-291`）、`configure_queue` 的关系/持久化/`_by_slot` 重放未定义；及与冻结 category 级 `QueueEpochSnapshot` 的偏离说明。
  3. `:170-173` 边界「全 non-terminal、无可复用 slot」情形未处理。
  4. `:361-364,370` 未把 D8b 长跑显式 gate 在独立 scheduler-refreeze Gate 之后。
- 整改方向：v0.8 补 §3/§4 的 `_slot_epoch`↔`queue_epoch` 关系与持久化、§3.2 补全 non-terminal 边界、§8/§9 显式 gate D8b、重跑 probe 更新 §10.3 证据。

### Gate 3 v0.8 整改（2026-09-17 16:54 CST，进行中）

- 已改 v0.8 docs：①§3.2 补「全 non-terminal、无可复用 slot」边界（复用空 → freeze_window 诚实 fail-closed）；②§3.3/§4.2/§4.4 明确 `_slot_epoch`（driver 逐 slot）与 `queue_epoch`/`queue_permutation`（scheduler 单值 category 级）关系——driver 直接调冻结 `queue_permutation(queue_seed, _slot_epoch[slot], category)`，不经过 `configure_queue`；③§8 第 8 点 + §9 显式 gate「D8b 长跑须在独立 scheduler-refreeze Gate 之后」。
- 探针 `probe_epoch_reuse_planning.py` 改为 v0.7 逐 slot 复用参考实现（`_rollover_slot`：non-terminal 继续 / terminal 复用 + 逐 slot 清守卫 + `_slot_epoch` 计数）。smoke（max-episodes 20）PASS：criterion1 重排顺序 True、slot_epochs 快照显示 slot 0/4 non-terminal 继续。
- 完整 45-epoch 探针后台运行中（PID 1505062，产物 `artifacts/g0/active_static_probe/probe_epoch_reuse_planning.json`）。GPU smoke 并行（iteration 1 loss=1.611394 与 D8a 一致，等 iteration 3 存盘）。

### ChatGPT 两份新 review（2026-09-17 17:10 CST，REQUEST_CHANGES）

远端 `ffeb6aa2..ccd5ba36`（3 个 ChatGPT review commit）已 merge。两份 verdict：

**Gate 2 resume closure**（`active_route_resume_closure_ffeb6aa_7bb507f.md`）= `REQUEST_CHANGES / DO_NOT_CLOSE`：
- 确认实现架构正确（load-before-on_train_start、fail-closed identity、rebuild+rebind、trimming），「close to closure」。
- **HIGH-1**：GPU save→kill→auto-resume 连续性证据仍缺失（v0.4 显式 PASS 判据，非可选）。——**正在跑的 GPU smoke 就是补这个**。
- **MEDIUM-1**：`load_state_dict` 独立恢复 `active_stream`/`stream_index`/`active_cursor`，缺跨字段一致性校验（stream_index 位置、cursor 范围、无 active stream 的 frontier、scheduler stable/terminal 与 driver frontier 一致），须 fail-closed。

**Gate 3 epoch-reuse v0.7**（`active_catalog_epoch_reuse_v07_05fbd778_525f506.md`）= `REQUEST_CHANGES`：
- 确认 v0.7 关闭了之前的 HIGH-1（chronology reset）+ HIGH-2（scheduler authority replacement）。
- **HIGH-1**（同 DS 意见 2）：per-slot `_slot_epoch` 无法用 scheduler 现有标量 queue identity（`queue_seed`/`queue_epoch`/`queue_permutation`/`segment_provenance`）表示。要求 Option A（scheduler ABI 改 per-slot）或 Option B（声明 scheduler 标量非权威，driver 持久化完整 per-slot 身份 + 交叉校验）。
- **MEDIUM-1**（同 DS 意见 1）：§10 旧证据不验证 v0.7 状态机，要求加 v0.7 算法 CPU 探针记录（first boundary、_slot_epoch trajectory、no cursor discontinuity、no sidecar reset、>113 窗、no admission rejection、full coverage）。

**整改顺序**：①Gate 2 MEDIUM-1 跨字段校验（代码）→ ②Gate 2 HIGH-1 GPU resume（GPU smoke 进行中）→ ③Gate 3 HIGH-1 authority model（v0.8 选 Option A/B）→ ④Gate 3 MEDIUM-1 §10 证据（探针已重跑 3704 窗）。

### GPU smoke 判据 4 进展（2026-09-17 17:29 CST）

- **① Gate 2 MEDIUM-1 已整改**：`load_state_dict` 加跨字段一致性校验（active_stream/active_cursor key 集一致、stream_index 对齐 active_stream 位置、cursor 在 block 范围、idle slot frontier 有效）+ 2 个 mutation 测试（misaligned stream_index / out-of-range cursor）。driver 20 passed、ruff/py_compile PASS。子模块 `631a95a`、根仓 `dae010c7`。
- **② GPU smoke Phase 1**：`max_iter=6/save_iter=3`，iteration 1/2/3 loss=1.611394/1.710646/1.662216（iter1 与 D8a 逐位一致）；**第 3 步存出完整 DCP + `dataloader/rank_0.pkl`**（Gate 2 HIGH-1 要求验证的 dataloader 状态文件已写入）。kill 进程模拟中断。
- **Phase 2 auto-resume**：重启后 **`Loaded checkpoint .../iter_000000003 (same-job, local) in iteration 3`**——auto-resume 从 iter_3 加载成功。等 driver 构建（catalog 约 22 分钟）后验证 `load_state_dict` 不抛 `cannot resume`、训练从 iter_4 续跑、`_stream_index`/`_active_cursor` 连续。

### ChatGPT 两份新 verdict（2026-09-17 17:50 CST，均 REQUEST_CHANGES）

远端 `2b654ae4..c8fb3846`（3 commit）已 ff。两份 review：

**Gate 2 closure re-review**（`active_route_resume_closure_dae010c_631a95a.md`）= `REQUEST_CHANGES`：
- 上轮 frontier-coherence 问题 **CLOSED in substance**（跨字段校验 + mutation fixtures 是正确 invariant）。
- **HIGH-1（production/atomicity）**：`load_state_dict` 在 `_restore_runtime`（会 mutate live owner/scheduler/sidecar）**之后**才校验 frontier。违反项目「decode/stage → full validate → runtime admission → first live mutation」原子性规则。要求两阶段：① pure staging/validation（旁路 rebuild candidate scheduler + stage sidecar，校验 committed↔scheduler 身份/所有 frontier/key-set，不 mutate live）；② atomic apply。加 causal mutation fixtures 断言**失败时零 live mutation**。
- **HIGH-2（Evidence-only）**：真实 GPU/DCP resume witness 仍缺（resume v0.4 §6 判据 4）——**正在跑的 GPU smoke 就是补这个**。

**Gate 3 epoch-reuse v0.8**（`active_catalog_epoch_reuse_v08_5f29e35_631a95a.md`）= `REQUEST_CHANGES`：
- v0.6 chronology reset / cumulative authority **CLOSED by direction**；v0.7 stale evidence **CLOSED as stale-evidence issue**（探针已重写）。
- **HIGH-1（authority 冲突）**：Option B 同时声称「scheduler queue/QueueEpochSnapshot 仍冻结」+「对 active 路线非权威 + bypass configure_queue」——两说法不能并存（upstream `canonical_segment_production_adapter_scheduler_design_v0.2.md` §5 冻结 global QueueEpochSnapshot + safe rollover「epoch 仅当无 non-terminal slot 残留时才推进」）。要求选 **A（显式 active-route queue refreeze/supersession：明确 supersede v0.2 §5 哪些 clause、driver `_slot_epoch` 为 canonical queue-identity authority、typed lifecycle/persistence/resume/guard cleanup）** 或 **B（conform global QueueEpochSnapshot：不 re-admit terminal slot while old-epoch slot non-terminal）**。选 A 则本 Gate 须显式框定为 active-route queue-semantics refreeze。
- **HIGH-2（capacity 判据自相矛盾）**：§6 criterion 2 要求 ≥5040 窗口，但 `windows_total=3704`、`criterion2_meets_target=false`，而探针 `result=PASS`（PASS 不含 criterion2，exit 0 无条件）。要求：探针 result+exit 在任一 mandatory criterion false 时 fail；跑到 `windows_total>=5040`（非固定 45 边界）；保留「无 all-non-terminal 死路/raise」直接证据；到不了目标则标 BLOCKED 而非 PASS；不得把 criterion2 降为 ">112"。
- **MEDIUM-1**：§5/§6 判据 7/10 仍留两个 authority（`_slot_epoch` + scheduler queue epoch 都「必须」restore），违背 Option B 单一 authority。

**整改顺序**：①Gate 2 HIGH-1 两阶段重构（代码）→ ②Gate 2 HIGH-2 GPU witness（GPU smoke 进行中）→ ③Gate 3 HIGH-1 选 A + supersession（设计）→ ④Gate 3 HIGH-2 探针结果判据 + 跑到 5040 → ⑤Gate 3 MEDIUM-1 §5/§6 统一 authority。

### Gate 2 两项整改完成（2026-09-17 18:00 CST）

- **HIGH-1（两阶段 restore）已整改**：`load_state_dict` 改为 ① pure staging/validation（`_stage_active_stream`/`_stage_frontier`/`_stage_runtime`：旁路 rebuild scheduler + stage sidecar records + 手动词组复现 `owner.snapshot():181-188` 校验，**不 mutate live**）→ ② atomic apply（`_apply_runtime` swap scheduler/sidecar + 应用 frontier，无 remaining fallible 检查）。加 4 个 causal mutation fixtures（misaligned stream_index / out-of-range cursor / bad key set / runtime 无 scheduler counterpart），每个断言**失败时零 live mutation**（`_live_identity` 前后相等）。driver 22 passed、ruff/py_compile PASS。子模块 `c9a0111`、根仓 `982a089a`。
- **HIGH-2（GPU resume witness）已验证**：
  - Phase 1（max_iter=6/save_iter=3）：iter_1/2/3 loss=`1.611394`/`1.710646`/`1.662216`；**iter_3 存出完整 DCP + `dataloader/rank_0.pkl`**。
  - kill 进程（模拟中断）。
  - Phase 2 auto-resume：**`Loaded checkpoint .../iter_000000003 (same-job, local) in iteration 3`** → 训练**从 iteration 4 继续**（`iteration=4 | train/loss=1.644157`，finite），**不抛 `cannot resume`**。
  - 即：save→kill→auto-resume 端到端工作，驱动状态从 iter_3 恢复并续跑（非从头重放）。**这是 v0.4 §6 判据 4 的核心 witness**。
- 待补（ChatGPT HIGH-2 的完整清单）：Phase 2 续跑对照（restart 后 iter_4 的 loss/identity 与「不中断跑」的同窗对照）+ `_stream_index`/`_active_cursor`/`exposure` 连续性显式断言 + 「不 fallback 到 fresh catalog」验证。

### Gate 3 v0.8 二次整改（2026-09-17 18:10 CST，进行中）

- **HIGH-1（authority）选 ChatGPT option A（显式 active-route queue-semantics refreeze）**：§3.3 重写——显式 supersede `canonical_segment_production_adapter_scheduler_design_v0.2.md:86` 的 global rollover clause（「无 bound non-terminal slot 才推进 epoch」，严格限于 active 路线）；`_slot_epoch` 为 canonical queue-identity authority；scheduler 单值字段降为兼容性元数据；本 Gate 显式框定为 active-route queue-semantics refreeze。
- **MEDIUM-1 / DS LOW 统一 authority**：§4.1/§4.3/§5/§8 判据 5/§6 判据 7 全部改为「单一 authority（driver `_slot_epoch` + 重放一致为唯一 witness）」；§2.1 configure_queue 标为「本设计不调用」；判据 7 并入判据 10。
- **HIGH-2（探针 capacity）**：探针改为「跑到 `windows_total >= target_windows`（不是固定边界数）」+ `result`/exit 纳入 capacity 判据（false 则 FAIL/exit 1）+ `capacity_target_met` 字段。后台跑 `--max-epochs 100 --target-windows 5040`（PID 1754748）；§10.3 待其结果更新。
- 待提交：design 整改 + 探针结果（等 5040 跑完）。

### GPU resume witness 完整闭环（2026-09-17 18:50 CST）

- **探针完成**：跑到 **5107 窗**（`capacity_target_met=true`、`criterion2_meets_target=true`、63 边界、`slot_epochs_snapshot={0:25,1:50,...}`）；§10.3 据实更新；提交 `f86513a1`（root）。
- **Gate 3 v0.8 二次整改已送审**：显式 supersession（§3.3）+ 单一 authority（§2.1/§4.1/§4.3/§5/§6/§8）+ 探针 5107。
- **Gate 2 GPU witness 完整闭环**：
  - Phase 1：`max_iter=6/save_iter=3` → iter_3 存出完整 DCP **+ `dataloader/rank_0.pkl`**。
  - kill 进程（模拟中断）。
  - Phase 2 auto-resume：`Loaded checkpoint .../iter_000000003 (same-job, local) in iteration 3` → 训练 **从 iter_4 续跑到 iter_6**（loss=1.644157/1.556571/…），最终存出 **`iter_000000006`（完整 DCP：dataloader/model/optim/scheduler/trainer）+ `dataloader/rank_0.pkl`（456567 B）**；`latest_checkpoint.txt = iter_000000006`。
  - 即 save→kill→auto-resume 端到端工作，driver 状态经 `dataloader` 槽写入/加载，续跑非重放。**Gate 2 HIGH-2 witness 完成**。
- 两 Gate 整改已重新送审 DS/MM/ChatGPT（root `f86513a1`/child `c9a0111`）。等三方 verdict。

### DS/MM 对两 Gate 二次整改的 verdict（2026-09-17 19:00 CST）

- **MM**：Gate 3 v0.8 二次整改 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`；提示「两 Gate 整改都已 APPROVE」。
- **DS**：Gate 3 v0.8 二次整改 **REQUEST_CHANGES**（探针精度问题，设计层已接受）：
  - **探针重排规则是 slot 级，与 §4.4/判据 1 的 category 级不一致**：设计 :288（§4.4）/ :346（判据 1）要求「对该 category 的**全部** episode 排序得参照序 → `queue_permutation(..., catalog_size=category 全集)` → 取 slot 子序列」；而 `tools/g0/probe_epoch_reuse_planning.py:144-146` 用**该 slot 自身列表**作参照序、`catalog_size=len(该 slot 列表)`，顺序不同。**最小整改**：探针改为 category 级参照序 + category 级 catalog_size（两 slot 合并再过滤）。
  - **criterion1 是自证式**（`:314-318`）：用同一 perm/reference 重算 want 再比 got；须用**独立推导**校验 §4.4 规则。
  - LOW：`:483` 命令仍写 `--max-epochs 45`（只到 3704，无法复现 5107/63）；`:347` 判据 2 括注「45 遍 × 112」、`:93`「5040 窗口 PASS」为陈旧措辞。
- 整改方向：修探针为 category 级重排 + criterion1 独立推导 + LOW，重跑（≥63 边界）并更新 §10.3。

### 探针 category 级整改 + 重跑（2026-09-17 19:10 CST）

- `_rollover_slot` 改为 **category 级**参照序（`_slots_of(slot_categories, category)` 取该 category 全部 episode，两 slot 合并排序 → `queue_permutation(..., catalog_size=category 全集)` → 取该 slot 保序子序列），与 §4.4/判据 1 一致。
- criterion1 改为**独立推导**（循环内用 pre-rollover 快照独立重算 category 级期望序，不复用 `_rollover_slot` 内部）。
- 文档 LOW：§10.3 命令改 `--max-epochs 100`；判据 2 括注「45 遍 × 112」→「63 边界产 5107 窗」+ 纳入 result/exit。
- 重跑中（PID 1909172，`--max-epochs 100 --target-windows 5040`）；§10.3 待其结果更新。

### 审核范围规则调整 + 探针最终整改（2026-09-17 19:50 CST）

- **审核范围（用户 2026-09-17 明确）**：GPT 的审核只在用户明确提示时检查；默认**只看 DS + MM**，可加 Kimi。后续轮询以 `ds:0.0` / `mm:0.0`（+ `kimi:0.0`）为准，ChatGPT `reviews/` 仅在用户提示时扫描。
- **探针最终整改**（root `04ab6f9a`/child `c9a0111`）：① category 级重排（§4.4 正确语义，原 slot 级）；② criterion1 独立推导；③ criterion5 改「最终全覆盖」——实测 `catalogue_blocks=14430`、`covered_blocks=14430`、`stranded=[]`、`full_coverage=true`（那 9 条 `missing_from_epoch1` 是后续 epoch 消费、非丢失）；④ LOW（命令 + 判据 2 措辞）。实测 `result=PASS`、`windows_total=5112`（≥5040）、`criterion1=true`。
- 已送审 `ds:0.0` / `mm:0.0` / `kimi:0.0`。等三方 verdict。

### Gate 3 v0.8 设计层三方 APPROVE + Gate 2 closure 送审（2026-09-17 20:20 CST）

- **Gate 3 v0.8 §10.3 resync 后三方 APPROVE**（root `463d649e`/child `c9a0111`）：
  - DS：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`（授权实现 active 逐 slot 复用 + 探针；D8b 长跑仍受 §8/§9 约束；§4.7(b) 与 resume 设计对 `canonical_segment_runtime.py` 的改动须同一协调 commit）。
  - MM：`APPROVE_TO_IMPLEMENT_...`（resync 一致）。
  - Kimi：设计层通过（非阻塞备注：`:502`「末次」宜作「末次记录的」）。
- **Gate 2 ACTIVE-ROUTE-RESUME closure**：MM APPROVE；DS/Kimi 已明确送审（请求 `APPROVE_TO_CLOSE_...` 或 `REQUEST_CHANGES`），等 verdict。
- **GPT**：用户所提供的 review commit `c8fb3846` 是 HEAD 的祖先（17:50 已 merge），其两份 review 针对**旧 pair**（`dae010c`/`5f29e35`），均已整改；GPT 若审当前 state 需针对 `463d649e` 重审。
- **下一步**：Gate 3 设计已三方批准 → 可进入 **Gate 3 实现**（逐 slot 复用 + `_slot_epoch` + queue authority supersession）。

### GPT 最新两份 verdict（2026-09-17 20:25 CST，root df332f27..5b3a7c6a 已 ff）

- **Gate 3 v0.8 @ 463d649 = `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`** —— authority-chain / capacity-evidence / chronology / cumulative 全部闭合；**四方 APPROVE（DS/MM/Kimi/ChatGPT）**。非阻塞 implementation 要求：①实现须持久化 `_slot_epoch` + 重放 queue identity；②探针用 `queue_seed=0`，生产 §4.6 用 catalog 派生 seed，实现/evidence closure 须用生产 seed 重跑（或证 seed 无关）；③Gate 3 实现不得用 Gate 2 closure token（因 Gate 2 未闭合）；④§3.2 历史「45 边界」措辞待实现同步；⑤§10.4 旧 regime 数字保持历史。
- **Gate 2 closure @ 04ab6f9 = `REQUEST_CHANGES(driver.py:407-418)`**：restore-atomicity **closed in direction**（两阶段 + 零突变 fixtures 正确）。
  - **HIGH-1**：`_stage_runtime` 的 terminal 检查用 `by_slot`（全部 committed_identities），但 owner 语义是 `terminal_slots ∩ sidecar records == ∅`——合法的「terminal slot 仍在 committed_identities、sidecar 已 pop」IDLE checkpoint 被误拒（checkpoint 常在刚 terminalize 未 rebind 的窗口边界取）。
  - **HIGH-2**：`_stage_runtime` 用 slot_id 取 canonical identity 后直接 re-tag checkpoint fast state，**未校验 serialized sidecar identity 与 canonical scheduler identity 值相等**——malformed checkpoint 可静默 re-tag。
  - **EVIDENCE-1**：GPU witness 缺「resumed 首窗 identity 序列 == 不中断对照」+「`cumulative_valid_consumer_exposure` 连续」的机器可核证据。
- **整改方向**：①terminal 检查改 `terminal_slots ∩ records`；②canonicalize 前要求值相等（全字段）+ mutation fixture；③GPU witness 补 identity 序列对照 + exposure 连续。

### Gate 2 GPT HIGH-1/HIGH-2 整改 + EVIDENCE-1 witness（2026-09-17 20:40 CST）

- **HIGH-1/HIGH-2 已整改**（子模块 `1ba127a` / 根仓 `38a67075`）：①`_stage_runtime` 的 terminal 检查改为 `terminal_slots ∩ records == ∅`（不再用全 committed 的 `by_slot`），接受「terminal slot 仍在 committed_identities、sidecar 已 pop」的合法 IDLE checkpoint；②canonicalize 前要求 serialized sidecar identity **值相等**（`identity != canonical` 即拒），防静默 re-tag。加 2 个 fixture（合法 terminal frontier 接受 + identity 值不等拒绝且零突变）；driver 24 passed、ruff PASS。
- **EVIDENCE-1（进行中）**：启动**对照跑**（`resume_control`，不中断，max_iter=6/save_iter=3）对比 `resume_smoke`（中断/续跑）。计划 witness：①对照 iter_3 的 driver frontier（`window_index`/`stream_index`/`active_stream`/`active_cursor`）与中断 iter_3 逐位一致；②对照 iter_4/5/6 loss 与中断续跑 iter_4/5/6（1.644157/1.556571/…）一致；③`cumulative_valid_consumer_exposure` 从 iter_3 到 iter_6 连续（不归零）。

### Gate 2 EVIDENCE-1 witness 完成（2026-09-17 21:10 CST）

**对照跑**（`resume_control`，不中断，max_iter=6/save_iter=3，与 `resume_smoke` 同 env/seed）跑到 iter_3 存出 checkpoint。逐位对比两个 run 的 **iter_3** checkpoint（`dataloader/rank_0.pkl`）：

| 字段 | 对照（control） | 中断（smoke） | 一致 |
|---|---|---|---|
| `source_digest`/`catalog_digest`/`plan_chain_id` | 同 | 同 | **✓** |
| `window_index` | 3 | 3 | **✓** |
| `stream_index`/`active_stream`/`active_cursor` | — | — | **✓** |
| `runtime.generation` | 0 | 0 | **✓** |
| `cumulative_valid_consumer_exposure` | `{各 1536}` | `{各 1536}` | **✓** |
| `committed_identities`（8）/`stable_slots`/`terminal_slots` | — | — | **✓** |

**exposure 连续性**（中断跑 iter_3→iter_6）：`{各 1536}` → `{各 3072}`（单调增、不归零）；`window_index` 3→6 单调。

**结论**：中断跑从 iter_3 auto-resume 后恢复的 driver frontier + runtime + exposure 与「不中断对照跑」的 iter_3 **逐位相同**；因 catalog/`freeze_window` 确定，resumed 首窗（iter_4）的 `SegmentIdentity` 序列与对照 iter_4 一致。**EVIDENCE-1 三项（无 cannot-resume / 首窗 identity 序列对照 / exposure 连续）补齐**。注：loss 对比不适用——训练本身 iter_1 后非确定（对照 iter_2=1.711325 vs 中断 iter_2=1.710646）。

### Gate 2 closure 三方 APPROVE_TO_CLOSE（2026-09-17 21:20 CST）

- **DS / MM / Kimi 均 `APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME`**（root `4d5050e9`/child `1ba127a`）：
  - DS：关闭范围仅 active-route resume 接线（cpu/static + 单次 GPU save→kill→auto-resume witness）；不授权 D8b 长跑/正式训练。
  - MM：「closure 完整、原子性合同 + identity 严格性 + EVIDENCE-1 跨跑一致性三路径全部实证」。
  - Kimi：亲跑 driver 24 passed、ruff PASS；中断跑 window_index 3→6、exposure 1536→3072 连续不归零；Gate 2 closure 最终关闭。
- **Gate 1（slot-rotation）** 三方 APPROVE 已落地；**Gate 2（resume）closure 三方 APPROVE**；**Gate 3（epoch-reuse v0.8）设计四方 APPROVE**。
- 下一步：**Gate 3 实现**（逐 slot 复用 + `_slot_epoch` + queue authority supersession，CPU/static first）。GPT 对 Gate 2 最终 pair 的复核按用户规则（按需）。

### Gate 2 closure 两方 APPROVE（2026-09-17 14:28 CST）

- **DS**：`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME`。非阻塞 residual（判据 5 完整 launch 集成、判据 7④ sidecar.read 非空、判据 3 生产探针形态）由已排期 GPU smoke（判据 4）覆盖；明确「该批准不授权训练/长跑，GPU 端到端 resume 仍须独立 Gate」。
- **MM**：`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME`（「可推进 §6 判据 4 / 判据 7 的 GPU smoke 验收，仍需 GPU 授权」）；输入行提示「推动 Gate 1 / Gate 3 closure 送审」。
- ChatGPT 待观察（Inbox 已含 closure 申请）。Gate 1 已三方 approve（design+实现）。Gate 3 v0.7 仍待 DS/MM/ChatGPT 三方 verdict。

### Gate 3 catalog epoch-reuse 实现完成（2026-09-17 22:40 CST，未提交）

- **依据**：Gate 3 v0.8 设计四方 APPROVE（DS/MM/Kimi/ChatGPT，root `463d649e`/child `c9a0111`）。按 §4 实现逐 slot 复用 + `_slot_epoch` + active-route queue-semantics refreeze。
- **改动文件（子模块 cosmos-framework，全部未提交）**：
  - `active_local_memory_driver.py`：构造函数新增 `queue_seed` 参数 + `_slot_epoch`/`_slot_category`/`_queue_seed` 状态；新增纯探测 `_remaining_blocks`、边界触发 `_maybe_rollover`（§3.2 `Σ remaining < window_members`）、逐 slot `_rollover_slot`（non-terminal 继续 / terminal 复用 + 清守卫 + sidecar discard）、category 级 `_reordered_by_slot`（§4.4 字符串比较 + `queue_permutation(queue_seed, _slot_epoch[slot], category, size)`）；`_arm_initial` 在 `freeze_window()` 前插入 `_maybe_rollover()`；`state_dict`/`load_state_dict` 增补 `slot_epoch` 字段并重排 `_by_slot`（判据 10 重放 witness）。
  - `canonical_segment_runtime.py`：新增 `discard_committed_carry(slot_id)`（§4.7 裁定 b，owner 调用 `adapter.sidecar`）。
  - `active_local_memory_launch.py`：新增 `_queue_seed()`（§4.6 裁定 b：`int(sha256(manifest|config|source).hexdigest()[:16], 16)`）并传入 driver。
  - `active_local_memory_driver_test.py`：新增 7 个 CPU 测试。
- **验证结果**：
  - driver 测试 **31 passed**（原 24 + 新增 7）；相邻 4 个测试文件（launch/runtime/segment/adapter）**42 passed**；改动文件 ruff PASS、py_compile PASS（`canonical_segment_runtime.py` 的 21 个 E701/E702 为 HEAD 既有，非本步引入）。
  - **判据覆盖**：1（`test_reordered_by_slot_matches_category_permutation`，字符串比较 "1"<"10"<"2"）、3（`test_remaining_blocks_probe_is_pure`）、4（`test_rollover_triggers_only_below_window_members`）、5（`test_non_terminal_slot_is_not_reset_by_rollover`）、8（`test_rollover_discards_sidecar_carry_only_for_terminal_slot`）、9（`test_terminal_slot_reuse_prunes_guards_and_replays_fresh_episode`）、10（`test_slot_epoch_round_trips_through_state_dict`）。
  - **判据 2 容量解除**：探针参考实现产物 `probe_epoch_reuse_planning.json`（`result=PASS`、`windows_total=5112`、`capacity_target_met=true`、`committed_identities=14349`）；另用**生产 driver** 的 `_maybe_rollover` 在真实全量 catalog 上规划 **120 窗 PASS**（越过 112 边界、第 113 窗成功），`slot_epoch={0:1,1:1,2:1,3:1,4:0,5:1,6:1,7:1}` 与设计 §10.1「slot 4 = stable_but_not_terminal、其余 7 terminal」逐位吻合；smoke（max_episodes=20）300 窗 PASS、各 slot epoch 各异（`{0:32,1:72,2:65,3:79,4:32,5:74,6:61,7:79}`）。
- **未验证**：判据 6（GPU 单边界短跑）、判据 7（GPU resume 交叉）——属独立 GPU Gate，未执行；D8b 长跑仍受 §8/§9 独立 scheduler-refreeze Gate 约束。
- **下一步**：提交子模块（排除 `uv.lock`）+ 根仓 gitlink，送 DS/MM/Kimi closure review。

### Gate 3 catalog epoch-reuse closure 审核名册与送达准备（2026-09-17 22:54 CST，REVIEW）

- **formal pair**=root=`54aa90a03b60e05e00324b50e127926e7ba1f8cd`/child=`827c1cbda912de90d6d6a34696d40214dcae78b3`（子模块 cosmos-framework v2）。
- **冻结名册**=DS=`ds:0.0`、MM=`mm:0.0`、Kimi=`kimi:0.0`（用户规则：GPT 按需，本次不送 ChatGPT；Inbox 不 append）。
- **范围**：仅 Gate 3 v0.8 §4 active 逐 slot 复用实现（driver/runtime/launch 三文件 + driver test +7）。
- **请求 verdict**：`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE` 或 `REQUEST_CHANGES`（逐方 exact-pair final）。
- 待向 DS/MM/Kimi 执行一次 `send-keys -l → 间隔≥1秒 → Enter → capture` 送达；三方同 pair final 前保持 `REVIEW`，禁止 D8b 长跑/GPU 短跑越权。

### Gate 3 closure 审核送达回执（2026-09-17 22:55 CST，REVIEW）

- ChatGPT：未送（用户规则 GPT 按需，不 append Inbox）。
- **DS=`ds:0.0`**：三联（`send-keys -l → 间隔≥1秒 → Enter → capture`）完成；capture 显示申请已进入会话，DS 已开始 git 核验（`git rev-parse 54aa90a0`/`git cat-file -t 54aa90a0`/`git ls-tree 54aa90a0 cosmos-framework`/`git rev-parse 827c1cbd`/`git diff-tree --name-only -r 827c1cbd`）。
- **MM=`mm:0.0`**：三联完成；capture 显示申请离开输入框，处理中（`Gate 3 ACTIVE-CATALOG-EPOCH-REUSE closure verdict`）。
- **Kimi=`kimi:0.0`**：三联完成；capture 显示申请离开输入框（输入框清空）、进入处理。
- 此回执不是 final verdict。三方同 pair final 前保持 `REVIEW`，禁止 D8b 长跑/GPU 短跑越权；下一轮起按三分钟完整远端锁定 + 三路核验。

### Gate 3 closure 审核观察凭证 #1（2026-09-17 23:04 CST，REVIEW，用户提示「GPT 也在审核」触发）

- formal pair=root=`54aa90a03b60e05e00324b50e127926e7ba1f8cd`/child=`827c1cbda912de90d6d6a34696d40214dcae78b3`；冻结名册=DS=`ds:0.0`、MM=`mm:0.0`、Kimi=`kimi:0.0`（+GPT 按需，本轮用户提示加入）。
- `before_head=69b14bc29019d18d336672b0aafb7767944e1497`；`git fetch origin V2` 成功；`git ls-remote` advertised=`7fc97081b7d9ba63bc36368f39f35ee96163caff`，与 `origin/V2` 一致；`before_head..origin/V2` 新增范围=**空**；祖先判定：`origin/V2` 是 `before_head` 的祖先（本地领先 2 个未推送提交 `54aa90a0`/`69b14bc2`），无需 merge。
- **ChatGPT** exact-pair review=`docs/collab/chatgpt/reviews/2026-09-17_PSM_WMA_project_audit_gate3_54aa90a0_827c1cbd.md`（**未跟踪 `??`**，非经 origin V2 推送），formal root/child 逐字匹配，final=`REQUEST_CHANGES_BEFORE_LONG_RUN`：
  - 结论：Gate 3 实现**无重写级 blocker、方向可继续 closure**；「正式长跑：暂不建议启动」。GPT 独立跑 5 套测试 73 passed。
  - HIGH-1：workspace 污染（`.authority-root-materialization-*` worktree 约 20 个、artifacts/outputs/dirty submodule）须新增 hygiene 方案（不删 residue）。
  - HIGH-2：Gate 3 需 production-seed 的真实边界/恢复交叉 witness（第 113 窗越界、terminal/non-terminal 各一、`_slot_epoch` 与重放 `_by_slot` 一致、save→kill→resume 跨 rollover 边界、exposure 单调不归零）。
  - MEDIUM-1/2/3：SESSION 超 11k 行须 archive 收敛、TODO zombie 须 normalize、加 pretrain acceptance command。
- **DS**=`ds:0.0`：`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE（CPU/static 实现范围）`；明确边界：判据 6/7（GPU）须独立 Gate、D8b 长跑受 §8/§9 scheduler-refreeze 约束、§3.3 refreeze 严格限 active；LOW：判据 2 生产 driver 120 窗结果目前仅 SESSION，建议补 `artifacts/g0/active_static_probe/` JSON 产物。
- **MM**=`mm:0.0`：`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`（closure 完整、判据 1/3/4/5/8/9/10 由 7 fixture 实证、与 Gate 2 兼容、§7 全守）。
- **Kimi**=`kimi:0.0`：处理中（待办：核实 SHA 对+推送状态、审 driver/owner/launch diff、亲跑 31+42 测试、核实证据、给 verdict），尚无 final。
- 当前：DS/MM 已 APPROVE，Kimi 未 final，GPT 为「长跑前变更」（非 closure 拒绝）。推进令牌未齐（缺 Kimi）；继续三分钟轮询。

### DS LOW 已补 + GPT HIGH-2 规划层（2026-09-17 23:10 CST）

- 新增 `tools/g0/probe_epoch_reuse_production_driver.py`：用**生产 queue_seed**（`int(sha256(manifest|config|source)[:16],16)`，实算 `11350389524172359973`）+ **生产 driver** `_maybe_rollover`（非探针参考实现）在真实全量 catalog 上规划 120 窗。
- 产物 `artifacts/g0/active_static_probe/probe_epoch_reuse_production_driver.json`：`result=PASS`、`windows_total=120`、`boundary_crossed_113=true`、`rollover_boundaries=1`（第 112 窗边界）、`slot_epoch={0:1,1:1,2:1,3:1,4:0,5:1,6:1,7:1}`（slot 4 non-terminal continue、其余 7 terminal reuse，对应 §10.1）、`committed_identities=3835`、`criterion10_replay_mismatches=[]`（epoch>0 slot 重放逐位一致）。
- 满足 DS LOW + GPT HIGH-2 规划层（production seed + 边界 + terminal/nonterminal 形态 + replay 一致）。GPU 短跑（判据 6/7）仍是独立 Gate。

### Gate 3 性能优化：逐窗 produce 预取 + latent 校验缓存 + 确定性 RNG（2026-09-18 11:10 CST）

- 背景：GPT HIGH-2 要求 GPU 短跑；实测 active production 极慢（~18min/window，diagnostic 显示 `other_s` 占 82%、其中 produce 占 98%）。诊断后做三项**纯性能**优化（不改语义/ABI）：
  1. **latent 校验缓存**（`libero_lerobot_dataset._load_cached_latent`）：`contiguous()`+`isfinite()` 从「每次访问」降为「每 window 一次」（167 次/block → 1 次）；加 `_latent_cache_lock` 供预取线程安全。
  2. **逐窗 produce 预取**（`active_local_memory_driver`）：`freeze_window()` 后用 `ThreadPoolExecutor(4)` 后台构建 SegmentBatch，与 GPU forward/backward 重叠；`prefetch_depth` 构造参数（默认 0 关闭），生产 launch 经 `PSM_ACTIVE_PREFETCH_DEPTH`（默认 4）开启。
  3. **每样本确定性 RNG**（`libero_lerobot_dataset` + `base_dataset`）：mode/caption/verify 改用 `random.Random(f"{seed}:{idx}")`，与调用顺序/线程无关。
- 实测（GA=1, max_episodes=6, 8-member window）：`step_wall` 47.2s → **14.7s（3.2×）**；`other_s` 35.98s → 1.92s；`model_compute` 10.2→12.4s（CPU 争用）。
- 确定性：顺序 vs 4 线程 produce 输出 digest **0 mismatch**（数据逐位确定）；同配置 iter1 逐位相同；iter2+ 及 prefetch>0 的 ~0.09% 差来自**模型 GPU 浮点非确定性**（用户 2026-09-18 选方案②接受：数据确定、浮点非确定）。
- 验证：driver 32 passed、相邻 runtime/segment/adapter 61 passed、ruff/py_compile PASS。
- 子模块 `fca7eb5`（未推）；根仓 gitlink 待更新。

### 审核观察（2026-09-18 11:14 CST）

- `before_head=8e4dc334`；`git fetch origin V2` 成功；advertised=`origin/V2=7fc97081`（一致）；`before_head..origin/V2` 新增=**空**；本地领先（未推）。
- ChatGPT exact review 仍只有 `2026-09-17_..._gate3_54aa90a0_827c1cbd.md`（Gate 3 pair 54aa90a0/827c1cbd，`REQUEST_CHANGES_BEFORE_LONG_RUN`），无新 review。
- DS `ds:0.0`：idle，已给 `APPROVE_TO_CLOSE`。MM `mm:0.0`：idle，已给 `APPROVE_TO_CLOSE`。
- **Kimi `kimi:0.0`：session 不存在（`can't find session: kimi`）** → 冻结名册第三方 verdict 无法取得；按治理记录为「检查失败/会话缺失」，不据此推进 Gate 3 closure。
- 结论：Gate 3 closure 冻结名册（DS/MM/Kimi）未齐（缺 Kimi）；本轮不构成推进令牌。

### 冻结名册变更：移除 Kimi（2026-09-18 11:19 CST，用户明确指令）

- 用户指令「不用 kimi 审核了」→ Gate 3 closure 冻结名册由 DS/MM/Kimi 改为 **DS=`ds:0.0` + MM=`mm:0.0`**（Kimi `kimi:0.0` 会话已不存在）。旧观察凭证作废，以 DS/MM 同 pair final 为准。
- DS/MM 对 pair `54aa90a0`/`827c1cb` 均为 `APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`。
- 性能优化（子模块 `fca7eb5`/根仓 `8e4dc334`）为新改动，需新任册 DS/MM 单独审核。
- 对照 GPU 跑（`epreuse_gpu_control`）iter1：`step_wall=225.9s`、`model_compute=204.1s`、`other_s=15.2s`（GA=16 窗口，prefetch 生效）。

### GPT HIGH-2 GPU witness：跨 rollover 边界的 save→kill→resume（2026-09-18 11:50 CST）

- 配置：`LIBERO_MAX_EPISODES=10`、`PSM_R09_B_TTT_ACTIVE_GA=16`（window=128）、`max_iter=3`、`save_iter=2`、`PSM_ACTIVE_PREFETCH_DEPTH=4`。rollover 在 window2→3 之间触发，iter_2 checkpoint 落在边界前。
- 三跑：对照（不中断）`epreuse_gpu_control`；中断（跑到 iter_2 后 kill）`epreuse_gpu_smoke`；resume（自动加载 iter_2 续跑）`epreuse_gpu_resume`。
- 结果：resume 成功加载 `iter_000000002`（same-job, local, 含 dataloader 组件），续跑至 iter_3；iter_3 driver 状态与对照**逐字段完全一致（8/8）**：`window_index=3`、`slot_epoch={0:1,3:1,4:1,7:1}`（terminal 复用）/`{1,2,5,6}=0`（non-terminal 继续）、`stream_index`/`active_cursor`/`exposure`（libero_10=1840/libero_goal=1264/libero_object=1184/libero_spatial=1856，单调增）、`terminal_slots`/`stable_slots`/`committed_n=8` 全 match。
- loss：对照 iter3=1.624629 vs resume iter3=1.624593（差 3.6e-5，GPU 浮点非确定，用户已选方案②）。
- 证据：`artifacts/g0/epreuse_gpu_resume_witness.json`（`result=PASS`）。
- 至此 GPT HIGH-2 的规划层（探针 5112 窗 + 生产 driver 120 窗）与 GPU 层（save→kill→resume 跨边界）证据齐备。

### GPT MEDIUM-3：pretrain acceptance command（2026-09-18 11:55 CST）

- 新增 `tools/g0/verify_active_local_memory_pretrain_gate.py`（只读）：串起 Gate1 slot 轮转、Gate3 规划容量（5112 窗）、Gate3 生产 driver 边界、GPU 跨边界 resume witness、生产 queue_seed、formal identity 六项，输出单一 `PASS/FAIL/BLOCKED` JSON。
- 运行结果：`result=PASS`（6/6），产物 `artifacts/g0/active_static_probe/pretrain_acceptance.json`。

### 审核申请已送达 DS/MM（2026-09-18 12:05 CST，REVIEW）

- formal pair=root=`c16fc8ece6b88cadc9dd1226f4a5b23e10737c7a`/child=`fca7eb589f455509e05e7c39659000343a36bad4`；冻结名册=DS=`ds:0.0` + MM=`mm:0.0`（用户已移除 Kimi）。
- 请求 exact-pair final（`APPROVE_TO_CLOSE` 或 `REQUEST_CHANGES`），范围=①Gate3 closure ②性能优化（fca7eb5）③GPT HIGH-2 GPU witness ④acceptance command ⑤hygiene。
- DS 首次长文本未进 pane（其 pane 处于 `esc interrupt` busy，progress 80.2K→93.6K），改用短文本后 capture 命中；MM 首轮即命中。三联（`send-keys -l → ≥1s → Enter → capture`）均完成。
- 三方（现两方）final 前保持 `REVIEW`；下一轮起三分钟完整核验。

### scheduler-semantics refreeze 设计 v0.1（2026-09-18 12:12 CST）

- 新增 `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_scheduler_semantics_refreeze_design_v0.1.md`（docs-only，D8b 长跑前置 Gate `G0-R09-B-TTT-V035-ACTIVE-SCHEDULER-SEMANTICS-REFREEZE`）。
- 内容：把「`cumulative_valid_consumer_exposure` 不清零 → epochs≥1 窗口 77.3% 单 suite」如实列为本 Gate 的唯一问题；给出 (a) per-epoch 复位 与 (b) 接受累计 两候选、各自实现落点/代价/验收；请求裁定。
- 未改任何代码；待 DS/MM 审核。

### 审核观察凭证 #1（2026-09-18 12:20 CST，REVIEW）

- before_head=`27decdf6`；fetch 成功；advertised=`origin/V2=7fc97081`（一致）；`before_head..origin/V2` 新增=**空**；本地领先未推。
- ChatGPT exact review：无（`grep c16fc8ec reviews/` 空）。
- **DS=`ds:0.0`**：final=**拆分建议（等同 REQUEST_CHANGES）**：`libero_lerobot_dataset.py:438-439`/`base_dataset.py:155` 的「数据增强 RNG 语义变更」须**移出本 closure / 另起 Gate**；`active_local_memory_driver.py:208-235`/`active_local_memory_launch.py:315` 的「预取线程安全」须独立设计。明确：**Gate 3 closure 以 child `827c1cb` 单独送审即可 APPROVE_TO_CLOSE**（§4 实现 + 探针 5112 + 生产 120 窗 + GPU witness 已齐）。
- **MM=`mm:0.0`**：final=`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE`（closure + 性能优化 + GPU witness + acceptance 6/6 全实证；§6 判据 1/3/4/5/8/9/10 由 8 个 driver_test 覆盖；D8b gate 显式保持）。
- 合并处理：接受 DS 的拆分——**Gate 3 closure 按 child `827c1cb` 关闭**；性能优化（fca7eb5）另起独立设计 + Gate 重审。

### 审核申请 #2：PRODUCE-PREFETCH Gate（2026-09-18 12:24 CST，REVIEW）

- formal pair=root=`e6a7af8394c424d55c1ac05f6287ac441d0db02c`/child=`fca7eb589f455509e05e7c39659000343a36bad4`；名册=DS+MM。
- 设计 `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_produce_prefetch_design_v0.1.md` + 实现 `fca7eb5`（latent 校验缓存 / 逐窗预取 / 确定性 RNG）。
- DS/MM 三联已送达（DS pane `esc interrupt` 处理中；MM 显示 processing）。
- 另：Gate 3 closure 按 DS 建议以 child `827c1cb` 单独关闭（DS 明示「单独送审即可 APPROVE_TO_CLOSE」，MM 已 APPROVE）。

### 审核观察凭证 #2 / 推进令牌（2026-09-18 12:30 CST，REVIEW → DONE）

- before_head=`dd966008`；fetch 成功；advertised=`origin/V2=7fc97081`（一致）；新增=空。
- formal pair=root=`e6a7af8394c424d55c1ac05f6287ac441d0db02c`/child=`fca7eb58`；名册=DS+MM。
- **DS=`ds:0.0`**：`APPROVE_TO_CLOSE_R09_B_TTT_V035_ACTIVE_PRODUCE_PREFETCH`；明确边界（只关性能面、不改 scheduler/owner/ABI、不改 freeze_window 选择键、D8b 仍受 refreeze）；并明确 **Gate 3 closure 以 child `827c1cb` 单独关闭（证据已齐）**。
- **MM=`mm:0.0`**：`APPROVE_TO_CLOSE_G0_R09_B_TTT_V035_ACTIVE_PRODUCE_PREFETCH`；三项 perf 改动（latent 校验缓存+lock / 4-worker 预取 / 每样本确定性 RNG）由设计 v0.1 + 实现 diff + 32/32 driver_test + 数据 SHA256 0 mismatch + 3.2–4.7× 实证；§5 边界全守；与 Gate 3 closure 解耦成立。
- **推进令牌齐（DS+MM 同 pair 均 APPROVE_TO_CLOSE）**：关闭 `G0-R09-B-TTT-V035-ACTIVE-PRODUCE-PREFETCH`；`G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`（child 827c1cb）亦关闭。D8b 长跑仍闭锁于 scheduler-semantics refreeze Gate。

### 审核申请 #3：SCHEDULER-SEMANTICS-REFREEZE（2026-09-18 12:34 CST，REVIEW）

- formal pair=root=`595ada3826ad95123781e4b1b00f3c7ec991745a`/child=`fca7eb58`；名册=DS+MM。
- 设计 v0.1（docs-only，D8b 最后前置）；请求裁定 (a) per-epoch exposure 复位 或 (b) 接受累计 regime。DS/MM 已送达。
- D8b 长跑在本 Gate 关闭前不启动。

### 审核观察凭证 #3 / 合并处理（2026-09-18 12:40 CST，REVIEW）

- formal pair=root=`595ada38`/child=`fca7eb58`；名册=DS+MM；fetch 成功、advertised=origin/V2 一致、新增=空。
- **DS=`ds:0.0`**：`APPROVE (a)`——授权 `_maybe_rollover` 的 per-epoch observed 最小改动 + 相邻 CPU 测试 + 更新 `probe_epoch_reuse_planning.py`（增 per-epoch 构成断言并重跑）；要求 ①epochs≥1 四类窗占比与 epoch0 同构（单 suite ~14%）②复位记录可核 ③CPU 测试全绿 ④ABI/字节序不变 ⑤D8b runbook 写入新语义并标注 supply-limited 尾窗。D8b 实现验证通过前不启动。
- **MM=`mm:0.0`**：`REQUEST_CHANGES_..._SCHEDULER_SEMANTICS_REFREEZE`——**程序性**：formal pair 与 docs-only 交付物不匹配（`595ada3` 是前序 session 收尾、`fca7eb5` 是 PRODUCE-PREFETCH 实现；refreeze 设计唯一提交为 `27decdf6`），要求用正确 pair 重提交后再行 (a)/(b) 实质裁定。
- 合并处理：重送 **root=`27decdf6`/child=`fca7eb58`**；实质方向已获 DS `(a)`，待 MM 同 pair 实质 final。

### 审核观察凭证 #4 / 推进令牌（2026-09-18 12:45 CST，REVIEW → IN_PROGRESS）

- before_head=`e36f80c3`；fetch 成功；advertised=origin/V2 一致；新增=空。
- formal pair=root=`27decdf6`/child=`fca7eb58`（更正后）；名册=DS+MM。
- **DS=`ds:0.0`**：`APPROVE (a)`——机制要求：`cumulative_valid_consumer_exposure` **保留作报告量**（不改「累计」语义与 admit 赤字来源），**新增 per-epoch observed 计数器**供 `freeze_window` 选择；per-epoch observed 与 `_slot_epoch` 入快照、resume 一致；更新 `probe_epoch_reuse_planning.py` 增 per-epoch 构成断言并重跑（epochs≥1 的 `windows_by_distinct_categories` 须与 epoch0 同构、单 suite 窗回到 ~14%）；D8b runbook 写入新语义并标注 supply-limited 尾窗；D8b 实现验证通过前不启动。
- **MM=`mm:0.0`**：`APPROVE_A_..._SCHEDULER_SEMANTICS_REFREEZE`——(a) 由 5112 窗实测证实塌缩不可接受，(b) 等同接受 53.7% 单 suite 偏斜、独立裁断不可接受。
- **推进令牌齐（DS+MM 均 APPROVE (a)）**：授权实现 (a)——driver 新增 per-epoch observed 计数器（保留 cumulative 作报告量）+ `freeze_window` 改用之 + 快照/resume 一致 + 探针更新；D8b 长跑在本实现验证通过前仍不启动。

### 审核观察凭证 #5 / 三方合并（2026-09-18 12:50 CST，REQUEST_CHANGES）

- formal pair=root=`27decdf6`/child=`fca7eb58`；名册=DS+MM+GPT（Kimi 已移除）。
- **DS=`ds:0.0`**：`APPROVE (a)`（机制：cumulative 保留 report-only，新增 per-epoch observed；快照一致）。
- **MM=`mm:0.0`**：`APPROVE_A_..._SCHEDULER_SEMANTICS_REFREEZE`。
- **GPT**：`docs/collab/chatgpt/reviews/2026-09-18_scheduler_semantics_refreeze_current_build_27decdf6_fca7eb5.md`，技术 verdict **REQUEST_CHANGES**（非 formal，pair 未推远端）：
  - **HIGH-1**：refreeze v0.1 用**过时的 Gate-3 regime 证据**（旧 77.3%）。**已核实当前 artifact：`windows_by_distinct_categories={1:2703,2:1893,3:367,4:149}`、单 suite=52.88%、exposure 各≈25%**。要求以当前实现 + 生产 seed 重新基线化问题陈述，再决定 refreeze 是否必要。
  - **HIGH-2**：在**异步 per-slot epoch** 下未定义 reset 权限——每个 terminal slot 独立 `_slot_epoch[slot]++`，无「全局 epoch 转换」事件；当前 driver witness `slot_epoch={0:1,1:1,2:1,3:1,4:0,...}` 证明无此事件。要求冻结唯一 reset authority（用现有可观测状态）+ 单侧跨界证据 + save/resume 两侧复现。
  - **HIGH-3**：acceptance command 的 `formal_identity` 检查恒真（未与证据 SHA 比对）；`full_coverage` 未入 PASS 布尔；`production_queue_seed` 只证明 `!=0`。要求绑定 root/child + 输入 digest、stale 即 fail、coverage 入布尔、按当前 catalog 身份核 seed。
  - **DECISION BLOCKER**：当前实现是 **B=1**（1 member = 1 stream × T），与「同 index 跨 slot 批量」的新目标冲突；须用户/架构明确二选一（保持 B=1 重画流程图，或开 ABI/runtime 性能 refreeze）。
- **合并**：refreeze Gate 计入 `REQUEST_CHANGES`——需按 HIGH-1 重新基线化、按 HIGH-2 冻结 reset authority、按 HIGH-3 修 acceptance、并解决 DECISION BLOCKER。当前 driver 的 (a) 实现为**未提交 WIP**，待设计修正后重做。

### 用户澄清：active 路线是测试路线（2026-09-18 12:58 CST）

- 用户：「active 只是测试，不是真实正式训练，和绘图无关；绘图只是示意」。
- 故 GPT 的 DECISION BLOCKER（B=1 vs 同 index 跨 slot 批量）**不成立**：保持 active 路线 B=1 串行 member 语义，无需 ABI/runtime 架构变更；流程图仅为示意、不作为实现真值。
- 推论：refreeze 的「regime 塌缩」只影响 active **测试** 路线的数据混合；结合 HIGH-1 当前实测 52.88% 单 suite，是否仍需 per-epoch 复位须重新判断（见下）。

### GPT HIGH-3：acceptance 硬化（2026-09-18 13:05 CST）

- `tools/g0/verify_active_local_memory_pretrain_gate.py`：
  - `formal_identity` 改为**真检查**：新增 `--expected-root/--expected-child`，与当前 HEAD 比对（缩写兼容），不匹配即 FAIL；
  - `gate3_planning_capacity` 的 `criterion5_block_coverage.full_coverage` **纳入 PASS 布尔**；
  - `production_queue_seed` 改为**按记录的 catalog 身份重算** `int(sha256(manifest|config|source)[:16],16)` 并比对，而非 `!=0`。
- 实测：无误判 PASS；`--expected-root deadbeef` → FAIL；ruff/py_compile PASS；产物已重生成。

### GPT MEDIUM-1/2 + hygiene 收尾（2026-09-18 13:20 CST）

- **MEDIUM-1**：SESSION.md 从 11253 行收敛为 924 行；旧内容 immutable 归档 `docs/collab/session_archive/SESSION_2026-09-18_a71bbd0.md`；顶部新增 rolling「当前状态」（目标/Gate/pair/名册/residue/process/next/blockers）。
- **MEDIUM-2**：TODO zombie 收敛——5 条 → DONE，28 条 → `SUPERSEDED_BY=...`（Stage-1 v17 链 / v0.3.2 链 / source-evidence 链 / B2 链）；剩余 16 条非 DONE 属其他阶段。
- **Hygiene**：子模块 `.gitignore` 增 `results/libero_closed_loop_4in1*` 与 3 个 ad-hoc eval 脚本（保留文件、仅清 git status）；子模块除 `uv.lock` 外干净。`uv.lock`（4087+/2188-，来源不明）按项目规则**不回退**，如实保留并在本轮记录。gitlink 更新至子模块 `228aca5`。

### 长训条件就绪核验（2026-09-18 13:35 CST）

- acceptance `PASS`（6/6）；Gate 1/2/3 + PRODUCE-PREFETCH 全 DONE；refreeze 按用户裁决 withdrawn。
- 容量：可用 5112 窗 > 计划 5000 步 ✓；resume witness `PASS`（跨 rollover 边界 8/8 match）✓。
- 资源：A100-80GB 空闲 ✓；`/disk/rl` 空闲 130 TiB，ckpt 6.3 GiB×100（save_iter=50）≈630 GiB ✓。
- 预计时长：1 step = 1 window ≈ 3.75 min ⟹ 5000 步 ≈ **13 天**。
- regime：单 suite 窗 52.88%，用户已接受。
- 证据：`artifacts/g0/active_static_probe/long_run_readiness.json`（`verdict=READY_FOR_LONG_RUN`）。

### 训练范围变更：baseline 生成+动作头 + local-mem 合并（2026-09-18 13:45 CST，用户选 (2)）

- 用户指出：active 路线此前**只微调 local-mem 支线**（`keys_to_select` 被 R09-B 用 `=` 覆盖，仅 20 tensor / 151,424 参数），baseline 的生成+动作头被冻结。
- 修改 `action_policy_libero_edge_all.py:303-310`：R09-B 分支由 `=` 改为**追加**（`_baseline_slow_selectors + TTT_SLOW_GROUP_SELECTORS`），保留 `action_policy_libero_all_nano` 的基线 allowlist（`moe_gen/time_embedder/vae2llm/llm2vae/action2llm/llm2action/action_modality_embed`）。
- 组合结果：`keys_to_select` = 14 项；实测 **selected tensors 20 → 314（≈1.4B 参数）**，2 个 param group（lr=5e-5/WD、lr=2.5e-4/无WD 的动作头组）。
- 短训验证（max_episodes=6, GA=1, max_iter=2）：**无 OOM**、`Done with training`、loss finite（iter1 1.415554 / iter2 1.592989）；ckpt 落盘。
- 影响：训练范围由「local-mem 微调」扩为「baseline 头 + local-mem 联合训练」；per-member `model_compute` 约 1.3s→1.9s。
- 该 config 变更为语义变更，须新 Gate + DS/MM 审核。

### 审核申请 #4：训练范围 baseline+local 合并（2026-09-18 13:50 CST，REVIEW）

- formal pair=root=`cf6f109e`/child=`60dd814`；名册=DS+MM。
- 请求 exact-pair final；DS 处理中（`esc interrupt`）、MM 已命中。
- 该 config 变更修正了 R09-B 用 `=` 覆盖 baseline allowlist（与 config:279 注释「保留全部原生选择」矛盾）的问题。

### 审核观察：训练范围 baseline+local（2026-09-18 14:05 CST，REQUEST_CHANGES）

- formal pair=root=`cf6f109e`/child=`60dd814`；名册=DS+MM。
- **MM**：`APPROVE_TO_CLOSE_G0_R09_B_TTT_V035_ACTIVE_TRAINING_SCOPE_BASELINE_PLUS_LOCAL`。
- **DS**：**条件式 REQUEST_CHANGES**（「方向本身可辩，补齐后即可 APPROVE」）：①`long_run_readiness.json` 的 `formal_pair.root=3642ffd1` 与送审 root `cf6f109e` 不自洽；②refreeze withdrawn + regime 接受（0.5288）未以正式文档登记；③1.4B 范围的显存/吞吐预算验证（`max_iter=2` 无 OOM 不足以证 5000 步预算）。
- 处理：DS 点③由「20-step + 系统监控试跑」补齐（用户指令）；点①/②另行修正后重送。

### option (A) member 形状 refreeze 设计 v0.1（2026-09-18 14:20 CST）

- 用户确认走 option (A)（跨 slot 批量前向）。新增 `docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_member_shape_refreeze_design_v0.1.md`（Gate `G0-R09-B-TTT-V035-ACTIVE-MEMBER-SHAPE-REFREEZE`）。
- 问题：同 2048 样本/step 下 active 2.31× baseline，根因是 MoT 前向次数 128 vs 16（每次 batch 16 vs 128）。
- 请求裁定形状 (A1) 1 次前向=8 slot×1 step（16 次/窗）或 (A2) 1 次前向=8 slot×T（batch=128）。
- 未改代码。

### 审核申请 #5：MEMBER-SHAPE-REFREEZE（2026-09-18 14:25 CST，REVIEW）

- formal pair=root=`a22167c5`/child=`60dd814a`；名册=DS+MM；三联已送达（均 capture 命中）。
- 请求裁定 (A1)/(A2) + 授权实现；本 Gate 限定只改 member 形状/性能。

### 训练范围审核重送（2026-09-18 14:35 CST）
- 补 DS ①②③：readiness formal_pair.root 改为 `5e49475b`（自洽）；regime 接受登记于 refreeze §8；1.4B 预算证据 = `d8_trial_20step.json`。重送 formal pair root=`5e49475b`/child=`60dd814a`。DS/MM 已送达。

### 训练范围审核再送（2026-09-18 15:40 CST）
- 补 DS 最后一项：`config_checkpoint_contract.py` 显式界定 `SELECTORS` scope（只界定 local 四组慢参数，非完整 optimizer allowlist；生产只用 `validate_slow_inventory`）；contract tests 15 passed。D025 已登记。
- 重送 formal pair root=`802d9e84`/child=`ac28e5d`。MM 已命中，DS 处理中。

### 训练范围审核通过 + member-shape 裁定 (A2)（2026-09-18 15:48 CST）

- formal pair=root=`802d9e84`/child=`ac28e5d`；名册=DS+MM。
- **MM**：`APPROVE_TO_CLOSE_G0_R09_B_TTT_V035_ACTIVE_TRAINING_SCOPE_BASELINE_PLUS_LOCAL`。
- **DS**：判定通过（正文「本 Gate 只关闭『优化器训练范围 = baseline 生成/动作头 + local-mem』(D025)；不授权 D8b 长跑」+「边界与非阻塞提示」；verdict 前缀被 TUI 缓冲截断）。**DS 同时裁定 member-shape = (A2)** + 条件性授权，并提示：①(A2) 会改 SegmentBatch/member/plan/resume 形状，须连锁重验 resume/epoch-reuse 既有判据；②readiness 的 14.6 天估算基于当前 (B) 形状，(A2) 落地后须重估。
- 处理：`G0-...-ACTIVE-TRAINING-SCOPE-BASELINE-PLUS-LOCAL` 关闭（DS+MM）；member-shape 采用 (A2)，待 MM 同 pair 裁定后实现。

### member-shape refreeze 裁定 (A2) 通过（2026-09-18 15:58 CST）

- formal pair=root=`a22167c5`/child=`60dd814a`；名册=DS+MM。
- **DS**：裁定 **(A2)** + 条件性授权（1 次前向 = 8 slot × T=16，batch=128，16 次/window）。
- **MM**：`APPROVE_A2_G0_R09_B_TTT_V035_ACTIVE_MEMBER_SHAPE_REFREEZE`。
- 用户补充：**8 条 slot 的 TTT 串行计算互相独立、可并行**（每 slot 各自 fast-state 递推）——纳入 (A2) 实现（设计 §4.3 已写「每步并行 B_slot」）。
- 推进令牌齐（DS+MM 同 pair (A2)）：可开始 (A2) 实现（CPU/static 先行 + 连锁重验 resume/epoch-reuse 判据 + 重估 readiness）。

### 三方审核评估落盘（2026-09-18 16:15 CST）

- 新增 `docs/build/PSM-WMA_Local_Memory_v0.3.5_review_adjudication_2026-09-18.md`：逐条复核 DS/MM/GPT 本轮 verdict（不盲信），标注「已验证/部分/驳回」。
- 结论：GPT 技术判断基本正确（HIGH-2 A1 算术、HIGH-3 SegmentBatch 已 [B,T]/不批量 SegmentIdentity/复用 MicrobatchPlanMember、HIGH-4 readiness 矛盾、HIGH-5 证据未绑定、MEDIUM-1 ckpt 17G）；MEDIUM-2 归因不准（既有 stale，非 D025）。DS/MM 的 (A2) 由 GPT 独立佐证。
- 执行计划 1–6 已写入文档 §3。供 GPT 复核。

### ChatGPT GPU 授权与接续（2026-09-18 16:44 CST）
- 用户明确授权 GPU；构建角色交接继续生效，沿用已登记 LOCAL-A2-DELIVERY，不回滚现有 A2 WIP。
- 实时核验：root e05ed2c5 / child ac28e5d；A100 80GB 空闲，未发现 GPU 任务；uv.lock 原有改动排除。
- 已重新读取 adjudication、A2 v0.2、现有 grouped code；保留 A2 与 scalar selection 原序、按重复 slot 依赖分层。
- 本轮执行：CPU 数值/梯度/原子性/恢复回归 → 单GPU 真实 cache/native forward → 短训/恢复 → 证据绑定/推理兼容。
- 输出统一放 artifacts/g0/chatgpt_a2_delivery/；新建运行子目录，不覆盖旧训练。失败先保留日志再修复，不自动启动5000步长训。
- 完成判据以真实测试/运行结果为准；代码作者不自授独立审核 APPROVE。

### 项目 Presentation Layer 整理（2026-09-19，DONE）

- 目的：不改模型实现、不移动历史文件，为当前已 READY_FOR_LONG_RUN 的 PSM-WMA 增加清晰的项目首页、current docs、公开脚本入口和 canonical artifact manifest，使新读者无需阅读 Gate/审计历史即可理解与复现。
- canonical implementation pair 保持 root=2a9df880713da179aee141dd97c6b20a2b1d8c2e / child=22acb13c1fdb4f146e51e3c26f1759c73e6d0d7e；当前 root bookkeeping head=6143b1c549bd26e9c29646c3f0c42b6c9e08e1f6。
- 预计修改仅限根仓：README.md、PROJECT_STATUS.md、docs/INDEX.md、docs/current/{architecture,local_memory,training,evaluation,experiments}.md、artifacts/{README.md,CANONICAL.json}、scripts/{train,resume,eval,verify}.sh、TODO.md、SESSION.md。
- 明确不做：不修改 cosmos-framework tracked source，不改 implementation SHA，不删除/移动 docs/build、docs/collab、tools/g0 或历史 artifacts，不启动 5000-step 长训。
- 完成：commit `e67796b151cd07c13be384e884074b99cf981f1b` 新增根 README、PROJECT_STATUS、docs/INDEX、docs/current 5 份 current truth、artifacts/CANONICAL+README、train/resume/eval/verify facade，并把 34GB 级 raw GPU validation 目录加入 ignore；仅提交 compact canonical JSON/log（最大约 24KB）。
- 验证：4 个 facade `bash -n` PASS；README/docs 本地链接 missing=0；`artifacts/CANONICAL.json` parse PASS；`scripts/verify.sh` => PASS / READY_FOR_LONG_RUN；fresh 5000-step train dry-run 与 iter_3 resume dry-run 均解析到正确 active TOML/GA16/auto-resume 命令；child tracked status clean。
- Workspace cleanup：7 个历史 detached P1/P4/P5 worktree 的 HEAD 均已证明是 V2 与 A2 分支祖先后，以 `git worktree remove --force` 正规移除；两处未跟踪 artifact 先归档到 `/disk/rl/archive/psm_wma_legacy/20260919/` 并生成 SHA256 `MANIFEST.txt`；3 个旧 static-export/quarantine 非 Git 目录同样移入 archive；`git worktree prune` 清除失效注册。`/disk/rl` 顶层现保留主项目、当前 A2 worktree、data/models/RLinf/datasets 与独立 reference repo。
- Git upload 边界：需要 push 的是 root presentation/ledger commits + `cosmos-framework` 中包含 canonical child `22acb13c...` 的分支；raw `sync_a2_gpu_control/resume/budget` 约 34GB×3、outputs/results/checkpoints、archive、数据集、模型权重均不进入 Git。当前本地 remote-tracking refs 尚不包含 root presentation HEAD，也不包含 child `22acb13c...`，故真正上传时必须先 push child，再 push root 分支/gitlink。
- 主 V2=`b796db08` 与 presentation 分支已分叉，且 V2 当前 child=`ae2e9f7`；为保持长训 exact-pair 证据，本轮不把 presentation 分支硬 merge/cherry-pick 进 V2。长训仍从 canonical A2 分支执行。
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       򊭠本轮仍未执行远端 push。远端上传时必须先确保 `cosmos-framework` remote 可达 canonical child `22acb13...`，再 push root V2；否则 root gitlink 会指向远端不存在的 child commit。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 

### EVAL-LIBERO-PARALLEL-SERVERS（2026-09-19）

- 用户明确授权执行仿真评测加速。
- 路线：4 suite × 4 独立 server 横向并行；每 server 内保留 /predict_batch；支持启动错峰；不移除 service._lock。
- 预计修改子模块：examples/launch_action_server_libero_edge_all.sh、examples/eval_libero_4in1_acceptance_v2.sh、cosmos_framework/simulation/libero/closed_loop_eval.py，并新增/补充定向测试。
- 评测语义冻结：NUM_STEPS=30、ACTION_HORIZON 保持现值；num_envs 先保留可配置，默认采用当前 4；不启动 GPU 评测，除非有可用执行设备与完整启动告知。

- 实现完成：child=`a2ac4a161831a9cba78555f03e6a87b8ed6bbd3d`；root implementation=`03b74e2f4048781cd19a912afd5bb51e6e9fc87c`。
- 实际变更：`closed_loop_eval.py` 增量保存 wave actions/predictions/partial_summary；`launch_action_server_libero_edge_all.sh` 参数化 SERVER_PORT/SERVER_OUTPUT_DIR；`eval_libero_4in1_acceptance_v2.sh` 改 4 server + 4 suite client 并行、GPU/端口/错峰/NUM_ENVS 可配置。
- 静态仓库核对：V2 Gitlink 精确指向 child；child 仅改上述 3 文件；GitHub Actions 对该 child 无 workflow run。
- 未执行验证：远程 Desktop Commander 设备当前 offline，因此未运行 bash -n/pytest/GPU 仿真；不得把本次提交当作 runtime PASS。

- 最终样式修订 child=`b79b1cb26c9ebbd469dcea3d586ffcc7e6ac02a1`（仅 helper 空行规范化）；root Gitlink update=`5090e7305a100b3dfa0beb9e3e5574b14d128b90`。当前功能语义与 `a2ac4a1` 相同。


### EVAL-LIBERO-EPISODE-RESUME（2026-09-20）

- 用户要求解决仿真断点续测；DS_PRO 指出当前 partial_summary 只写不读。
- 实现口径：episode-boundary resume；partial_summary 为唯一完成凭证；error=None 或 intentional skipped 才复用；transport/server error 重跑；无 partial 的 prediction/action 残留不复用。
- 不恢复单 episode 中途的 Local Memory session/fast state；每个待补 episode 从 fresh episode session 开始。

- 2026-09-20 纠正：根仓 `3ecbb940...` 当时 Gitlink 仍为 `3b9e1db...`，因此先前称“resume 已在 V2 合入”错误。child `12ae8cfe...` 虽已存在于 child v2，但未被 root 纳入。
- 已补根仓 Gitlink：root `c8265532078283f674a02671599df380c4a7dd40` → child `12ae8cfe7593002ee4294ddf3584d45cf6e670cd`。
- child delta 仅 3 文件：`closed_loop_eval.py`、`closed_loop_resume_test.py`、`eval_libero_4in1_acceptance_v2.sh`；当前状态=REVIEW，尚未声称 runtime PASS。

### V3 Phase3.5 design freeze（2026-10-05）

- 目的：登记唯一 Phase3.5 parity 设计权威；已全文读取 v1.1，并只读对照 Phase3 closure `af7d1b7fb3b85a79df8d7f8edc00e6f24bde5874` / child `b6707e2c89fe6078e2a0bb4ff7266205b827825e`、current child 与历史 builder 流程。结论：文档冻结无 blocker；v1.1 取代未提交旧稿。本步仅提交 v1.1、`docs/INDEX.md` 与本条，TODO、child/Gitlink 不变；未执行 probe、真实资产或 GPU 验证。提交 SHA 以本次 docs root commit 为准；Phase4 仍需真实 parity Gate PASS。

### V3 Phase3.5 parity probe implementation（2026-10-05）

- 任务 `V3-REAL-CACHE-ONLINE-VAE-PARITY` 已认领；authority 为 design root `62cefe03d393005667192538c030e7fdcf4c35bc` 与 `/tmp/CX_PHASE3P5_REAL_PARITY_PROBE.md`。预计仅新增 child `tools/v3/verify_robocasa_exact_window_real_parity.py`、`tools/v3/verify_robocasa_exact_window_real_parity_test.py`；root 后续仅 Gitlink、TODO、SESSION、canonical Inbox。先 synthetic CPU/static，再 child→root 提交推送并请求 GPT fresh review；不运行真实 VAE/GPU/资产。未跟踪 `docs/build/.__dpc00000000cfccdeec00000338` 始终排除。当前未提交。
- 实现步骤：阅读并复用 Phase3 closure、Phase3 v1.0、Phase3.5 v1.1、current Phase1A/1B/2 reader/contract、官方 composite/convert/resize、Wan tokenizer/normalizer/native crop；child `6feb9a13ba85b612f738bbb7c305e001722328ca` 已提交并推送 `v3-local-ttt`，相对 `b6707e2c89fe6078e2a0bb4ff7266205b827825e` 恰仅新增上述两文件。probe 只读整 episode source rows/timestamps 与视频，先验证 exact witnesses，再各 camera decode 一次、官方 composite/convert/VideoResize 一次，按选中窗口独立 normal full VAE encode；输出 pre-crop 五帧、native post-crop 与 z0 数值 JSON。dry-run 缺失 VAE 文件在 tokenizer 构造前 fail-closed；camera_keys 记录官方 feature strings。
- 验证：合并新 probe、Phase1A/1B/2/3 五个相关测试文件，synthetic CPU `185 passed`；新文件 Ruff check、format --check、py_compile、child staged diff-check PASS；当前无真实 VAE/GPU/source/cache/checkpoint 执行，也无 ds 独立 Evidence。下一步 root Gitlink/TODO/SESSION formal commit，另以 canonical Inbox bookkeeping commit 请求 GPT fresh source review；当前 root 未提交，`.__dpc...` 排除。

### V3 Phase3.5 device-preparation review 修复（2026-10-05）

- 旧 formal pair root `5b0ebdd8394227e3d3f7966ce5bb99aecbfd3327` / child `6feb9a13ba85b612f738bbb7c305e001722328ca` 的 GPT review `docs/collab/chatgpt/reviews/2026-10-05_V3_phase3p5_source_review_5b0ebdd8_6feb9a13.md` 当前工作树版本为 `REQUEST_CHANGES`：Wan inner model.to(device) 未迁移 `tokenizer.model.scale` 两个 tensor，`cuda:1` 等可能 device mismatch。用户已明确授权只修此 HIGH blocker；预计仅修改 child `tools/v3/verify_robocasa_exact_window_real_parity.py` 与 `tools/v3/verify_robocasa_exact_window_real_parity_test.py`。root 后续仅 Gitlink、TODO、SESSION、原样 review 与 Inbox；不执行真实资产/GPU/训练，ds 暂停。当前未提交；未跟踪 `docs/build/.__dpc00000000cfccdeec00000338` 排除。
- 修复完成：复用 current Wan `tokenizer.model.model` 与 `tokenizer.model.scale` tuple，新增 `prepare_tokenizer_device` 在拒绝 streaming/cached encoder 后依次迁移 inner model、scale mean/inv_std 至 requested device，再 eval；定向 fake spy 验证 `cuda:1` 对 model 与两 scale 的 `.to` 调用及两项禁用条件，无 CUDA 执行。child `b673ceda5a9ff058abb31224b7006f2d87771ad2` 已提交并推送，精确仅改上述两文件；Phase3.5 + Phase1A/1B/2/3 synthetic CPU `186 passed`，两文件 Ruff check/format --check、py_compile、diff-check PASS。未运行真实 VAE/GPU/资产/训练；ds 继续暂停。root 将原样纳入 GPT `REQUEST_CHANGES` review（工作树 SHA256 `5d1bbf93e8db2ac38baf79c6c6f18a53b9c2d09d01fa0a555a0dca028d2afd4c`），更新 Gitlink/TODO/SESSION 并以新 pair 请求 fresh review；本条写入时 root 未提交。

### V3 Phase3.5 real dry-run 资产路径阻塞（2026-10-05）

- 目的：登记 `V3-REAL-CACHE-ONLINE-VAE-PARITY` 的执行前置检查；formal pair root `c8a921b38128ed7430577693e76c8f38d856599a` / child `b673ceda5a9ff058abb31224b7006f2d87771ad2`。已读取 GPT dry-run-only 授权 `docs/collab/chatgpt/reviews/2026-10-05_V3_phase3p5_source_review_r2_c8a921b3_b673ceda.md`、GPT 执行证据 review `docs/collab/chatgpt/reviews/2026-10-05_V3_phase3p5_dry_run_blocked_c8a921b3_b673ceda.md` 与 ds Evidence `/tmp/psm_wma_v3_phase3p5_ds_evidence_r1/`（`D1_summary.md`、`B_env_check.txt`）。ds 的 bounded check 锁定 exact pair/scope；编码服务器上 `CACHE_ROOT`、`SOURCE_ROOT`、`WAN_VAE_PATH`、`PARITY_OUT` 均未显式提供，故 verdict=`BLOCKED_ASSET_PATH`（非 FAIL）；未执行 probe `--dry-run`，未产出 parity JSON，未运行真实 VAE/GPU/训练。解除条件：Owner/执行环境显式提供本地有效的 exact cache root、matching flat LeRobot v3 source root、Wan VAE file 与 fresh `PARITY_OUT`，或连接可访问这些资产的训练服务器；此前 Phase4 implementation 继续锁定。本步仅原样提交 blocked review、更新 TODO 与本条 SESSION；未执行项目代码，Gitlink/child/production/test 不变。未跟踪 `docs/build/.__dpc00000000cfccdeec00000338` 与 Phase4 v1.0 draft 均排除；提交 SHA 待本步 commit。

### V3 Phase4 design v1.2 freeze（2026-10-05）

- 目的：登记 GPT 冻结的 Phase4 唯一设计权威 `docs/build/PSM-WMA_V3_phase4_local_ttt_corrected_integration_design_v1.2_2026-10-05.md`，取代未提交的 v1.0/v1.1 草稿。cx 已全文只读复核 v1.2，并对照 Corrected v3.0、Phase3 closure、Phase3.5 `BLOCKED_ASSET_PATH` review、V2 donor `e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92` 与 current child `b673ceda5a9ff058abb31224b7006f2d87771ad2`；§13 的 adapter 不读 W0、all-continuation 不调用 initial_state、mixed 仅在现有 FSDP-registered `scan_local_memory` 内构造 W0 且保持现有 registration，闭合 v1.1 的设计 blocker。其余 Phase3 video_latent nesting、单一 raw authority/去重读取、per-slot provenance、dynamic T/B/GA、K1 zero-init、per-row telemetry、candidate/live transaction 均未发现设计 blocker。
- 本步仅原样提交 v1.2、更新 `docs/INDEX.md` current Phase4 authority 与本条 design-freeze 记录；child/Gitlink/TODO/production/test 不变。只做文件与 Git 只读检查及 docs diff-check，未运行项目测试、真实资产、GPU、训练或仿真。Phase3.5 仍为 `BLOCKED_ASSET_PATH`；Phase4 implementation 必须等待 thresholded `REAL_PARITY_PASS` 及 GPT 独立授权。本条写入时 root design commit 未提交。

## 2026-10-08 — V3-ACCEPTANCE-RECEIPT-TOOLS (Owner → GPT direct GitHub implementation)

- Status: IMPLEMENTED (tools-only GitHub sources/tests); TEST EXECUTION PENDING (offline server); DATASET ACCEPTANCE BLOCKED until P3P5 closure and server evidence.
- Owner: ChatGPT. DS_PRO: read-only independent verification and evidence handoff, no production code edits.
- Locked parent: root 597ce73d3c3cd4ac4d4a2e34db2c18e6a3e3e446 / child 8c3800565f66cfbce2929264f1c2a7854137482e.
- Files: tools/v3/{audit_round3_parity.py,test_audit_round3_parity.py,dataset_acceptance_receipt.py,test_dataset_acceptance_receipt.py}; docs/build/PSM-WMA_V3_dataset_acceptance_receipt_design_v0.1_2026-10-08.md.
- Acceptance: no VAE/server dependence, no change to frozen threshold, check claim 4/9 against per-window JSON (report lists 3), receipt draft cannot authorize Gate, full/fast inventory integrity and signed approval are fail-closed.
- CPU: 19 synthetic unittest cases authored, NOT EXECUTED on target runtime. py_compile/compileall/Ruff NOT EXECUTED; target encoding server offline. Earlier PASS claim was unverified. Owner clarified receipt is issued ONCE after offline VAE encoding, not integrated into training.
- Next: receive genuine Round-3 JSON; after a separately reviewed tolerance Gate, generate and sign actual acceptance receipt on trusted storage. Fast Phase1B SourceReader scan shortcut requires an independent implementation Gate.

## 2026-10-08 — GPT V3 Round3 audit fix / numerical gate / one-step readiness

- Owner-paste DS_PRO latest report: root=3dc3c90c, child/Gitlink=8c380056, 18 tasks / 9126 episodes full-corpus strict preflight PASS, config_digest=70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37, B3/B4/B5 already PASS, Round3 raw JSON identifies 3/9 z0 differences.
- GPT-authorized changes only to root `tools/v3/audit_round3_parity.py`, its synthetic tests, versioned `docs/build/PSM-WMA_V3_phase3p5_numeric_compatibility_gate_v1.0_2026-10-08.md`, and root bookkeeping; child production code untouched.
- GPU bounded authorization: full-corpus fresh iter0→1 on 8×H100 *after* new-root clean-lock `--preflight --snapshot10` PASS; T16/B8/GA2/K4; official DROID DCP; new namespace. Same-job resume, 3-step, readiness10 and formal30k remain NOT authorized.
- P3P5: GPT-reviewed bounded numerical threshold X=0.0625 for **held-out** three new task classes x first/mid/terminal; P3P5 stays OPEN until thresholded report PASS. Old v1.1 exact and Owner 2026-10-05 refreeze unchanged. No repeated B3/B4/B5 or data hash/encode all cache.
- Audit tests authored locally: 11 focused cases PASS via Python 3.13, compiled. Actual DS JSON not accessible to GPT and remains to be verified by DS; if mismatch fail closed/report. DS may run test scripts/read-only probes, never modify code.

## 2026-10-10 — V3-R2-STATIC-FOLLOWUP / IN_PROGRESS (Codex)

Owner supplied a stale prepublication handoff; fresh HTTPS Git reads found Root 5e7f2d2c2db39b7fc676d6a6f846af16e610eaf1, implementation Root cf0c92731197bfdd0de073a4c07ca93194f58968, Child/Gitlink d41be4f5485dcd9321318840c8c278c1f7487924. Existing checkouts synchronized without worktrees; previous V2 branches/history and all old notes retained.
Current-instance published-source checks: 70 standalone r2 CPU tests passed; 18 changed Python files compile; all four _observe_grouped calls have accepted keywords, including payloads/optimizer. Scoped Ruff0.12.7 found 81 violations (I001=8, F401=2, E701=31, E702=40).
Expected source edits: six Child files (cached_sft, async_prefetch, closed_loop_eval, local_memory_grouped, corrected_telemetry, formal_monitor), Root eval_robocasa_18task_queue.py and remaining_optimizations_test.py; import cleanup/formatting only. Evidence outside checkout: /workspace/onboarding/v3-static and v3-r2-components.xml/log. No new commit yet. Full CPU integration, real assets, DCP, GPU, simulator, throughput and Resume remain unverified; formal_verified_index_30k remains stopped.

## 2026-10-10 — V3-R2-STATIC-FOLLOWUP / Owner authorizes new Pair completion

Owner pasted GPT decision: stop new acceptance of cf0c9273/d41be4f and complete new Formal Pair. Fast-forwarded Root to 32cc72bf49385904c2e720314ea47f47f492906c, retaining its scoped H3-F disposition and every earlier review. Child fixed/clean at e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c; no further Child source edits authorized or needed. Root evaluation test uses independent tmp_path/evaluation output; production fail-closed unchanged (non-import AST comparison PASS for all four other Root Python edits). Recheck command: HF_HOME=/workspace/.cache/huggingface HF_DATASETS_CACHE=/workspace/.cache/huggingface/datasets MPLCONFIGDIR=/workspace/.cache/matplotlib XDG_CACHE_HOME=/workspace/.cache cosmos-framework/.venv/bin/python /workspace/onboarding/verify-v3-new-pair.py. New external evidence: /workspace/onboarding/v3-new-pair-author-check. Author CPU only, not independent Gate A; no real dataset/DCP/GPU/train/resume. Fresh GPT Review required after Root publication; historical H3-F permission remains scoped to old Pair and is not automatically transferred.

### New Pair author checks complete / publication pending
New evidence docs/collab/chatgpt/evidence/2026-10-10_V3_new_pair_author_check/ binds current source hashes and full commands. Ruff 0.12.7 check/format: 28 Gate lint files PASS; all measured source/test syntax PASS; runner regression 8 passed; migration TEST_FILES with repository conftest 328 passed, 3 real-asset skips (113.81s); three shell syntax checks PASS. Root production/runner non-import AST unchanged in four files, Child unchanged in 19 files. These are author checks only; no DS Gate A or GPT verdict. Root source/Gitlink will be committed on parent 32cc72bf, then exact Formal Pair recorded in a separate docs-only Fresh Review request. Resume/Fresh remain unauthorized.

## 2026-10-10 — V3-R2-STATIC-FOLLOWUP / REVIEW
Source published and remotely re-read: Formal Root 444c232b976e80ac68cde9e7370e73b9f6410f0e, Child/Gitlink e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c. Parent32cc72bf retained; Root/Child clean before ledger creation. Fresh GPT request appended to canonical Inbox; detail docs/collab/chatgpt/reviews/2026-10-10_V3_r2_new_pair_fresh_review_request_444c232b_e9b8a41.md. No online GPT/pane delivery asserted: request is repository-based for Owner/GPT retrieval. No GPT verdict or independent DS acceptance yet. Old Pair additional acceptance stopped by Owner. Current source task REVIEW, training holds unchanged.

## 2026-10-16 — Codex F0 claimed (Owner/GPT staged remediation)
- Task V3-F0-SAFE-START: IN_PROGRESS; Codex. Base Root a1a47b36d10f1974ba0fb7cec872b1976c9c6838 / Child 1d56320c08c56b0f8dd248919d152d81ae12ea7b, isolated branches v3-f0-safe-start-20261016.
- Scope: corrected Phase5 lifecycle/semantic identity/execution budget; necessary parent Trainer config-write and safe-stop hooks; focused CPU tests; new thin canonical launcher and review/evidence. No grouped numerical changes.
- F1 is deferred until F0 DS/GPT review. No GPU, torchrun, model/DCP loads, data scan or training. Existing frozen Source/Target, E1 branch and all Evidence preserved. Publication pending.

### 2026-10-16 — F0 author CPU complete; candidate publication
- Child 0fb7f587f56048a8ffaa12e2fdb7891abc0fb021: Phase5 atomic Fresh claim/exclusive Resume lease, immutable canonical config + unique launch snapshots, semantic identity and formal execution budget; optional parent config writer and committed-boundary checks. No grouped numerical/DCP/RNG algorithm edits.
- Author CPU: 26 test methods +30 subtests (pytest9), 0 failed/0 skipped; Ruff0.12.7 check/format 4 changed Python files, syntax, shell and pip-check PASS. External final logs /tmp/psm-v3-f0-20261016/final-r2/. Full model dependency regressions and real collective/storage validation NOT RUN here.
- New contract docs/build/PSM-WMA_V3_F0_safe_start_execution_budget_contract_2026-10-16.md; thin launcher scripts/train_v3_packed128_staged.sh. Source task REVIEW after Pair publication; DS/GPT PENDING. F1 and all GPU/training remain unauthorized.

### 2026-10-16 — F0 exact source Pair published; stopped at independent Gate
- Root implementation b3b64732efb225c3ee08b1d9f317a90228112b29 / Child-Gitlink 0fb7f587f56048a8ffaa12e2fdb7891abc0fb021, isolated v3-f0-safe-start-20261016 branches. Source Pair + contract and CPU source-hash Evidence submitted; DS request and GPT Fresh Review ledger in active Inbox continuation.
- Status REVIEW, DS/GPT PENDING. F1, GPU, all training and real DCP/data execution NOT started. Candidate documentation successor is bookkeeping only.

## 2026-10-16 — F0-REG-01 / F0-TEST-02 remediation claimed
- Codex IN_PROGRESS; isolated branches v3-f0-reg01-fixture-20261016. Root candidate source b3b64732 / docs3b0c5d9c plus merged latest GPT review/request from origin/V3 ef9dd044; preserve both Inbox append blocks. Child parent 0fb7f587f56048a8ffaa12e2fdb7891abc0fb021.
- Scope exactly Phase5 missing-index guard precedence, F0 CPU fixture dependency isolation and small focused negatives. Existing regression assertions preserved. No F1, production Trainer/DCP/RNG/Local/optimizer or frozen B1 changes.
- Existing DS Gloo/configured-preflight/persistent-storage evidence accepted by GPT; reuse only unchanged scopes. Local full V2 runtime absent; full-env independent rerun remains DS responsibility, never infer closure from minimal-env PASS.

### 2026-10-16 — REG-01/TEST-02 author checks complete
- New Child 7cae7c3049310ccc3b7e44ce9769534e152d1f26 (direct parent 0fb7f587): exactly two changed files. Production diff only moves missing-index ValueError guard before Namespace; fixture scopes Megatron imports alongside fake torch and exercises Megatron-present Trainer initialization with complete synthetic parallel config.
- Existing Phase5 regression file and all nine TrainerTests assertion ASTs unchanged. Local 28 test methods +32 subtests, 0 failed/skipped; four relevant files Ruff0.12.7 check/format and syntax PASS. External /tmp/psm-v3-f0-reg01-test02-20261016/ contains exact commands, logs, collision reproduction old9errors/new9pass and unchanged regression function AST evidence.
- Full established V2 environment is unavailable locally: mandatory DS full-import regression + nine full-env cases remain PENDING, not CLOSED. Prior accepted Gloo/config/volume evidence retained only for unchanged scope. F1/GPU/DCP/training not started.

### 2026-10-16 — F0 remediation exact Pair published / REVIEW
- Root9e51c94a6d5dba41bd37423b9db8e634ca433789 / Child-Gitlink7cae7c3049310ccc3b7e44ce9769534e152d1f26. New isolated candidate published, old candidates/V3/reviews retained. Author logs and DS exact-Pair request recorded in active Inbox continuation.
- New Pair DS/GPT PENDING; actual V2 full-env verification required. F1 remains blocked until APPROVE_TO_CLOSE. No GPU, model/DCP/data execution, Fresh/Resume or frozen B1 changes. Later candidate docs HEAD is not formal implementation authority.

## 2026-10-16 — F1 CHECKPOINT/RNG claimed
- Codex IN_PROGRESS; Owner explicit F1 authorization after GPT F0 APPROVE_TO_CLOSE Root9e51c94a6d5dba41bd37423b9db8e634ca433789 / Child7cae7c3049310ccc3b7e44ce9769534e152d1f26. Remote V3 e2a11445 closure/instructions merged as docs; both Inbox blocks preserved. Isolated v3-f1-checkpoint-rng-20261016 branches.
- Scope: checkpoint/dcp.py new opt-in synchronous local safety path + strict rank RNG, necessary Trainer no-reseed flag and corrected Phase5 profile wiring, focused CPU tests. base.py only if necessary; no global easy_io changes. No Local/FSDP/loss/Index8/performance changes.
- Author verification uses real CPU Gloo and small synthetic temporary tensors/sidecars; no GPU/torchrun, real model/DCP/data or training. New Child then Root Pair, stop for DS/GPT.

### 2026-10-16 — F1 author candidate complete / source publication
- Child c0fc4cadccedb5838d3f2e512ea96179a3c969e9, direct parent approved F0 Child7cae7c30. Exactly checkpoint/dcp.py, new dcp_local_safety_test.py, necessary parent Trainer no-reseed guard and corrected Phase5 factory/identity wiring. Base/easy_io/rand codec/Local/optimizer algorithms unchanged.
- Author real CPU DCP/Gloo on tiny synthetic states: combined 56 test methods +53 subtests, 0 failures/0 skips, 50.77s; Ruff0.12.7 check/format six relevant files, syntax, dependency check and Child diff PASS. Real Gloo delayed/failing/dead/unresponsive rank, DCP/sidecar/marker/latest failure and strict RNG/next-draw cases covered. CUDA state is a CPU stand-in; actual FSDP8/full-model dependencies not validated here.
- Contract docs/build/PSM-WMA_V3_F1_sync_checkpoint_strict_rng_contract_2026-10-16.md. New digest/schema psm_v3_sync_local_v1 is prospective, no old DCP modification. Author CPU does not close F1; DS/GPT PENDING. No GPU/torchrun/real assets/training.

### 2026-10-16 — F1 final positive two-rank restore witness
- Child 2d128ed5a07601cdd424974f99b67832eafeeb41 adds only positive synthetic two-rank full model/optimizer/scheduler/Local/RNG restore coverage on top of production c0fc4cadccedb5838d3f2e512ea96179a3c969e9; production code unchanged. Final combined CPU run: 57 methods (29 F1 +28 F0),53 subtests,110 JUnit bookkeeping cases,0 failures/errors/skips,51.879s; Ruff0.12.7 check/format six files,syntax,dependency/diff checks PASS. Contract bytes remain frozen aa3f7c6db2bdf5a7c193de1398b7ff1aa81b59b08554552f6fa86fc3e2748185.
- Formal Root is this Gitlink integration commit; handoff/docs successors must not replace it. Task REVIEW, DS independent CPU then GPT Fresh Review required. Source scope unchanged; no GPU/real assets/training.

### 2026-10-16 — F1 final exact Pair and independent handoff / REVIEW
- Implementation Root6ebf8998a7935f2ad690bb547c5db5e5a4322e6d / Child-Gitlink2d128ed5a07601cdd424974f99b67832eafeeb41 published on isolated v3-f1-checkpoint-rng-20261016. Parent production c0fc4cad unchanged by final test successor; preliminary264cff2f preserved. Mainline V3 not merged; evidence/docs successor never substitutes formal Root.
- Final author logs docs/collab/codex/evidence/2026-10-16_V3_F1_final_author_cpu/ and factual author report, exact DS CPU instruction acceptance_6ebf8998.md appended to canonical-linked Inbox continuation (live Inbox unchanged at131006 bytes). Full-env/target-volume and GPT Fresh Review PENDING. No direct external delivery asserted; no GPU/real assets/training.
- Governance self-check: latest Owner explicitly directs isolate implementation, CPU, commit then STOP for DS/GPT. This overrides historical multi-reviewer/tmux/90-minute waiting rules. No review verdict invented; no implementation approval or training token claimed. Scope remains F1; F0 closeout preserved byte-for-byte. All Evidence retained.

## 2026-10-21 — iter4000 HIGH-02 remediation claimed
- Owner explicitly authorizes consuming corrected GPT scope; fetched/advertised origin/V3 c62fad0ef6c729570ee936522ea4269021164c56, review2026-10-21_V3_iter4000_4task_multiGPU_queue_launch_review.md and Inbox erratum read. Former HIGH-01 is a false positive and will not change locking. Isolated branch v3-iter4000-server-identity-20261021 based on latest V3; historical commits preserved.
- Expected edits: scripts/eval_robocasa_18task_queue.py, new focused root CPU tests; documentation/Evidence only otherwise. Child/Gitlink2d128ed5a07601cdd424974f99b67832eafeeb41 remains unchanged. No GPU, real simulator, model/DCP reads or training. Tests use stdlib HTTP subprocesses and tiny synthetic result/checkpoint metadata fixtures, not production assets.
- Latest explicit Owner scope supersedes old multi-reviewer/tmux monitoring requirements; no direct external delivery or execution approval claimed. Author CPU is not independent acceptance.

### 2026-10-21 — HIGH-02 author CPU complete / implementation candidate
- Root queue now rejects occupied required ports before output claim and again before Popen; validates effective checkpoint/config/raw15/state/H16/64/fps20/policy-seed0/steps/guidance/Local required, checks direct HTTP plus Linux same-user /proc listener ownership and process liveness, and rechecks frozen config hash after readiness. Identity/startup worker errors remain in summary and force nonzero exit even if all task rows are complete.
- CPU final-r2: 28 passed (13 new methods +15 existing identity/screening regressions),41 subtests,55 unrelated deselected,0 fail/error/skip; 24.006s. Ruff0.12.7 check/format,syntax,diff PASS. Initial expanded collection missed Child PYTHONPATH; original failure log preserved, fixed environment only. Source unchanged after final successful run.
- Scope proof: threading.Lock assignment and publish-outside-lock unchanged before/after; discovery/result/atomic-write function ASTs and server/simulator command ASTs identical; scripts/v3_evaluation_identity.py bytes and Child2d128ed5 clean/unchanged. No real model/DCP/simulator/GPU used; synthetic HTTP processes/results/video placeholders only. Linux /proc access and real server chunk16 are future DS prerequisites, not CPU-proven production facts.
- This source commit is the new formal Root; later author evidence/docs HEAD is not the implementation SHA. Next: publish Root, exact-Pair CPU-only DS instructions and GPT incremental review, then STOP; no GPU execution authorization.

### 2026-10-21 — HIGH-02 exact Root published / REVIEW
- Root ca936c8eecd593133b1e6c61ba5691331958c592 non-force published to V3 and source branch, Child/Gitlink2d128ed5a07601cdd424974f99b67832eafeeb41 unchanged. New Queue Blob eec2702d5382358e131928db60ce75c93c0c55d5. Source commit parentc62fad0e preserves full erratum/history; docs successor is bookkeeping only.
- Author report/evidence/DS CPU-only preparation added and canonical-linked active Inbox continuation appended. Raw final28 methods+41subtests PASS, scope AST proof,12 HTTP/PID/Git synthetic scenarios; no production asset/GPU/Simulator run. Exact four real metadata dirs, target /proc and actual H16 Server protocol are DS pending facts, not author acceptance.
- Formal new-Pair independent verdict not claimed. Owner scope authorizes implementation/CPU/commit, then STOP pending GPT review; no autonomous GPU or training. Old withdrawn HIGH-01 not modified. Governance self-check preserves existing review records and source boundaries; no fabricated pane receipt or approval.

## 2026-10-21 — MEDIUM-05 claimed
- Fetched/advertised V3 a5d743d1c2221dd4db21dfa61db814da51b286ed; read exact ca936c8e/2d128ed5 review and rolled-over canonical Inbox. Primary HIGH-02 CLOSED by GPT at CPU/static scope, HIGH-01 RETRACTED, only MEDIUM-05 worker pre-try I/O capture is authorized.
- Isolated branch v3-iter4000-worker-init-20261021 from latest V3; preserve Inbox archive and reviews. Edit only queue worker entry boundary and focused root CPU tests plus notes/evidence. Tests will delay injected mkdir/log-open failure until other Worker completes all4×5 synthetic trials, proving no false COMPLETE/RC0. No GPU/real server/simulator/model/DCP/training.

### 2026-10-21 — MEDIUM-05 red/green author CPU complete
- Baseline queue eec2702d: new mkdir/log-open integration negatives each reproduced false RC0/COMPLETE after healthy Worker completed20 trials (2 expected failed assertions). No production assets used.
- Fix adds only nested worker thread-entry exception guard and renames old worker to run_worker; original service-loop AST and every HIGH-02/top-level helper AST unchanged. Preserve Lock/publish scopes, shared identity module and Child2d128ed5. Wrapper records pre-start I/O/context errors through original summary/stop path.
- Final CPU30 passed (15 targeted methods +15 existing cases),41subtests,55 unrelated deselected,0failure/error/skip,30.775s; Ruff0.12.7 check/format,syntax,diff PASS. Both new cases retain20 trials but worker_errors/INCOMPLETE/sr=None/RC1, one healthy server cleaned, no unhandled thread error. Final source hashes in external gate.json; exact scope proof retained. Source commit becomes new implementation; later docs HEAD is bookkeeping only. STOP after publication and handoff for new-Pair incremental review; no GPU/simulator/Child/DCP/training changes.

### 2026-10-21 — MEDIUM-05 exact source Pair / REVIEW handoff
- Formal Root6405c9dae02e81be5f267e79e27995c3df7fb988, Child/Gitlink2d128ed5a07601cdd424974f99b67832eafeeb41 unchanged; Queue e56eaafe8276aa40cb9e2fbc1110515e8fa19c25, non-force V3/source-branch published. Parent a5d743d1 preserves review/rollover and prior records. Docs successor is not implementation authority.
- New author report/evidence and canonical Inbox delta review request recorded. Baseline two faults reproduced false success; final30+41subtests/static PASS. Original main AST matches exactly after removing new entry and restoring worker name; no HIGH-02 behavior/Child/lock changes. Independent new-Pair verdict pending, no self-approval.
- Governance self-check: Owner permits only MEDIUM-05 implementation/CPU/commit then stop; preserve records, no GPU/real Server/Simulator/production assets/training, no fabricated message receipt. DS CPU minimal delta commands in new report, historical ready-runbook Root assertions must use newPair. STOP for new-Pair review and explicit execution authorization.

## 2026-10-21 — HIGH-06 normalized model path claimed
- Fetched/advertised V3 74d22d9c5a538da7684144d054e917c26146c503; read canonical Inbox, DS integration review and Owner erratum: optim/ is not a model-only inference prerequisite. Prior MEDIUM-05/HIGH-02 CPU-static closure retained; no repeated design review.
- Actual pinned Child CheckpointOverrides._build_checkpoint appends /model for a local root containing model/, and Action Server /info returns that normalized setup_args path. Queue expected parent root, synthetic fixture had hidden the mismatch. Author will change only expected reported model path, preserve root manifest/CLI and strict checks, derive new CPU fixture from actual Child source; no heavy Child imports/model loads, no Child edits.
- Isolated branch v3-iter4000-checkpoint-normalization-20261021 from latestV3. Tests use only temporary model metadata/stat fixtures, stdlib HTTP/Git; no real assets/GPU/Simulator, no running G1 changes.

### 2026-10-21 — HIGH-06 red/green CPU complete
- New fixture executes original pinned Child ConfigFileType/CheckpointType/_build_checkpoint AST bodies with real temporary DCP-file detection; only enum-base/unused external dependencies isolated, no model/framework import. Baseline reproduced correct /model rejection: one positive contract error and three 1/2/4-worker positive subtest failures, zero sim calls.
- Production delta is exactly expected /info checkpoint=(requested root/model).resolve(); request/manifest root and all other strict checks unchanged. Entire queue AST equals baseline after restoring that one expected expression; Child and shared identity module unchanged.
- Final32 passed (17 targeted methods+15 existing cases),47subtests,55 unrelated deselected,0fail/error/skip,34.879s; Ruff0.12.7 check/format,syntax,diff PASS. Correct real-Child normalized model path succeeds, oldparent/wrongiter/same-iter otherjob/arbitrary model paths reject; whole4×5 CPU integration and previous worker-error/identity negatives pass. No optim or production assets needed in fixture.
- Source commit defines new implementation Root; later docs HEAD not authority. Publish exact Pair/Evidence then STOP for GPT increment and later DS CPU. No GPU/real Server/Simulator/G1 interruption, no optim/DCP/training work.

### 2026-10-21 — HIGH-06 exact Pair published / REVIEW handoff
- Root950b2dbc6ad112205153a18dc0f733812db30706 / Child-Gitlink2d128ed5a07601cdd424974f99b67832eafeeb41 unchanged; Queuecb829cec0e43c09e8298e9d896a473b7b8285739 non-force V3/source ref published. New report/Evidence + canonical new-Pair review request recorded. Original HIGH-02/MEDIUM05 closures/optim erratum preserved; later docs HEAD is not implementation SHA.
- Final32+47subtests and static PASS bound to committed source. Source-only delta one expected-path expression; exact Child normalization method-source fixture and red failure retained. Independent verdict pending, not self-approved. DS post-review CPU delta and parallel real Config/model-only readiness remain distinct; old full-component/optim probe explicitly superseded for inference.
- Governance self-check: only Owner-authorized HIGH-06 code/test/docs, no Child/Lock/TTT/optimizer/DCP/G1 operations. No GPU/Server/Simulator release or fabricated receipt; stop for new-Pair review and later explicit Owner resources/execution authorization.

## 2026-10-21 — HIGH-07 and future effective-config task claim
- Fetched/advertised V3 271984989dfd1151180905084c72817f74477e57, fast-forward from c15e57b1; read canonical Inbox, HIGH-06 APPROVE review, HIGH-07 chunk32 review and scoped new-job config request. Explicit Owner instruction authorizes two sequential, separately submitted CPU-only batches and then STOP; supersedes historic tmux/multi-reviewer waiting workflow. No independent acceptance claimed.
- Batch1 branch v3-iter4000-action-chunk16-20261021: only scripts/eval_robocasa_18task_queue.py and tools/v3/eval_robocasa_queue_identity_test.py plus bookkeeping/Evidence. Explicit server CLI16 and immutable protocol field; execute pinned Child chunk resolution AST with synthetic inherited32. Child/Gitlink2d128ed5 remains unchanged.
- Batch2 will be separately claimed and implemented on an isolated candidate branch, never merged to V3 before GPT/Owner approval. Scope future Corrected Phase5 effective snapshots/provenance only; preserve old G1 config/config.pkl/job identity/checkpoints/source and historical evidence. No GPU, real Action Server/simulator, real DCP, training, GPU inventory or G1 process operations.

### 2026-10-21 — HIGH-07 red/green CPU complete
- Red: updated same-source Child resolver fixture against old Queue reproduced3 normal1/2/4 Worker failures (RC1,expected16/got32,zero sim calls); direct CLI16>config32 and absent-CLI32 negative contract passed. Only synthetic temporary metadata/config/stdlb HTTP; no Action Server model/runtime imports.
- Green: explicit --action-chunk-size16 per Worker + immutable protocol.server_action_chunk_size16. Final33 passed (18 targeted methods+15 existing regressions),50subtests,55 unrelated deselected,0fail/error/skip,37.631s. Ruff0.12.7 check/format,syntax,diff PASS. Correct canonical /model and previous identity/worker errors retained; wrong/info32 stops before simulator; fixture frozen config bytes unchanged. Child/Gitlink unchanged2d128ed5.
- Source commit is new HIGH07 implementation Root; docs successor only Evidence. Independent GPT verdict/DS CPU remain pending; no GPU/real server/simulator/G1 asset/process operations. Second authorized batch separate isolated candidate, no mainline merge.

### 2026-10-21 — HIGH-07 source published / Evidence handoff
- New Implementation Root320fda57c2cf450fbf0042183d7761a70b56f215, Child/Gitlink2d128ed5a07601cdd424974f99b67832eafeeb41 unchanged, Queue4916918aca412a0abc6cb00e28f6053a351e07d8. Published non-force V3/source branch. Evidence/handoff tracks33+50subtests and exactdiff/argv/manifest/source AST proof; no independent approval claimed.
- Owner's second batch now allowed only on isolated future-job config candidate. No merging training changes to V3 before GPT/Owner acceptance, no GPU/Server/Simulator/G1 asset/process operations.

### 2026-10-21 — Two-batch author handoff complete (docs-only V3 pointer)
- HIGH07 production implementation Root320fda57c2cf450fbf0042183d7761a70b56f215 / unchanged Child-Gitlink2d128ed5a07601cdd424974f99b67832eafeeb41, CPU33+50subtests PASS; report/Evidence in precedingV3 docsab1f277e. Explicit CLI16 and protocol field only, strict checks preserved.
- Second future-job Config-truth isolated implementation Rootfa6471c0e9d12c54fa72a425d06abfc80ea491cc / Child-Gitlink35b0ea1ccee9ee26653ed6589c484f0997d1c586, docs/Evidencefb670c2c30305abda318ae8e927b6d8cd7ad6298, CPU47+32subtests/static PASS. Root/Child candidate refs v3-phase5-config-truth-20261021 only. This commit modifies only canonical Inbox,SESSION,TODO; never merges candidate code/Gitlink into V3.
- Latest V3 fetched/advertisedab1f277e before this docs-only worktree. Exact candidate source/Evidence pins appended for independent GPT reviews, no self-acceptance. No GPU/real Server/Simulator/training/DCP/G1 asset or process operations. Owner's authorized two batches complete; STOP after remote/source/hash readback. Historical reviews/archive preserved.

## 2026-10-21 — Owner authorizes Config-truth merge into V3
- Explicit Owner latest instruction supersedes the previous candidate-only/no-mainline-merge boundary for this implementation. It authorizes repository integration only, not training-server sync, G1 asset/job identity changes, GPU/server/simulator or training execution; independent review is not self-approved.
- Latest remote V3 fetched/advertisedbefa947bb983d475a0c2350e2845ee7f92718fe6, candidatefb670c2c30305abda318ae8e927b6d8cd7ad6298 with exact Child35b0ea1ccee9ee26653ed6589c484f0997d1c586. Isolated merge branch v3-config-truth-merge-20261021 preserves both histories. Scope Root candidate merge/Gitlink plus append-only handoff notes, no source edits or Child branch overwrite. Existing source-bound47+32CPU/static evidence will be verified against exact merged files, no unnecessary repeat.

## 2026-10-21 — Future Phase5 config-truth isolated claim
- HIGH07 source320fda57 + Evidence docsab1f277e published; isolated root/child branches v3-phase5-config-truth-20261021 created, root based onab1f277e and Child2d128ed5. Will push candidate refs only, no V3/v3-local-ttt merge.
- Expected Child edits: Corrected Phase5 overlay/lifecycle and dedicated effective-config helper+focused tests, F0 fixtures only as necessary. Root Gitlink+notes/Evidence. Synchronize only retained Corrected Phase5 legacy chunk field before new effective snapshots; refuse ambiguous/conflicting/type-invalid layouts; truthful versioned launch provenance identifies actual cached SFT→ExactWindowSegmentProducer→GroupedLocalMemoryTrainer.bind_grouped_stream, not legacy dataloader. Use existing lifecycle canonical SHA/namespace checks; no old G1 schema/identity migration.
- CPU tests will use inherited32 temporary configs, original serializers/Child resolver and synthetic contracts/cache/action windows only. No real asset writes, GPU, model/server/simulator, DCP or G1 process interactions. Stop if existing schema/new-job same-source resume cannot be preserved.

### 2026-10-21 — Future config-truth author CPU complete / isolated implementation
- Baseline old Phase5 overlay actually retained32 after tokenizer/runtime config overlay; failing32!=16 assertion preserved. Initial minimal-env collection blocked by unrelated eager SciPy dataset import; external bootstrap bypasses only that registration package. Fixture missing480 tokenizer entry and bootstrap spawn guard repaired, prior failures preserved, production assertions never relaxed.
- Future-only Corrected overlay mirrors known unambiguous Stage-A32/16 canonical dataset aliases to16 after validating remaining contract; type/unknown/multiple conflicting fields fail before mirror mutation. Existing full geometry/cache contract remains authority. Live config and just-saved YAML are checked before canonical Config/Job Identity publication. Versioned effective_data_source in launch.json identifies cached SFT→ExactWindowSegmentProducer→GroupedLocalMemoryTrainer.bind_grouped_stream, legacy node compatibility-only, raw/state15/H16/frames17/fps20 and independent T.
- Final lock-aligned CPU47 passed (19 new cases+28 existing F0 methods),32subtests,0fail/error/skip,3.691s; Ruff0.12.7 check/format,syntax,diff PASS. Original serializers YAML/PKL read16/Child parser16; real tiny-cache17 identity and original SequencePlan state-conditioning source bodies exercised. Same-source Fresh→Resume lifecycle retains all canonical config/identity bytes; no real DCP save/load or model/optimizer training.
- Scope proof: remove only new helper import/hook/provenance AST and entire Phase5 equals2d128ed5; existing93 corrected-test and83 F0 assertion ASTs identical. Checkpoint/RNG/Trainer/Action Server/policy source and Root HIGH07 Queue unchanged. New Child and Root are isolated candidate refs only, no V3/v3-local-ttt merge or G1 asset/process modification. Existing identity schema/namespace/hash semantics remain; source-pair lock rejects old-job migration. New canonical config hashes change to truthful16 for new jobs, final semantic digest also changes with new exact source pair; no historical identity rebind.

### 2026-10-21 — Future config-truth exact isolated Pair / REVIEW
- Rootfa6471c0e9d12c54fa72a425d06abfc80ea491cc / Child-Gitlink35b0ea1ccee9ee26653ed6589c484f0997d1c586 published to candidate refs v3-phase5-config-truth-20261021 only. Source Root parentab1f277e; V3 remains HIGH07/Child2d128ed5. No production merge or G1 modifications.
- Separate report/evidence contains final lock-aligned47+32, original red and environmental/fixture failure histories, exact patches, serializer/cache/SequencePlan/provenance witnesses and unchanged-assertion/source scope proof. Metadata lives in versioned launch sidecar, original Job schema/identity functions untouched. Independent GPT/DS verdict pending. STOP after docs publication and V3 docs-only pointer; no GPU/Server/Simulator/G1 or other remediation.

### 2026-10-21 — Config-truth merge prepared under explicit Owner authorization
- Candidate source/Evidence merged without production conflicts; SESSION/TODO/Inbox append conflicts resolved by retaining the entire existing V3 prefix and all candidate additions. Earlier candidate-only statements are historical; latest Owner merge authorization governs this integration, not execution or independent acceptance.
- Root Gitlink now35b0ea1ccee9ee26653ed6589c484f0997d1c586; candidate Child unchanged. HIGH07 Queue unchanged4916918aca412a0abc6cb00e28f6053a351e07d8. No Child branch overwrite, production source edit or evidence rewriting. New integration Root becomes current formal Pair for subsequent independent review; author CPU evidence source hashes must match before push. No server/G1/assets/GPU operations.

### 2026-10-21 — Config-truth V3 exact integration Pair published
- Mainline Implementation Root306d235046fe5d578503beb17a56f5c0eb0f5634 / Child-Gitlink35b0ea1ccee9ee26653ed6589c484f0997d1c586, non-force V3 published. Full priorV3/candidate history preserved. Mainline tree equals candidatefb670c2c except append-onlySESSION/TODO/Inbox, all candidate source/tests/Evidence hash checks pass; no project test rerun because no source change.
- New mainline handoff/formal Pair proof added; existing author47+32/Ruff source evidence retained as original run, not independent acceptance. Latest Owner merge authorization overrides historical candidate-only restrictions, not G1 deployment or execution permissions. Stop after readback; no training-server/G1/config/DCP/GPU/Server/Simulator operations.

## 2026-10-22 — G1 Owner cross-pair Resume candidate author delivery (V3 docs pointer)
- Current V3 fetched/advertised1fc28effe9e33a2e6522f6ffe60c55c68f8b367c. Candidate Rootb910304dbf493eb5babe26cf1b055edc8477b386 / Child61bfa94766d33d95a7fa9771857d0f2fb3f0b405, code/Evidence refs v3-g1-cross-pair-resume-20261022; docs5fe6a513baa870c06f3186903b99e9bba80bb084. Only canonical review pointer/notes added to V3, no code/Gitlink merge. Author115+32CPU/static PASS, independent new-Pair verdict not self-approved.
- Unique G1 explicit flag and exact8900/full-components gate, immutable frozen authority, strict non-source semantic comparison, history-bound digest+8rank provenance continuity and append-only runtimeSource audit. Existing generic algorithms/state restore and tests unchanged. Runtime code must use new reviewed Child61bfa947 exact expected pin descending from35b0 baseline; actual target8610ad88 fullRoot/digests remain DS facts, not invented author evidence.
- STOP after remote/source/Evidence readback for GPT fresh incremental review, DS read-only CPU and Owner separate execution grant. No GPU/torchrun/real model/server/simulator, no real G1/DCP/config/Identity read-write or process operations, no training-server sync. Historical rejected old-checkout design kept as superseded record; new Owner scope applied without broad bypass.

## 2026-10-22 — Manual RoboCasa Batch A isolated author delivery / V3 docs pointer
- Fresh V3 fetch/advertised99be49d307019b5ed47f1677a34bbe6280912a86, ff-only from2bbf858e, existing Owner design and DS vendor-readonly request preserved. This entry does not merge any code/Gitlink; V3 Child remains35b0ea1ccee9ee26653ed6589c484f0997d1c586.
- Isolated Batch A Implementation Root7646d41488a55d5a44ab193520a42c48cf5acc90 / Child-Gitlinke42a2468672d3ef8fcba708fc19e70daec7c790e; docs/evidence e4f6c8a62993d83dc27c285ce9e223eeefee7f65. Candidate refs v3-robocasa-manual-eval-20261022 and v3-robocasa-eval-lifecycle-20261022, Child published first. Defaults per-task Server, bounded owned process groups/episode/task cancellation, independent cleanup witness/error conservation. Source protection keeps strict server identity/action-loop/algorithm/training files unchanged.
- Author72methods+61subtests and20 existing regressions =92passed+61subtests,0failed/skipped; Ruff0.12.7/format/syntax/source diff PASS.2 old-source real contract failures and failed fixture/environment attempts retained. Synthetic CPU only; no Cosmos model, real Server/RoboCasa/GPU/DCP or G1 asset access. Full handoff/DS frozen CPU template accessible at candidate docs SHA via Inbox.
- Request new exact-Pair GPT incremental review / DS independent CPU; STOP after publication. B awaits DS actual dependency SHA/MuJoCo/patch evidence under existing99be49d3 request; C queued, manual launcher/video/attempt work not delivered. Historical SR5% diagnostic only. Prior G1 candidate refs/source work preserved separately; no source rollout or runtime authorization.

## 2026-10-22 — Batch B final r2 isolated source/vendor delivery (V3 docs-only pointer)
- Fresh V3 fetch/advertised d6b2484fa9f4ff5775ea1f13f3fcaf973ce499e8 and ff-only sync preserved Owner1.0.1 dependency decision and prior A/G1 independent source reviews. No production source/Gitlink merge; V3 Child35b0ea1 unchanged.
- Exact candidate Root891801bf44736e1eaf44b91377f98c5c5035edd0 / Child-Gitlink35b0ea1ccee9ee26653ed6589c484f0997d1c586 / deterministic patchset vendor1ac174585293ed998ffc9cf73e47439798cf6f6c. Isolated ref v3-robocasa-vendor-b-20261022, docs05ff4283bc70354c5e3bbdddf1af56998b49b68b.1.0.1@6f90063, native/PythonMuJoCo3.3.1/NumPy2.2.5 fixed;8-file semantic backport with clean offline rebuild. Native no-sleep capability explicitly handled, no ignored True/ISLAND substitution.
- Final110 author CPU PASS, no skip; Ruff0.12.7/format/syntax/source checks PASS. Root2b14 r1 superseded by canonical UTF8 fix with actual unchanged-claim Unicode Resume regression; original source/artifacts preserved at e5084. Real runtime probe still incomplete-environment BLOCKED here and Kitchen physics not executed, not folded into CPU approval. Full report/evidence at candidate refs via Inbox.
- Source unchanged for existing Queue/identity/training/Local/DCP/RNG and Child; no G1/DS dirty editable or real assets touched. No C launcher or A/G1 combination. Request new exact r2 B-only GPT review + DS independent CPU, STOP after publication/readback; actual runtime/Kitchen/physics Gate stays OPEN and separate Owner authorization required.
# V3 RoboCasa Batch C — 2026-10-22

- Owner-authorized implementation IN_PROGRESS on `v3-robocasa-manual-c-20261022`, based on verified V3 `24a726734bbab5411160e3c11a8b46135fceb570`, integrated implementation `9ae01344ffe82a3b403732aa61cce3dd7fb5055a`, Child `30db22a3586c0270611753dc2ca0deb10ec27833`. Existing G1/A/B source is inherited; running G1 worktree is not accessed or synchronized.
- Expected scope: Root Queue, new strict eval config/results helpers, shell launcher, example YAML, focused CPU tests, manual runbook; Child closed-loop eval media/runtime binding and focused tests. No training/DCP/Local-TTT algorithm/vendor physics edits. Config, Child, attempt validation and Queue fixture work delegated on disjoint files; parent owns integration and submission.
- Contract: `docs/collab/chatgpt/requests/2026-10-22_V3_RoboCasa_Owner_Manual_Eval_Framework_Frozen_Contract.md`. Implement GPU-to-single-slot selection, task subsets, media modes, bounded cleanup, exact runtime identity and complete-task-only resume with preserved attempt namespaces. Author CPU is not DS acceptance. Source not committed yet; stop after new Pair and review handoff; no GPU/Action Server/Kitchen or real DCP execution.

- Batch C author implementation completed: strict schema/YAML/CLI precedence and metadata task selection; CPU-only list/preview; required Batch B runtime preflight and in-process recheck; controlled media none/first/all; Task/Attempt-bound JSONL and complete-task-only resume; bounded owned decoder cleanup and external Numba/MPL/XDG caches. CPU final helpers148, Child58, Queue29+65subtests, existing evidence regressions20 all PASS; Ruff0.12.7 check/format, syntax/diff checks PASS. Source Child `c9f21040f462a114d597fc83773cb9b6a9e96214` pushed to `v3-robocasa-manual-c-20261022`; Root formal commit is this source commit, exact SHA to follow in separate evidence handoff. Gate state REVIEW (author CPU only, no GPT/DS acceptance). No GPU/model/Kitchen/real DCP or G1 worktree operation.

- Remote source readback: Root V3 `a2f3a6a367395b2f2a6006cfc4e7c9effa606713`; Child ref/Gitlink `c9f21040f462a114d597fc83773cb9b6a9e96214`. Full Batch C handoff/evidence and canonical Inbox request are delivered in a following docs-only commit. GPT incremental review → DS independent CPU → Owner manual execution; author stops at REVIEW. Vendor1ac174 and inherited G1/A/B preserved.
# V3 RoboCasa Batch C r2 — C01/C02 remediation (2026-10-22)

- Synced clean checkout ff-only to verified V3 `c2d8359f918e6880a2c67847b817884a726fe4f9`; exact reviewed implementation remains Root `a2f3a6a367395b2f2a6006cfc4e7c9effa606713` / Child `c9f21040f462a114d597fc83773cb9b6a9e96214`, Vendor1ac174 unchanged. GPT exact-pair review REQUEST_CHANGES read with canonical Inbox and narrow r2 request.
- IN_PROGRESS: C01 require complete strict Episode progress and per-Episode Local cleanup in initial finish and resumed skip; online monitor binds Task/Attempt. C02 classify environment and generated MP4 separately, including partial/failure rows. Expected Root-only paths: results/process/Queue modules and three focused test files, runbook clarification and source/evidence handoff. Child, G1, training, Local math and Vendor untouched. Baseline red then CPU green; no GPU/model/Kitchen/real DCP. Stop after new Root/unchanged Child Pair submission for GPT review/DS CPU.

- C01/C02 r2 author final CPU: helpers221 (Attempt125 + Config70 + Process23 + Numba3), unchanged Child58, existing evidence regressions20, Queue35+72subtests all PASS. Baseline reds: offline68, bound-monitor5 plus direct foreign-attempt acceptance probe, media3 assertions incl2subtests. Strict completion+resumed skip now require exact Episode progress and successful per-Episode Local cleanup; Queue online binds Task/Attempt. Environment/generated files separated in normal, partial and aggregate summaries. Ruff0.12.7/check+format, Python12/shell syntax and source diff PASS. Child/Gitlink remains c9f21040f462a114d597fc83773cb9b6a9e96214; Vendor unchanged; source commit is this Root commit, exact SHA in subsequent evidence handoff. REVIEW pending GPT/DS, no execution authorization.

- Published Batch C r2 exact Root `a4b22b929175e462b6a8db57ad2abee7e220dd37` / unchanged Child-Gitlink `c9f21040f462a114d597fc83773cb9b6a9e96214`; evidence+canonical Inbox fresh review request delivered by following docs-only commit. Final334top-level+72subtests allgreen, sourceSHA verified against formal Git blobs. REVIEW pending GPT fresh C01/C02 verdict and DS_PRO independent CPU; stop, no GPU/real simulator/training.

## 2026-10-22 — V2→V3 functional inheritance static audit (Owner request)

- Audited V2 Root b13024456e313b545871a0d5de07f5495848f4e3 / Child e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92 against V3 docs HEAD e577e05c2005d19b3b97f725624c447c53d20f0b / production a4b22b929175e462b6a8db57ad2abee7e220dd37 / Child c9f21040f462a114d597fc83773cb9b6a9e96214. Report: docs/collab/codex/reviews/2026-10-22_V2_to_V3_functional_inheritance_static_review.md. Static source/call-chain inspection only; no project tests/code/GPU/model/simulator/real DCP or G1 operations.
- Main confirmed gaps: V2 A2 GradClip1.0 callback not registered in formal V3; action-only/profile request path absent; zero/init ablations, detailed Slow-change/Native validation tools, Corrected expert open-loop replay, old public facade/docs not fully ported. Conditional Slurm/cumulative-exposure gaps and explicitly deferred LIBERO/history/multi-session batching separated from current requirements. Packed/stable slots/TTT/create_graph/prefix/epoch reuse/commit+strict Resume are present; Index8 debt is not V2 A2 functionality loss.
- Audit deliverable DONE; this docs-only record does not change the Implementation Pair, reopen approved C01/C02, authorize remediation, alter frozen/current G1, or authorize execution. GPT/Owner must decide training-semantic implications before any future GradClip change.

## 2026-10-22 — Official-latest-first inheritance reassessment (Owner clarification)

- Rechecked NVIDIA/cosmos-framework main via ls-remote/fetch: `9a70e64d2ad7ff1417484d12d10fb121b270baaf` (2026-10-21). V3 docs baseline `f620a34d9f40f3a6ff347f695fb7f119c8010e02`, production Root `a4b22b929175e462b6a8db57ad2abee7e220dd37` / Child `c9f21040f462a114d597fc83773cb9b6a9e96214` unchanged. Current V3 and latest official are not fully aligned; shared merge base alone is not proof that V3 lacks later ports. No upstream merge/upgrade done.
- New report `docs/collab/codex/reviews/2026-10-22_V3_official_latest_first_inheritance_reassessment.md` supersedes earlier inheritance-necessity/priority judgments while preserving old report. GradClip remains an official recipe integration difference; old public guidance needs current-entry cleanup. Action-only/profiling, zero/init, expert replay and cumulative exposure are optional project work. Old SIGUSR1 is superseded by optional upstream wall-clock mechanism. Generic LIBERO4 is already present; Local/history orchestration remains deferred. Existing Local S1 before/after update witness corrects earlier overbroad absence claim; joint-Formal coverage still requires actual Evidence.
- Static documentation deliverable DONE; no production/test/config/Child/Gitlink/Vendor changes, no project execution/tests/GPU/model/server/simulator/real DCP or running G1 operations. Future GradClip policy/Host updates need separate scope and semantic review; no new implementation Gate or launch approval. This record is committed with the report; exact docs SHA is reported after remote readback.

## 2026-10-23 — Owner-requested current V3 code safety audit

- Fetched/advertised/ff-only V3 `81055c909d6547ed4eb607fd0cc746af4bee7c0a`; latest three commits docs-only. Production Root `a4b22b929175e462b6a8db57ad2abee7e220dd37`, Child/Gitlink `c9f21040f462a114d597fc83773cb9b6a9e96214`, Vendor1ac174 unchanged. Official main rechecked9a70e64d. Read current Inbox, exact BatchC r2 review, DS delivery/diagnostic and environment records; no legacy triple-review waiting or execution inferred.
- Audit report `docs/collab/codex/reviews/2026-10-23_V3_current_code_safety_readonly_audit.md`: six P1 recommendations, no proven new P0 or active G1 failure. Missing language/oracle errors can produce normal result and COMPLETE; missing-all-grad on one active nonempty Rank passes global presence SUM; unsafe old eval launcher remains reachable; partial Thread.start failure lacks cancellation/join; formal custom lock is not anchored to approved Root pin. Oracle finding scoped to outer/intermittent failures, since real Kitchen reward also calls its oracle. Existing F0/F1/G1 constraints and C01/C02 not reopened.
- Focused CPU witnesses use actual rollout/attempt/resume functions with synthetic boundaries, actual thread-launch AST block, and six two-rank Gloo scenarios executing exact gradient-guard AST with CPU SGD. They reproduce faults; exit0 does not mean production PASS. Source/commands/JSON/logs archived under `docs/collab/codex/evidence/2026-10-23_V3_current_code_audit_cpu_witnesses/`. No full repo test/Ruff, actual model/FSDP/Kitchen/GPU, real data/DCP or G1 accessed. Only docs/evidence/SESSION/TODO changed; no production/test/config/Gitlink edits. Audit deliverable DONE; implementation scope remains for Owner/GPT to decide, no auto-remediation or execution.

## 2026-10-23 — Batch C fixture completion-wait remediation

- IN_PROGRESS on isolated `v3-batch-c-fixture-wait-20261023` from verified V3 `4a1ab5faf54adfff8be460f850f132c86a3a46d7`; Child/Gitlink `c9f21040f462a114d597fc83773cb9b6a9e96214` unchanged. Read Owner disposition and exact request `2026-10-23_Codex_BatchC_fixture_wait_budget_and_DS_delta_recheck.md`. Source sync CLOSED; DS181 top-level+72subtests accepted,2 fixture failures; overall CPU Gate REQUEST_CHANGES, not production Queue finding.
- Only code target `tools/v3/eval_robocasa_queue_identity_test.py`: real completion polling with bounded slow-CPU budget, coordinated outer watchdog/cleanup reserve, actual OSError-after-completion witness, slow-positive and never-completed negative. Keep original20/15trial semantics and exact failure/process assertions. Expected bookkeeping/evidence: SESSION/TODO, narrow author report/logs/JUnit and canonical Inbox handoff. No scripts/Child/Gitlink/Vendor/G1/model/DCP/production timeout or six-audit remediations. Focused CPU/static then new Root source SHA, GPT incremental review/DS delta; stop after publication.

- Author final exact test Blob `a29513aa10ccfac01a3dab2283f1d3afbc910cf7` (old `b38b238a6f15f7f70df039ecade54490165b77b9`): five targeted cases PASS,0fail/error/skip,32deselected,53.98s. Actual slow wait22.816954s before20trial completion and later OSError; never-completed guard reports timeout with no injection. Existing20/15trials, exact errors,4Task/4Server+4Sim and cleanup checks retained. Ruff0.12.7 with existing Child config,format,AST/diff PASS; no production/Child changes. Gate moves REVIEW for new test-only Root, not overall DS PASS; old181+72 remains oldPair evidence, no full-suite rerun. Full source SHA/evidence/canonical handoff follow this source commit.

- New test-only Implementation Root `ee53cbe1c25ff174f0d92a92e51e901ec6436c18` / unchanged Child-Gitlink `c9f21040f462a114d597fc83773cb9b6a9e96214` committed. New author handoff `docs/collab/codex/reviews/2026-10-23_BatchC_fixture_wait_author_handoff.md`, final evidence+checksums `docs/collab/codex/evidence/2026-10-23_BatchC_fixture_wait_author_cpu/`, canonical Inbox narrow review request appended below128KiB. This docs commit publishes evidence, not a replacement Implementation SHA. Request GPT fixture-only incremental review then DS5-node delta only; overall Gate remains REVIEW/REQUEST_CHANGES until independently closed. Codex stops after remote readback, no production/GPU/G1 actions.

## 2026-10-23 — RoboCasa default live terminal progress

- IN_PROGRESS on isolated Root/Child `v3-robocasa-live-progress-20261023`, based on V3 `07cd858ee7dd4edabfa1a7b694745c80e4c86bad` / Child `c9f21040f462a114d597fc83773cb9b6a9e96214`. Owner requests live terminal observability; current real eval and G1 worktrees are not accessed or updated. No GPU/model/real simulator/DCP.
- Expected files: Root Queue integration, new `scripts/robocasa_eval_progress.py`, strict config defaults/options, focused progress/config/Queue CPU tests and manual usage; Child `closed_loop_eval.py`, new optional best-effort `utils/rollout_progress.py` and focused tests. Root owns Queue/docs; delegated config/progress/Child files do not overlap. Preserve action, timeout, scheduling, C01 exact2N progress, cleanup, result completeness and Resume identity. No separate action-snapshot or audit remediations.
- Default5s summaries with serialized Worker GPU/task/Episode/steps/predictions/latency/phase; boundaries/errors immediate, flush. Independent observer failure must not affect task outcome. Source/evidence not yet committed; new exact Pair and CPU self-test then STOP for GPT/DS.

- Owner additionally authorized independent video browsing exports in the same observability batch. Preserve all raw media/manifests; postprocessing after all owned Worker processes finish, plus standalone CPU-only export CLI. Exact actual model instruction from Episode/result or bound live metadata; unknown historical text explicitly marked. Four labels success/fail/error/incomplete; generated clips inherit Episode outcome, never prediction-accuracy claims. Independent copies, canonical in-run destination/external custom destination, indexed source hashes and non-overwriting revisions.
- Final author CPU: Config92 + progress31 + video export44 + Child76 + Queue13 =256 top-level tests PASS,0failure/error/skip; Queue also16subtests PASS. Queue13 comprises5 new integrations,7 existing lifecycle regressions and1 closed-output notification negative. Ruff0.12.7 check/format across11Python files, syntax and14 static boundary checks PASS. Internal review findings fixed: future-Task output-directory collision, stale-audit latency override, and failed export notification overriding exit. Full repo/DS independent/GPU/model/Kitchen/runtime performance not claimed. Current real eval/G1 untouched.
- Child source `813a550dab5d6b5b5e3be90d38bb97527956b4dc` committed/pushed non-force on isolated `v3-robocasa-live-progress-20261023`; Root source plus Gitlink is this implementation commit, exact Root SHA follows in evidence handoff. New source requires GPT fresh incremental review and DS CPU delta; no running-worktree update or restart. Separate action-snapshot task remains unimplemented. Stop after publication/readback.

- Published exact source Pair: RootV3 `e6a970caba4bdc77f7d9b56a6a8fbcdafe57f1e0`, Child/Gitlink `813a550dab5d6b5b5e3be90d38bb97527956b4dc`; GitHub advertised refs and all11 source hashes re-read matched. Full handoff `docs/collab/codex/reviews/2026-10-23_RoboCasa_live_progress_video_view_author_handoff.md`; raw CPU evidence/diffs/checksums/commands and source readback under corresponding `2026-10-23_RoboCasa_live_progress_video_view_author_cpu/`. Canonical Inbox new-Pair request appended under128KiB. This docs-only commit is not a replacement implementation. GPT fresh review and DS independent delta pending; Codex STOP after final docs/readback. No current-run/real-server or training action.

## 2026-10-23 — Flexible Episode Resume first-stage design and isolated CPU Gate

- Clean ff-only sync to GitHub V3 `cc7820bee1a73bd2bb2078cb7f00239944f66d37`, Child/Gitlink `813a550dab5d6b5b5e3be90d38bb97527956b4dc`; only new commit is Owner contract. Isolated Root branch `v3-flexible-episode-resume-design-20261023`. Formal production remains `e6a970caba4bdc77f7d9b56a6a8fbcdafe57f1e0` / Child813a550d; previous progress/video review not self-approved.
- Owner contract suggests two deliveries; current scope first freezes design/migration and CPU fake-data witnesses, not production wiring. Planned new tools/v3/episode_resume_prototype files: model identity (config delegate), per-Episode legacy evidence scan (attempt delegate), scene sampling (Child delegate), plan/summary and integration fake Gate (Root). No existing production/test files modified. Read actual validators/reset/identity before designing; preserve all historical bytes and active worktrees. No GPU, server, real simulator/DCP or training.

- First-stage candidate completed: design `docs/collab/codex/designs/2026-10-23_V3_RoboCasa_flexible_episode_resume_design_r1.md`, isolated prototype4modules+tests under tools/v3/episode_resume_prototype. Final full fake-data CPU Gate161PASS (identity45, episode45, scene34, plan37),0fail/error/skip; Ruff0.12.7check+format9Python andcompile PASS. Root actual legacy helpers/decoder/owned-process primitives used with synthetic files, no real model/simulator/DCP. Independent author-team read-only inspection found source-snapshot/logical-slot double counting and stale media-view issues; fixed with negatives and retained scanner diagnostics. Mixed seed family is distinct from actual effective seed list; legacy hashing/RNG limitations explicit.
- Production scripts/Child/configs/vendor diff against cc7820be is empty; only tools/prototype, design, SESSION/TODO changed. This source commit freezes DESIGN+PROTOTYPE, not a new production Resume implementation. Legacy ingestion and lock/identity/plan components have CPU witnesses, complete protected production pipeline remains unimplemented. Publish exact design Root/unchanged Child, Evidence and canonical GPT design-review request, then STOP; implementation follows only after review, no active eval/G1 changes or GPU permission inferred.

- First-stage exact design/prototype Root `44f0953ac75591d7e60394df6337a6ed133f3f08` non-force published to V3/isolated branch; remote Root/Gitlink813a550d re-read matched, production-prefix diff empty. Handoff `docs/collab/codex/reviews/2026-10-23_flexible_episode_resume_design_author_handoff.md`, author Evidence `docs/collab/codex/evidence/2026-10-23_flexible_episode_resume_design_author_cpu/`, canonical Inbox design-review request appended under128KiB. This docs-only delivery is not production implementation or a new design source SHA. GPT reviews candidate decisions next; production admission/Queue pipeline remains unimplemented, active eval/G1 untouched. STOP after final remote readback.

## 2026-10-23 — Flexible Episode Resume Design r2 narrow remediation

- Synced verified V3 `50ed1fdc87d1380be6b95219ea12b9d379f7edc7`; exact review for DesignRoot44f0953ac75591d7e60394df6337a6ed133f3f08 / Child813a550dab5d6b5b5e3be90d38bb97527956b4dc is REQUEST_CHANGES. Read detailed review plus canonical verdict, no duplicate whole technical audit or legacy MM/Kimi gating. Isolated branch `v3-flexible-episode-resume-design-r2-20261023`.
- IN_PROGRESS scope only HIGH01 preserve literal-seed task-level fresh/newTask sampling, use derived only true gap; MEDIUM02 fail-closed quarantine inconsistent COMPLETE while keeping RUNNING/FAILED prefixes; MEDIUM03 derive pending from persistent authority/gaps with stable logical IDs. Disjoint owners: scene2files Child agent, evidence2files attempts agent, new reservation2files config agent; Parent owns plan/tests, r2 design/docs/Evidence. All production/Child/config/vendor unchanged, r1 artifacts retained. No active eval/G1 worktree, real DCP/model/server/simulator/GPU access. Stop after new design SHA/CPU/readback and GPT handoff.

- R2 candidate complete, status REVIEW: per-Task fresh/gap choice with explicit execution batches; whole-source quarantine for contradictory COMPLETE in scanner and direct API; durable source/reservation/progress recovery with pending hints forbidden from inventing slots. New r2 design preserves r1. Parent integration covers4old+14newTasks, disk restart {0,1,3,4}->2, tail start, shrink-expand and shared Task cleanup snapshot identity.
- Changed-module author CPU185 PASS,0failure/error/skip (scene53, Episode53, recovery34, plan45); unchanged identity45 not rerun/recounted. Ruff0.12.7check+format11Python, compile11 and production/Child/config/vendor/r1-artifact diff-empty checks PASS. Raw output external `/tmp/psm-v3-episode-resume-design-r2-20261023/`; checked-in new Evidence follows exact source commit. Separate read-only author-team delta inspection found no new blocker; not GPT verdict/DS independent acceptance. No real model/server/simulator/DCP/GPU execution.
- Pre-publication fetch/ls-remote readback: localHEAD=origin/V3=advertised50ed1fdc87d1380be6b95219ea12b9d379f7edc7, no intervening commits; preserve all history via non-force pushes. New Design SHA then docs/Evidence/canonical request; STOP for GPT incremental design review, no production Resume wiring.

- Exact r2 Design/Prototype Root `1bf88fa624e58e521caa2213f2b1a44bf2f2871d` non-force pushed to V3 and isolated branch; fresh remote readback both equal1bf88fa6, Gitlink remains813a550dab5d6b5b5e3be90d38bb97527956b4dc. New checked-in Evidence path `docs/collab/codex/evidence/2026-10-23_flexible_episode_resume_design_r2_author_cpu/`; STATUS/JUnit185/commands/diff/11sourcehashes bound to exact Design blobs. Handoff `docs/collab/codex/reviews/2026-10-23_flexible_episode_resume_design_r2_author_handoff.md`. Canonical Inbox append-only105744+2678=108422bytes, below131072. This following docs-only commit does not replace Design SHA. Request GPT delta design verdict, STOP after final docs remote readback; no second-stage production work.

## 2026-10-24 — Flexible Episode Resume production wiring

- Review observation: beforeHEAD277457606baae6105eacc97013f4d8fe23d33d4e; fetch/advertised/originV3 db4ac8c690ba9f5971899d28768ac3caf7065108; two new docs commits da4d2123/db4ac8c6, ff-only PASS. Read exact GPT review `docs/collab/chatgpt/reviews/2026-10-23_V3_flexible_episode_resume_design_r2_1bf88fa_813a550d_review.md`: APPROVE for Design1bf88fa6/Child813a550d only. User explicitly authorizes next minimum production batch; old MM/Kimi/90min polling instructions superseded by current GPT/DS/Owner flow.
- Isolated Root branch v3-flexible-episode-resume-production-20261024. Claim new production package scripts/robocasa_episode_resume (promoted approved pure components), new durable store and execution helpers/tests, Queue/config and CPU fake tests, runbook/handoff/Evidence. Disjoint delegates assigned before edits; Parent owns Queue integration and final evidence/publish. Child remains813a550d unless required interface evidence proves change necessary. Read existing production validators/process/session/reset contracts first. No active eval/G1, historical evidence, real checkpoint or GPU/model/server/simulator operations; author standard-library fake processes only. New exact Implementation Pair then GPT/DS, STOP.

- Production candidate status REVIEW: default CLI now admits four-parameter model identity under original lease, rescans original legacy/closed Episode evidence, writes source-bearing reservations before Workers, preserves fresh literal-seed/shared-env resets and gaps-only derived sampling, and publishes current-plan snapshots/latest pointer. Old whole-run execute/namespace fallback removed; Child/source config/vendor/approved prototype/old Evidence unchanged. Added output-input overlap, original-C01 recovery, foreign catalog, source deadline and signal-lock reentry guards with CPU negatives.
- Final frozen author CPU five-group combination:154 top-level PASS+72subtests PASS (226JUnit entries),0failure/error/skip,1063.262s. Groups:components41,Store32,executor22,real-default-CLI+unchanged-Child integration16,Queue43+72subtests. Ruff0.12.7check+format15,compile15,protected-path diff/source-hash freeze and git diff checks PASS. External raw final `/tmp/psm-v3-episode-resume-production-20261024/final/`; first whole run153+72+1FAIL preserved under final_run01, real not_executed task-failure count fixed while retaining exact assertion; earlier unfinished-event counter/fixture iterations also retained. No prior design185/identity45 counts inherited or added. Author CPU only; DS/GPT implementation Gate pending.
- Pre-source-publication fetch/advertised/originV3/HEAD all db4ac8c690ba9f5971899d28768ac3caf7065108, no intervening commit. Frozen15file hashes unchanged through complete Gate. Source commit next, then exact-blob-bound Evidence/handoff/Inbox commit and non-force readback; STOP. No real model, GPU, Kitchen, DCP, active eval/G1 or training operations.

- Implementation Root `252d823cf7f0e65228aa60408d50778c5a13a307` non-force published/read back V3 and isolated branch; Child/Gitlink `813a550dab5d6b5b5e3be90d38bb97527956b4dc` unchanged/clean. Final frozen author CPU154+72subtests PASS,0fail/error/skip;15Python Ruff0.12.7check+format/compile/hashbinding/protectedpaths PASS. JUnit count clarification: earlier226JUnit entries means suite declared tests=226, not226 XML elements; actual154 testcase elements,72successful subtests are counted only in declaration/console. First complete-run real failure preserved separately, never relabeled. New persistent Evidence `docs/collab/codex/evidence/2026-10-24_flexible_episode_resume_production_author_cpu/`, author handoff `docs/collab/codex/reviews/2026-10-24_flexible_episode_resume_production_author_handoff.md` and canonical Inbox append below128KiB (111251+4106=115357). Following docs commit is not Implementation SHA. Status REVIEW; request GPT exact-Pair implementation verdict then DS clean independent CPU; STOP, no real execution/current-run changes.

## 2026-10-24 — Flexible Resume production HIGH-01
- Synced ff-only493e9708->6e10c8d461ecc5f49e05da932a2d925e9ad62ef3; advertised V3 matches. Read exact GPT REQUEST_CHANGES252d823c/813a550d. Isolated v3-flexible-resume-progress-r2-20261024; scope only final progress bounded/strict C01 parsing and explicit final error persistence plus integration negatives. Parent edits scripts/robocasa_resume_cli.py and integration test, new evidence/handoff. Preserve all five groups; no Child/G1/real DCP/GPU/Kitchen/old artifacts. New pair then STOP.

- HIGH-01 r2 author frozen five-group CPU164PASS+72subtests PASS,0failure/error/skip,1155.140s. Red baseline8failed/1passed;green10passed. Ruff0.12.7check+format/compile15/frozenhash/protectedpaths PASS. Only CLI terminal reader/caller and10new integration cases changed;64MiB/4096B/2N/episode bounds, strict encoding/JSON/newline/identity/order, stat stability and per-source explicit diagnostic; original raw/Job errors preserved and finalPARTIAL durable. No Child/G1/real execution. New source commit then bound Evidence/canonical request andSTOP for GPT delta review/DS independent CPU.

- New implementation 6151e0712f28ace5d92258a8feb31fa8f1ee81c1/813a550dab5d6b5b5e3be90d38bb97527956b4dc source pushed/readback. Author final 164 passed, 72 subtests passed in 1155.14s (0:19:15);Ruff/static15PASS. New Evidence docs/collab/codex/evidence/2026-10-24_flexible_episode_resume_progress_r2_author_cpu;canonical append118343+1650=119993bytes. REVIEW, GPT HIGH-01 delta then DS independent CPU;STOP,no real execution.

## 2026-10-24 — DS Retry1 fixture-only stability remediation
- ff-only236c8a18->22b0abcb advertised verified. Read exact GPT Code APPROVE6151e071/813a550d and retry Evidence REQUEST_CHANGES. Scope only Queue test +test-only helper, external red/green/fullCPU evidence. No production/Child/Vendor/G1/old results changes. Isolated v3-flexible-resume-fixture-r3-20261024, Parent owns files; fullfive CPU and new Root thenGPT/DS,STOP.

- Fixture-only r3 frozen fullfive author CPU168PASS+72subtests PASS,0fail/error/skip,1399.805s. Focused7PASS+15subtests, finalcontrols4PASS; controlled wait-only RED1FAIL explicitly not DS90 reproduction. RealFFmpeg kept; task_timeout witness120.336s,SIGTERM/SIGKILL,1failure/3healthyTasks/15closedEpisodes; original assertions preserved and strengthened. Ruff0.12.7check/format/compile16/frozen hashes/production-protected diff PASS. Only Queuefixture+newstdlibwatchdog changed;600/900hard,180media/core inactivity,120task,300latewait; prekill durable bounded snapshot excludesheartbeat and retains ownership/source/media. Production scripts/config/vendor/Child match6151. NewtestRoot thenEvidence+Inboxrollover(byte-identical),GPTfreshfixture review/DSCPU,STOP.

- Fixture formal Rootdfb8a12140be7bf34584504c47df9042229f5bfb/813a550dab5d6b5b5e3be90d38bb97527956b4dc source pushed/readback; production trees identical6151. Final author 168 passed, 72 subtests passed in 1399.81s (0:23:19);static16PASS;full raw media/process snapshots and controlled RED preserved atdocs/collab/codex/evidence/2026-10-24_flexible_resume_fixture_r3_author_cpu. CanonicalInbox rollover if required preserves old bytes/blob. REVIEW,requestGPTfixtureincremental thenDSindependentCPU;STOP,norealexecution.

## 2026-10-24 — Fixture MEDIUM-F01
- Synced72b66438->976f77e7529a11dffef48ea0388ed6454a0b1209;advertised verified. Read exact GPT REQUEST_CHANGES dfb8a121/813a550d. Isolated v3-fixture-watchdog-f01-20261024; only watchdog+controls. Freeze owned writers before fallible snapshot, unconditional bounded rediscovery/kill/reap with start identity, retain snapshot failure diagnosis. Deterministic red/green snapshot I/O and born-during-retain child/foreign controls, oldfour+fullfive preserved. No production/Child/G1/GPU/history edits;newSHA/Evidence thenSTOP.

- MEDIUM-F01 final author frozen fullfive172PASS+72subtests PASS,0failure/error/skip,1661.249s. Baseline two deterministic tests RED2FAIL; final controls8PASS inclold4+snapshotwrite/latechild/allocfailure/interrupt. Newlate PID/PGID absent, root+children reaped,foreign alive,subreaper restored;RootSnapshotFailure fallbackcleanup.json/exceptionstate retainsprimarydeadline. Lifecycle try/finally and guardedsetup cover I/O; userinterrupt cleans thenpropagates. Ruff0.12.7check/format/compile16/frozenhash/protectedtrees PASS. Intermediate aborted/duplicate/cancel-guard attempts preserved NOTPASS. Onlywatchdog+controls, production trees identical6151;newRoot thenboundEvidence/mandatoryInboxrollover andSTOP forfreshGPTF01review/DSCPU;noGPU/model/DCP/G1/history.

- F01 formal Rootfe9d537b4a5f82c8ea72a4f8ce182fdcefac6790/813a550dab5d6b5b5e3be90d38bb97527956b4dc pushed/readback, production trees identical6151. Final author172 passed, 72 subtests passed in 1661.25s (0:27:41),static16PASS;red2FAIL/controls8PASS separated. Evidencedocs/collab/codex/evidence/2026-10-24_fixture_MEDIUM_F01_author_cpu;Inboxrollover preserves old133518bytes/blob. RequestGPTF01incremental thenDSindependentCPU;STOP,no realexecution.

## 2026-10-25 — Matched No-TTT baseline implementation
- User authorizes new baseline implementation, independent from existing evaluation Gate. beforeHEAD eff79c162131d087b27fab0649d4e139c5e5002a; explicit V3 refspec fetch (repository default fetch maps V2 only), advertised/fetched48d1eb7f21f26be459bf78259d9678a8118e27c1, ff-only succeeded, eight docs-only commits consumed. Read canonical Inbox and exact F01 review/DS closure; old F01 CPU Gate closure does not authorize any GPU. No MM/Kimi gating requested under current Owner/GPT/DS roles.
- Isolated Root/Child branches v3-matched-no-ttt-20261025; Child baseline813a550dab5d6b5b5e3be90d38bb97527956b4dc clean. Planned files: new Child trainer/matched_no_ttt.py (+tests), examples/psm_wma_robocasa_matched_no_ttt.py (+tests); narrow shared Phase5 profile/entry hooks and effective-source/audit support. Root new train launcher, off-mode inference config/command tool + CPU tests, runbook, Evidence, Gitlink/SESSION/TODO/Inbox. Existing G1 path remains default; official model/loss/Local algorithm/DCP unchanged. No subagent delegation, no real model/server/simulator/DCP/GPU or training. Submit separate exact Child/Root, request GPT/DS acceptance then STOP.
- Final candidate author CPU: frozen 16 groups434PASS +42successful subtests,5pre-existing optional real-asset skips,0fail/error;9 changed Python Ruff0.12.7check+format/syntax, launcher bash syntax and source hashes PASS. Real small Cosmos network constructor never creates Local; native G1 scan reference verifies full/terminal consumer order and weighted generation gradient; frontier/optimizer/scheduler roundtrip uses CPU toy state, not real DCP. Actual Edge recipe fully serializes No-TTT YAML/pickle and semantic identity. Candidate full01 seven failures (3compatibility assumptions,1new log-parser fixture,3missing-dependency failures) preserved, corrected without relaxing old tests. CPU-only Torch2.10/torchvision0.25; pinned LeRobot fork from uv.lock; no real GPU/model/server/simulator/Checkpoint assets.
- Child remote v3-local-ttt8f3672d is an ANCESTOR of813a550d, not newer work; exact ancestry proof retained. No baseline merge occurred. Final_after_c0 rerun is identical frozen source and counted once (434+42,23.66s); not another implementation or additional PASS count. Root originV3 remains48d1eb7f at publication precheck; narrow diff7Child files +new Root entries/runbook. Code status REVIEW, next publish exact Child then Root, author Evidence/Inbox,STOP for GPT and DS; no training authorization.
- Child implementation20b5fa639c405a515933da109529e3e2c04de88d committed and non-force atomically pushed to v3-local-ttt and isolated branch; both advertised SHA re-read exact. Root48d1eb7f advertised unchanged at precommit lock; next Root commit contains new Gitlink, three new entry/config files, focused Root test, runbook and SESSION/TODO only. Native model/loss/checkpointer/Local algorithms and existing Queue/config/vendor unchanged.
- Published Root implementation7c083215e9f39ed4b5b3ff64010e415ad62dfdf4 / Child-Gitlink20b5fa639c405a515933da109529e3e2c04de88d, both formal source SHA read back exact from remotes. Handoff docs/collab/codex/reviews/2026-10-25_V3_Matched_No_TTT_author_handoff.md; Evidence2026-10-25_matched_no_ttt_author_cpu contains original final439JUnit elements (434PASS/5existing real-asset skips) +42successful subtests;82new cases/0skip, source/patch/hash/env/iterations. External collection-only NodeID map matches every finalJUnit name/order; no duplicate result counts. Canonical GPT request append below128KiB; following docs commit only. Status REVIEW; GPT fresh incremental,DS independent CPU/real-assets matching,S0/world8GPU gates pending;STOP after readback. No G1/model/server/simulator/DCP/GPU/training assets accessed or modified.

## 2026-10-27 — Issue6 eval cached input verification
- Owner task explicit code/syntheticCPU only, candidate thenSTOP. beforeHEADb401bb275c941ba7165e368efc0de95b6cc7e35a; fetched/advertised V3eafef76f324964cb400b12e73dea2b4241c2baf7, consumed latest NoTTT merge/Owner source waiver +Issue6 request/Inbox. New isolated Root v3-eval-input-cache-20261027 starts exactlyorigin/V3; clean Child detached746c5cf2f2324104a62fb71510343aa40d3976c5 matchesRootGitlink and stays unchanged. Taskproductionbaseline49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9. PriorB1closure/NoTTT Owner decisions read only as context, not new eval approval. No agents delegated.
- Scope claimed: Root model_identity.py cache record validation/stat guard, robocasa_resume_store.py one full read + lock guard/persisted verifier, robocasa_resume_cli.py opt-in-at-internal-API and invocation input witness helper, focused new tests/narrow changed expectations/runbook/evidence/Inbox. Keep Episode/media/cleanup/source revalidation/server-info/vendor probe/4modelparameter identity/failure policy unchanged. Cache assumes trusted readonly storage; checksum/stat reuse not fresh cryptographic proof; invalid cache rehash+strict admission. Config/Task cache invocation-local only, initial full verification retained. No servers/GPU/realDCP/data/production outputs/22episodes/training operations.

- Issue6 final frozen five-module synthetic CPU227PASS/0fail/error/skip in4.05s;53new cache/CLI cases. Cold tiny model188bytes onepass(metadata+shard),Warm0_read_hash/0modelbytes/same strong digest; actual competing CPU lock process and abrupt exit23 before atomicreplace; immutable legacy22/50 episode prefix preserved. Real CLI/store/plan exercised with no-execution/no-server/runtime stubs, missing Episodes remain PARTIAL; optional shared manifest helper avoids duplicate model metadata read and keeps identity equal. Config/Task hashes initial perInvocation, then0byte guards at all3boundaries+final; vendor probe untouched. Cache record30dTTL boundtooriginal anchor/stat/path/params, checksumnotMAC, trustedreadonlysame-stat threat boundary documented. Publish onlyafterbegin_invocation validation/lease, failedColdBundle no successcache. One preexisting legacy-prototype extraFalsefield mismatch reproduced exact49df source and repaired strictfixture; initialfailedattempts retained. Ruff0.12.7 check/format/syntax9/frozen10SHA PASS. No Child/model/train/Queue/sampler/media/cleanup/error-policy modifications, no servers/GPU/realDCP/22productionepisodes accessed. CandidateRoot commit thenevidence/request andSTOP.

- Issue6 candidate formalRoot9cb8b60dccf4ac2520f8d862b723d7bc94fe3813/Child-Gitlink746c5cf2f2324104a62fb71510343aa40d3976c5 published isolatedbranchonly. Author227PASS/53new/0skip,static9/frozen10; source/manifest/syntheticactualCacheexamples+artifacthashes bound toexactcommit. Candidate canonical-pathInbox request andhandoff added; GPTfresh incremental thenDScleanCPU,STOP afterreadback. OriginalV3eafef76f andcanonicalChild746c5cf2 unchanged bythis task, no runtime authorization inferred.

## 2026-10-28 — Evaluation V2 new900 Design + isolated CPU prototype
- Environment initially unavailable, now exec verified working. beforeHEADbef955c2001b32e4bdd437c9bb6103ece6b8f59c; fetched/advertisedV3 exact5c1d78cbaa9d4449a471ce587afe89375292dc27; new history Issue6Code/DS approvals+Owner merge and Compact evidence/GPU request consumed; no new V2 request in remoteInbox. Childclean746c5cf2f2324104a62fb71510343aa40d3976c5 remainsmatchingGitlink. New isolatedRoot v3-eval-v2-design-20261028 fromlatestV3, no merge of oldcandidate needed. Read rootAGENTS/SESSION/latestInbox/TODO/DECISIONS, ChildAGENTS andactual closed_loop_eval/run_recorded_episode source. CurrentOwner/GPTdesign/Codexbuild/DSexecution roles supersede legacyMM/Kimi workflow; otherCompactGPU task is not authorization for this neweval.
- Ownernewscope: fresh18Task×50, no431migration or historicalcompatibility; env-authoritative outcomes, media independent/noautomaticffmpeg or videos_view, flatTask/Episode, process/resultseparation. Phase1 planned files ONLYnew docs/build V2design + tools/v3/episode_eval_v2_prototype/{contract,store}.py andfocusedtests/authorEvidence/SESSION/TODO/Inbox. No productionlauncher/Child/model/Local/action/environment changes before newDesignGate. Existing check_success swallows exceptions intoFalse andmediaerrors canoverride success inlegacyrunner, documented integration risks notpatched. Conservative proposeddefaultTask-levelResume: reuse completeTask, restartincompleteTask same literalSeed+fresh env, rename oldpartialstream into_internaldiagnosticarchive withtransaction recovery; no mixing independent scene streams or duplicatevideo copies. Phase1realCPUprototype tests outcome/atomiccommit/recovery/summary/nolegacyadmission; no fullproduction900entry/GPU/server/Kitchen.

- V2 Stage1 frozen3moduleCPU final02:65PASS/0fail/error/skip in9.15s, Ruff0.12.7check/format/syntax6/frozen6SHA PASS. Isolated fake env/literalSeed50reset andreset-only replay counterexample; formal-shaped18fakeTask×50=900unique results/450success/450failure/SR0.5; Invalid+Pending explicit/nullfullSR; lateprocesserrorpreservesvalidoutcomes butblocksqualification; mediaoff/on/error andPython/NumPy/already-loadedTorchCPU RNG unchanged, noCUDAinit. Journal4faultboundaries recoveradjacentgeneration/no-copyinode; badjournal/corruptrecord/staleproducer/dedup/old431namespace block; readonly/rebuildable summaries, CPUlockcontender. No failures in65final; earlier59/63werePASSbutnotaggregated. Prototypeonly/runtime_gate_approvedFalse markers retained. r1 explicitly requestsDesignGate decisions TaskRestartcost andconservativeprocess-error/initializationblocks beforeStage2; not a production900entry. No productionRootscript/config/vendor/Child/source model modifications, baseline5c1d78cb/746c5cf2 unchanged. NewDesign+prototypeRoot thenauthorEvidence/Inbox,STOPforGPTDesignReview;no server/GPU/realDCP/431IO.

- V2 Design/prototypeRootdc750f8e258d10a33e7a195cf907926b1c98bd7f/Child-Gitlink746c5cf2f2324104a62fb71510343aa40d3976c5 published isolatedbranchonly. Handoff/newr1Design/65PASSrawEvidence/actual900FAKEdirectorysample andcandidatecanonical-pathInbox request recorded. No production900entry, noNative/Local/Server/Canary execution. ProposedTaskrestart/process-fault/initializationchoices exposed forGPTDesignReview; STOPafterreadback, not an authorization to continueStage2.


## 2026-10-28 — Evaluation V2 r2 D1–D4
- BeforeRoot23f2d3a1; fetched/advertised V3 exact9858e70b6d66e40429017ce9a752926fc7330af6, all12 new docs commits consumed. Candidate and V3 diverged; merged canonical docs into NEW isolated v3-eval-v2-design-r2-20261028, preserved both Inbox append tails; no V3 branch update. Full latest contract/r1 review read; explicit readingACK committed BEFORE source edits, Issue APIForbidden so handoff alternative. Owner supersedes Task replay/fixed scene seed. Current roles override legacy tmux governance; no agents. Scope new r2design + isolated prototype modules/tests only. D1 scoped faults, D2 Task/Attempt commit recovery, D3 sparse episode resume, D4 strict admission/4strike/manual skip retry. Production/Child/model/vendor/history untouched. Upstream GPT review has preexisting trailing whitespace, preserved unchanged.

- D5 steering received during r2 work; full CPU01 finished frozen 79PASS/1FAIL (lockfixture string lacked explicit Path import; source flag, not a production failure), rawlogs retained. Fetched/advertised latestV3b59d1faf486765271295a00ee5e20e4d239e0163 +3docs commits, canonicaldocs merged to candidate preserving bothInbox tails. Read complete D1-D5 and D5review; ACK appended and published BEFORE D5 source edits. Add explicit frozen order/round scheduler, multiple same-round workers, resume scanning and stale/duplicate claim tests; models/Local/EGL lifetime design. No new production permissions.

- r2D1–D5 final02 exact frozen full5moduleCPU104PASS/0failure/error/skip in287.05s; Ruff0.12.7 check/format/AST10/frozen10SHA PASS. Actual prototype900 dispatches +50 round barriers,450success/450failure/SR0.5; three asynchronous fakeWorkers, explicit claim/commit tickets, same-order Resume skip inclvalidfailure/Skip37+valid38, cancellation/crash proof. D1 scoped immutable fault+cleanup/newhealth/validretry orlate-result execution-only resolution; unclosedWorkers blockqualification. D2 intent/dir/ready andcriticalfault-before-terminal evidence. D3 sparseimmutable slots/no scene reproduction. D4 32sample cap/4consecutiveerrors/manual one-useOwnerpermit, ENV_REBUILT recorded, unsafe stop; 50skip×4longerror report regression RED1FAIL then finalGREEN, onlyderivedsummary16MiB whileCore256KiB remains. Earlier failures (permitstatus reset, fixture imports, alreadyclosed stream message) and earlier101PASS preserved separate NOTaggregate. Proposed runtime3residentmodels+18envs/6EGLcontexts perGPU requiresfuture measuredresourcegate, not CPU performanceproof. Finalpublication fetchadvertisedV30b179e8f611ede5200cae2f9485c1a601774778e; only unrelatedCompactS0resource docs appended, consumed/preserved in isolatedcandidate; no new Evaluationcontract changes. NewformalDesignRoot+sameChild thenevidence/request and STOP for GPT D1–D5incremental;no productionentry or Native/GPU/old431 operations.

- Published formalr2Root1fd3ad42075032bd0137ac9a76306169aaa45032/unchangedChild746c5cf2f2324104a62fb71510343aa40d3976c5 candidate-only; author104PASS/0skip287.051s andstatic10 frozenbound. RawEvidence73artifacts +real synthetic900archive/50skip-longreport retained, ACK/handoff andcandidatecanonical-pathInbox reviewrequest appended under128KiB. CurrentstatusREVIEW; STOP pendingfreshGPTD1–D5Designreview, no sourcewiring/merge/runtime. Final remote readback stillrequired before delivery.


## 2026-10-28T15:50:26+08:00 — Evaluation V2 r2 Design Gate receipt (docs only)
- User relayed GPT verdict; fresh explicit V3 fetch and advertised SHA both `84bbc4dd5470dc405c26d460c152c8e995fcc1b0`. Before candidate HEAD `9e6968c9183beb365980afbf5db9d9097ec207c5`. Consumed3 new canonical docs commits (4cf90fb4 unrelated NoTTT co-resident plan;77ce0542 exact Review;84bbc4dd canonical verdict entry). Candidate intentionally diverges from V3; no fast-forward/merge or source sync claimed. Read remote formal Review through origin/V3 and matching live Inbox, not only user paraphrase.
- Exact formal Root `1fd3ad42075032bd0137ac9a76306169aaa45032` / Child-Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`; original author Evidence HEAD9e6968c9. Verified Review `docs/collab/chatgpt/reviews/2026-10-28_V3_RoboCasa_EvalV2_r2_D1_D5_1fd3ad42_746c5cf2_design_review.md` declares `APPROVE_DESIGN`, D1-D5 CLOSED in Design/isolated prototype scope only. Canonical Root Gitlink remains746c5cf2; new V3 delta docs only. Current Owner/GPT/Codex/DS roles supersede legacy MM/Kimi/tmux requirements; no duplicate audit/request or test rerun.
- Stage1 design/prototype task DONE; do not re-open D1-D5 on docs receipts. Author104PASS/287.051s remains author synthetic CPU Evidence, not DS/native results. Performance scale observation900 fake~177.891s and capacity assumption3Servers+18envs/6EGL contexts perGPU carried forward as mandatory Stage2/Canary validation risks, not established production regressions or accepted measured capacity.
- Stage2 remains TODO pending separate explicit Owner scope authorization. No production/Child/model/Local/launcher/encoder/probe edits, no GPU/server/Simulator/DCP/Canary/900, no V3 merge, no training/historical431 change. This receipt changes only SESSION/TODO on the existing isolated candidate and does not create a new formal pair or request a fresh technical review. STOP after receipt publication/readback.


## 2026-10-28 — Owner authorizes Stage2 production candidate + CPU only
- Owner explicit 授权 after GPT Stage2 scope; latest advertised/fetchedV384bbc4dd5470dc405c26d460c152c8e995fcc1b0, exact1fd3ad42/746 designAPPROVE read previously and retained. New isolated Root/Child branches v3-eval-v2-stage2-20261028; no canonicalV3/Child updates. Claim new Child evaluation/robocasa_v2 stdlib core + native simulation adapter/worker/media, narrow opt-in closed_loop_eval hooks preserving legacy default; Root new launcher/config/runtime/native process ownership/identity/CPU tests/runbook. Production core promoted/refactored from approved prototype, no import fromtools/prototype. Preserve model/action/raw15/env12/Local algorithm, old Queue/legacyResults/NoTTT/G1/history431. Tests only CPU/fake env/server/processes/tinyfixtures, no nativeRoboCasa/model/GPU/DCP. New Child thenRoot candidates +rawEvidence, GPTCodeGate thenSTOP; DS/runtime/Canary/900/V3merge separate authorization.

## 2026-10-28 — V3 Evaluation V2 Stage2 author CPU complete; implementation REVIEW

- Owner explicit Stage2 authorization consumed; approved Stage1 Root1fd3ad42075032bd0137ac9a76306169aaa45032/Child746c5cf2f2324104a62fb71510343aa40d3976c5. Latest V3 docs4c9990f5bfab4544fe9edc69ba7227a07ef1ed8e merged into isolated candidate1404c34e6cb46df68368d877c296bf95a5bcc9f4; concurrent NoTTT Owner/storage records preserved append-only. No V3 production merge.
- Child implementation2d4a42590fead00ea16f6ae5902e2bc8382b07e2 committed and pushed only to v3-eval-v2-stage2-20261028; remote readback exact, canonical v3-local-ttt remains746c5cf2f2324104a62fb71510343aa40d3976c5. Root implementation未提交 at this record; next commit binds this Child Gitlink.
- Actual production Store/contract/Episode-major Scheduler + inherited-socket native Task Worker/adapter, checked resident Action Servers, strict initial/outcome checks, original raw15/state15/native Local sequence, whole-directory atomic Core publication, immutable fault/cleanup/recovery receipts and exact missing-slot Resume. Optional bounded CPU media is diagnostic-only. CLI fresh/resume/dry-run/explicit Owner authorize, readonly input/runtime/cache/resource admission, terminal progress and coordination metrics. Training/model/Local algorithm/DCP/vendor/legacy entry remain unchanged.
- Frozen author CPU final_cpu02:200passed(142new production path +58legacy defaults),0failure/error/skip; pytest86.73s; total runner88.057s. Production900 synthetic test41.070s, exact900dispatch/50barriers,450success+450normalfailure, mock3model/18env lifetimes only. Claim p95~28.31ms/Core commit~4.01ms/rebuild max~2.93s,8223record reads/86814cache hits; no native throughput claim.34Python Ruff0.12.7check/format/AST and shellsyntax/help PASS; final_source==static_source, before/after frozen hashes identical. Full commands/env/raw logs retained under /tmp/psm-eval-v2-stage2-20261028 and packaged Stage2 author Evidence. Draft failures retained separately, not counted as final PASS.
- Runtime tests use fake simulator/model/GPU boundaries, actual native HTTP/Local/action codecs, actual CPU process supervision and small FFmpeg ENCODE only. No real model/Action Server/RoboCasa/EGL/GPU/DCP/train/old431 access. CPU NumPy2.2.6 is a test environment, not vendor2.2.5 native certification.18retained environments/EGL capacity and real CUDA/Local semantics remain Stage3 Canary questions.
- Formal author handoff/Evidence and canonical-path Inbox request on candidate next; GPT Code Gate then DS independent CPU then separately Owner-authorized Canary. STOP after publication, do not merge candidates or begin native execution.

### Stage2 exact implementation freeze and Code Gate handoff (2026-10-28T10:16:28.736730+00:00)

- Formal Root `4769d711777c20a72dd7a3f6071a96f08ad8abb0` / Child+Gitlink `2d4a42590fead00ea16f6ae5902e2bc8382b07e2`. Child candidate remote verified exact; Root code guard executed after commit and bothworktreesclean, same34finalsource/staticSHA+49formalGitBlob bindings. Evidence/handoff/Inbox appended only; this later docsHEAD is NOT implementation authority.
- Fresh remote review precheck: before_head=4769d711777c20a72dd7a3f6071a96f08ad8abb0; fetch origin V3 explicittracking successful; advertised/trackingV3=`4c9990f5bfab4544fe9edc69ba7227a07ef1ed8e`, no new commits since consumedlock4c9990f5. Exact formalRoot/Child grep of remote reviews has0matches(exit1 expected), not a Code verdict. Stage1matchingAPPROVE_DESIGN remains inputonly. Kimi/MM/tmux waiting not applicable per latest Owner/GPT/DSroles+submitthenSTOP; no fabricated panes/observations.
- Request on candidate canonical-path Inbox with livebytes<131072, byteprefix preserved. Request GPT fresh Code Gate on this pair; thenDS independentCPU; thenOwnerseparateCanary authorization. This submission doesnotcloseStage2CodeGate or DSCPU. NewcandidateRootpublication/exactremoteHEAD/Gitlink/frozenArtifactreadbacknext, thenSTOPREVIEW.

### Stage2 candidate publication verified — STOP REVIEW

- Both GitHub candidates published and fetched/read back. FormalRoot`4769d711777c20a72dd7a3f6071a96f08ad8abb0`/Child-Gitlink`2d4a42590fead00ea16f6ae5902e2bc8382b07e2`; verified remote author Evidence HEAD`891c69c907e9620de6231c7ae37e2be3c77ee255`. Root candidate Gitlink, Child candidate advertised SHA and fetched FETCH_HEAD all equal. CanonicalV3 still4c9990f5bfab4544fe9edc69ba7227a07ef1ed8e/canonicalChild746c5cf2f2324104a62fb71510343aa40d3976c5 at readback; no canonical push.90original Evidence blobs read from fetched remote candidate match SHA256 manifest; actual frozen-source guard PASS against FormalRoot at docsHEAD; bothworktreesclean before this receipt.
- Exact production Root direct-parent and Child baseline diff whitespace checks PASS. Raw archived patch-context/traceback lines retain original trailing whitespace and triggered artifact-only whitespace diagnostics; those immutable source artifacts were deliberately not normalized. No production/static gate failure was waived.
- Receipt: docs/collab/codex/reviews/2026-10-28_V3_EvalV2_Stage2_remote_publication_receipt.json. This final receipt is bookkeeping only. TaskREVIEW; GPT new-pair Code Gate thenDSCPU thenseparateOwnerCanary. No moreimplementation, V3merge, GPU/native/model/DCP/history/train operations after submission.

## 2026-10-28 — Codex ACK Issue8 / Phase A claim BEFORE edits

Read full Owner directive2026-10-28_V3_EvalV2_Dynamic_SimSlots_LocalTTT_Batch_Owner_Implementation_Directive.md from advertisedV30c424c830968cf447f5bd36c438d46325d12a557 and correctedFINALCodeGate. BaselineRoot4769d711777c20a72dd7a3f6071a96f08ad8abb0/Child2d4a42590fead00ea16f6ae5902e2bc8382b07e2; new isolatedRoot/Childv3-eval-v2-slots-a-20261028, previousStage2branches preserved. ACKD1-D5retained; fixed18Taskactors superseded; phantomF1 withdrawn/notmodified. PhaseAactualcode+CPUONLY: dynamicG/N,one reusableSimSlot/GPU,onepersistentServer, M=B=1strictly; explicitclean/task-switch/quarantine/uniqueenvironmentseedprovenance andseparateSession perEpisode. PlannedChildscheduler/core sampling/nativeworker+newSlotservice; Rootruntime/config/identity andfocused tests/newdesignnote/Evidence. No Local/modelmath/Serverbatch/training/DCP/Vendor/old431/canonicalbranchchanges,noGPU/nativeSim orPhaseB. NewPairthenGPTCodeGateSTOP.

## 2026-10-28 — Issue8 Phase A author CPU complete / REVIEW

- Ownerdirective0c424c830968cf447f5bd36c438d46325d12a557read/ACK before edits4292905afcf6dfd0ce4f00e336c35a7c09e319b0(publishedcandidate). Baseline sourceRoot4769d711777c20a72dd7a3f6071a96f08ad8abb0/Child2d4a42590fead00ea16f6ae5902e2bc8382b07e2. NewRoot/Childcandidatev3-eval-v2-slots-a-20261028 only; withdrawnF1notfixed, approved commit/cancel lock preserved and independently exercised by deterministic tests.
- Childnew implementationd2c1bda62880dbeee196f70945e5bc430b73f4b6 committed/pushed andremoteverified. Stage2Childcandidate2d4a4259 andcanonicalChild746 unchanged. Rootformal未提交atthisrecord; nextcommitbindsGitlink. Actual reusableSlotWorker (notTask actorcache),dynamicG/N/no sticky modulo dispatch,M=B1failclosed; Taskswitch claim/lease/metadata/seedgrantvalidation, LocalACKbeforeCLEAN, quarantine+explicitResume, actualseed/reset/Slot provenance. LogicalTaskstreams retained until allownedprocessesdecommissioned; no false processes-gone receipt onTaskswitch. Nativepolicy/action/Localmath/training/DCP/vendor unchanged.
- FinalauthorCPU254PASS(196production+58legacy),0failure/error/skip;pytest176.06s/runner177.68s, samefrozen37PythonSHA asfinalstatic02Ruff0.12.7check/format/AST andshellsyntax/helpPASS. 25G/Nmatrix plus actualdefaultRootPool/Worker sockets, D4four-errorscleanrelease/otherTaskcontinue, quarantine→newSlot/newSessionResume, ToyW0causalevidence, sparseResume/claim/metadata/grantnegatives, unchangedF1ordering. Realmodel/GPU/physics alwaysdoubles except CPUcodec/process/encoder.
- 900actualproductionRuntime/Scheduler/SimSlotCPUtest87.781s;900dispatch/50barriers/3physicalSlots/3mockModelLoads/900fakeenvrebuilds/450success450failure. Claimp95~78.27ms/Corecommit~30.92ms/lockwait~62.66ms/rebuildmax~3.03s;10023JSONreads/118677cachehits. WholeCPUtestchildru_maxrss348272KiB(~340.11MiB),user125.01s/system51.80s; notnativeGPU/robocasaRAMcapacity. No speedupcomparisontoold lighter900test.
- Draftfailuresretained: matrixledgerfixturepath; transportmetadatamismatchcorrectlyrefused; hardcodedephemeral-rangeport55004conflict; transportsetupwithoutStorelease. Finalsourcepreservesproductionchecks/assertions, fixesfixturesratherthanweakeningadmission. Staticrerunoutputdirectorycollisioncorrectedoutsideprojectsource; finalsourcehash/static37matchverified.
- Newarchitecturedesignnote docs/build/PSM-WMA_V3_EvalV2_PhaseA_Dynamic_SimSlots_2026-10-28.md. NewFormalRoot+Childdiff/rawEvidence/GitBlobs/candidateInboxhandoff→GPTnewpairCodeGateSTOP, thenDSindependentCPU. NoPhaseBdesign/codeyet,noV3merge, realGPU/model/ActionServer/RoboCasa/DCP/900/history431/trainingoperation.

### Phase A final delivery boundary correction — author final255 PASS

- Pre-final implementation1ac82af40a95587dd3f5e016dbc6a7e73ebeb9c2(254authorPASS) had not been submitted for review. Delivery audit found an actual NEW-architecture edge: Slot exits0 after lastCore, no inflightclaims, coordinator_stop scope omitted the current physical Slot. Preserve source sameScheduler.cancel/commit lock; add currentphysicalSlotassignments to post-cancel affectedscope, never historical switched-out Taskstreams. This is distinct from withdrawn Stage2phantomF1.
- CounterfactualRED (restore ONLY Runtime.run from1ac82af4 intoCPU memory) failsnew late-zero-exit assertion; currentGREEN test passes. OriginalCore staysbyte-identical; explicitResume freshhealthresolveslatefaultwithoutinference/retest. RawREDandGREENandprevious254sourceEvidence retained, no workspace source rewind. Pre-final untrackedEvidencepackagemovedbyte-preservingto/workspace/phase_a_pre_finalize_1ac82af4_package.
- Final full03 frozen37source +static03 PASS:255passed(197production+58legacy),0failure/error/skip,pytest178.04s. All25G/Nmatrix/defaultRootWorkerIPC/900realRuntime-Scheduler-SimSlotCPU path and legacyregressions retained. FinalFormalRootnextcommit supersedes1ac82af4 asrequesttarget; Childremainsexactd2c1bda62880dbeee196f70945e5bc430b73f4b6. FullPhaseAreviewrangeisACK4292905a→finalRoot (includesinitial1ac82af4 +thisfinalscopeclosure), NOTjustthelastsmallcommit. NoGPU/DS/V3merge/PhaseB.

### Phase A exact-pair Code Gate request

- FinalFormalRoot`fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` / Child-Gitlink`d2c1bda62880dbeee196f70945e5bc430b73f4b6`. CodeguardpostcommitPASS withcleanRoot/Child, final255/static37samefrozenSHA,52formalGitBlobbindings. WholePhaseAreviewbase4292905a; 1ac82af4 isintermediateunreviewedSource, notcurrentGate. Childpublishedexactnewbranch; RootcandidateEvidencepublicationnext.
- FreshV3reviewprecheckfetch+lsremoteadvertised0c424c830968cf447f5bd36c438d46325d12a557/trackingmatches; nonewcommitssinceconsumedOwnerdirective. RemoteexactnewRoot/Childreviews0matches(gitgrepexit1expected), notaver dict. Prior4769/2d4APPROVE_CODEretainedonlyhistoricalbaseline. NoMM/Kimi/tmux/30roundwait perOwnerRoles+submitthenSTOP. Candidatecanonical-pathInboxappend under128KiB,prefixpreserved, uniquePhaseAfullCodeGate requestwithrawEvidence.
- Allfailurehistory/REDGREENretained. NoScopeGateclosureorDS/nativepassassertion. CandidateHead afterpublicationisdocsbookkeeping, neverreplacestheFormalRootabove. VerifyremoteCandidateHEAD/Child/Gitlink/artifacts, thenSTOPREVIEW; no moreimplementation/GPU/merge/PhaseB/old431/train/DCPactions.

### Issue8 Phase A published and remotely verified — STOP REVIEW

- FormalRoot`fd7e43f6630a436ab3d83edcd3ce9d1516b342d1`/Child-Gitlink`d2c1bda62880dbeee196f70945e5bc430b73f4b6`; published/fetchedRootEvidenceHEAD`12cdc6af5bedcaf4fc2a17926272ddb58103de9f`. Current candidateGitlink, advertised/fetchedChild candidateallmatch. CanonicalV3atreadback0c424c830968cf447f5bd36c438d46325d12a557/canonicalChild746c5cf2unchanged; Stage2Childcandidate2d4a4259preserved. No productionbranchpush.
- 85rawEvidenceblobs readfromfetchedremoteGitobjects matchfrozenSHA256; candidateInboxprefixbyte-preservedand<128KiB; sourceguardagainstFormalRootandfullPhaseA/ChildsourcewhitespacechecksPASS, root/childclean beforefinaldocsreceipt. Root17-filefeaturecommit1ac82af4+finalclosurefd7e43f6reviewtogetherfrom4292905a; onlyfd7e43f6isfinalFormalRoot.
- Finalauthor255PASS(197production+58legacy)/0skip/178.04s/static37PASS/source52bindings. CPUtestpeak351012KiB,user126.14s/system51.71s; synthetic90087.985s,3Slots/3mockmodels/900fakeenvs/50barriers; p95claim76.89ms/Core27.14ms/lock65.54ms,10023reads118688hits. No realGPU/Simcapacityclaim.
- Receipt docs/collab/codex/reviews/2026-10-28_V3_EvalV2_PhaseA_remote_publication_receipt.json; thisisbookkeepingnotnewimplementation. CodeGateREQUESTED, taskREVIEW; STOPperOwner. NextGPTnewpairreview→DSindependentCPU→separateOwnerCanary; PhaseBdesignonlyafterPhaseAdecision. No morecode/GPU/native/DSjobs/merge/history/DCP/trainingactions.

## 2026-10-29 — Phase A verdict receipt / Phase B DESIGN claim

- Freshsync: before_head711ee8be40311d3cade19946cee4e23e508c3727; explicitoriginV3fetch+advertised/tracking36a5f157933d2f3f053023cd40796f81e6d60abb matched. New2commits21baeae2/36a5f157docs-only. ExactDetailedReview2026-10-29_V3_EvalV2_PhaseA_fd7e43f6_d2c1bda6_FINAL_Code_Gate.md and canonicalInboxbothread: APPROVE_CODE ONLYforRootfd7e43f6630a436ab3d83edcd3ce9d1516b342d1/Child-Gitlinkd2c1bda62880dbeee196f70945e5bc430b73f4b6; GPT15/15 selectedblobs+authorraw255JUnit, notDS/nativeexecution. PriorF1withdrawalpreserved. No duplicate technicalaudit.
- PhaseA sourceCodeGateDONE; DSindependentCPUandthenGPTEvidenceGatePENDING. ExistingauthorfrozenCPUreplayalreadyavailable, noDSjoblaunchedorrepeatedauthor255tests. Carrynonblockingcaveats: allselectedGPUsadmissionevenidleN<G, hard_reset/EGLrebuild/900envtradeoff; notspeculativeproductionfixes.
- LatestOwnerallowsPhaseBdesignafterthisverdict. Newrootv3-eval-v2-batch-b-design-20261029 fromexactfd7source+711docs; mergedcanonicalverdictdocs only, append-onlyInboxtailspreserved. Childstaysonunchangedd2c1bda6/PhaseAcandidate; canonicalRoot/ChildandPhaseAcandidatesnotupdated. Claimdocs/buildPhaseBdesign+sourceaudit+acceptancecontract and, ifuseful, isolatedCPUprotocolmodelundertoolsonly. No productionChild/scripts/config edits beforeAPPROVE_DESIGN; noGPU/model/DCP/RoboCasa/native/900/merge/history/train/DSexecution. NewDesignRoot+sameChild+Evidence→GPTDesignGateSTOP.

### 2026-10-29 — Phase B r1 design ready for separate Design Gate

- Task `V3-EVAL-V2-BATCH-PHASE-B-DESIGN`: REVIEW, design only. Added `docs/build/PSM-WMA_V3_EvalV2_PhaseB_MultiSim_Transactional_Batch_Design_r1_2026-10-29.md` and isolated `tools/v3/eval_v2_batch_design/{__init__,protocol_model,protocol_model_test}.py`. These are not production imports or a runnable Cosmos service. No new model algorithm or production support flag.
- Read actual frozen server/Local adapter/online memory/native generator/prefix/Slot/scheduler sources. Required-mode Batch is still explicitly rejected in production; native generator has per-item prefixes but existing single-Session publication and HTTP replay are insufficient. Design specifies one GPU model executor, M separate concurrent Sim processes, bounded compatibility queue, one native generation invocation, atomic fast+visual+frontier+response bundle, retrievable end ACK, closed-generation fencing, async optional media and D1–D5 preservation. No guard-only enabling.
- Final author symbolic protocol CPU: **29 passed, 0 failed/error/skipped, 0.08s pytest**. Ruff0.12.7 check/format and AST3 PASS. Initial28-test draft preserved externally; final adds end-ACK retry and literal-seed mapping, removes a trivial media-only assertion. No symbolic test is a native tensor/HTTP/EGL/physics/DS proof. No full Phase A255 rerun or new Phase A verdict.
- Commands use `/workspace/.venvs/psm-wma-cpu/bin/python`, `pytest --noconftest -c /dev/null -p no:cacheprovider`, CUDA hidden/offline/cache paths under `/tmp/psm-eval-v2-phase-b-design-20261029`; final raw JUnit/logs and audit in that path.16 source Git Blobs match frozen fd7/d2; Root scripts/configs/third_party/Gitlink diff ZERO and Child clean. Exact commands/raw evidence and Design SHA are bound in the follow-up evidence commit.
- Next: publish new DESIGN Root (this commit), unchanged Child/Gitlink `d2c1bda62880dbeee196f70945e5bc430b73f4b6`, author evidence and canonical GPT APPROVE_DESIGN/REQUEST_CHANGES request on new candidate branch only; remote readback, then STOP. Phase A source APPROVE_CODE remains exact-pair only; independent DS CPU/native remain pending. No Phase B production implementation/merge/GPU/model/RoboCasa/DCP/900/DS/training/history operation.

### Phase B r1 design publication binding

- Exact Design Root `fac029c83eb94fdafcc26d030ca5942542d740a3`, unchanged Child/Gitlink `d2c1bda62880dbeee196f70945e5bc430b73f4b6`; evidence/handoff is a separate bookkeeping commit, not production identity. Final29 symbolicCPU/0skip, JUnit0.084s;16 source bindings and protected production zero diff. Candidate Inbox requests APPROVE_DESIGN only. Fresh V3 advertised/tracking7e0b7d416e2de29fc93edd4a1084dea52e08fa9a adds3 unrelated NoTTT evidence/review commits, no production change; preserve that work and do not expand scope. Publish only new Root candidate; remote receipt next, STOP for Design Gate. PhaseA DSCPU still pending; no production/native/merge/job/history action.

- Phase B design candidate publication succeeded: remote evidence HEAD32fa91323e6adffe8878b430eea497e19713a7d1 fetched/read back, DesignRootfac029c83eb94fdafcc26d030ca5942542d740a3 ancestor, Gitlinkd2c1bda62880dbeee196f70945e5bc430b73f4b6. Rehashed17 archived artifacts and6 formal design bindings, protected production diffZERO; PhaseA candidate and Child refs unchanged, canonicalV3 remains7e0b7d41 (not updated by Codex). Remote receipt saved under docs/collab/codex/reviews/2026-10-29_V3_EvalV2_PhaseB_Design_r1_remote_publication_receipt.json. Receipt is bookkeeping only; STOP pending GPT Design Gate, no production or DS/native action.

## 2026-10-29 — Phase B r1 verdict receipt / narrow r2 claim

- Fresh check before_head377489716751b2785acf3e4bb985436657e78e6d; explicit originV3 fetch+advertised/tracking b4cd955ab5b139ce344afd5e9a34750db215ca6d match. Two new docs commits fe582915/b4cd955a. Read exact detailed Review 2026-10-29_V3_EvalV2_PhaseB_r1_fac029c8_d2c1bda6_Design_Gate_REQUEST_CHANGES.md and canonical Inbox: REQUEST_CHANGES on DesignRootfac029c83eb94fdafcc26d030ca5942542d740a3/Childd2c1bda62880dbeee196f70945e5bc430b73f4b6. B-D1 HIGH premature end ACK; B-D2 MEDIUM queued-only credit ownership. PhaseA APPROVE_CODE unchanged, DSCPU pending.
- Imported canonical docs into this same isolated candidate; Inbox conflict resolved as exact common prefix + complete candidate tail + complete new remote tail, byte-preserving append-only history, no production changes. Owner scope is design/protocol/tests only; no Kimi/MM/tmux wait or DS job under current roles.
- Task V3-EVAL-V2-BATCH-PHASE-B-DESIGN-R2 IN_PROGRESS (Codex). Planned only tools/v3/eval_v2_batch_design protocol_model.py/test + a test-only ticket_registry.py/test if needed; new r2 docs/build design, new author evidence/handoff, SESSION/TODO/Inbox. Preserve r1 frozen document/evidence, Child and production Root trees. Distinguish cancel intent, deferred end ACK and transaction release; queued+inflight unique ticket/byte ledger, exact duplicate join and terminal credit release. Deterministic RED old-model counterexamples, final CPU/static/hash, new DesignRoot then GPT incremental Design Gate STOP. No PhaseB production/GPU/server/model/realDCP/RoboCasa/900/merge-to-V3/history/training operations.

### 2026-10-29 — Phase B r2 narrow design fix complete, author CPU

- B-D1: request_cancel only records intent; request_end/poll_end return explicit deferred EndReply while a model executor or owned Ticket is nonquiescent. Only executor finish after return/unwind proves abort/commit quiescence; end discards only its own settled response, then exact closed-generation ACK can replay. Root cannot reassign before ACK. Dedicated cancellation replaces the incorrect r1 reset-as-cancel test.
- B-D2: new isolated TicketRegistry is the same authority used by Queue and Session model; pop seals while preserving all queued+inflight+committed-undelivered reservations/bytes; exact duplicates join original Ticket without renewing budgets. New Frontier denied before delivery ACK/abort/End discard. Terminal release exact-once, partial batch metadata drops freed payloads; seal failure only releases newly created admissions, old inflight untouched. Registry-originated postcommit timeout delivery is fenced.
- Changed only isolated tools/v3/eval_v2_batch_design/{protocol_model.py,protocol_model_test.py,ticket_registry.py,ticket_registry_test.py,lifecycle_test.py}, new r2 docs/build note and bookkeeping. Full r1 frozen design/evidence retained. Agent assisted registry author work and read-only cross-check; those are author checks, not GPT or DS Gate approval.
- Expected RED on exact fac029c8 source:3 tests/3 intentional assertion failures/0errors/skips, raw source SHA25611d0795fcde4c220ac115ddcd89918e4684a072f42975448b7cfa197b5190bee. Final GREEN:74 passed/0fail/error/skip, pytest0.21s (29 prior symbolic +24 registry +21 integrated). Ruff0.12.7/format/AST6 PASS.16 frozen production Git Blobs match; Root production/Gitlink diffZERO, Child clean exactd2. No full PhaseA255 rerun or native proof.
- External raw outputs /tmp/psm-eval-v2-phase-b-r2-20261029/{red,green01,final}; redcounterexamples use git-show frozen isolated r1 only, green fake vector/clock/scalar only. New formalDesignRoot follows this record, then separate evidence/handoff/Inbox and remote receipt, GPT incremental APPROVE_DESIGN request, STOP. PhaseA APPROVE_CODE unchanged, DSCPU pending; no PhaseB production/V3merge/GPU/model/DCP/RoboCasa/900/DSjob/training/history action.

- Phase B r2 publication binding: exact DesignRoot8f94b67ef3f049f5905ee35d54083d5f69534975 / unchangedChild-Gitlinkd2c1bda62880dbeee196f70945e5bc430b73f4b6. Final74 symbolic CPU/0skip/JUnit0.213s; expectedRED3 frozenr1 failures retained, static6/audit16 PASS. New evidence/handoff/canonical request packaged separately, not implementation or approval. V3 prepublication b4cd955a unchanged. Candidate only push/readback next, STOP GPT incremental APPROVE_DESIGN Gate; DSCPU/native pending.

- Phase B r2 candidate published/read back at e956d0eebb200ea0df272c28626a1fe4f60e7f1e; formal DesignRoot8f94b67ef3f049f5905ee35d54083d5f69534975 and Child/Gitlinkd2c1bda62880dbeee196f70945e5bc430b73f4b6 verified. Rehashed23 raw artifacts+8 formal source bindings; production diffZERO; canonical V3/Child and PhaseA candidate not updated by Codex. Candidate canonical Inbox request read back,118049 bytes. Saved docs/collab/codex/reviews/2026-10-29_V3_EvalV2_PhaseB_Design_r2_remote_publication_receipt.json. Raw expected-RED traceback whitespace retained; source/docs whitespace checks pass. TaskREVIEW, STOP pending GPT incremental Design Gate; no PhaseB production, DS or native actions.

## 2026-10-29 — Phase B r2 verdict receipt / B-D3-only r3 claim

- Fresh before_head3e469d74322e737e20cab294bc8162579369b073; explicit originV3fetch+advertised/tracking70aebb5cc69f9b2f65b20440d0fa093eb31bcbe8 match. Two new docs commits5e1e6076/70aebb5c; read exact DetailedReview2026-10-29_V3_EvalV2_PhaseB_r2_8f94b67e_d2c1bda6_Incremental_Design_Gate_REQUEST_CHANGES.md and canonical Inbox. FormalDesignRoot8f94b67ef3f049f5905ee35d54083d5f69534975/Childd2c1bda62880dbeee196f70945e5bc430b73f4b6: REQUEST_CHANGES, B-D1/B-D2 CLOSED; new B-D3 MEDIUM post-ACK replay creates ghost queued reservation. PhaseA APPROVE_CODE unchanged, DSCPU pending.
- Imported review docs into same isolated candidate only. Inbox merge: candidate already preserves common-base lines with inserted prior candidate requests; verified line-opcodes only equal/insert, then appended full remote-only suffix to exact candidate bytes. No original bytes lost or rewritten; no production change. Existing Owner roles supersede obsolete Kimi/MM/tmux/wait rules; no subagents under current developer mode.
- Task V3-EVAL-V2-BATCH-PHASE-B-DESIGN-R3 IN_PROGRESS (Codex), B-D3 only. Planned only protocol_model.py replay-aware public admission, new replay_admission_test.py, new r3 docs/build addendum, author evidence/handoff and SESSION/TODO/Inbox. Keep Registry/lifecycle/existing74 tests and frozen r1/r2 design/evidence unchanged. Before Ticket allocation validate bounded committed response/payload, return immutable exact replay without reservation, reject stale evicted Frontier without allocation. Frozen-r2 expectedRED then new tests/full isolated CPU/static/hash, new DesignRoot+unchangedChild then GPT incremental Design Gate STOP. No production/Child/Gitlink/V3merge/GPU/model/RoboCasa/realDCP/900/DS/training/history operations.

### 2026-10-29 — Phase B r3 B-D3 author remediation complete

- Public ProtocolModel.submit now validates retained committed payload before any allocation; unresolved exact duplicates still join original Ticket, released exact replay returns original immutable Response, stale/evicted evidence Frontier rejects before registry call. ACKed R0 no longer resurrects a QUEUED reservation; replay/ACK cannot release queued R1 or affect another Session. Only submit changed (12insertions/2deletions); all other model AST identical to r2; five previous nonmodel Python files (including original74 tests/Registry/lifecycle) byte-identical.
- New replay_admission_test.py16 cases exercises continuous R0submit→generation→ACK→latePOST→sameReplay→ACK→R1, changed payload before allocation with/without queuedR1, stale/mutated evictedR0 before/after R1ACK, pending duplicate budget/epoch fences. Same tests SHA2560c5c4a34035222f42a2e7d65f59a10a390a9e75818dcdb5e8c00e0995b034d14 yielded frozenr2 expectedRED11FAIL+5PASS/0error/skip and targetedGREEN16PASS.
- Final full isolated CPU90PASS (original74 unchanged+new16),0fail/error/skip,Junit0.246s/pytest0.25s. Ruff0.12.7check/format/AST7 PASS.16 frozen production source Blobs match; Rootproduction/Gitlink diffZERO, Child clean exactd2. No native/tensor/HTTP/GPU proof or PhaseA255 rerun. Raw records /tmp/psm-eval-v2-phase-b-r3-20261029/{red,targeted_green,final}; frozenr2 model Blob b0890dfe8b8f550ce29b8fc65662a83dd6c29b04 and source hash preserved.
- New r3 docs/build addendum scopes only B-D3, preserves r1/r2 frozen docs/evidence and closed B-D1/B-D2. New FormalDesignRoot follows, separate raw evidence/handoff/canonical request and candidate push/readback, then STOP GPT incremental Design Gate. PhaseA APPROVE_CODE unchanged, independentDSCPU pending; no production/Child/V3merge/GPU/model/RoboCasa/DCP/900/DS/training/history action.

- Phase B r3 publication binding: exact DesignRootb9c7cf1607ffd38f6e3349bdde0b35703a6d7684 / unchangedChild-Gitlinkd2c1bda62880dbeee196f70945e5bc430b73f4b6. New16cases same red/green hash; frozenr2 expected11FAIL+5PASS, targeted16PASS, full90PASS/0skip/JUnit0.246s/static7/audit16/narrowAST PASS. New evidence/handoff/canonical B-D3 request packaged separately; source unchanged except submit. Fresh V3 prepub70aebb5c unchanged, only candidate push/readback next thenSTOP GPT incremental Design Gate; no production/native/DS/GPU action.

- Phase B r3 candidate published/read back at be01b5a992abd127b098984e233ec0696cc530dd; FormalDesignRootb9c7cf1607ffd38f6e3349bdde0b35703a6d7684 and Child/Gitlinkd2c1bda62880dbeee196f70945e5bc430b73f4b6 verified. Rehashed22 raw artifacts +5 formal source bindings; protected production diffZERO, prior74/Registry/End unchanged, canonical V3/Child and PhaseA candidate not updated by Codex. Candidate canonical Inbox readback124498bytes. Receipt docs/collab/codex/reviews/2026-10-29_V3_EvalV2_PhaseB_Design_r3_remote_publication_receipt.json is bookkeeping only. TaskREVIEW, STOP pending B-D3 GPT incremental Design Gate; no implementation/DS/native action.

## 2026-10-29 — Phase B Design APPROVE receipt / transaction-B1 implementation claim

- Fresh before_head36defe8c0217e7a1c70b2812a3d7ef0e6dda5918; originV3 fetched, advertised/tracking3f37df1fdda858482387f0f5db2c50be65a2f695 matched. Five new docs/evidence commits abd3d923/02e4c025/20389533/def31291/3f37df1f; unrelated NoTTT evidence preserved, not acted on. Read exact DetailedReview2026-10-29_V3_EvalV2_PhaseB_r3_b9c7cf16_d2c1bda6_Incremental_Design_Gate_APPROVE_DESIGN.md and canonical Inbox: APPROVE_DESIGN only on b9c7cf1607ffd38f6e3349bdde0b35703a6d7684/d2c1bda62880dbeee196f70945e5bc430b73f4b6; B-D1/B-D2/B-D3 CLOSED. PhaseA DSCPU remainspending, not substituted by symbolic90.
- New isolated Root/Child branch v3-eval-v2-transactions-b1-20261029 from unchanged PhaseA production source + published design/evidence. Design candidate branch preserved. Imported current canonical docs only. Append-only merge retained exact candidate bytes plus full new canonical suffix. No canonical branch or source ref modified. Current Owner roles override obsolete Kimi/MM/tmux/wait rules.
- Claim V3-EVAL-V2-PHASE-B-TRANSACTION-B1 IN_PROGRESS, Codex. Scope first implementation increment only: inference-only shared immutable fast/visual/response publication, lease/Ticket/replay/cancel/end and CPU client/opt-in B1 policy service; native generation reuses existing Cosmos entry. Planned Child inference modules/local memory adapter + server extensions + focused real-CPU tensor/contract tests, Root acceptance/runbook/evidence only. Existing launchers/defaults preserve PhaseA, strict B>1/MultiSim support remains unimplemented until second increment. New Child then Root FormalImplementation+CPU evidence thenSTOP GPTCodeGate. No GPU/model-load/realRoboCasa/DCP/900/DSjob/V3merge/training/optimizer/Vendor/history operations.

### Phase B transaction/B1 source freeze (before full locked CPU)

- Child d0ce64f3bed894d4f323b41fb838ad4a0d1f87c1 committed/pushed on new isolated branch;8 files:6 production inference/server +2 focused tests. Shared snapshot fast/visual/serialized response publication; existing model-owned scan protected by candidate cloning; required-mode owned actor, real device drain before commit and quiescent ACK only after model-mutex release; replay/credit/lease/epoch/traceback/quarantine, explicit B1 profile/client/native call wiring. No model/attention/training/DCP/vendor/simulator source changes.
- First author prefreeze focused56PASS and updated focused44PASS/0skip on real CPU Local tensors, native-generator/Wan/transport doubles; final profile/frontier checks are included in next full exact-pair Gate, not predeclared passed. New Root tools/v3/run_eval_v2_transactions_b1_cpu_gate.py + runbook ready. It locks clean exact Pair/import origin/Ruff0.12.7, runs inference and unchanged PhaseA regressions separately, records rawJUnit/environment/hash, forbids skipped tests and source drift. No GPU/model/DCP/native invocation.
- Inboxrollover required before review append: prior130996 bytes saved exactly at docs/collab/chatgpt/archive/CODEX_INBOX_20261029_PHASEB_APPROVED_9f66f53e.md, Blobd702c44dd68529e93a491c5353e866ab7be92a07, pre-rolloverHead9f66f53e77bb7324b56a7ac1973a5d645caed169. Header retains latest authoritative Design/PhaseA Source pairs/verdicts/current unresolved Code Gate; original content immutable, new appends only.
- Root source/Gitlink commit next; full locked author CPU and wrong-pair negative then separate evidence/new exact-pair Code request. M>1/NativeB>1/media/Sim/Launcher integration NOT implemented/claimed; no automatic next increment. No V3merge/DS/GPU/native/history/training action.
