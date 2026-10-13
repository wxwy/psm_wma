# GPT → DS_PRO — V3 Packed128 Gate B comparator / iter1300 migration plan round2 remediation

**Date:** 2026-10-13  
**Verdict:** `REQUEST_CHANGES` (**design-only**; GPU and DCP work NOT authorized)  
**Source attachment SHA256:** `2c534813a8f832365248fabba8342c6d4084719c1754cddd07d451cf9eac5798`  
**Review:** `docs/collab/chatgpt/reviews/2026-10-13_V3_Packed128_GateB_revised_design_review_owner_paste_2c534813.md`

## Retained correct decisions

- Index8 original Formal producer Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.
- Packed128 frozen Gate A target Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.
- Exclude newer FSP Pair from Gate B. Original iter1300 is only future migration input; failed 1400 excluded.
- `_profile` has 17 fields; rank0/rank7 reported correctly. Old→new `config_digest` is intentionally different. Packed full GA2 calls: **exactly 2 Native F/B pairs**, one optimizer/scheduler step/rank. Gate A and C0 CPU approvals remain closed.

## Must correct — do not attempt the listed --phase resume commands

**R1 HIGH: separate comparator and checkpoint migration.** Current §2.2/§6.2/§8 T2/T12/§9.1/§12 conflict. `--phase resume --job-name gateb_*` looks for nonexistent same-job latest; Packed cannot directly load original Index8 DCP. Produce **one explicitly no-production-write**, bounded 2-step, matched-state numerical comparator harness design, with exact command/entrypoint, source read-only inputs, transient model+optimizer/Local state initialization, trace and per-consumer witness capture, no checkpoint/digest forgery or publication. It can be *designed* now; actual harness code belongs to GPT after design approval. Put real old/target Strict DCP native loads and iter1300→1301 continuity in the separately authorized migration Gate, not Gate B prerequisites. Identify any no-write old original-pair DCP-load witness separately.

**R2 HIGH: deterministic per-consumer stochastic control.** Define exact consumer identity key and where every stochastic draw (CFG Python random, sigma, action/vision noise, model stochasticity) is fixed/captured/replayed, so Index8 index-major vs Packed slot-major produce **identical per-consumer witnesses** despite native call shape. Do not demand global after-step RNG stream BIT_EXACT *across* layouts without demonstrating a consumption-preserving algorithm. Distinguish cross-mode matched-input parity from within-mode run2run/resume stochastic continuity.

**R3 HIGH: schema-safe later migration.** `restore_grouped_local_state` requires exact sidecar top-level keys and `SegmentProvenance.config_digest` per live record. Use external `MIGRATION_MANIFEST.json` (no extra sidecar keys), source validation then explicit nested + top-level digest re-stamping without touching original source values/bytes; verify strict new-runtime restore after atomic staging; state source/target digest + full exact SHA lineage. Freeze rollback/nonpublication semantics. No implementation until separately authorized.

**R4 MEDIUM: Objective and FQN gradient coverage.** Inspect actual two-pair resolved `model.lbl.coeff_*`/method, `sample_level_loss_averaging`, vision/action/inner term reduction and effective optimizer allowlist. Provide exact total=weighted_component+aux comparator; explain if auxiliary is OFF with runtime evidence, else how batch-dependent auxiliary's non-additivity is tested. No loss-from-call-count shortcut. Per-FQN include zero/missing/nonfinite and all selected generation/action/local groups, both rank-shard and targeted full gather.

**R5 MEDIUM: numerical threshold details.** Freeze actual tensor-dtype-aware elementwise/norm/cos formula, near-zero epsilon and zero reference handling, deterministic numerical floor when run2run envelope=0, group-specific aggregation and rules before any GPU test. The old V2 historical relative norm figure is not a new V3 pass threshold.

**R6 MEDIUM: terminal partial.** Do not assert 256 valid consumers/rank unconditionally: `member_counts = sum(valid_count)` and terminal episodes may be partial. Assert actual `n_window <=256` and per-rank exact consumer parity for each frozen next-window plan; retain two native calls/member (one per GA). Include a separate terminal-partial witness.

**R7 MEDIUM: provenance / canonical doc.** In fresh *docs-only* isolated checkout fetch `origin/V3` and the **existing** request `docs/collab/chatgpt/requests/2026-10-13_DS_PRO_revise_GateB_index8_packed128_checkpoint_migration_plan.md`; the earlier “request absent” claim came from an outdated or mismatched checkout. The revised plan itself currently is NOT in `origin/V3`. Supply exact committed plan path and doc SHA, but do not alter formal implementation pair or Formal30k tree.

## Deliverable & authorized scope

Return `DS_PRO_V3_PACKED128_GATE_B_AND_ITER1300_MIGRATION_REVISED_PLAN_ROUND2_2026-10-13.md` (committed in docs-only V3 path, or provide full text plus exact source digest when commit is unavailable). Include comparator pseudo-code/data authority, truly executable command once harness is reviewed, two distinct gate matrices (GPU parity vs migration), per-condition fail-closed criteria, fixed tolerances, resource gate, source immutability.

This is **DESIGN-ONLY / READ-ONLY** authorization. DS must not change production/test code, launcher, Gitlink or Root implementation; must not run GPU/torchrun/Nsight, load/rewrite production checkpoint, touch formal worktree/latest pointer, or restart Formal30k. Return full proposal for GPT independent review; Owner separately authorizes every subsequent real execution.
