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

- immediate prior live blob SHA: `1b9fc2ce3e0b1758386252d1409dda4ec07328cf`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 v1.7 launcher replay parent-binding remediation APPROVED

Formal pair:
- root implementation SHA: `50b0bffeb4c94b0994d7c7bf705077fb51a9e48f`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`

Verdict:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC_IMPLEMENTATION`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_launcher_replay_parent_binding_50b0bff_93a89ba.md`

Canonical review commit:
`fc268cce990b6e5ac60ba386ebb7c4f777bf0476`

Current blockers: `0`; Design/Authority: `0`; Production/Authority: `0`; Evidence/Scope: `0`; child/runtime: `0`.

Closure summary:
1. The prior parent-field bypass is closed for the canonical replay path. The helper freezes canonical base SHA `8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`; when that base is injected, `formal_parent` must equal `08d5828cdb4c12afa3b798ff01826c91ceb8755a` or replay fails as `base_identity` before table mutation.
2. After canonical parent closure, exact parser/source table digests are authenticated before mutation, so extra/no-op/reordered replacement-program bypasses remain fail-closed.
3. The direct `test_canonical_parent_bypass_fails` covers the previously exploitable parent-field drift. Submitted evidence reports `py_compile`, direct unittest `13/13`, and `git diff --check` PASS.
4. Previously closed controls remain: pure/no-I/O injected bytes; embedded canonical base `18966 / 8b0fad...`; flag/adjacent parser targeting and order; zero→one owner-FD insertion; `boot()`/`main()` function/span source targeting; exact parser `2336 / 1a9543ec...`; exact outer `18875 / 658e9b9e...`; full base/RAW/source/parser/owner/table/relocation failure matrix.
5. Formal root Gitlink resolves exactly to reachable child `93a89ba...`; child/runtime production bytes are unchanged.

Authorized consequence:
- this exact CPU/static launcher-freeze implementation is closed;
- a future v1.7 exact execution request may only be **constructed separately** after the project’s normal coordination requirements, using fresh observations, and must undergo its own exact-pair request review before any execution authority exists.

Still explicitly NOT authorized by this close verdict:
- Stage-1 retry/materialization;
- revival/reuse of consumed v1.6 authority;
- source/checkpoint/manifest/data/cache I/O;
- child/runtime/config mutation;
- GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
