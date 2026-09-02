# R09-B2 P4-v4 execution-preflight v0.4 design review

## Request / design

- Request commit: `fd59f0b332ecae56a687accb2878bd650bc6e673`
- Design commit: `5de996bf2c1e5b5b8ac11300b190d76eae8a21dd`
- Previous ChatGPT review: `d210e0cd9caa92eb9a0f21544e3ed9a7e00901fe`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_STATIC_TOOLS`

This approval is limited to root static tooling and stdlib CPU tests. It does not authorize real preflight execution, staging, candidate generation, record/refreeze, evidence publication, P5 export/compose, torchrun/GPU, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory training.

## Findings

### PASS — candidate PASS payload is now byte-for-byte the final P5 evidence payload

`docs/build/PSM-WMA_R09_B2_P4_v4_execution_preflight_design_v0.4_2026-09-02.md` separates candidate-only identity into non-published `candidate_link.json`. The three published payloads `request.json`, `result.json`, and `verification.json` must already satisfy the existing P5 `load_p4_v4_preflight()` schema and canonical-byte grammar at candidate creation time. Record/refreeze is explicitly forbidden from parsing, rewriting, reserializing, or otherwise transforming those payload bytes.

This closes the v0.3 HIGH where candidate-only top-level fields would have made the candidate bytes incompatible with the exact P5 evidence schema or required a later lossy transform.

### PASS — recurrent and TTT are a single atomic six-blob publication unit

Record/refreeze accepts exactly the ordered backend set `["recurrent", "ttt_fast_weight"]`, with one PASS candidate per backend. Missing, FAIL, poisoned, or duplicate backends block publication. Pair-level shared-source and cross-backend invariants must be reverified before publication.

All six payload files must be published in one commit-or-none Git commit, and post-commit authority remains out-of-band in a later independently reviewed `AUTHORIZED_P4_V4_EVIDENCE` verifier revision. Partial backend publication therefore cannot become P5-authorized evidence.

This closes the v0.3 MEDIUM atomicity blocker.

### PASS — prior provenance / publication blockers remain closed

The design retains the resolvable P4 anchors `f362b824735807278b74ccc553fc8f556598a8d2`, `3d990e6fb65c192f12e3c2b58ae49356d3eba1e7`, and ChatGPT review `4088920d96bfb63cb64e06fe4315e74f7fbe67aa`; P5 evidence Git-authority prerequisite is closed by implementation `3e3a853c61dd32888932041e6afbfac466818e09` and ChatGPT closure `507a343154cb14239f25480927827a5fb05c9c30`.

The design also keeps failure poison/no-retry semantics and prevents P4 payloads from self-authorizing their containing Git commit.

## Implementation hard constraints

1. `candidate_link.json.attempt_id` must equal the enclosing `<attempt-id>` directory component; `backend` must equal the backend directory and payload backend; `run_token` must equal the nested P4 `p4_run.run_token`. Reject mismatch rather than normalize it.
2. PASS payload verification must be byte-oriented: compute hashes from the exact bytes that will later be copied, and refreeze must copy those exact bytes only.
3. Static tests must include transformation negatives such as parse+reserialize, newline/whitespace drift, extra candidate-only top-level key, and link/path mismatch.
4. The future record/refreeze path must start from a full-clean publication worktree and must not convert a failed/partial publication workspace into a later PASS. Actual record/refreeze execution remains a separate Gate.

## Gate decision

`APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_STATIC_TOOLS`

No runtime or publication authorization follows from this design approval.
