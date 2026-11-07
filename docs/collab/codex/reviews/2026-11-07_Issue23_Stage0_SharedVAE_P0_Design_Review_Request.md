# Issue23 Stage0 design handoff — P0 single-instance cost/benefit

Owner date: 2026-11-07 Asia/Shanghai. Request **GPT independent design review**:
`APPROVE_DESIGN_STAGE0` or `REQUEST_CHANGES`. No implementation approval claimed.

## Exact target and provenance

- Requirement: https://github.com/wxwy/psm_wma/issues/23 including latest P0 addendum.
- Task-start official Root V3: `a77f3d4bd8a691435d1935025cc1a9766da646a1`.
- Official Child/Gitlink: `1ca308055fc41fb69efaeb9efaa23808f164a18e`.
- **Child design review commit: `8a170d56014af937b146b35e2b89753313614785`.**
- Root/Child independent branch: `v3-sim-shared-vae-issue23-stage0-20261107`.
- Child delta is six documentation/specification files only, 649 insertions.
- Root Gitlink remains `1ca308055fc41fb69efaeb9efaa23808f164a18e`.

This is not a new runnable Formal Pair. Child design SHA identifies documents;
Root handoff/ledger SHAs identify supporting evidence. Neither updates official
V3, PR4, the running source or checkpoint identities. Child production package
tree `77501c5e1623028cb9ef0826ad772a9d22831785` equals the official baseline.

## Review package

At the exact Child design SHA, read
`docs/designs/issue23_sim_shared_vae_stage0/`:

- `DESIGN.md`: first table is mandatory strict 1Server×1Sim A/B/C P0; architecture,
  causality/trust, numerical/backend, deadlines, ownership, timing and statistics.
- `acceptance_matrix.json`: Stage0→1→2→3 prerequisites and NOT_RUN Gates.
- `recipes/single_latency.json`: A native No-TTT; B original official server_vae;
  C same Local checkpoint as B, Worker B1/wait0, 15 Encode1 + Policy boundary;
  same/split GPU strata, raw timing and paired SR. Optional D is unsupported.
- `recipes/multi_sr_throughput.json`: independent M16/Bpolicy8, 32 total Sims,
  seven Bvae/wait combinations; no barrier; matched throughput comparison.
- `feature_envelope.schema.json`: complete public Lease identity, signed source/
  action/feature/VAE provenance, immutable budgets. Capability is not public data.
- `trace.schema.json`: raw correlated CPU/GPU spans, phase enums and timing strata.

P0 asks how much Local-TTT costs, what blocks execution, and whether paired SR
gain justifies that cost. Total background compute is not added as serial Replan
latency. A vs B/C checkpoint confounding is explicit; B vs C shares exact weights.
18×2 is smoke only. Larger SR, GPU and deployment claims remain separate Gates.
Historical Issue23 performance numbers are labeled reported, not measured here.

## Validation and limits

Command executed once, from `/workspace/work/psm-wma-sim-shared-vae-issue23`:

```bash
/workspace/.venvs/psm-wma-cpu/bin/python \
  /workspace/work/issue23-stage0-evidence/validate_design.py \
  --root /workspace/work/psm-wma-sim-shared-vae-issue23 \
  --evidence-dir /workspace/work/issue23-stage0-evidence/validation-01
```

Exit0, **20 document consistency checks PASS**. No environment overrides, GPU,
network, project/model imports or tests. Uses existing Python3.12 and jsonschema.
Raw report: `docs/collab/codex/evidence/2026-11-07_issue23_stage0/design_validation.json`;
exact validator archived as `validate_design.py.txt`; stdout archived alongside.
Report was produced before Child commit; six content SHA256 values match the
committed package. HEAD fields describe that pre-commit validation state, not a
claimed implementation Pair.

The checks parse five JSON files without duplicate keys, validate both Draft2020
schemas/local refs, recipes/P0/phase consistency, independent sweep and smoke
restrictions, local links, docs-only changes, unchanged Gitlink and protected
production tree IDs. They do not test Worker, model correctness, numerical parity,
RoboCasa, GPU, actual latency/throughput or SR. All these are **NOT_RUN**.

Three read-only collaborator audits identified and then confirmed closure of:
exact Lease field binding/generation/epoch equality; canonical RGB digest bytes;
Stage3 CPU prerequisite for P0; trace phase consistency; true model-owned scan
reference and transitive dataset import disclosure; fatal Worker cleanup proof.
These internal audits do not substitute for GPT's independent design Gate.

## Decisions and next stage

Please review (1) HMAC trust/isolation and loaded-VAE attestation, (2) bit-exact
default/preregistered tolerance procedure, (3) absolute budget before payload,
(4) Policy-owned boundary/private candidate/End recovery, and (5) P0 timing and
paired SR protocols separate from multi throughput. Preregister real checkpoint,
hardware IDs, tolerance if any, latency margin and meaningful SR effect before
hardware execution. Optional same-Local-checkpoint ablation D may be deferred;
existing off/required validators remain intact.

An approved Stage0 unlocks **standalone Worker/protocol and focused CPU/synthetic
implementation only**. Stage2 real Wan/GPU/EGL and Stage3 Action Path integration/
single/multi real runs require their additional Gates. No automatic V3 merge,
official Gitlink change, PR4 modification, training, running-job operations or
large SR evaluation. No Worker implementation has begun in this submission.
