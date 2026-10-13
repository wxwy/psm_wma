# GPT → DS_PRO — Gate B0 CPU 批量验证（一次执行 / 一份证据 / 一次 GPT 审核）

**Date**: 2026-10-13
**Scope**: B0 diagnostic CPU only. Owner D1–D4 frozen. **GPU/B1/Migration/Formal30k NOT AUTHORIZED**.
**Review target**: diagnostic candidate identity (complete pinned source SHA/ZIP hash) + Index8 Root b159f45906f7261d028aecc226ab7f2bb9807eb9 / Child 937066ffd90f2bf783ad4fbb4909e9c0b8922982 + Packed128 Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 / Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686.
**Baseline**: Full Prefetch C0 closed but excluded from Gate B0/B1. Original iter_000001300 is read-only sole source; failed iter1400 excluded.

## Delivery status / first gate

The isolated candidate ZIP supplied in Owner ChatGPT session is named **V3_GateB_B0_Comparator_CPU_Candidate_20261013.zip**, SHA256 **911946134effd478071ef61180ff0eaadaee4721f4b7dc70080a6b5e348c6852**; includes 5 files (README, validation instructions, tools/gates/v3_packed128_gateb_compare.py, v3_gateb_numerics.py, test_v3_packed128_gateb_compare.py). Author local CPU: 21 passed; py_compile PASS; Ruff NOT YET RUN. The isolated GitHub branch **v3-gateb-comparator-b0** (previously at **853cf9a850d62e01596cd175683e89b5cbab97ff**) contains only numerics; it is **NOT the complete remote implementation**. No assumption that ZIP is already present on DS host. DO NOT mix partial branch helper with ZIP candidate, or report a Git SHA for code not committed. If no complete artifact is accessible, mark **BLOCKED_CANDIDATE** and continue independent read-only baseline inspections; do not invent tests/execution. Once complete candidate is provided (single ZIP verified byte-for-byte OR full reviewed branch commit), pin it before launching related tests. DS does not edit/commit code.

**Batch instruction**: Perform all independent B0 tasks in a single isolated DS run; do not send a sequence of partial asks to GPT. Independent lanes may run concurrently (static tests; immutable source/checkpoint inventory; dataset/catalog/profile read-only checks). Heavy disk sweeps and per-leg CPU materialization should run sequentially, avoiding storage contention and cross-leg Python imports. One lane's failure blocks its dependents only; collect all safe independent evidence and first traceback for each failing lane. Do not weaken checks or change code; at most one consolidated reply.

## Lane A — identity/security/environment (can parallel with B/C)

1. Pin candidate exact ZIP SHA256 **or** full commit SHA and record the five extracted file hashes; verify no ZIP path escapes; isolated folder only, never extract into formal tree.
2. Pin both independent source+target root/child Gitlink pairs (all 40 hex chars), each actual Python module __file__, no dirty child; check config/model/cache/dataset index existence without performing a GPU model load.
3. Capture python/torch/pytest/ruff versions, SHA and env. Force **HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH=''**, no internet access.
4. Fail closed if source DCP is not exactly the owner-frozen iter_000001300; never inspect or repair iter1400, never modify checkpoint/latest/formal worktree.

## Lane B — all diagnostic static/negative/unit checks (independent of C)

From the isolated **complete** candidate with the validated V3 .venv, run and record each exit code:
- \`python -m py_compile tools/gates/v3_packed128_gateb_compare.py tools/gates/v3_gateb_numerics.py tools/gates/test_v3_packed128_gateb_compare.py\`
- \`python -m pytest -q tools/gates/test_v3_packed128_gateb_compare.py\`
- \`ruff check\` on precisely those 3 files, using repository-authoritative Ruff configuration; capture actual selection/config.
- Negative protection: \`--mode paired-run\` must exit **2** with \`GPU_B1_NOT_IMPLEMENTED_OR_AUTHORIZED\`; unrelated/dirty Root/Child, output namespace escaping /tmp, altered digest and nested provenance, malformed sidecar, nonfinite fast-state, duplicate/wrong consumers, illegal RNG shapes must fail closed. May use already provided unit tests and their exact test names; do not invent PASS for uncovered negative cases.
- Confirm no import of GPU runner, no real train/checkpointer save/migration path, no GPU allocation.

## Lane C — source DCP & dataset read-only audit (parallel with Lane B)

- Confirm source model/optim/scheduler/trainer four DCP metadata and **32 shards**, eight dataloader rank_*.pkl (only trusted pinned pickle); rank0/7 full 17-element profile, all8 rank-specific slot/epoch/frontier/scheduler keys and top-level+nested source digest; verify source config digest from actual source/checkpoint, do not treat a chat value as a freshly read result.
- Calculate source file manifest/sha256 once before and once after any candidate run; if all-shards full hash too costly, record explicit degraded evidence and do **not** report immutability PASS. Reuse a single trusted pre-hash in subsequent dependent lanes rather than 2 independent workers both rehashing large shards at once.
- CPU pure-function read-only derive two consecutive windows per each rank; record per-rank GA0/GA1 member_counts, Consumer identity, terminal, Index8 FSDP collective-call rhythm. Unequal rhythm -> BLOCKED_RHYTHM for GPU path, **never** issue GPU commands or paper over by padding/truncation. If the full artifact is unavailable, separate read-only probes can still be reported as source-audit evidence, NOT B0 complete.

## Lane D — paired real CPU producer/transforms (after A+C, serial legs)

Use the complete candidate's packaged command contract \`docs/DS_PRO_V3_GATEB_B0_CPU_VALIDATION_2026-10-13.md\` without substituting the existing formal \`--phase resume\`.
- Source leg **only** in its pinned Index8 process with Source child PYTHONPATH; target leg **only** in separate pinned Packed128 process with its child PYTHONPATH; \`--mode cpu-plan-only --num-workers 0 --steps 2 --hash-all-shards --verify-payloads\`, distinct brand-new /tmp outputs, original iter1300 immutable.
- Heavy source/target file I/O **sequential**. The same CPU checksum manifest is used to confirm pre/post source files and avoid concurrent multi-GiB sweeps.
- Compare both JSON reports via \`--mode compare-cpu-reports\`; verify identical 8rank×2 window consumer plans, actual partial member counts, Native CPU transformed payload bytes, scoped Python CFG reproducibility and main-thread RNG preservation, target **in-memory only** top-level/nested digest conversion (no sidecar rewrite).
- If a production API/real payload type fails, keep command/first traceback and classify BLOCKED; never modify source/diagnostic/production code locally. Note B0 synthetic P0/P1 CPU RNG witnesses **do not implement B1 training distribution-matched sigma injection**.

## Parallelism & fail-closed

Concurrent allowed: Lane A static provenance, Lane B tests/lint and Lane C read-only metadata/catalog (provided no shared large shard rehash concurrency). Lane D requires A/C and **runs Index8 then Packed128 serially**; report compare only if both success. Do **not** run two DCP full-hash sweeps or both real materialization legs simultaneously. Failures in a lane do not erase independent evidence; **one consolidated report**, no iterative partial messaging unless safety/source immutability requires immediate STOP.

## One consolidated acceptance report — ONE GPT review

Write \`DS_PRO_V3_PACKED128_GATE_B0_BATCH_CPU_ACCEPTANCE_2026-10-13.md\` in isolated evidence space, containing:
- exact complete candidate digest/SHA + source/target formal pair; resolved module paths; env;
- evidence matrix A/B/C/D with \`PASS / FAIL / BLOCKED / NOT_RUN\`, all commands and exit codes, first failing traceback per lane, precise file/line root causes when identified;
- 3-file Ruff, compile, tests (no synthesized test count); actual 8rank sidecar/profile, two-window member counts/collective rhythm, terminal witness/limitations;
- source checkpoint before/after fingerprint, payload parity JSON hashes (or explicitly not run), no unauthorized write/GPU;
- complete list of **not validated**: real Cosmos3-Edge FSDP8 DCP load; B1 GPU F/B, P1 real sigma/noise injection, per-FQN gradients, optimizer parity, Gate M migration, formal resume; no performance or causal gpu_data_stall claim.
- first failure per lane + remediation proposal *as evidence only*, **NO DS code fix or code commit**.

Submit **one final consolidated reply** to GPT and stop. GPT will perform **one independent audit** against exact diagnostic candidate and direct evidence. Do not self-approve B0; it does not authorize B1 GPU, torchrun, Nsight, training/inference, DCP/latest mutation, migration or Formal30k. Owner separately freezes actual numerical tolerance and authorizes later B1.
