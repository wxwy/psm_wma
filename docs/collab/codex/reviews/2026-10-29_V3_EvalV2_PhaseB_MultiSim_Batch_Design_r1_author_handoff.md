# Phase B r1 — author design handoff (not a reviewer verdict)

Date: 2026-10-29. **REQUEST APPROVE_DESIGN / REQUEST_CHANGES.**

| Identity | Exact value |
| --- | --- |
| New **Design Root** | `fac029c83eb94fdafcc26d030ca5942542d740a3` |
| Unchanged Child / Gitlink | `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |
| Isolated candidate | `v3-eval-v2-batch-b-design-20261029` (Root only; no Child source commit) |
| Frozen production Root | `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` |
| Exact Phase A source verdict | GPT `APPROVE_CODE`, `docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_PhaseA_fd7e43f6_d2c1bda6_FINAL_Code_Gate.md` |

The evidence/handoff HEAD is bookkeeping, not the design target or a new implementation. Phase A's independent DS CPU remains pending and is not run by this delivery. Its original255 author tests are not rerun or relabeled as Phase B tests. No production support for M>1 or required-mode Batch is claimed.

## Deliverables and source findings

- Full proposed contract: `docs/build/PSM-WMA_V3_EvalV2_PhaseB_MultiSim_Transactional_Batch_Design_r1_2026-10-29.md`.
- Isolated protocol examples: `tools/v3/eval_v2_batch_design/`; stdlib symbolic state, fake clock and fake vector generator. No production imports or Launcher wiring.
- Raw final JUnit, Ruff0.12.7, format, syntax hashes,16 frozen source Git Blob bindings and formal design diff: `docs/collab/codex/evidence/2026-10-29_eval_v2_phase_b_design_author_cpu/`.
- `STATUS.json`, `commands.json`, `formal_design_bindings.json` and `artifact_sha256.json` distinguish source, design, author evidence and unexecuted gates. Earlier28-test draft logs are retained as an explicitly unfrozen earlier draft; final29 tests bind this design.

The actual server rejects required-mode `predict_policy_batch`. The native generator accepts per-item Local Prefix and seed carriers; that is reusable, but current single-Session commit, separate fast/visual stores and no complete HTTP response replay do not establish Batch semantics. Current serial video decode precedes action commit, so merely looping the serial path would also retain optional-media coupling. The design does not reimplement Cosmos or Local-TTT and does not modify these sources yet.

Proposed future implementation uses M separate Sim processes/GPU, one model executor/GPU, bounded compatibility queue with partial flush, one native generation invocation/batch, an atomic fast+visual+frontier+response publication, canonical tickets and bounded response replay, explicit lease generations and retrievable end ACKs, and optional asynchronous media. B>M is legal as a ceiling but cannot create more simultaneous requests than M. D1–D5 and Episode-major barriers remain authoritative; N=1 cannot demonstrate Batch>1 within one round. Resource caps are proposed validation limits, not measured H100 capacity.

## Author checks actually executed

- Final **29 passed, 0 failures, 0 errors, 0 skipped**; raw JUnit0.084s (pytest rounded0.08s).
- Ruff **0.12.7 check + format --check PASS**;3 new Python files AST PASS.
- Frozen production audit:16/16 checked Git Blobs match fd7/d2, Root `scripts/`, `configs/`, `third_party/` and Child Gitlink diff ZERO; Child clean. Design commit directly changes6 files: design,3 protocol files, SESSION and TODO.
- Existing CPU environment `/workspace/.venvs/psm-wma-cpu/bin/python`, CUDA hidden, model network flags offline, writable caches outside repo. No model, dataset, Checkpoint or simulator input. Exact argv/environment in `commands.json`.
- No tensor-level scan/aliasing/RNG, HTTP concurrency, native diffusion, real process-cleanup timing, media delivery, VRAM/EGL, physics or throughput proof. A fake vector call counter is not a claim of true native Batch acceptance.

## Review request and next boundaries

Please review the **new design pair** above, particularly the feasibility of consolidating Session stores into one publication owner, response/end-ACK replay, closed lease fencing, full-batch abort policy, deadlines, media isolation, native carrier mapping and inherited D1–D5. Request `APPROVE_DESIGN` or precise `REQUEST_CHANGES`; do not issue or infer APPROVE_CODE from this document.

Only after this new Design Gate may Codex implement Phase B in isolated candidates, with new exact Child/Root implementation SHAs and production-path CPU evidence. Thereafter GPT Code Gate, independent DS CPU and separately authorized native Canary remain required. No V3/Child merge, GPU/model/real RoboCasa/DCP/900, DS dispatch, training or old result operation was performed or authorized.

Publication updates the **candidate branch's** canonical Inbox path only. It does not overwrite the V3 Inbox or unrelated collaborators' work. Fresh remote V3 fetch before publication reached `7e0b7d416e2de29fc93edd4a1084dea52e08fa9a`; its three new commits concern No-TTT evidence/review, have no production source changes and do not replace Phase A's exact source verdict. Those independent tasks are not expanded here. Remote publication/readback is recorded separately, without turning its bookkeeping commit into the Design Root.
