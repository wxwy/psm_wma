# ChatGPT independent design review — R09-B TTT v0.3.2 active wiring v0.11

## Verdict

`REQUEST_CHANGES`

## Formal target

- root/design SHA: `59609f14bcd56d92629db04dc88f1837c5055baa`
- child/Gitlink: `dce279a966b6feef39ceb269cc064f6cd8f2240f`
- request/bookkeeping HEAD observed before review write: `332b4c08309bf615551bd90e7d6ebecb78a81ff5`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.11_2026-09-05.md`

v0.10 approval remains valid for its frozen scope. This review covers only the v0.11 terminal-provenance extension.

## Blocking finding

### HIGH-1 — manifest tail truncation contradicts the frozen terminal verifier invariant

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.11_2026-09-05.md` §2.1-2.2 / §4; `tools/g0/build_r09_b2_stream_manifest.py` current fixed-record loop; `tools/g0/verify_r09_b2_stream_manifest.py` fixed expected-count arithmetic.

v0.11 correctly forbids marking the maximum `start_frame` merely present in the manifest as terminal; `is_episode_end=true` must denote the dataset's real last valid window. But the current builder emits exactly `optimizer_updates * grad_accum * max_samples_per_batch` records and can stop in the middle of the final shuffled episode block. In that valid construction, the trailing `(suite, epoch, episode_index)` group contains no real terminal row.

The same v0.11 then freezes verifier behavior requiring **every** such group to contain exactly one `is_episode_end=true`, and its acceptance explicitly includes a block-midway truncation negative case. Those requirements cannot all hold simultaneously: the builder must either fabricate a false terminal (forbidden) or the verifier must reject a manifest the builder can legitimately produce.

This also leaves the TTT lifecycle undefined at end-of-manifest: a trailing incomplete episode may leave an open terminal remainder with no real terminal signal.

**Frozen-contract violation:** v0.11 real-terminal provenance rule + verifier exactly-one-terminal-per-group invariant + current fixed record-count construction.

**Acceptance:** freeze one coherent tail policy before implementation. For example: (A) ensure the manifest always ends on a true episode boundary and define how record_count / optimizer-update accounting changes, or (B) explicitly permit only the final truncated group to have zero terminal and freeze end-of-stream abort/cleanup semantics so no pending Local transaction leaks. Add CPU/static fixtures proving the chosen policy for a manifest ending mid-episode, with no false terminal and deterministic lifecycle closure.

## Accepted / unchanged

- manifest-provided `is_episode_end` is the correct provenance direction;
- wrapper additive attach + missing-key fail-closed is acceptable;
- model-side required-key check when Local TTT is enabled is acceptable;
- v0.10 approved scope remains valid and is not reopened by this blocker.

## Scope after this verdict

Allowed remediation is docs/status/ledger only for `G0-R09-B-TTT-V032-ACTIVE-WIRING-DESIGN-V011-TERMINAL`.

No authorization is granted to modify the three newly proposed v0.11 files until a remediated design receives fresh same-pair review. Existing v0.10 CPU/static implementation scope remains separately authorized.
