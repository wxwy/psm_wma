# PSM-WMA V3 — DS_PRO Config-truth Independent CPU Evidence Intake（新证据 Gate）

日期：2026-10-21
Gate：V3 Config-truth mainline exact pair — **DS_PRO independent target-host CPU Evidence intake**；与原生产代码增量审核分开。
Formal Implementation Root：`306d235046fe5d578503beb17a56f5c0eb0f5634`
Child/Gitlink：`35b0ea1ccee9ee26653ed6589c484f0997d1c586`
HIGH-07 Queue Blob：`4916918aca412a0abc6cb00e28f6053a351e07d8`
截至本次 intake，最新已核对的 V3 docs HEAD：`d41e2723535e860aa21443ea288ec8c99850d545`（仅文档 SHA）。
当前同 Pair 的**生产源代码/static source Gate** 正式 `APPROVE` 保持有效：`docs/collab/chatgpt/reviews/2026-10-21_V3_Config_truth_mainline_306d2350_35b0ea1c_incremental_review.md`。**Formal pair 未变，禁止重做代码增量审核**。本报告仅审新增 DS_PRO 执行证据和可证明的测试边界。

## 1. Evidence Intake Verdict

**`REQUEST_CHANGES` — EVIDENCE-ONLY（归档可复核性待补），不是新的 production bug。**

- 根据 DS_PRO 2026-10-21 19:03 CST 提交给 GPT 的现场报告：独立检查 **22 PASS**，Config-truth 3 文件 **107 passed / 1 skipped / 32 subtests passed**，HIGH-07 Queue 文件 **18 passed / 50 subtests passed**，Ruff check/format RC0；Root/Child/Gitlink/Queue Blob 与已正式批准 Pair 一致，Root/Child worktree clean。
- 本次文本报告包含针对旧 Dataset chunk32→16、YAML/PKL 序列化、Child parser CLI 优先级、冲突 fail-closed、manifest及 strict `/info` 的具体行为 witness。**测试覆盖按报告为 PASS，暂无需要 Codex 修复的生产代码 Finding。**
- 然而 DS_PRO 原始证据存在于目标机器 `/mnt/data1/data_v2_0617/dspro_verify_iter4000_306d2350_20261021/evidence/config_truth_cpu/`。ChatGPT 的远程 Desktop Commander 连接当前设备 Offline；GPT **未读到独立22-case脚本源文件、现场完整执行日志、实际命令/退出码/报告的所有子测试细节**。GitHub V3 未提供此次新 DS CPU Evidence 的可访问归档；对这些测试只可标记 `DS-attested`，不可冒称 GPT 原始 evidence independently inspected。
- 符合项目 Evidence Gate 的 `contract→behavior→raw evidence` 原则：新报告已构成详细线索与 DS attestation，但正式独立执行 **Evidence closure 仍需可访问原始证据**。不需要重跑，先归档已经产生的文件即可。
- **没有授权 GPU、训练、真实 Action Server、真实 Simulator、Checkpoint 修改或任何真实评测。** Owner 已明确取消本阶段 GPU 状态核验，不运行 `nvidia-smi`；`optim/` 也不是 model-only inference 阻断条件。

## 2. 正面验证与唯一 skip 定位

ChatGPT 独立从 GitHub 固定 Child `35b0ea1c...` 检查相关测试源码，确认 Config-truth、Exact-Window 新 job 正向/负向测试文件存在，HIGH-07 Queue Blob 与已审版本一致；本次不重做生产代码审查。

**唯一 skip 的性质已由实际源代码定位**：
`cosmos_framework/examples/psm_wma_robocasa_corrected_phase5_test.py:324-340`（子仓路径从 `examples/` 起）：
`test_optional_real_strict_snapshot10_preflight` 具有 `@pytest.mark.skipif`，仅在配置环境变量
`PSM_PHASE5_CACHE_ROOT`、`PSM_PHASE5_SOURCE_ROOT`、`EDGE_POLICY_CHECKPOINT`、`BASE_CHECKPOINT_PATH`、`WAN_VAE_PATH` 全部提供时运行；缺少相关真实资产路径时以“未提供真实 exact-window cache/source/Edge/base/VAE 路径”正常跳过。此项**不属于被授权 CPU 合成 Gate 的必需检查**，不是新增 HIGH/MEDIUM 问题，不要求为消除一条 skipped 而加载生产资产/GPU。

按用户提供的 DS_PRO 行为报告（**非 GPT 读取原始运行结果**）：
- **A**：旧 canonical dataset chunk=32 `overlay_config→synchronize_legacy_chunk_length` 后两个 alias均16；producer provenance 与 H16/17frame/state15/raw15/fps20/T分离匹配；
- **B**：保存 YAML/PKL 一致，新的 Child 解析16；旧 G1 的保存 Config32仍需 Queue `--action-chunk-size 16`；无 CLI 时旧值32、缺省 fallback32；
- **C**：错误候选8/24、alias不同、canonical path外字段、contract错误、fps错误与 snapshot drift均拒绝；
- **D**：Root manifest `server_action_chunk_size/H_pred/R=16`，Queue实际 CLI16；`/info`=32及缺值 fail-closed；
- 目标现场未运行 GPU/真实模型/仿真，未写冻结 G1 资产，符合执行边界。

## 3. 唯一 Evidence-only 缺口 — EVIDENCE-01

- **Severity**：MEDIUM（Evidence provenance-only；**不是 production 代码缺陷**）。
- **Artifact locus（无需生产代码 file:line）**：目标机 `/mnt/data1/data_v2_0617/dspro_verify_iter4000_306d2350_20261021/evidence/config_truth_cpu/`，尤其报告所述 `dspro_independent_config_truth_check.py` 和各测试原始输出；当前 GitHub V3 中尚无此次新 DS 文件。
- **根因**：原始独立执行程序、日志、精确命令/环境/RC 与测试/子测试计数，尚未以 GPT 可访问的 Evidence 形式发布；当前只是 DS_PRO 用户转述的报告。
- **违反/未达成的 frozen Evidence contract**：formal independent CPU Evidence closure 要求同 exact Pair、可检查 `contract→behavior→raw logs` 的自证材料，不能把单纯聊天测试数字当成原始机证据。
- **验收修复条件**（仅旧文件归档，**无需新运行**）：
  1. 将原 `dspro_independent_config_truth_check.py`、22项实际命令/输出和退出码、Config-truth `107/1skip/32subtests` 的原始日志或 JUnit、Queue `18/50subtests` 原始日志或 JUnit、Ruff 两个日志/RC，以及版本和 clean/Root/Child/Gitlink/Queue Blob provenance 整理为一个可由 GPT 读取的提交/文件附件；
  2. 如可能添加小型 `gate.json` 显示文件 SHA256、执行命令/CWD/Python/Ruff、env主要非敏感变量、实际 positive/negative witnesses；不可伪称事后重新执行，重现信息要从已生成记录中取；
  3. 明确一项 skipped 的 nodeID：`test_optional_real_strict_snapshot10_preflight`（无需因本 CPU Gate 额外提供所有真实资产）；隐去密码/token/私密路径中的凭据，不修改测试原始结果；
  4. 核对归档的代码哈希与 `306d2350 /35b0ea1c /4916918a` 一致。之后 GPT **只做 Evidence closure**，不重新代码审查、不要求 CPU 整套重跑。

## 4. 后续 Gate 边界

- 生产代码技术 verdict `APPROVE` 不受本次 Evidence-only pending 影响；新提交或日志归档文档只改变 docs HEAD，不改变 formal pair。
- DS 若补齐可访问 raw evidence，本 Gate 可按该 same formal pair 完成 Evidence closure，无需 Codex生产代码修改；**不批准**将已保存旧 G1 `config.yaml` 的32原位改写为16，旧 G1 推理仍必须从已审 Queue显式传CLI16。
- Owner 自行决定何时停止训练和释放 GPU。后续真实模型加载 +`/info` canary 与 4Task×5Episode 分属独立执行许可；不能把合成 CPU 结果或本报告当真实 SR。

**本 `REQUEST_CHANGES` 是为了可访问原始 DS evidence 的最小补齐，非新模型/代码 blocker，不要求重新改代码或重复测试。**

## 2026-10-21 Evidence handoff round 2 — textual logs received; archive still inaccessible

The Owner forwarded a second DS_PRO handoff specifying the **existing** source evidence bundle path:
`/mnt/data1/data_v2_0617/dspro_verify_iter4000_306d2350_20261021/evidence/DS_PRO_V3_config_truth_306d2350_35b0ea1c_evidence.tar.gz`, reported 10.5 KB and sha256 `aeb7389e6bb5ec136db731e6ca710db65d175d959152823c2550b46f87793aff`; source evidence directory `.../evidence/config_truth_cpu/`; DS local-only commit `2db54163` reportedly not pushed.

**What GPT directly could check this round:**
- Text copied into this conversation has exactly **22** separate `[PASS]` entries (A4+B5+C7+D6). The copied pytest summaries say Config-truth `107 passed, 1 skipped, 32 subtests passed in 42.11s`; HIGH-07 `18 passed, 50 subtests passed in 34.85s`. Reported Ruff check/format OK. The previous source review identified the optional real-assets skip, not a required gate failure.
- GitHub V3 remote is still a docs-only head above the same implementation Root `306d235046fe5d578503beb17a56f5c0eb0f5634` and Child/Gitlink `35b0ea1ccee9ee26653ed6589c484f0997d1c586`. No formal pair change, **no repeated production code review**.
- GitHub API lookup for commit `2db54163` yielded no commit (unpublished). Connected Remote Desktop Commander reported target device **Offline**; container `/mnt/data` did not have the named `.tar.gz`; current Project/Library file search found no named archive or standalone independent script.

**Still not verifiable:** `.tar.gz` bytes/claimed SHA256, the true independent `dspro_independent_config_truth_check.py` file, `execution_record.json` with exact commands and RC, the authored manifest, raw logs/JUnit and file hashes. The pasted text is an informative *transcript supplied by DS*, **not** a readable original file archive. Do not replace source evidence with a newly synthesized tar or claim original hash verification.

**Verdict unchanged: `REQUEST_CHANGES` — EVIDENCE-ONLY (EVIDENCE-01, MEDIUM provenance)**. Production CPU/static `APPROVE` remains unchanged; user-reported execution checks are consistent with PASS but do not yet meet auditable raw evidence closure. **Acceptance**: attach the **existing 10.5KB tar.gz directly to this chat** (preferred; no GitHub PAT), or place exact raw files in an accessible GitHub Evidence directory and provide URL. GPT then verify tar digest, inspect script/manifest/commands/RC/witness consistency and close this same-Pair Evidence Gate without new code review or rerun. No new GPU/Action Server/Simulator authorization; Owner chooses when to free GPU.

## 2026-10-21 — Owner evidence waiver and staged execution-readiness disposition

**New Owner decision**: "不用了，信任ds" (2026-10-21); Owner declines requiring the original 10.5 KB DS_PRO tar.gz for this CPU Evidence Gate and explicitly accepts DS_PRO's execution report as credible. Subsequent Owner question: "是不是可以让ds启动仿真测试了". This Owner decision **supersedes** earlier EVIDENCE-ONLY `REQUEST_CHANGES` as a *waiver of the original-archive verification condition*, **not** as proof GPT received/hashed the tar.gz or independently executed DS's CPU tests.

### Final Evidence-only verdict

**`CLOSED — OWNER_ACCEPTED_DS_ATTESTATION` (owner-waived raw-file archival requirement).** The user-supplied execution transcript reports:
- 22 independent checks PASS; Config-truth 107 passed / 1 optional assets skipped / 32 subtests; HIGH-07 18 passed / 50 subtests; Ruff check/format PASS, code Pair SHA clean.
- The 22 check-line texts, summarized pytest outcomes and expected optional skip were reviewed for internal consistency; checked exact GitHub Root/Child/Queue and the skip's source condition. Target independent script/tar original bytes/claimed sha256 **remain unverified** because remote device offline and DS local Git commit not pushed.
- **No new production bug or requirement for Codex/test rerun**. Previous source-static verdict `APPROVE` remains as-is. This formal Evidence exception is a documented Owner acceptance, not a falsified independent archived raw-evidence verification.

### Execution readiness — conditional, not a GPU status assertion

**`CONDITIONAL_GO` for a staged real RoboCasa test, only after Owner personally stops the competing training and identifies GPU IDs as explicitly released for this test.** Owner has not yet reported which GPUs are free. No DS `nvidia-smi`/GPU inventory request now; no DS killing or preempting existing training.
- Formal implementation Root `306d235046fe5d578503beb17a56f5c0eb0f5634`; Child/Gitlink `35b0ea1ccee9ee26653ed6589c484f0997d1c586`; Queue Blob `4916918aca412a0abc6cb00e28f6053a351e07d8`. Use clean exact Pair and **new** evaluation output namespaces (same-Pair manifest/digest only), never older root/child partial result imports.
- Keep G1 iter4000 `config.yaml` bytes and SHA `f87e2e49c6931ce7dc32b467aa3f8026269f5ad255216e1cdd8fafb1d7e7374e` unchanged, `checkpoint/iter_000004000/model` model-only, no `optim/` requirement. The Queue passes `--action-chunk-size 16`, verifies `/info` checkpoint canonical `/model`, config, raw15/state, required Local-TTT, H16, maxdim64, 20fps, steps30/guidance1, same-server PID/port.
- **Stage A: one real E2E smoke episode** on one Owner-released GPU (e.g., exact CloseFridge metadata source with `--expected-tasks 1 --num-test-episodes 1`, separate fresh smoke namespace). The queue itself loads real Action Server, performs `/info`/owner PID identity checks, then runs the actual simulator + Local-TTT /predict. It is more valuable than HTTP /info alone. Accept smoke only on RC0, valid `server_info.json`, result with outcome success **or** behavioral_failure (but not runtime_error), no worker error and actual nonempty decodable MP4. Success rate may be 0/1 without indicating infrastructure failure.
- **Stage B: if smoke passes**, use new independent output namespace for exactly `CloseFridge, TurnOnSinkFaucet, PickPlaceSinkToCounter, NavigateKitchen` × 5 = 20 episodes with queue `--expected-tasks 4 --num-test-episodes 5`, one or two GPUs actually released by Owner. Strict required Local-TTT, raw15/state/left_wrist/base raw/fps20, H_pred16/R16/seed0/sampler0/numsteps30/guidance1, each worker `local_memory_max_sessions=1`, serial episodes, no partial episode resume. Save server_info/logs/results/MP4/full evaluation_manifest/summary and exact return code. Do not label CPU fixture output as real SR.
- On any model load, `/info`, Local memory predict, simulator or runtime-error/hang, stop **only owned evaluation process**, keep artifacts/logs, report Gate BLOCKED to GPT/Owner, do not blanket retry with mutated old Config or switch Local mode to off. Avoid stopping unrelated training.
- The Queue's `subprocess.run()` for a simulator does not set a whole-rollout watchdog timeout; the CLI `--timeout 600` is forwarded to simulator and is **not** a blanket process-kill timer. DS should visibly supervise progress and pause/stop only its own evaluation processes if stalled; avoid allowing a hung GPU job to run unbounded.

This Owner-accepted CPU Evidence closure / staged plan does **not** prove GPU availability or successful model load and **does not** itself launch anything. Real GPU start is dependent upon Owner explicitly releasing assigned devices and instructing DS to start.
