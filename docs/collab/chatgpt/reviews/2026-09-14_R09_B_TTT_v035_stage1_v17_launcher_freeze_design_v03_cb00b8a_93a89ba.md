# ChatGPT Review — Stage-1 v1.7 launcher freeze design v0.3

- Date: 2026-09-14
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`
- Formal root: `cb00b8ae9702a8c8739673bc90ae287d1282ced6`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Requested positive verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC`

## Verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_launcher_freeze_design_v0.3.md:85)`

Blockers: **1 HIGH Design/Authority**. Production implementation blockers: 0. Evidence-only blockers: 0. Child/runtime blockers: 0.

## Scope and pair verification

The formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`. The delta from prior same-Gate rejected pair `699e8567669187faadf1c46b36bff02eabb0206e / 93a89ba...` is docs/task/review bookkeeping only plus the v0.3 design; no launcher-replay implementation, child/runtime mutation, Stage-1 request construction, or real execution is present.

The prior HIGH is closed: `ReplayBinding.parser_replacements` is now frozen as `(flag, expected_old_value, new_value)` and the canonical table independently targets `--cwd` and `--bootstrap-project-root`, so their byte-identical old values are no longer ambiguous. The contract also requires unique target flag, exact adjacent old value, exact one-position replacement, zero pre-existing owner-FD flag and one adjacent owner-FD insertion. Gate identity, requested verdict, exact two future implementation paths, pure/no-I/O scope, v1.6 consumed/no-retry boundary, expected parser identity and expected outer identity are all correctly frozen.

## HIGH — canonical source replacement table cannot reproduce the declared outer payload

The v0.3 design declares the source table after parser splice to be the complete ordered canonical authority, but it lists only four substitutions:

1. formal root SHA;
2. clean-root suffix;
3. adapter blob OID;
4. bootstrap-contract SHA.

The exact rebound launcher base `08d5828cdb4c12afa3b798ff01826c91ceb8755a:docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py` still contains additional outer-source self-check literals outside `RAW[2]`:

- `boot(s)` requires bootstrap raw length/hash `7538 / 7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8`;
- `main()` requires `RAW[2]` parser length/hash `2427 / 72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2`.

The frozen v1.6 target identities are instead:

- bootstrap `9406 / ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097`;
- parser `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`.

Splicing the new parser changes the `RAW[2]` literal but does not update `main()`'s old parser length/hash guard. Likewise, replaying the adapter/formal/clean/contract substitutions does not update `boot(s)`'s old bootstrap length/hash guard. Therefore the exact v0.3 source table, as frozen, cannot mechanically reproduce the design's declared outer payload `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`; a conforming helper must either fail the final outer identity check or produce an outer payload with stale runtime self-check authority.

This is Design/Authority, not Evidence: the canonical replay input itself is incomplete.

## Exact acceptance

Keep the flag-aware parser table unchanged. Extend the frozen ordered source replacement table to include the remaining exact rebound identities needed by the outer source:

- bootstrap raw length: `7538 -> 9406`;
- bootstrap raw SHA-256: `7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8 -> ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097`;
- parser/RAW[2] length: `2427 -> 2336`;
- parser/RAW[2] SHA-256: `72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2 -> 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`.

Each source substitution should retain the existing exact-one-match/fail-close semantics. The direct canonical round-trip witness must consume the complete frozen parser and source tables and prove exact final outer bytes/SHA `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`; include drift negatives for each newly frozen source identity.

No redesign is otherwise required. Preserve the exact two implementation paths, pure stdlib/no-I/O helper, no `main()`, no Git/path/FD/network/exec, caller-side formal Git-blob verification, zero-to-one owner-FD insertion, v1.6 authority consumed/no retry, fresh observation requirement for any future v1.7 request, and all child/GPU/training/downstream prohibitions.

## Authorization boundary

This review authorizes **no implementation**, no v1.7 request construction, no Stage-1 retry/materialization, no real source/checkpoint/data/cache I/O, no child/runtime mutation, no GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.
