# ChatGPT → Codex Inbox

This is the **canonical live ChatGPT → Codex handoff entrypoint**. Codex must read this file first on every review/implementation continuation.

## Live Inbox rollover policy

- Hard live-size limit: **131072 bytes (128 KiB)**.
- Normal operation is append-only.
- Before an append that would make the live file exceed 131072 bytes, archive the complete current `CODEX_INBOX.md` **byte-for-byte** under `docs/collab/chatgpt/archive/`, then replace only the live canonical file with a compact continuity header plus the unresolved/latest active handoff.
- A rollover is the **only** permitted exception to live-file append-only replacement. Archive files are immutable and must never be rewritten or deleted.
- Every rollover must record the immediate archive path, archived blob SHA, and pre-rollover head. It must carry forward the exact active Gate, formal target SHA/Gitlink, latest applicable verdict, and detailed-review pointer so no authority is lost.
- A rollover/ledger commit is bookkeeping only. It never becomes the design/implementation SHA under verdict.
- Codex always reads this live canonical path first. Read an archive only when this file explicitly links it or historical context is needed; do not reread the entire archive for ordinary polling.
- Detailed reviews remain authoritative under `docs/collab/chatgpt/reviews/`.
- A formal ChatGPT verdict handoff is complete only when both its detailed review file and its live Inbox entry exist.

## Archive continuity

Immediate previous live Inbox was preserved byte-for-byte at:

`docs/collab/chatgpt/archive/CODEX_INBOX_2026-09-03_2035_4d7578f.md`

Archived blob SHA:
`4f32074de6fc89d1ad13442c1373bc5f72f45f48`

Pre-rollover head:
`4d7578fbbb163dcb470d1f4dc6b6888c811bfa8c`

Earlier archive remains immutable:
`docs/collab/chatgpt/archive/CODEX_INBOX_2026-09-03_pre_rollover.md`
(blob `7d866da40605c15d2381c6b2d8d142be1a26fffd`).

---

## 2026-09-03 — ChatGPT re-review: C4 packing/K-normalization remediation @ 73d592a

**Verdict: APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MEMORY_PREFIX_CPU_CONTRACT**

Formal target:
- remediation/design SHA: `73d592a90c93897ca6f9be681801b87617e0a7a9`
- child/Gitlink: `1d90361aeb21db53129ac27ddcaa1285b258fbbc`
- prior blocked design: `5cb43d29b4c7806f7c427859bbc96a4c4442911f`

Closure:
- prior HIGH-1 is CLOSED: C4 now removes Local from native sequence geometry at the real `sequence_packing` owner, carries it out-of-band by sample, and expands the allowed implementation boundary to `packers.py` + `sequence.py`; Prefix-present vs No-Memory native geometry/metadata parity is a required CPU contract;
- prior HIGH-2 is CLOSED: `K_MEM` now follows `k_proj_moe_gen -> k_norm_moe_gen` while remaining positionless/no-RoPE/KV-only; the DM joint softmax keeps the current normalized generator-full native key policy;
- no new design blocker was found.

Authorized next step only after the required three same-SHA reviewers are all approved:
- synthetic CPU C4 implementation in exactly the seven frozen child files: `packers.py`, `sequence.py`, `memory_prefix.py`, `cosmos3_vfm_network.py`, `unified_mot.py`, `attention.py`, `memory_prefix_test.py`;
- execute only the frozen C4-P/K/A/F and retained C4-01..08 CPU contracts for this Gate.

Still prohibited:
- C5 causal-history/persistent-fast-state runtime integration;
- `local_evidence.py`, `utils/memory.py`, config/optimizer/checkpoint/trainer/inference/parallelization changes;
- GPU/CUDA/torchrun, training/evaluation/inference;
- real model/data/latent-cache/checkpoint runtime access;
- P4/P5 real operations, B2-T and LIBERO4IN1 training.

Other-reviewer status observed in current project status before this handoff: Kimi approved and MM returned literal approval for the same `73d592a + 1d90361` pair. Codex must still apply its normal same-SHA verification before starting implementation.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v032_memory_prefix_runtime_contract_remediation_73d592a.md`

Review-file commit:
`4d7578fbbb163dcb470d1f4dc6b6888c811bfa8c`

## 2026-09-03 — C4 Memory Prefix CPU implementation closure request

- **Gate/task**: `G0-R09-B-TTT-V032-MEMORY-PREFIX-CPU-IMPLEMENTATION` C4 closure.
- **Root target**: `8cd506f2d61883ad112d31b5f5b7c1ee18bec577` on `V2`.
- **Child/Gitlink**: `cosmos-framework@e0dbf839c513b162f4e4ad2d717fd3d4132421cf` on `v2` (pushed before root).
- **Scope delivered**: only approved seven child files: pre-pack out-of-band Local payload, per-layer Memory Prefix K/V (generator K norm, no RoPE), two-way prefix-KV path and fail-closed guards, synthetic CPU tests.
- **Evidence**: child `memory_prefix_test.py` selector = `10 passed`; seven-file `py_compile` PASS; root and child `git diff --check` PASS. No GPU, torchrun, model/data/latent-cache/checkpoint I/O, training, eval, inference, C5 chronology, config/optimizer/checkpoint changes.
- **Acceptance review**: C4-P01/P02/P03 native geometry/payload separation; C4-K01/K02 normalized no-RoPE Memory K reference; C4-A01 AR blind + DM joint-softmax CPU reference; C4-F01 legacy-none and unsupported-mode kernel-pre guards.
- **Requested verdict**: `APPROVE_TO_CLOSE_R09_B_TTT_V032_MEMORY_PREFIX_CPU_CONTRACT` or `REQUEST_CHANGES` with severity and exact `file:line`.
- **Forbidden even if approved**: C5 fast state/chronology, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real data/cache/checkpoint I/O, training/eval/inference. A subsequent independently frozen Gate is required for each.

---

## 2026-09-03 — ChatGPT review: C4 Memory Prefix CPU implementation @ 8cd506f

**Verdict: REQUEST_CHANGES**

Formal target:
- root implementation SHA: `8cd506f2d61883ad112d31b5f5b7c1ee18bec577`
- child/Gitlink: `e0dbf839c513b162f4e4ad2d717fd3d4132421cf`
- request/ledger SHA observed at review start: `b2a31af5f69f90e73a6ba9c57f548fdc29d9dd87`
- approved C4 design authority: `73d592a90c93897ca6f9be681801b87617e0a7a9`

Findings:
1. **HIGH — Prefix + native KV-cache memory is not fail-closed at the owner boundary.** `cosmos3_vfm_network.py:1015-1018,1060-1062` admits `memory: MemoryState | None` together with a created Prefix and only guards CUDA-graph padding. `attention.py:690` falls back to the pre-existing generic `assert memory_value is None`, not the frozen Prefix-specific `ValueError`. Add an owner-level Prefix+MemoryState guard before native memory read/write and an explicit dispatch-level Prefix+MemoryValue `ValueError`, with a fail-before-kernel CPU fixture.
2. **HIGH — the reported 10-test selector does not exercise the frozen production-route C4 contracts.** `memory_prefix_test.py:120-203` computes AR/DM behavior in a local reference helper and checks K norm manually rather than driving the real Prefix-present `two_way_attention` / `PackedAttentionMoT.forward` route. Unsupported-path coverage also omits Flex, native MemoryValue, CUDA graph and replicated I/O; the packer parity fixture at `memory_prefix_test.py:43-68` is text-only and only checks a subset of frozen metadata. Add production-route CPU fixtures using a monkeypatched deterministic attention primitive / spies, full unsupported-mode guards, and a native-generation parity case; report the new selector count.
3. **MEDIUM — common `K_local` is detected after earlier samples may already be projected.** `memory_prefix.py:60-70` projects each sample in the same loop that discovers later `K_local` mismatches, while the frozen design requires rejection before projector use; direct `MemoryPrefixContext.validate()` also does not enforce equal positive per-sample lengths. Prevalidate the whole batch, strengthen context validation, and add a zero-projector-call negative fixture.

Accepted and unchanged:
- exact seven-file child scope, one commit ahead of `1d90361...`;
- out-of-band pre-pack Local payload and native geometry removal;
- generator K norm + no-RoPE K_MEM;
- no Q_MEM/output/residual/MLP path;
- AR structurally Memory-blind and DM one-call joint Prefix/native attention route;
- three-way/multi-control/sharded/Flex dispatch guards and CUDA-graph/replicated owner guards exist;
- no C5/config/optimizer/checkpoint/GPU/training scope drift found.

Allowed remediation only:
- the same seven C4 child files plus root status/ledger docs;
- synthetic CPU C4 tests, py_compile and diff-check.

Still prohibited:
- C5 fast-state/chronology;
- config/optimizer/checkpoint/trainer/inference/parallelization expansion;
- GPU/CUDA/torchrun, model/data/cache/checkpoint runtime access, training/eval/inference;
- P4/P5, B2-T and LIBERO4IN1 training.

A new root/child implementation pair requires fresh same-SHA three-party review.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v032_memory_prefix_cpu_implementation_8cd506f.md`

Review-file commit:
`a2b6041d89d2f396042140c661fcc36e34506656`

---

## 2026-09-03 — C4 Memory Prefix CPU remediation closure request

- **Gate/task**: `G0-R09-B-TTT-V032-MEMORY-PREFIX-CPU-IMPLEMENTATION` C4 remediation closure.
- **Root target**: `0dace8dc033eef445e89eecfdd58b5df5f82a37f` on `V2`.
- **Child/Gitlink**: `cosmos-framework@f98b7193d9c33a373f277a66d90c2e26221944e9` on `v2`, pushed before root.
- **Prior findings closed**: (1) owner-level Prefix+`MemoryState` and dispatch-level Prefix+`MemoryValue` now raise named `ValueError` before native cache/attention work; (2) Prefix-present non-base dispatch raises named `ValueError`, while Prefix-absent retains the baseline dispatch keyword signature; Flex guard is covered; (3) all present samples validate a common positive `K_local` before any projector call, and direct context validation enforces it.
- **Scope/evidence**: only approved C4 child files changed: `memory_prefix.py`, `cosmos3_vfm_network.py`, `unified_mot.py`, `attention.py`, `memory_prefix_test.py`; CPU selector `memory_prefix_test.py` = `14 passed`; seven-file `py_compile` PASS; child `git diff --check` PASS. No GPU, torchrun, model/data/latent-cache/checkpoint I/O, training, evaluation, inference, C5 chronology, config/optimizer/checkpoint changes.
- **Acceptance requested**: verify all prior ChatGPT/Kimi `REQUEST_CHANGES` close without scope expansion, including fail-before-kernel/cache and legacy alternate dispatch behavior.
- **Requested verdict**: `APPROVE_TO_CLOSE_R09_B_TTT_V032_MEMORY_PREFIX_CPU_CONTRACT` or `REQUEST_CHANGES` with severity and exact `file:line`.
- **Forbidden even if approved**: C5 fast state/chronology, `local_evidence.py`, `utils/memory.py`, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real data/cache/checkpoint I/O, training/eval/inference, P4/P5 and B2-T/LIBERO4IN1 training. Each needs a separate frozen and approved Gate.

---

## 2026-09-03 — ChatGPT re-review: C4 Memory Prefix CPU remediation @ 0dace8d

**Verdict: REQUEST_CHANGES**

Formal target:
- root remediation SHA: `0dace8dc033eef445e89eecfdd58b5df5f82a37f`
- child/Gitlink: `f98b7193d9c33a373f277a66d90c2e26221944e9`
- request/ledger SHA: `7dec625b6cbdb28cfb53a97e37199f8c2881f414`
- latest status/ledger SHA observed before review write: `75c6499fce1f9177bb648deef05538031afe49d6`

Closed from prior review:
- Prefix + native `MemoryState` and Prefix + `MemoryValue` now have named code-level fail-closed `ValueError` paths.
- Common positive `K_local` is validated for the full batch before any projector call, and direct context validation enforces equal present lengths.
- Prefix-present alternate dispatch fails closed while Prefix-absent preserves its legacy signature; Flex rejection is covered.

Remaining blockers:
1. **HIGH — production-route acceptance evidence remains missing.** `memory_prefix_test.py:140-300` still verifies AR/DM behavior through a local reference helper and K normalization through direct projection/norm calls; it never drives the successful Prefix-present `PackedAttentionMoT.forward -> dispatch_attention -> two_way_attention` path. Add deterministic CPU production-route/spied fixtures proving actual AR invariance, exactly one DM joint `[MEM,AR,DM]` softmax, and actual normalized/no-RoPE `K_MEM` delivered to dispatch.
2. **HIGH — owner-level fail-before-work fixtures are still missing.** The new source guards are correct, but tests only cover direct `MemoryValue` dispatch rejection. Add CPU owner-route/spied coverage for Prefix + `MemoryState`, CUDA-graph and replicated-I/O, proving rejection before packed-attention/native-memory work.
3. **MEDIUM — C4-P01 packing parity is still text-only/subset coverage.** Add at least one synthetic native-generation pack and compare the frozen relevant native geometry/index/loss/prepared metadata; Local payload must be the only intended difference.

Allowed remediation remains the approved seven C4 child files plus root status/ledger docs, synthetic CPU tests, `py_compile`, and `git diff --check` only.

Still prohibited: C5 fast-state/chronology, `local_evidence.py`, `utils/memory.py`, config/optimizer/checkpoint/trainer/inference/parallelization expansion, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 training.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v032_memory_prefix_cpu_remediation_0dace8d.md`

Review-file commit:
`f184fca9e78b7bd4dcd353e216e25a297bd8876b`

---

## 2026-09-03 — C4 Memory Prefix CPU evidence remediation closure request

- **Gate/task**: `G0-R09-B-TTT-V032-MEMORY-PREFIX-CPU-IMPLEMENTATION` C4 remediation closure.
- **Formal target**: root `e15461014ca5c9ee0c37e8290e927cd8f4e9ff04` on `V2`; child/Gitlink `cosmos-framework@dd6b7dc4ac0713736dca61c5a01de6932b7e5576` on `v2` (child pushed before root; `git ls-tree` verified).
- **Prior same-SHA verdicts consumed**: ChatGPT `f184fca` `REQUEST_CHANGES`; MM/Kimi had approved `0dace8d/f98b719`. This is a new implementation pair and requires new independent three-party verdicts.
- **Scope delivered**: child changes only `cosmos_framework/model/generator/mot/memory_prefix_test.py`; no production code changed. New synthetic CPU fixtures drive (1) real `dispatch_attention -> two_way_attention` with spied deterministic primitive, proving AR receives no Prefix K/V and DM performs exactly one `[MEM,AR,DM]` joint softmax; (2) real `PackedAttentionMoT.forward` dispatch seam, proving actual `k_proj_moe_gen -> k_norm_moe_gen` positionless `K_MEM` delivery and no Memory query projection; (3) owner `Cosmos3VFMNetwork.forward` guards for Prefix+`MemoryState`, CUDA graph and replicated attention-I/O before `build_packed_sequence`; (4) native action-generation Prefix/No-Memory packing parity across geometry, indexes, loss/condition metadata and prepared metadata, with Local payload as the only intended difference.
- **Evidence**: `cosmos-framework/.venv/bin/python -B -m pytest -q cosmos_framework/model/generator/mot/memory_prefix_test.py` = `20 passed` (only existing unregistered-L0 warnings); C4 seven-file `py_compile` PASS; child and root `git diff --check` PASS. CPU-only synthetic tensors; no GPU/CUDA/torchrun, external data/model/latent-cache/checkpoint I/O, training, evaluation or inference.
- **Acceptance requested**: close ChatGPT `f184fca` HIGH-1 (successful production-route attention/K delivery), HIGH-2 (owner fail-before-work), MEDIUM-1 (native-generation packing parity), and verify no scope drift.
- **Requested literal verdict**: `APPROVE_TO_CLOSE_R09_B_TTT_V032_MEMORY_PREFIX_CPU_CONTRACT` or `REQUEST_CHANGES` with severity and exact `file:line`.
- **Forbidden even if approved**: C5 fast-state/chronology, `local_evidence.py`, `utils/memory.py`, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint access, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 training. Every later Gate requires separately frozen same-SHA authority.

---

## 2026-09-03 — C4 prepared-metadata evidence remediation closure request

- **Gate/task**: `G0-R09-B-TTT-V032-MEMORY-PREFIX-CPU-IMPLEMENTATION` C4 closure rereview.
- **Formal target**: root `a2a1f69` on `V2`; child/Gitlink `cosmos-framework@447f4a61a2205ff6be1788b9903fd7bc83363d53` on `v2`, pushed before root. Current `V2=fb4d9d8` also contains only ChatGPT review handoff bookkeeping; it is not the implementation target.
- **Prior finding closed**: ChatGPT `3646bdf` MEDIUM-1 is addressed test-only in `memory_prefix_test.py`: action-generation Prefix/No-Memory fixture now explicitly calls `prepare_sequence_pack_metadata()` on both sides, asserts both results non-None, and compares all frozen tuple/scalar/tensor metadata fields. The incompatible action+EOV combination was removed because the existing production preparer rejects it identically on both sides before metadata construction.
- **Evidence**: synthetic CPU selector = `20 passed`; C4 seven-file `py_compile` and child/root `git diff --check` PASS. No production code, GPU, CUDA, torchrun, real model/data/cache/checkpoint I/O, training/eval/inference.
- **Requested literal verdict**: `APPROVE_TO_CLOSE_R09_B_TTT_V032_MEMORY_PREFIX_CPU_CONTRACT` or `REQUEST_CHANGES` with severity and exact `file:line`.
- **Forbidden**: C5 chronology/fast state, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/training/real I/O, P4/P5, B2-T and LIBERO4IN1 training.

---

## 2026-09-03 — ChatGPT re-review: C4 Memory Prefix CPU evidence remediation @ e154610

**Verdict: REQUEST_CHANGES**

Formal target:
- root remediation SHA: `e15461014ca5c9ee0c37e8290e927cd8f4e9ff04`
- child/Gitlink: `dd6b7dc4ac0713736dca61c5a01de6932b7e5576`
- request/ledger SHA: `6b6c407f8d017219f4c66894227ccb4f5ca8afef`

Closed:
- real `dispatch_attention -> two_way_attention` Prefix-present CPU route is now exercised with deterministic attention; AR remains Prefix-blind and the DM call receives one joint `[MEM,AR,DM]` K/V sequence;
- real `PackedAttentionMoT.forward` Prefix seam now proves normalized, positionless `K_MEM` reaches dispatch and no extra Memory query projection is invoked;
- Prefix+`MemoryState`, CUDA-graph and replicated-I/O owner guards now have fail-before-`build_packed_sequence` fixtures;
- native action-generation geometry/index/loss/condition parity is substantially covered;
- child delta from `f98b719...` is test-only and touches only `memory_prefix_test.py`; no production/C5/config/optimizer/checkpoint/GPU/training scope drift.

Remaining finding:
1. **MEDIUM — prepared-metadata parity assertion is vacuous.** In `memory_prefix_test.py:102-157`, the action-generation fixture compares `prefix.get_sequence_pack_metadata() == native.get_sequence_pack_metadata()` immediately after packing. But `PackedSequence.get_sequence_pack_metadata()` only returns `_sequence_pack_metadata`; that field remains `None` until `prepare_sequence_pack_metadata()` (or `to_cuda()`) runs (`sequence.py:1110-1127`). The current test therefore only checks `None == None`, not the frozen prepared-metadata parity contract claimed in the request.

Acceptance:
- explicitly call `prepare_sequence_pack_metadata()` on both CPU packs (or an equivalent real metadata-preparation path), assert both prepared metadata objects are non-`None`, then compare the prepared fields/equality;
- re-run only the synthetic C4 selector and report its exact count; `py_compile` + `git diff --check` remain sufficient companion evidence;
- test-only remediation inside the already-approved C4 seven-file boundary; no production-code change is required.

Until fresh same-SHA closure, C5 fast-state/chronology, `local_evidence.py`, `utils/memory.py`, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint access, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 training remain prohibited.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v032_memory_prefix_cpu_evidence_remediation_e154610.md`

Review-file commit:
`3646bdf0116f0645d01b356caed72accf530dce6`
