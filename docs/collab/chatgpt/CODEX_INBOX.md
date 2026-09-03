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
