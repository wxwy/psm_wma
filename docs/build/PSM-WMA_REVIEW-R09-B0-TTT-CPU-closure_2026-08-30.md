# R09-B B0 TTT CPU Backend Closure 复审报告（Kimi）

- 日期：2026-08-30
- 复审对象：Codex 的 B0 closure 整改（root `21b48f1`、submodule/Gitlink `cc848c3`、verifier provenance `9186e55`）
- 审查人：Kimi（审核者角色）
- 结论：**APPROVE_TO_CLOSE_B0**

## 验证范围与方法

只读复审：git 状态核对、diff 审阅、pytest 复跑、verifier 独立复现比对。未执行 B1/runtime/GPU，未编辑锁定文件。

## ChatGPT 四项 blocker 逐项核对

1. **remote SHA**：PASS。root `21b48f1` = origin/V2；submodule `cc848c3` = origin/v2；gitlink = submodule HEAD，均已推送。
2. **完整 provenance/schema**：PASS。artifact schema v3（`artifacts/g0/r09/b0_ttt_contract.json`）含 root/submodule/gitlink SHA、root_clean/submodule_clean、gitlink_matches_submodule、tool_sha256、完整 argv/cwd/python。verifier 新增 `--require-clean` 门控（`tools/g0/verify_r09_b0_ttt_contract.py:114-118` 区域 `_git` provenance 采集）。
3. **N=1/2/3/5/6/7 tail + unaligned state/token/present exact**：PASS。
   - `_tail_checks`（verify_r09_b0_ttt_contract.py:51-75）用 `mock.patch torch.autograd.grad` 统计各 N 的 update 次数，artifact 记录 expected/observed 全相等（1/2/3→0 次，5/6/7→1 次），terminal_progress 与 present 逐案记录。
   - unaligned exact：主流程 7 步 evidence（segment_steps=4，非整除），`replay(:2)+replay(2:, state)` 分段续算 vs 一次性 replay，state/token **exact 0 diff**（artifact segment 块，tolerance=0.0），present 逐位相等。
4. **实际 shape**：PASS。state members 逐一列出 shape/dtype/bytes：W [32,256] bf16=16384B、pending_evidence [4,256]=2048B、last_evidence [256]=512B、initialized bool=1B、segment_progress int64=8B，合计 18953B = bytes_limit，`bytes_limit_pass=true`。

## 关键契约核对

- mask/isolation：`masked_timestep_inert`、`padding_inert`（mask 位 evidence 置 ±1e6 后输出逐位不变）、`batch_permutation_isolation`、`cross_sample_isolation` 均 true。
- partial+full reset：`TTTLocalMemoryBackend.reset_mask`（local_evidence.py:214-230）按 sample `torch.where` 重置；verifier `partial_reset`（未选样本逐位保留、选中样本清零）与 `full_reset` 均 true。
- boundary：`boundary_isolation`、`boundary_state_zero_or_reinitialized` true（空 mask 续算无泄漏）。
- detach：`detach_value_exact`（token 与 `einsum(state)` 闭式逐位相等）、`graph_detached` true。
- optimizer/checkpoint exclusion：`named_parameters_excluded`、`optimizer_excluded`、`checkpoint_excluded` true，slow_learned_parameters=0。

## 独立复现

- `pytest cosmos_framework/model/generator/mot/local_evidence_test.py -k ttt`：**2 passed**（含新增 `test_r09_b0_ttt_backend_isolates_samples_and_resets_selected_state`，local_evidence_test.py:136 起）。
- 独立复跑 `verify_r09_b0_ttt_contract.py --require-clean --output /tmp/b0_v3_kimi.json`：status=PASS；除 `command` 块与 `root_revision` 外与 tracked artifact 逐字段一致。`root_revision` 差异为正确语义——artifact 生成于 `9186e55`（随后 `1e1f051` 才提交 artifact 本身），复跑记录当前 HEAD `21b48f1`；`root_clean/submodule_clean/gitlink_match` 复跑仍为 true。

## 我上一轮 REQUEST_CHANGES 的关闭确认

- MEDIUM-1（permutation/isolation/all-mask-continuation 无入库测试）：已关闭，新测试覆盖。
- MEDIUM-2（partial reset 语义缺失）：已关闭，`reset_mask` + 测试 + verifier check。
- LOW-3（bytes_limit 魔法数无注释）：已关闭，`BYTES_LIMIT = 18_953` 带 audit 引用注释。

## 意见

无阻塞项，无 HIGH/MEDIUM/LOW 遗留。**APPROVE_TO_CLOSE_B0**，可进入 B1 规划（GPU/runtime 仍待独立 Gate）。

---

# 第二次 closure 复审（2026-08-30 23:41 CST）

- 复审对象：root `685ca9a`（verifier 强化 `a9b7443`、artifact `f4ca0fc`）、submodule/Gitlink `ee1b78d`，均已推送并与 origin 一致；gitlink = submodule HEAD。
- 结论：**APPROVE_TO_CLOSE_B0**（附一条 LOW 收尾项）

## ChatGPT 三项整改核对

1. **frozen state schema exact hard-gate**：PASS。`EXPECTED_STATE_MEMBERS` 五成员 shape/dtype/bytes 全量冻结（verify_r09_b0_ttt_contract.py:21-27），`schema_pass = members == EXPECTED_STATE_MEMBERS` 并入 required 硬门（:165 区域），artifact state 块同时记录 schema_expected/members/schema_pass。
2. **canonical_command_hash**：PASS。command 块排除 tool_sha256 后 sorted-keys JSON 的 sha256（:168-170），我独立复算 verified=True；tool_sha256 与当前 verifier 文件逐字节一致，亦 verified=True。
3. **done/non-done partial reset**：PASS。verifier 与测试均由硬编码下标改为布尔索引泛化：保留侧 `value[~done]` 逐位等于原 state、清零侧 `value[done]` 全零（verify :138-141；local_evidence_test.py:164-167），另断言 `partial[3].tolist()==[True,False,False]`（initialized 标志同步复位）。

## 独立复现

- `pytest -k ttt`：**2 passed**。
- verifier 复跑（--require-clean → /tmp）：status=PASS，schema_pass=true，与**工作区 artifact** 除 command 块外逐字段一致（含 root_revision=685ca9a）。

## LOW-1（不阻塞关闭）

tracked artifact（f4ca0fc）的 `root_revision=a9b7443`，HEAD 已是 `685ca9a`（两次 docs 提交漂移，内容差异仅 provenance 时间戳语义，可接受）；但**当前工作区 artifact 是在 685ca9a 上重新生成且未提交的版本**（`git status` 显示 `M artifacts/g0/r09/b0_ttt_contract.json`）。我已验证该未提交版本确为 verifier 真实输出（与我的独立复跑逐字段一致），无篡改迹象。请 Codex 在关闭 B0 前二选一：提交该再生版本，或 `git checkout` 恢复 f4ca0fc 版本——保持工作区 clean 再进入 B1。

## 意见

三项整改全部落实且被我独立复现确认，无 HIGH/MEDIUM。**APPROVE_TO_CLOSE_B0**，LOW-1 属工作区卫生收尾，不影响契约结论。

---

# 第三次复审：post-closure provenance hygiene（2026-08-30 23:54 CST）

- 复审对象：root `b5df815`（canonical 口径提交 `4204408`，均 = origin/V2），submodule/Gitlink `ee1b78d`（= origin/v2，未变）。
- 结论：**APPROVE_PROVENANCE_HYGIENE**

## 核对项

1. **唯一 canonical 落实**：PASS。commit `4e85ba8`（"test: record R09 B0 verifier rerun"）是 HEAD 祖先，仅改 artifact 4 行：`root_revision a9b7443→685ca9a`、argv 顺序、`canonical_command_hash`；契约内容零变化。HEAD 工作区 artifact 与 `4e85ba8` 版本 md5 逐字节一致，`4e85ba8..HEAD` 对 artifact 无 diff——我上一轮的 LOW-1（未提交再生版本）已通过正式提交关闭。
2. **canonical artifact 字段**：PASS。root=`685ca9a`、submodule/gitlink=`ee1b78d`、gitlink_matches_submodule=true、status=PASS、全部 checks 与 schema_pass=true。`canonical_command_hash` 与 `tool_sha256` 经我独立复算均自洽。
3. **口径统一**：PASS。`4204408` 仅改 `SESSION.md`/`TODO.md`：SESSION B0 条目与 TODO 表格均明确唯一 canonical=`4e85ba8` artifact，`f4ca0fc`/`a9b7443` 降级为历史 initial-generation provenance；B1-RUNTIME-PREFLIGHT 已转 BLOCKED 并以前置条件写明。
4. **范围确认**：PASS。本轮未触碰 backend/test/verifier/artifact 内容/runtime/GPU；子模块 SHA 未变，verifier 文件与 artifact 记录的 tool_sha256 逐字节一致。

## 意见

无 HIGH/MEDIUM/LOW。provenance 口径已统一且可机器验证。**APPROVE_PROVENANCE_HYGIENE**，B0 post-closure 收尾完成；B1 可解除 BLOCKED 进入三方 preflight 审核流程（runtime/GPU 实施仍须独立 APPROVE_TO_IMPLEMENT_B1）。

---

# 第四次复审：R09-B1 B1-S 实施范围（2026-08-31）

- 复审对象：runbook `docs/build/PSM-WMA_R09_B1_TTT_runtime_preflight_runbook_v0.1_2026-08-30.md`；root `6ff6b1c`（范围对齐 `5005e4f`，均 = origin/V2），submodule/Gitlink `ee1b78d`（= origin/v2，未变）。B0 technical/provenance 三方关闭状态已在 TODO/SESSION 核实。
- 结论：**APPROVE_TO_IMPLEMENT_B1**（限 B1-S 静态接线 + 定向 CPU 覆盖；附一条 LOW 澄清）

## runbook 入口引用逐项核验（全部属实）

- `omni_mot_model.py:302-313`：✓ 精确。production 构造 `LocalHistoryRuntime(encoder, readout, RecurrentLocalMemoryBackend(...))`，第三个参数即 backend 插槽。
- `local_evidence.py:253-300`：✓。`LocalHistoryRuntime.__init__` 第三参类型为 `RecurrentLocalMemoryBackend | None`，replay 路径 `self.recurrent_backend.replay(evidence, history_mask)` 不传 state——每 forward fresh state 的 §3.3 前提成立；§3.2 的"本地类型注解扩宽"确有必要。
- `local_evidence.py:202-250`：✓。`TTTLocalMemoryBackend` 无 `nn.Parameter`，五成员 initial_state 全 zeros，docstring 明确 "not wired into production"。
- `action_policy_libero_edge_all.py:189-195`（实际路径 `cosmos_framework/configs/base/experiment/action/posttrain_config/`）：✓。`PSM_R09_A1_ENABLED=1` 时 allowlist 为 4 key：`encoder`、`recurrent_backend`、`local_memory2llm`、`local_memory_modality_embed`。
- `callbacks/r09_a1_runtime_probe.py:52-90`（实际路径 `cosmos_framework/callbacks/`）：✓。probe 直接访问 `backend.cell.weight_ih`，GRU 专属，不能误用于 TTT——§2 表格判断正确。
- `tools/g0/verify_r09_a1_smoke.py:116-168`：✓。硬编码 GRU 四 tensor added-set 与 `exact_allowlist_yields_16_tensors`，§3.5 禁止复用这些数字的判断正确。

## 范围与合同核对

- 默认关闭/显式 opt-in（§1、§3.1）✓；数据/VAE/cache/packing/mRoPE/native loss 不变逐项列出 ✓。
- §3.4 不套用 A1 GRU 断言、要求派生实际 optimizer membership + TTT parameter count=0 + encoder 无 TTT 回传证明 ✓，与 B0 detach 语义一致。
- §3.5 warm-start 仅 model-only、DCP added/removed 从 metadata 派生、frozen 公共 tensor 逐位 hard-gate、fast state 未序列化 ✓。
- §4 分轮：B1-S 仅 CPU/静态，B1-G 需独立 `APPROVE_TO_RUN_B1_SMOKE` + D005 sidecar ✓；§5 证据 schema 不预写 A1 数字 ✓。

## LOW-1（澄清，不阻塞批准）

runbook §3.4 与 B1-G 写"三条既有 prefix"/"三个参数组"，但实际 allowlist 是 **4 个 key**（action_policy_libero_edge_all.py:190-194）。合理解读是 TTT 下 `recurrent_backend` prefix 匹配为空、有效参数组为 3 个——建议实现时在证据 JSON 的 `prefix_matches` 中逐一列出 4 个 key 的匹配集（含空集），避免"三/四"歧义被误读为静默放宽。§3.4 已要求机器可读列出实际 membership，该硬门足以兜底，故不升级为 REQUEST_CHANGES。

## 意见

**APPROVE_TO_IMPLEMENT_B1**。授权上限 = B1-S：selector 默认关闭、Local runtime 最小类型/构造适配、TTT 专用 probe/verifier 与 recipe opt-in 解析的定向 CPU 测试。GPU/多卡/长训/B1-G 不在本次授权内。

---

# 第五次复审：R09-B1 合同整改（2026-08-31 00:10 CST）

- 复审对象：root `ecbe34d`（整改 `4d48c95`，均 = origin/V2），submodule/Gitlink `ee1b78d` 未变；diff 证实仅文档（SESSION/TODO/runbook/Inbox/GPT review），无 runtime/config 改动，工作区 clean。
- 结论：**APPROVE_TO_IMPLEMENT_B1**（B1-S 上限不变；无遗留项）

## GPT HIGH：outer-grad / training-only —— 已关闭

- §1 明确 training runtime 专用，eval/inference/closed-loop 显式不授权、须独立 inference-runtime Gate（runbook:13-14）。
- §3.3 改为"state 与 grad-mode 生命周期"：`torch.is_grad_enabled()` 为 false（含 `no_grad`/`inference_mode`）时**在任何 state mutation 前 fail-fast**；CPU hard gate 覆盖 normal-grad PASS、no-grad/inference-mode fail-fast 且 state/token 不变、outer graph 完全 detached（runbook:33）。
- §3.6 与 B1-G 明确 Normal/Zero/Shuffle 三模式仅限训练 runtime，不得作为 eval/inference 证据（runbook:36, 49）。

## GPT MEDIUM-1：selector exact —— 已关闭

- §3.1 冻结：`OmniMoTModelConfig.local_history_backend: Literal["recurrent","ttt_fast_weight"]="recurrent"`，非法值构造前 fail-fast；env `PSM_R09_B1_TTT_ENABLED=0|1`（默认 0）；须 `local_history_enabled=true`；与 `PSM_R09_A1_ENABLED=1` 或非空 `PSM_R09_A1_PROBE_OUTPUT` 在 recipe 解析期互斥 fail-fast（runbook:30）。默认 recurrent 与 R08/A1 路径逐项不变的承诺保留。

## GPT MEDIUM-2：static artifact —— 已关闭

- §5 新增 `artifacts/g0/r09/b1/static_contract.json` + `tools/g0/verify_r09_b1_static_contract.py`（B1-S 内新建），schema v1 含 selector/backend/optimizer/command 五块；hard-gate 清单覆盖 source clean/Gitlink、default recurrent、opt-in、A1 互斥、B0 dimensions、fresh state、zero-param/empty state_dict、三 exact key、grad-mode contract、detached graph、command/tool SHA；并明确"定向 pytest 文本不能替代该 JSON"（runbook:64-80）。

## 我上一轮 LOW-1（三条 vs 4-key 歧义）—— 已关闭

- §3.4 改为精确替换 `keys_to_select` 为 `encoder`/`local_memory2llm`/`local_memory_modality_embed` 三项，显式"不保留 parameter-free TTT backend 的第四项"（runbook:34）；§5 optimizer schema 带 `exact_keys`+`matched_parameter_names` 机器可读兜底。比"留第四 key 匹配空集"更干净，歧义消除。

## 意见

三项 GPT 整改与我的 LOW-1 全部落实且无新引入问题。**APPROVE_TO_IMPLEMENT_B1**：授权上限仍为 B1-S（selector、Local runtime 最小类型/构造适配、grad-mode fail-fast guard、TTT probe/verifier、recipe 解析测试，CPU/静态）；eval/inference/closed-loop、GPU/B1-G 均不在授权内。

---

# 第六次复审：R09-B1 B1-S closure（2026-08-31 08:30 CST）

- 复审对象：root `f66f005`（verifier 强化 `519ba24`、artifact `fb4b423`，均 = origin/V2），submodule/Gitlink `0381335`（= origin/v2，实现提交 `0381335`）。双仓工作区 clean。
- 结论：**APPROVE_TO_CLOSE_B1_S**

## 实现 diff 核对（submodule `ee1b78d..0381335`，75+/4-）

- **selector**：`model_config.py:306` 新增 `local_history_backend: Literal["recurrent","ttt_fast_weight"]="recurrent"`；`omni_mot_model.py:127-128` disabled 时非 recurrent fail-fast，`:306-320` 三分支构造（recurrent 原样/ttt/非法值 fail-fast），默认路径逐项不变 ✓。
- **recipe**：`action_policy_libero_edge_all.py:46-50` `_strict_bool_env` 只接受 0|1；`:66-74` TTT 须 local_history_enabled、与 A1 flag/probe 解析期互斥；`:213-218` opt-in 时 `keys_to_select` 精确替换为三 key（落实上一轮 LOW-1 的关闭方式）✓。
- **grad-mode guard**：`local_evidence.py:232-233` TTT `replay` 首句 `torch.is_grad_enabled()` false 即 raise，先于任何 mutation；测试 `local_evidence_test.py:173-181` 对 no_grad/inference_mode 断言 raise 且 state 逐成员不变 ✓。
- **测试**：`local_history_runtime_test.py:224-241` monkeypatch+reload 验证 opt-in config/三 key/A1 互斥 ✓。

## verifier 与 artifact

- `verify_r09_b1_static_contract.py`：真实 `LocalHistoryRuntime.forward` 反传（非直接 backend.replay）；exact-union 硬门（selected==三 key 匹配并集）、backend 空匹配、backend-specific optimizer state 空、encoder 经 TTT 无回传（present=false）、projection/modality grad present/finite/nonzero、outer graph detached（token 不 requires_grad、evidence requires_grad）✓。
- canonical artifact `artifacts/g0/r09/b1/static_contract.json`：status=PASS，**23/23** checks true（申请消息写 22/22，实际 23，纯计数笔误）；recipe 快照显示默认路径 optimizer keys 不变、TTT 路径精确三 key；hash 我独立复算自洽（canonical_command_hash、tool_sha256 均 verified）。
- HEAD artifact 与 `fb4b423` 版本 md5 逐字节一致，`fb4b423..HEAD` 无 artifact diff。

## 独立复现

- `pytest local_evidence_test.py local_history_runtime_test.py -k "ttt or b1"`：**4 passed**。
- verifier `--require-clean` 复跑至 /tmp：status=PASS，23/23；与 tracked artifact 除 command 块和 `source.root_revision` 外逐字段一致——差异为正确 provenance 语义（生成于 `519ba24`，HEAD 经 docs 提交移至 `f66f005`，`519ba24` 是 HEAD 祖先，clean/gitlink 复跑仍 true）。

## 意见

B1-S 合同（selector exact、grad-mode fail-fast、fresh state、无注册/无优化/无序列化、三 exact key、encoder 无回传、默认路径不变）全部机器可读硬门通过且独立复现一致。**APPROVE_TO_CLOSE_B1_S**。B1-G（单卡有界训练 smoke）与 eval/inference/closed-loop 均需独立审批，不在本次关闭范围内。

---

# 第七次复审：R09-B1-G TTT probe 静态/instrumentation（2026-08-31 08:55 CST）

- 复审对象：root `496b600`（= origin/V2），submodule/Gitlink `abe8272`（= origin/v2，唯一提交即本 probe）。双仓 clean；未启动 GPU/训练/评测。
- 结论：**APPROVE_B1_G_INSTRUMENTATION**（附两条 LOW 备注）

## 实现核对（submodule `0381335..abe8272`，190+）

- **注册约束**：`action_policy_libero_edge_all.py:269-276` 仅当 `PSM_R09_B1_PROBE_OUTPUT` 非空且 `PSM_R09_B1_TTT_ENABLED=1` 才注册 callback，否则 fail-fast；经 B1-S 既有互斥（:66-74）传递覆盖 A1 flag/probe。默认关闭、不改任何既有路径 ✓。
- **state 证据**（`r09_b1_runtime_probe.py:52-100`）：五成员 shape/dtype/bytes、unaligned 4+3 分段 token/state/present exact、fresh-replay 逐项 exact、token/members detach（requires_grad+grad_fn 双查）、reset_mask 选中清零/initialized 复位/progress 归零/未选逐位不变、all-mask 续算 absent+token 零+detached ✓。
- **optimizer/梯度**（:102-126）：三 prefix targets、optimizer 实际参数 id 比对（matches/missing/unexpected）、逐参数 gradient present/finite/max_abs 与三组分组；encoder 无 TTT 回传以"encoder 组 grad 全 not present"落证（测试 :44 断言）✓。
- **CUDA peak**（:118-126）：max_memory_allocated/reserved + device name；`allow_nan=False` 严格 JSON ✓。

## 独立复现

- `pytest r09_b1_runtime_probe_test.py`：1 passed；mot 两文件 `-k "ttt or b1"`：4 passed。
- B1-S verifier 在新子模块 SHA 下复跑仍 PASS 23/23（--require-clean），无回归。

## LOW 备注（不阻塞）

1. `r09_b1_runtime_probe.py:17-21` `_PREFIXES` 中 `local_memory2llm`/`local_memory_modality_embed` 无尾点，理论上可前缀误匹配（如 `local_memory2llm_extra`）；与 recipe 既有语义一致且当前无此模块，记录备查。
2. probe 本身只记录不硬门（`:105` 起首次 step 后幂等）；PASS/FAIL 判定依赖后续 B1-G verifier 消费本 payload——B1-G 审批时必须包含该 verifier 及其硬门清单，本批准不含 GPU 执行。

## 意见

instrumentation 范围与合同一致，证据字段覆盖五成员 state/optimizer/梯度/显存且无 GPU。**APPROVE_B1_G_INSTRUMENTATION**。B1-G smoke 启动仍需独立 `APPROVE_TO_RUN_B1_SMOKE` 与用户确认。

---

# 第八次复审：R09-B1-G GPU smoke 运行审批（2026-08-31）

- 复审对象：root `24a953d`（= origin/V2，纯 Inbox/SESSION/TODO 文档），submodule/Gitlink `abe8272`（未变，probe 已审）。双仓 clean。
- 结论：**APPROVE_TO_RUN_B1_SMOKE**（仅限 Inbox 列出的两条命令；附两条范围备注）

## 资源与命令核验

- GPU0 实测空闲：A100-SXM4-80GB，0 MiB used（我独立 `nvidia-smi` 确认，与 Inbox 申报一致）。
- 启动器环境变量全部存在且语义相符：`DISABLE_AUTO_RESUME`（launch:92-93）、`OUTPUT_ROOT`（:77-79）、`BASE_CHECKPOINT_PATH`（_sft_launcher_common.sh:50-54）、`EXTRA_TAIL_OVERRIDES`（launch:73）。
- 前置资产就位：LIBERO 数据集、shared-VAE cache root、base DCP（6.3G）均存在；`/localdisk-tmp` 100G 空盘，两个 bounded checkpoint（预估各 ~7-13G）容量充足。
- 命令 1 重建 Gate-A：`PSM_R09_B1_TTT_ENABLED=0` → 默认 recurrent 路径（selector 合同 :306-320），2-step、workers=0、`LIBERO_LATENT_CACHE_VERIFY_RATIO=0`（无在线 VAE fallback 路径）；显式禁止用 base checkpoint 静默替代，符合 runbook §3.5。
- 命令 2 B1 smoke：model-only warm-start（`checkpoint.load_training_state=False`）自重建 iter_000000002，`PSM_R09_B1_TTT_ENABLED=1` + probe 写持久 `artifacts/g0/r09/b1/runtime_probe.json`，5-step 有界。
- recipe TOML 仍带 `trainer.cudnn.benchmark=false`（FIX-CACHE-CUDNN-BENCHMARK 已提交），两条命令同一 recipe，数值上下文一致。
- PASS/FAIL 判据（finite loss、probe 五成员/18,953B/三 key/encoder 无回传/CUDA peak、无 VAE fallback、OOM/缺产物即停）覆盖 runbook §4 B1-G 的有界部分。
- Inbox 条目本身含完整命令、双仓 SHA、checkpoint、cache、GPU、输出路径与资源上限，且已提交持久化——满足 D005 sidecar 的内容要求。

## 范围备注（不阻塞本次运行批准）

1. **本批准不等于 B1-G 关闭**。runbook §4 B1-G 的 PASS 含 Normal/Zero/Shuffle 三模式 capture + non-history invariants exact + DCP bitwise verifier；本次请求明确不进入三模式。B1-G 关闭须以三模式 capture 与 verifier 的独立申请为准。
2. **`/localdisk-tmp` 易失**。B1 final DCP 与 Gate-A 重建 checkpoint 在临时盘；三模式 capture 和 DCP 逐位 verifier 必须在任何清理/重启前完成，否则需重建。probe JSON 已落持久盘 ✓。

## 意见

**APPROVE_TO_RUN_B1_SMOKE**：授权按 Inbox 两条命令串行执行（Gate-A 2-step 重建 → B1 TTT 5-step），GPU0 单卡、上限 80G、无外网。任一 FAIL/BLOCKED 条件触发即停止并保留现场日志。eval/inference/closed-loop、多卡、长训不在授权内。

---

# 第九次复审：R09-B1-G 最终运行审批（2026-08-31 09:18 CST）

- 复审对象：root `63d279d`（本地 HEAD；origin/V2 已推进到 `e6e693c`，多出的是 ChatGPT 评审文档，与本复审对象不冲突），submodule/Gitlink `abe8272` 未变。双仓 clean。
- 结论：**APPROVE_TO_RUN_B1_SMOKE**（维持第八次批准范围，verifier 补齐后无新增障碍）

## verify_r09_b1_smoke.py 硬门核对（107 行，py_compile PASS）

- `training_losses_finite`（:47-54,76）：loss/action-loss 正则与 A1 verifier（verify_r09_a1_smoke.py:69-71）逐字符一致，格式来源已验证；要求 "Done with training." + ≥5 step + 全 finite ✓。
- `checkpoint_schema_only_removes_gru`（:69,77）：added/removed 由**实际 DCP metadata 集合差派生**，再断言 added 为空、removed 恰为 GRU 四 tensor。说明：runbook §3.5 禁止的是"假设 A1 checkpoint 相容并把数字当无条件 PASS"；此处派生是真实的，expected removed set 是 recurrent→TTT 接线的结构性预测（命令 1 保证 warm-start 为 recurrent Gate-A），失配即 FAIL——语义成立，不算违反 §3.5。
- `frozen_common_tensors_bitwise_unchanged`（:70,78）：非选中公共 tensor 全量逐位 `torch.equal`，选中（可训练）tensor 正确排除 ✓。
- optimizer 三 key exact membership、encoder absent-or-zero、双 adapter present/finite/nonzero、五成员 schema + 18,953B、fresh/segment/reset/detach 全项、CUDA peak、双仓 clean（:79-90）✓；strict JSON（`allow_nan=False`）✓。

## LOW 备注（不阻塞）

1. command 块只有 argv+tool_sha256（:99），缺 B0/B1-S 已有的 canonical_command_hash/cwd/python/output 字段；两仓 clean 有记录但无 gitlink==submodule 断言。建议后续 verifier 迭代补齐统一口径，本次 smoke 不因此阻断。
2. 第八次复审的两条范围备注仍然有效：本批准不含 Normal/Zero/Shuffle 三模式 capture（B1-G 关闭需独立申请）；`/localdisk-tmp` 易失，verifier 必须在清理/重启前跑完。

## 意见

verifier 硬门完整覆盖 Inbox 判据，且 FAIL 语义明确。**APPROVE_TO_RUN_B1_SMOKE**：按 Inbox 两条命令串行执行（Gate-A 2-step 重建 → B1 TTT 5-step），结束后立即运行 `verify_r09_b1_smoke.py` 并将 JSON 落 `artifacts/g0/r09/b1/`。任一 FAIL/BLOCKED 即停止并保留现场。

---

# 第十次复审：R09-B1-G GPT 整改（2026-08-31 09:35 CST）

- 复审对象：root `78b066f`（= origin/V2），submodule/Gitlink `eaa0f97`（= origin/v2）。双仓 clean，未启动 GPU。
- 结论：**APPROVE_TO_RUN_B1_SMOKE**（第三次批准，范围同前两条命令；附一条 LOW）

## GPT 五项 blocker 逐项核对

1. **B0 逐成员 state schema**：✓。probe `_state_members` 改用 B0 canonical 五名（W/pending_evidence/last_evidence/initialized/segment_progress）+ shape_per_sample/dtype/bytes_per_sample（r09_b1_runtime_probe.py:44-54）；verifier `STATE_SCHEMA` 与 B0 `EXPECTED_STATE_MEMBERS` 逐字一致，`ttt_state_schema` 为 exact dict 相等 + 18,953B（verify_r09_b1_smoke.py:26-32,95）。probe 测试在新 schema 下复跑 1 passed。
2. **D005 writer + verifier binding**：✓。`write_r09_b1_d005.py` 运行前落盘 source 三 SHA/command_sha256/cache/checkpoint/GPU/output/network=false/steps；verifier `--training-sidecar` 硬门绑定 phase=b1_smoke、single-rank、TTT=1、history=normal、cache ratio=0、checkpoint==initial、probe 路径一致，并把 sidecar sha256 记入结果（verify_r09_b1_smoke.py:95,109）。
3. **hermetic/unset 环境**：✓（带 LOW 备注）。sidecar 固定全量 environment 并记录 unset 清单（A1/R07/R08 probe、ONLINE_VAE_PROBE_OUTPUT、LIBERO_MAX_EPISODES，write_r09_b1_d005.py:40-44）。
4. **cache-only hard gate**：✓。sidecar `LIBERO_LATENT_CACHE_VERIFY_RATIO="0"` 且 verifier 硬门检查；cache root 非空断言。
5. **Gate-A-compatible rebuild 标识**：✓。Inbox 明确改称 "Gate-A-compatible rebuilt warm-start"，不再冒充原 approved Gate-A artifact。

## 独立复现

- probe test 1 passed；两工具 py_compile PASS；writer `--help` PASS；B1-S static verifier 在 `eaa0f97` 下复跑 23/23 PASS 无回归。

## LOW 备注（不阻塞）

- `unset_environment` 是 sidecar 声明，verifier 无法机器证明运行时这些变量真的不存在。建议实际启动命令用 `env -u PSM_R09_A1_PROBE_OUTPUT -u ONLINE_VAE_PROBE_OUTPUT ...` 显式清除，使命令与 sidecar 声明逐字一致。

## 意见

五项 blocker 全部落实。**APPROVE_TO_RUN_B1_SMOKE**：按 Inbox 两命令串行（Gate-A-compatible 2-step 重建 → B1 TTT 5-step），先写 D005 sidecar 再启动，结束后立即跑 `verify_r09_b1_smoke.py`（含 --training-sidecar）落 `artifacts/g0/r09/b1/`。第八/九次复审的范围备注继续有效：三模式 capture 不在内、`/localdisk-tmp` 易失需及时验证。

---

# 第十一次复审：R09-B1-G 启动证据整改（2026-08-31 09:55 CST）

- 复审对象：root `79e4758`（实现 `9dc7dd3`，均 = origin/V2），submodule/Gitlink `eaa0f97` 未变（tracked clean）。未运行 GPU。
- 结论：**APPROVE_TO_RUN_B1_SMOKE**（第四次批准；附两条 LOW）

## 三文件核对

**launch_r09_b1_smoke.sh（新增 70 行）**：两阶段串行；`env -u` 显式清除 8 个变量（A1/R07/R08 probe、ONLINE_VAE_PROBE_OUTPUT、LIBERO_MAX_EPISODES）——**我第十次复审的 LOW 就此关闭**；环境全量显式（NPROC=1/history=1/dummy=0/history_mode=normal/A1=0/cache root/verify_ratio=0/workers=0/prefetch=4/TTT 按 phase/probe/BASE_CHECKPOINT_PATH/OUTPUT_ROOT/DISABLE_AUTO_RESUME/tail overrides 含 load_training_state=False）；每 phase 先写 D005 sidecar（含 `%q` 逐字 resolved command + command_sha256）再执行；Gate-A checkpoint 存在性硬门后再进 B1；结尾自动调 verifier 并以 git 实值绑定 expected 三 SHA。DRY_RUN=1 只打印不执行。Gate-A phase `PSM_R09_B1_PROBE_OUTPUT=""` 经 recipe 空值 falsy 不注册 callback ✓。

**write_r09_b1_d005.py**：新增 `--output-checkpoint` 落入 `output.checkpoint`，供 verifier 绑定 ✓。

**verify_r09_b1_smoke.py 新硬门**：
- `_complete_dcp`（:64-65）：Gate-A 重建 checkpoint 的 model/optim/scheduler/trainer 四件 `.metadata` 齐全；
- `_sidecar_matches_command`（:67-75）：重算 command_sha256 + 必要子串（env -u、NPROC、verify_ratio=0、workers=0、DISABLE_AUTO_RESUME）——sidecar 声明与实际命令绑定；
- `_cache_only_no_fallback`（:77-81）：双 phase 日志无 fallback 关键词 + env ratio=0；
- `gate_a_rebuilt_warm_start_complete`（:137）：phase/2-step/双 loss finite/checkpoint+log 路径绑定/完整 DCP；
- `two_phase_d005_provenance_chain`（:138）：双 sidecar 三 SHA 一致且 gitlink==submodule、phase/steps/input/output 全路径绑定、两 phase 同 libero/cache root；
- `b1_model_only_loads_exact_rebuilt_checkpoint`（:139）：B1 日志含 initial checkpoint 路径。

## 静态验证

bash -n PASS；py_compile 双 PASS；DRY_RUN 实跑生成 gate_a sidecar 并逐项验证（phase/steps=2/TTT=0/output checkpoint/8 unsets/sha256 自洽），事后已删除 dry-run sidecar，artifact 目录恢复原状。

## LOW 备注（不阻塞）

1. DRY_RUN 在 Gate-A phase 后即 exit（launch_r09_b1_smoke.sh:66），b1 phase 命令/sidecar 无法 dry-run 预览。
2. `b1_model_only_loads_exact_rebuilt_checkpoint` 是日志子串检查，依赖启动器回显 BASE_CHECKPOINT_PATH；有 sidecar/DCP 硬门兜底，风险低。

## 意见

启动合同已闭环：hermetic 命令 → 运行前 sidecar → 双 phase → 自动 verifier 全硬门。**APPROVE_TO_RUN_B1_SMOKE**：以 `bash tools/g0/launch_r09_b1_smoke.sh` 一次执行（GPU0/80G/无外网）；结束后 `smoke_contract.json` 落 `artifacts/g0/r09/b1/` 并送三方 closure 复审。此前范围备注不变：三模式 capture 另行申请，`/localdisk-tmp` 易失。

---

# 第十二次复审：R09-B1-G 四项整改（2026-08-31 10:35 CST）

- 复审对象：root `e327bb7`（实施 `f52898d`；origin/V2 已含其上的 GPT 批准 `2417c88`），submodule/Gitlink `eaa0f97` 未变。双仓 tracked clean，未启动 GPU。
- 结论：**APPROVE_TO_RUN_B1_SMOKE**

## GPT 四项逐项核对

1. **HIGH-1 GPU 身份/容量实测**：✓。launcher 启动即 `nvidia-smi` 实测 name/total，非 A100 或 <80000MiB 立即 fail-fast（launch_r09_b1_smoke.sh:21-23）；命令含 `CUDA_VISIBLE_DEVICES=0`（:39）；sidecar 记实测 `gpu.name/total_memory_mib`；verifier `approved_single_a100_80gb_bound_and_recorded` 硬门双 sidecar 实测字段 + probe 运行时 `device` 含 A100（verify_r09_b1_smoke.py:162）。DRY_RUN 实测落盘：A100-SXM4-80GB/81920MiB。
2. **HIGH-2 structured argv exact**：✓。sidecar 新增 `command_argv`（真实 argv JSON 数组，writer 校验 string 数组，write_r09_b1_d005.py:35-37）；`_sidecar_matches_command` 改为结构化验证：argv[0]=="env"、`-u` 次数==unset 清单长度且每个 unset 变量恰出现一次、每个 environment 键值在赋值中恰出现一次（重复/冲突即 FAIL）、DISABLE_AUTO_RESUME=1（verify_r09_b1_smoke.py:82-96）。DRY_RUN 产物我手工复算全部通过。
3. **HIGH-3 model-only 成功标记**：✓。正则匹配 `Loaded checkpoint from <path> in iteration 0`——该日志格式确认存在于主 DCP checkpointer（cosmos-framework/cosmos_framework/checkpoint/dcp.py:944）；并硬门 sidecar command 含 `checkpoint.load_training_state=False`（verify_r09_b1_smoke.py:166）。
4. **MEDIUM DCP manifest**：✓。`_dcp_manifest` 枚举全部文件 size+sha256 落证据，非空为硬门（:68-78,163,176）；截断/缺失另由 `_load` 的实际 dcp.load 与 `.metadata` 四件检查兜底。

## 静态验证

bash -n PASS；py_compile 双 PASS；DRY_RUN 端到端生成 gate_a sidecar，GPU 实测值、argv 结构、unset/env exact-once、sha256 全部复算通过；dry-run 产物已清理。

## 意见

四项整改全部落实且可机器验证。**APPROVE_TO_RUN_B1_SMOKE**：以 `bash tools/g0/launch_r09_b1_smoke.sh` 执行（GPU0/80G/无外网）；结束自动产出 `smoke_contract.json`，送三方 closure 复审。三模式 capture 与 `/localdisk-tmp` 易失性备注继续有效。

---

# 第十三次复审：R09-B1-G PATH 重试（2026-08-31 11:07 CST）

- 复审对象：root `da91c0e`（实施 `040cb78`，均 = origin/V2），submodule/Gitlink `eaa0f97` 未变。GPU0 实测 0 MiB（上次失败未占卡）。
- 结论：**APPROVE_TO_RETRY_B1_SMOKE**

## 整改核对（5+/3-，两文件）

- 根因对齐：上次 `env -u ...` 命令里无 PATH 注入，`torchrun` 依赖调用 shell 的 PATH，在最小环境下失败。本次将 `PATH=$VENV_BIN:$PATH` 写入**实际 argv 第一个赋值**（launch_r09_b1_smoke.sh:40），venv bin 在最前，`torchrun` 必解析到 `.venv/bin/torchrun`（我已确认该文件存在且可执行）。
- D005 同步：writer 新增 `--path` 必填，`environment` 记录同一 PATH 值（write_r09_b1_d005.py:34,42）；因 PATH 进入 environment 字典，既有 `_sidecar_matches_command` 的 exact-once 硬门自动覆盖它，无 verifier 改动需求。

## 静态验证

bash -n PASS；py_compile 双 PASS；DRY_RUN 端到端：argv 中 `PATH=` 以 venv bin 开头、sidecar environment.PATH 与 argv 逐字一致、exact-once 成立、command_sha256 自洽；dry-run sidecar 已清理。

## 意见

最小且正确，无非 PATH 相关改动。**APPROVE_TO_RETRY_B1_SMOKE**：`bash tools/g0/launch_r09_b1_smoke.sh` 重试；若再次失败，保留日志与 sidecar 现场送审，不得自行扩大改动范围。

---

# 第十四次复审：R09-B1-G smoke profile 方案（2026-08-31 11:20 CST）

- 复审对象：root `9cfcf95`（方案申请；基点 `e0ef815`，均 = origin/V2），submodule/Gitlink `eaa0f97` 未变。仅方案审核，未编码、未启动 GPU。
- 结论：**APPROVE_SMOKE_PROFILE_REWORK**（附两条实施要求）

## 方案核对

- **事实链可信**：PATH retry 实跑完成四 suite cache-only prewarm + model-only warm-start 但无 optimizer step；现场保留（日志 + gate_a D005）；同 `config.pkl` CPU 测量 dataloader init 8.039s、首个 128-sample batch 4.151s——排除 MP4/VAE/cache/`next(dataloader)` 卡死。正式配置 128×16=2048 samples/step 且 probe/stdout 仅在 optimizer step 后输出，24min 无日志确实不能区分"慢"与"死锁"。诊断表述克制、无过度断言 ✓。
- **profile 充分性**:`max_samples_per_batch=1`+`grad_accum_iter=1` 使每个 optimizer step=1 sample，秒级出日志，能快速判别慢/挂；B1-G 要证明的合同（TTT 接线、三 key optimizer、梯度事实、DCP schema、fresh/detach/reset、finite loss、cache-only）均不依赖 batch=128 的 packing 规模——probe 的 state contract 用合成 evidence，梯度 present/finite/nonzero 在 batch=1 下同样成立 ✓。
- **边界声明正确**：明确不称正式规模/Gate-A、不替代正式训练结论；Gate-A 重建改称 Gate-A-compatible 的既有口径延续 ✓；范围仅 root launcher/D005/verifier/文档，子模块不动 ✓。

## 实施要求（纳入下次整改复审，不阻塞方案批准）

1. profile 两个 override 必须进 D005 structured argv（`EXTRA_TAIL_OVERRIDES` 内），verifier 从 `command_argv` 解析并 exact-once 硬门 `dataloader_train.max_samples_per_batch=1` 与 `trainer.grad_accum_iter=1`，沿用 HIGH-2 既有机制。
2. sidecar/artifact 增加显式 profile 标识字段（如 `"profile": "smoke_batch1"`），使产物自描述、无法被误读为正式规模证据。

## 意见

**APPROVE_SMOKE_PROFILE_REWORK**。可编码；GPU 重跑仍需编码完成后按既有三方针对方案落地版做最终确认（若实现与本方案逐字一致，我预期直接维持批准）。

---

# 第十五次复审：R09-B1 bounded smoke 最终运行审批（2026-08-31 12:00 CST）

- 复审对象：root `40296e2`（实施 `34695a3`，均 = origin/V2），submodule/Gitlink `eaa0f97` 未变。未运行 GPU。
- 结论：**APPROVE_TO_RUN_SMOKE_PROFILE**

## 第十四次复审两条实施要求的落实

1. **argv exact-once 硬门（双侧）**：✓。launcher 把两 override 注入 `EXTRA_TAIL_OVERRIDES`（launch_r09_b1_smoke.sh:38）；**writer 侧** `_profile_overrides_exact` 在 sidecar 落盘前 fail-fast（write_r09_b1_d005.py:18-26,51-53）——命令 malformed 根本不会启动，我已用缺 override 的假 argv 实测触发 ValueError；**verifier 侧** `_sidecar_matches_command` 独立复查恰好一个 EXTRA_TAIL_OVERRIDES 且两 profile override 各恰一次（verify_r09_b1_smoke.py:108-120）。
2. **profile 自描述 + noncanonical**：✓。sidecar `smoke_profile={name: smoke_batch1, bounded_noncanonical: true, ...}`（writer :87-92）；verifier `SMOKE_PROFILE` 冻结字典 exact 相等 + 双 sidecar steps 2/5 硬门（:33-39,122-131,196）；结果 JSON 带 `warnings` 明确"非 canonical Gate-A/正式规模/吞吐/收敛/SR 证据"并回显 profile（:208-211）。

## 其他核对

- D005 schema 升 v2，`launch_diagnostics`（started_unix float + dmesg returncode/tail/stderr）为后续挂死/OOM 提供内核级事后证据；verifier 类型硬门 ✓。
- 静态验证：bash -n / py_compile PASS；DRY_RUN 端到端 sidecar v2 全字段复算通过（profile、overrides exact-once、sha256 自洽）；产物已清理。
- 范围：仅 root 三工具 + 文档/状态，子模块未动；GPU 未运行。

## 意见

方案与实施逐字一致。**APPROVE_TO_RUN_SMOKE_PROFILE**：唯一命令 `bash tools/g0/launch_r09_b1_smoke.sh`（GPU0/80G/无外网）；任一 FAIL 即停止并保留日志/sidecar/dmesg 现场；结束后 `smoke_contract.json` 送三方 closure 复审。该 PASS 不可引用为正式规模或 canonical Gate-A 证据。

---

# 第十六次复审：R09-B1 batch2 profile 修订方案（2026-08-31 12:20 CST）

- 复审对象：root `d0ea0d3`（申请；基点 `fab9ab4`，均 = origin/V2），submodule/Gitlink `eaa0f97` 未变。仅方案审核，未编码、未授权 GPU。
- 结论：**APPROVE_B1_BATCH2_PROFILE_REWORK**（附一条实施要求）

## 失败事实与根因核对

- 实跑事实：Gate-A batch1/accum1 2/2 finite 且完整 `iter_000000002` 已保存——** smoke 合同的前半已实证**；B1 model-only warm-start 后首次 backward `element 0 of tensors does not require grad`，无 B1 产物，GPU 已释放、现场保留。事实陈述与证据路径齐全 ✓。
- 根因与 B0 冻结语义自洽：确定性首窗口 `start=0` 的 causal history 全 absent；B0 合同 `all_mask_absent` 要求 token 全零且完全 detached（b0_ttt_contract.json checks），而 B1 optimizer 只含 Local 三 key、其余参数冻结——单样本全 absent 时 loss 确实无任何 requires-grad 路径。Gate-A 能过是因为 recurrent 路径在同一输入下经验上仍有 grad 通路（已实跑 2/2 证明），两 backend 对 absent 样本的梯度行为差异正是 TTT 的已冻结语义，不是新 bug ✓。
- 修复逻辑成立：B1 改 `max_samples_per_batch=2` 后，确定性连续第二窗口 `start=1` 有 1 条有效 history（horizon 16），且后续每 step 的窗口对 `(2i, 2i+1)` 恒含 present 样本——5 步全程有 Local grad 通路，probe 的 adapter present/finite/nonzero 与 encoder absent 断言才真正被 exercised（batch1-absent 下这些证据反而拿不到）✓。

## 范围核对

- 仅 B1 phase 改 2，Gate-A 保持已实证的 batch1 配置——避免重建已通过的 Gate-A 产物 ✓；accum=1、2/5 steps、模型/cache/env/TTT/provenance 不变 ✓；root-only，不动子模块/正式 recipe ✓；明确勿授权 GPU ✓。

## 实施要求（下次整改复审核对）

1. D005 `smoke_profile` 与 verifier `SMOKE_PROFILE` 改为 phase-specific（Gate-A=1、B1=2），`bounded_noncanonical` 标识保留；profile 名称建议同步更新（如 `smoke_b1batch2`）防止旧产物被误读。
2. verifier 继续在 writer 落盘前 + 验收时双侧 exact-once 硬门两个 phase 的 override 值。

## 意见

**APPROVE_B1_BATCH2_PROFILE_REWORK**。可编码；GPU 重跑仍须实现落地后的三方最终确认。
