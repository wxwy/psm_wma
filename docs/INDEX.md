# PSM-WMA Documentation Index

This repository intentionally keeps historical design, Gate and review material. Use the layers below instead of browsing all files alphabetically.

## 1. Current truth — read these first

- **Corrected V3 design authority:** `build/PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md` — Owner-confirmed latest Cosmos RoboCasa/raw15 host + V2 Local-TTT; cache-first shared composite latent; H_pred/R default16; implementation still pending.
- **Current Corrected V3 Phase 2 authority:** `build/PSM-WMA_V3_phase2_raw15_state15_hpred16_design_v1.1_2026-10-05.md` — GPT-frozen official raw15/state15 and H_pred16/VAE cache contract; supersedes the damaged, uncommitted v1.0. This docs-only freeze does not implement Phase 2 or authorize ds/GPU, training or simulation.
- **Closed Corrected V3 Phase 1B authority:** `build/PSM-WMA_V3_phase1b_cache_source_binding_design_v0.4_2026-10-05.md` — GPT-frozen cache-to-flat-source binding design; closure review: `collab/chatgpt/reviews/2026-10-05_V3_phase1b_closure_d7aa5673_21e60d6e.md`.
- **V3 supersession:** earlier migration v1.0/v1.1 and their B1/iter500/current-frame/streaming execution Gates are historical and superseded by v3.0. Publishing v3.0 does not approve the existing child implementation or authorize training/evaluation.
- `../README.md` — project overview and entrypoints
- `../PROJECT_STATUS.md` — current SHA, readiness and validated metrics
- `current/architecture.md` — current system architecture
- `current/local_memory.md` — canonical Local Memory / TTT semantics
- `current/training.md` — train and resume workflow
- `current/evaluation.md` — LIBERO evaluation workflow
- `current/experiments.md` — current experiment matrix and evidence

For Corrected V3, read v3.0 first; conflicting older operational summaries do not override the Owner-confirmed design or the newest exact-pair review/handoff.

## 2. Canonical design authority

- `build/PSM-WMA_00_project_proposal_v1.4_frozen.md`
- `build/PSM-WMA_01_technical_survey_v1.7_frozen.md`
- `build/PSM-WMA_02_detailed_design_v2.1_frozen.md`
- `build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md`
- `build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.9.md`
- `build/PSM-WMA_Local_Memory_v0.3.5_active_route_member_shape_refreeze_design_v0.3.md`
- `build/PSM-WMA_Local_Memory_A2_delivery_runbook_2026-09-18.md`
- `build/PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md` — current Corrected V3 design authority; production conformance requires subsequent implementation and Evidence.
- `build/PSM-WMA_V3_migration_detailed_design_v1.1_2026-10-04.md` — historical B1/iter500 migration design, superseded by v3.0; not an execution authority.

## 3. Historical engineering record

`build/` also contains superseded versions, implementation designs, source audits, remediation plans and Gate runbooks. They are retained for provenance. A newer frozen/refrozen document or an explicit durable decision in `../MEMORY/DECISIONS.md` supersedes older conflicting text.

`collab/` contains agent inboxes, independent reviews, feedback and archives. It is useful for reconstructing why a decision was made, but it is **not** the recommended way to learn the current architecture.

## 4. Machine-readable evidence

- `../artifacts/CANONICAL.json` — authoritative pointers
- `../artifacts/g0/sync_a2_final_verification_2a9df880_v3.json` — engineering verifier
- `../artifacts/g0/a2_long_run_readiness_2a9df880/a2_long_run_readiness_v1.json` — long-run readiness verifier

## 5. Internal ledgers

- `../TODO.md` — current task queue
- `../SESSION.md` — execution / handoff ledger
- `../MEMORY/DECISIONS.md` — durable engineering decisions
- `../AGENTS.md` — agent collaboration and execution governance; Corrected V3 role overrides are recorded in v3.0 and the newest canonical handoff.

These files are operational infrastructure, not the project introduction.
