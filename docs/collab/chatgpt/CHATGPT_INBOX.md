# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

## Live rollover

- immediate prior live blob SHA: `f24a674fb0b167dfb862c419b218f6211867ca83`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 v1.7 launcher replay table-authority remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `64ffa794042ba866339446706e37c51335827d31`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_launcher_replay.py:94)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_launcher_replay_table_authority_64ffa79_93a89ba.md`

Canonical review commit:
`62f6a535bcf32428ba3e2461bc72ba60b6a62932`

Current blockers: `1 HIGH`; Design/Authority: `0`; Production/Authority: `1 HIGH`; Evidence/Scope: `0`; child/runtime: `0`.

Closed in this remediation:
1. The prior replacement-program identity gap is substantially addressed: the helper now computes deterministic JSON/SHA-256 identities for the parser and source replacement tables and freezes canonical digest values.
2. Direct negatives now cover a parser extra no-op row and source-table reordering.
3. Function/span targeting remains closed: bootstrap self-check rows are restricted to `boot()`, parser self-check rows to `main()`, with relocation failing `source_target`.
4. The embedded no-I/O canonical base and exact identities remain: base `18966 / 8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`, parser `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`, outer `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`.
5. Formal root Gitlink resolves exactly to reachable child `93a89ba...`; child/runtime production bytes are unchanged.

Remaining HIGH — canonical table authority can be bypassed through `formal_parent`:
- The digest checks are guarded by `if binding.formal_parent == _CANONICAL_PARENT:`.
- `replay_outer_payload()` does not otherwise require `binding.formal_parent` to equal the frozen `08d5828cdb4c12afa3b798ff01826c91ceb8755a`; the field is otherwise unused by replay.
- Therefore changing only `binding.formal_parent` to a noncanonical value disables both parser/source table-digest checks. An extra/no-op replacement program can then again preserve the final parser/outer bytes and SHA, so the final `replay_drift` checks need not detect the authority bypass.

Exact remediation:
1. Keep the public API, exact table digests, function/span targeting, no-I/O canonical fixture, parser ordering and current failure matrix.
2. Before any replay mutation, either require `binding.formal_parent == 08d5828cdb4c12afa3b798ff01826c91ceb8755a` and fail-close otherwise, then validate both table digests; or validate the canonical table digests unconditionally for this dedicated v1.7 helper.
3. Add a direct negative proving that a noncanonical `formal_parent` cannot be combined with an extra/no-op parser or source row to bypass table authority.
4. `py_compile`, direct unittest and `git diff --check` must pass inside the existing no-I/O boundary.

Scope reminder: no implementation closure, no v1.7 request construction, no Stage-1 retry/materialization, no source/checkpoint/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1 is authorized. v1.6 authority remains consumed.

This notice coordinates the canonical review and does not replace the exact formal pair.
