# V3 Gate B1 P0 a3239591 — DS_PRO GPU Smoke 启动前准备报告独立审核

**日期：**2026-10-15  
**审查人：**GPT / independent Gate & evidence reviewer  
**审核性质：**READ-ONLY launch-readiness evidence + operational runbook review, **不是**新的代码技术审核、CPU Gate 重开或 GPU Gate closure。  
**诊断 implementation formal pair（未变）：**Root `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / Child Gitlink `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`。  
**冻结 Source：**Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`。  
**冻结 Target：**Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`。  
**Owner 冻结 r2 policy SHA256：**`bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`。  
**B0 authoritative iter1300 DCP fingerprint：**`2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`。  
**审核输入：**DS_PRO pasted `V3 B1 P0 GPU Smoke — 启动前准备报告（P0_GPU_READY_FOR_OWNER_AUTHORIZATION）· a3239591` (2026-10-15, 191 lines) + Github pinned diagnostic `tools/gates/v3_gateb1_run.py` + V3 old Owner receipt. DS machine /tmp、GPU 和 DCP 均未由 GPT 远程访问。  
**Formal scoped disposition：`REQUEST_CHANGES` — RUNBOOK / EXECUTION-READINESS ONLY。** CPU CFG Local-RNG Gate remains **CLOSED**; no confirmed code blocker; **GPU_NOT_AUTHORIZED / GPU_NOT_STARTED / P0_GPU_UNVERIFIED**.

## 1. Accepted read-only readiness facts

1. DS reports all three frozen Root/Child pairs and Gitlinks clean, exact historical B0 DCP/latest untouched, source/index/cache/model/VAE/base assets present. These are executor reports; paths/stat/VRAM are not independently probed by GPT on the DS host.
2. GitHub diagnostic branch still resolves to exact `a3239591...`; its `tools/gates/v3_gateb1_run.py` provides `--mode prepare` (no Cosmos/PyTorch import, dataset scan or CUDA), `--mode execute` 8-rank CUDA requirement and exact `_owner_receipt` mandatory SHA/policy/frozen pairs/FP check. That guard must reject old Owner `46e9cc0e...` receipt.
3. Frozen Child root as subprocess CWD correctly addresses the prior relative `Nemotron-2B-Dense-VL.json` lookup failure. The report's SOURCE and TARGET commands use each corresponding frozen Child directory; diagnostic runner imports the pinned Child during execution.
4. Both runs are isolated `P0_FIXED`, repeat0, 8×H100, iter1301→1302, source first then separately target; no Gate M, Formal30k, DCP/latest mutation or P1/repeat1 authorized. Isolated `/tmp` namespace planned. Different `--job-name` values across legs do not themselves violate the report artifact directory contract, which keys capture by leg/profile/repeat; avoid unintended namespace reuse nonetheless.

## 2. Current mandatory operational blockers (not production source findings)

**B1-P0-OWNER-AUTH — HARD HOLD (external authorization).** No **new** Owner GPU authorization binds diagnostic root `a3239591...`. Existing V3 receipt explicitly binds `46e9cc0e...` and is invalid for new runner. No document/receipt may be forged, copied with edited SHA, or inferred from the previous approval. Owner may later give a *separate, explicit* P0-only co-resident authorization; it never waives resource/safety conditions.

**B1-P0-VRAM — HARD HOLD (resource).** Per DS two read-only nvidia-smi snapshots: GPU5 at 13466 MiB (snapshot1), GPU4 at 13588 MiB (snapshot2), each below the prior Owner-approved **16384 MiB per GPU** floor. A different GPU is below floor at each snapshot: there is **no passing eight-GPU simultaneous snapshot in the supplied evidence**. Re-check all eight cards immediately before *each* separate authorized torchrun; if any card is below 16384 MiB, STOP, no eviction/renice/kill/pause of other users. GPU compute contention is acceptable only when *independently* reauthorized and memory safety holds. Don't reinterpret historical snapshots as current real-time VRAM.

## 3. Additional runbook finding — EVIDENCE/COMMANDS-ONLY

**B1-P0-LAUNCH-UTF8 — MEDIUM, file:line = DS report §7.1 export and §7.3–§7.5 command blocks (report lines ~106,131-136,145-152,159-166).**  
**Root cause:** text as supplied has U+00A0 non-breaking-space before `--leg` / `--dataset-index-root` / `--owner-authorization-json` and pipe/redirection continuations. Independent parsing of uploaded bytes finds 6 standalone NBSP tokens in PREPARE, 8 in SOURCE, 8 in TARGET commands; `export OWNER_GPU_APPROVAL_JSON=...\u00a0 #...` also has NBSP. In shell these are NOT ordinary ASCII separators and can become stray argv tokens or invalid export syntax. This is a **launch artifact error**, not a diagnostic code bug.  
**Frozen contract violated if directly run:** pre-authorized exact CLI and auditable error-free launch; incorrect argv must fail before GPU or output.
**Acceptance:** DS_PRO creates a new, genuine ASCII executable runbook/script in `/tmp` (not GitHub), with no NBSP or other Unicode whitespace in executable command lines; verifies bytes, `bash -n`, actual parsed flags without invoking `--mode execute`, and no unauthorized process started. Record provenance and keep launcher read-only until authorized. No need to change diagnostic SHA.

**B1-P0-SCOPE-PREFLIGHT — MEDIUM, operational, `tools/gates/v3_gateb1_run.py:98-123` + DS report §7.2.**  
**Root cause:** `_owner_receipt` enforces critical identity gates but **does not itself enforce every key in `approved_scope`**. DS's proposed external JSON `assert` snippet checks some key fields but omits `require_manual_source_to_target_release`, `min_free_gpu_memory_mib_at_launch`, `forbid_checkpoint_save`, `forbid_latest_pointer_change`, `forbid_automatic_retries`, `stop_on_OOM_or_nonfinite_or_CUDA_error_or_DCP_mutation` and various non-interference constraints. Other safeguards may exist elsewhere; these operational Owner boundaries still need **explicit out-of-band check + evidence**.  
**Acceptance:** once Owner signs *new* receipt, DS executes an authoritative scope validation against exact new JSON (not a synthetic receipt), checks all critical P0-only booleans/16GiB floor/output namespace/source→manual release→target/order and hard stop conditions, stops on mismatch. Before receipt issuance, prepare script can only be staged, NOT run as if authorization existed. Human clearance must be recorded from actual complete eight-rank SOURCE iter1301/1302 evidence before TARGET, not self-inferred from typing `ALLOW_PACKED128`.

**B1-P0-PREPARE — PENDING PRE-LAUNCH WITNESS, report §7.3 and §8(3).**  
DS report provides two CPU-only `prepare` commands but **does not state they were actually run at `a3239591`** (the report says evidence root not created). Require exactly two lightweight `prepare` runs on pinned source/target (no dataset scan/B0/dcp contents/GPU) with exit0, exact output digests, correct CWD and `PREPARE_ONLY_NO_GPU_OR_DATASET_SCAN`, then STOP. This is execution-readiness evidence, **not** a rerun of previously closed B0, old144/149 tests, 451GB dataset, or previous B1 comparator acceptance.

## 4. Next actions and Gate boundary

- **NOW (DS_PRO, still no GPU):** sanitize ASCII launcher, check external scope validation plan, run/read the two legal CPU-only prepare outputs; preserve both logs and receipts in `/tmp`; report concise evidence with exact Root/Child and exit codes. DS doesn't edit GitHub production, frozen children or existing receipt.
- **OWNER:** may issue a new explicit SHA-bound P0-only GPU authorization after reviewing this readiness; approval is independent of and subject to the previously frozen co-resident VRAM safety floor. This review is **not** an Owner authorization and has not issued a receipt.
- **BEFORE SOURCE EXECUTE:** live all-eight GPU VRAM >= 16384 MiB, source/target/diagnostic worktrees still clean, authorization receipt passes full scope validation, logs/evidence namespace collision-free. Any violation => STOP.
- **AFTER SOURCE / BEFORE TARGET:** DS returns SOURCE 8 ranks × iter1301/1302 raw native witnesses, log/error summary, and original DCP/latest unchanged; explicit human source-to-target clearance must be recorded. Before TARGET again check live memory floor and exact frozen pair. No auto-run.
- **GPU result:** if eventual P0 authorized, Source then Target two separate jobs; thereafter independent numerical review under *unchanged* r2 policy; do not claim numerical parity or allow full B1/Gate M/Formal30k without their later gates.

**Verdict scope:** This is `REQUEST_CHANGES` *only for launch readiness artifacts*. No unresolved B1 CFG diagnostic implementation blocker in this review. No production implementation SHA change necessary, and B1 CFG CPU gate remains `APPROVE_TO_CLOSE`. No GPU or training authorized by this report.
