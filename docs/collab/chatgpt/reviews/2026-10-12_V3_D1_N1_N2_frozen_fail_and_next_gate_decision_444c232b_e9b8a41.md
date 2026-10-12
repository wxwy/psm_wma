# PSM-WMA V3 — D1 N1/N2 Evidence final incremental review and next decision

**Date:** 2026-10-12
**Formal Root (unchanged):** `444c232b976e80ac68cde9e7370e73b9f6410f0e`
**Child/Gitlink (unchanged):** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**Formal verdict for EXISTING frozen D1:** **`REQUEST_CHANGES`**, `D1_PRESTEP_NOT_PASSED`
**Previous accepted Gate:** `C1_RESTORE_PASS / C1_CLOSED`
**Current execution state:** `FORMAL30K_STOPPED / E_F_HOLD / NO_NEW_GPU_AUTHORIZED`
**Owner-relayed current N1/N2 report:** `docs/collab/chatgpt/evidence/2026-10-12_V3_D1_gpu/DS_PRO_2026-10-12_N1_N2_fullrank_frozen_audit_owner_relay.md`. Training-host raw evidence inaccessible to GPT; no code implementation re-review, since formal pair unchanged.
**Prior frozen D1 numeric contract:** `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_paired_8H100_shadow_prestep_numeric_execution_authorization_444c232b_e9b8a41.md`.
**Previous incremental review:** `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_noise_calibration_gate_request_changes_444c232b_e9b8a41.md`.

## 1. N1/N2 Evidence acceptance vs D1 approval

**N1 completed its prescribed Evidence reconciliation, NOT numerical PASS:** Rank0–7 each have 255–264 frozen numeric FAIL entries and 0 unverified; original rank0 comparator still 72 bit_exact, 24 within_tol, 263 FAIL, 2 BLOCKED, 2 not_tested. 8 ranks reported equal pairs of dtype/shape/presence, exact member losses, RNG/Local state. Strong operational and forward-equivalence signals, but **not sufficient for all selected gradients under frozen tolerance**.

**N2 completed its instructed Evidence limitation audit:** Mode vs same-mode differences occupy a similar absolute band, but sample64/full-valid fractions and only one v2 invocation per mode, v1→v2 harness version change, no prospective margin/CI, and correlated FQNs prevent a causal NCCL-only or statistical equivalence conclusion. Preserve `NOISE_EQUIVALENCE_UNESTABLISHED`. The old strict Gate cannot be relabeled PASS after seeing FAIL.

**No observed production Model/Optimizer/Local checkpoint defect** established by this numerical evidence; likewise no proof that OFF and ON have the same full-gradient numerical behavior. All findings below are Evidence/protocol coverage, not implementation defects.

## 2. Current blockers (incremental)

### D1-G1 — Frozen gradient acceptance remains FAIL

- **Severity HIGH**, Evidence acceptance blocker.
- **Artifact:** `/tmp/ds_pro_v3_d1_r1/audit_n1/comparator_rank_{0..7}.json` (original rank0 `/tmp/ds_pro_v3_d1_r1/gpu_run/comparator_rank0.json`); user-relayed report `docs/collab/chatgpt/evidence/2026-10-12_V3_D1_gpu/DS_PRO_2026-10-12_N1_N2_fullrank_frozen_audit_owner_relay.md`, N1 rank table.
- **Root cause:** strict fp32 grad `atol=1e-6,rtol=1e-4` rejected many actual rank-local full gradients in each independent reference/optimized GPU run; no prospective stochastic acceptance was authorized.
- **Frozen contract violated:** Any FAIL/BLOCKED/UNVERIFIED means no `D1_PRESTEP_PASS`.
- **Closure:** either later meet this SAME frozen criterion (not currently shown), or define an explicitly separate **prospective** engineering stochastic-consistency Gate; the latter NEVER changes this original verdict.

### D1-G2 — Inadequate noise-baseline evidence and contradictory row labels

- **Severity HIGH** for causal noise-equivalence claims.
- **Artifact:** report `docs/collab/chatgpt/evidence/2026-10-12_V3_D1_gpu/DS_PRO_2026-10-12_N1_N2_fullrank_frozen_audit_owner_relay.md`, N2 §2.1 and §2.7.
- **Root cause:** v1 clean full-grad ref valid211/296 and opt7/296 rank0, v2 has only one documented run per mode; N2 table nevertheless labels `v2 REF vs REF run2run 296/296` and `v2 OPT vs OPT run2run 296/296`, incompatible with the single v2 run timeline without new independent run IDs. Earlier v1/v2 harness versions differ.
- **Frozen contract violated:** independent within-mode calibration requires independent runs with matched executable/source and full rank/FQN tensor evidence, not self-comparison or contaminated shards.
- **Closure:** identify each actual run ID and source path/hash for those N2 rows or correct them as invalid/unavailable; if choosing a new stochastic Gate, freeze matched replicates and margin before new GPU data.

### D1-G3 — Selected optimizer inventory count needs mapping

- **Severity MEDIUM**, coverage provenance.
- **Artifact:** current N1 report `docs/collab/chatgpt/evidence/2026-10-12_V3_D1_gpu/DS_PRO_2026-10-12_N1_N2_fullrank_frozen_audit_owner_relay.md`, N1 §1.3 `296 unique FQNs / 300 entries incl four w0` versus earlier `docs/collab/chatgpt/reviews/2026-10-10_V3_w0_fast_fsdp2_parity_gateB_closure_formal30k_authorization.md` (314 selected per rank = 289 generation +5 action +20 local).
- **Root cause:** selection identity/counting conventions un-reconciled; the 18-name gap could be aliases/flattening/omission, unknown.
- **Frozen contract violated:** must establish that the comparator covers all selected groups and all required FQNs, not only internally aligned observed subset.
- **Closure:** a CPU-only explicit mapping between 314 optimizer entries and 296 unique local captured FQN; report aliases/empty shards/skips by actual identity. No inventing missing gradients.

### D1-G4 — Zero/empty grad provenance blocking predicate

- **Severity MEDIUM**, diagnostic-only finding.
- **Artifact:** `/tmp/ds_pro_v3_d1_r1/h2/pre_step_comparator.py:149` as reported; two zero `action2llm/llm2action.bias.weight` and one empty `slot_queries`.
- **Root cause:** a universal `grad_hash != weight_hash` / `identical_to_weight=False` check falsely rejects valid zero or empty local gradients if actual `param.grad` source is separately demonstrated. Conversely equal data does not itself prove origin.
- **Frozen contract violated:** complete gradient **provenance** is required; numeric equality and capture-source checks must not be conflated.
- **Closure:** separate and test true `param.grad` source proof from value equality, then retain original comparator BLOCKED as historical and classify only this diagnostic artifact. Do not change the original frozen numeric FAIL conclusion.

### D1-G5 — Executable/artifact lineage incomplete

- **Severity MEDIUM**, protocol evidence.
- **Artifact:** N2 report `docs/collab/chatgpt/evidence/2026-10-12_V3_D1_gpu/DS_PRO_2026-10-12_N1_N2_fullrank_frozen_audit_owner_relay.md`, §2.5–2.6 and prior formal D1 hash authority.
- **Root cause:** original exact v1/v2 Harness/Launcher diffs not recoverable; v1 archived and v2 reused name `attempt_01` despite earlier explicit separate `attempt02` restriction. Script changes can confound same-mode noise interpretation.
- **Frozen contract violated:** independent matched-replica source identity and immutable per-attempt Evidence expected.
- **Closure:** prospectively lock a single executable version and unique attempt namespaces, avoid claiming v1/v2 as fully controlled same-code repeats.

## 3. Decision — Separate a future stochastic-consistency Gate from unchanged-mode formal resume

**Choose A for scientific/optimization validation:** design a **new prospectively frozen** `D1-S` stochastic-consistency *engineering* Gate if there is value in proving OFF/OFF vs ON/ON beyond their existing byte-identical forward inputs/loss. Original `D1_PRESTEP_NOT_PASSED` remains unchanged and may never be 'relabelled' by the new Gate. Do not claim NCCL as sole noise cause.

**In parallel**, assess the distinct operational question: **was the original `formal_verified_index_30k` iter1–800 actually trained under a specific OFF/OFF or ON/ON mode, and can resumed iter801 preserve that exact mode and same source?** If concrete launcher/env/telemetry evidence proves old mode and restored code/data/optimizer paths identical, a separately reviewed **UNCHANGED_MODE_FORMAL_RESUME_GATE** could consider monitored original-job continuation without falsely claiming cross-mode D1 PASS. This is an option, **not an authorization to resume**. Default env values or frozen config digest alone do not establish the effective original mode because these env toggles are outside `config_digest`.

## 4. Scoped next authorization

Only the two independent CPU-only evidence/design tasks in `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_parallel_original_mode_resume_feasibility_and_prospective_noise_design_444c232b_e9b8a41.md` are authorized, in parallel, with one combined report. No GPU, no Formal30k resume, no code changes or new gradient-comparator tolerance adjustment. If original mode is not provable, return `MODE_IDENTITY_BLOCKED`; if the stochastic plan cannot freeze a defensible margin, return `D1_S_DESIGN_BLOCKED`. C1 remains closed.

**Formal result: `REQUEST_CHANGES` for D1 only**, persisted together with canonical CODEX_INBOX entry; no fresh implementation technical audit was done.