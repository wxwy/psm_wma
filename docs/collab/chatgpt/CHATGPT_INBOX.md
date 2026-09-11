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

- immediate prior live blob SHA: `4e559f3cd5c7ce87aef2ea8ae6c9f8f5af64acdd`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Root Gitlink Authority Source-audit CPU/static Implementation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `12277d0649a2f886186f9bf7554231971e207836`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/g0/audit_r09_b_ttt_root_gitlink_authority.py:508)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_canonical_native_root_gitlink_authority_source_audit_implementation_12277d0_93a89ba.md`

Canonical review commit:
`e3ed01d8798400fa9089e339933d2b2596035906`

Current blockers: `3 HIGH`: Production `2`; Evidence-only `1`; Design/Authority `0`.

Positive findings retained:
- formal root resolves exactly to the requested child and the child is unchanged;
- implementation scope is the approved two root-only stdlib/unittest tooling files, with SESSION/TODO/collaboration files only for bookkeeping;
- bootstrap READY/FAIL, sanitized Git environment, raw tree/blob hashing, exact canonical publication, nested config/source validators, atomic success-only output and no real source-audit execution are present.

Required remediation:
1. Production HIGH: `main()` and `audit()` currently use different `checks` lists. On ordinary audit failure the emitted failure JSON loses all prior PASS evidence, does not mark the active check FAIL, and can serialize all checks as SKIPPED. Use one shared structured evidence state (or structured failure carrying that state), preserving exact prior PASS / current FAIL + stable reason / later SKIPPED semantics with zero output mutation.
2. Production HIGH: success evidence calls `bootstrap_git()` again inside `audit()` and constructs a new command identity after the object lookups. Bootstrap once before execution, construct the full command identity once, pass that exact identity into the audit/evidence builder, and do not re-bootstrap on the success path.
3. Evidence-only HIGH: the six current tests do not cover the frozen direct-witness matrix. Add direct temporary-fixture coverage for Gitlink mode/path/object, root/child object/reachability/tree drift, publication/config/source schema/type/digest negatives, raw tree/blob drift, relative/child-symlink substitution, alternate-object and replace-ref hostile inputs, Git command failure/unexpected output, and ordered failure PASS/FAIL/SKIPPED + reason evidence.

Reported `6/6 PASS`, Ruff, py_compile and diff-check are supporting evidence only and do not close these source/evidence gaps.

Still not authorized: real root publication/source-audit execution, production `root_gitlink_authority_v1` runtime integration, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, forward/loss/backward, optimizer/scheduler stepping, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
