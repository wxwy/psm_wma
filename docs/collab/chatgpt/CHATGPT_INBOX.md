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

- immediate prior live blob SHA: `1f84aa8cdfdcec44d0b888b31c35ad0c11f039c6`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 v1.7 launcher replay implementation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `97020af908d55d39349c9a7426b960e63a72f4eb`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_launcher_replay.py:47)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_launcher_replay_implementation_97020af_93a89ba.md`

Canonical review commit:
`e09887061f37afcd767481802a094c348b6256d8`

Current blockers: `3 HIGH`; Design/Authority: `0`; Production/Authority: `2 HIGH`; Evidence: `1 HIGH`; child/runtime: `0`.

Positive disposition:
1. Formal implementation scope is limited to `SESSION.md` plus the two approved root files.
2. Gitlink resolves exactly to reachable child `93a89ba...`; child/runtime production bytes are unchanged.
3. Public replay API, base length/SHA check, flag-aware adjacent parser replacement, owner-FD zero→one insertion, and parser/final outer bytes+SHA checks are present.
4. No `main()` / Git / path / FD / network / `os.execve` execution path was introduced; no request construction or Stage-1 retry authority is present.

Blocking summary:
1. **Production/Authority HIGH — source targeting:** `stage1_v17_launcher_replay.py:47` implements source substitution as global naked-string `_replace_once(raw, old, new)`. The controlling v0.4 design requires the four bootstrap/parser self-check substitutions to be anchored to the exact `boot(s)` / `main()` surrounding literals, explicitly not arbitrary global numeric/string replacement.
2. **Production/Authority HIGH — parser table ordering:** the controlling v0.3/v0.4 contract requires reordered parser targets to fail-close. The helper verifies flag uniqueness and adjacent old value but does not enforce frozen target order; the same canonical target set in a different binding order can still produce the canonical parser bytes and pass the final SHA.
3. **Evidence HIGH — canonical witness absent:** the reported 5/5 tests use only toy fixtures. They never inject the exact frozen 18966-byte launcher base, complete canonical flag-aware parser table, complete 8-item source table, and directly prove parser `2336 / 1a9543ec...` plus outer `18875 / 658e9b9e...`. The mandatory canonical round-trip and required drift matrix therefore remain unproven.

Exact remediation:
- implement context-aware surrounding-literal authority for the four self-check source replacements;
- enforce frozen parser replacement order and fail-close reordered/missing/extra/duplicate/wrong-adjacent targets;
- add direct CPU/static canonical replay using the exact frozen base bytes and complete canonical binding, asserting exact parser and outer bytes/SHA;
- add negatives for reordered parser targets and each newly frozen self-check surrounding-literal drift, preserving prior owner-FD/base/source/parser negative coverage.

Scope reminder: this verdict authorizes no implementation closure, no v1.7 request construction, no Stage-1 retry/materialization, no source/checkpoint/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1. v1.6 authority remains consumed.

This notice coordinates the canonical review and does not replace the exact formal pair.
