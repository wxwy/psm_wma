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

- immediate prior live blob SHA: `79414baceb10c34701e9c5f6307afa320d51012d`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root PASS Lifecycle Remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `bc40191f0e80f98201774cce8a1b551fa2343128`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:289)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_pass_linearization_cpu_static_implementation_bc40191_93a89ba.md`

Canonical review commit:
`a1ec3adf7ce0ccfb13e19a0356fa08f85359b453`

Current blockers: `3 HIGH`.

Prior finding closure:
- no-finalizer PENDING success bypass: CLOSED; `publish_candidate` now rejects `finalizer=None` before ref mutation.
- terminal state member mutability: CLOSED AS WRITTEN; `_AuthorityTerminalState` is now frozen.
- private AcceptedPass: PARTIALLY CLOSED.
- A/B/C crash/restart fail-stop: PARTIALLY CLOSED.

Remaining HIGHs:

1. **The mutable terminal cell itself escapes to the finalizer callback.** `PublicationWitness` and `EvidenceCommit` expose `_terminal`; `_AuthorityTerminalCell.state` is writable. A callback can set `witness._terminal.state = _ACCEPTED_TERMINAL_STATE` and return without seal/evidence/ref witness/guard transition. `publish_candidate()` then sees `commit.committed == True`, skips rollback, preserves refs and returns a witness. Make the semantic pointer transition authority-private and add a direct callback-forgery negative.
2. **`_AcceptedPass` is under-bound.** It currently stores only witness/activation/terminal/token and is constructed before evidence seal and before the v0.10 last exact ref observation. It therefore cannot bind the frozen candidate/binding digest + sealed evidence identity/digest + historical local/remote witness facts. Complete the pre-accept binding and add wrong-evidence/binding/ref-witness/replay negatives, or explicitly return to design to supersede that retained capability contract.
3. **The real B crash window still rolls back and restart classification is not in the CLI path.** If the real guard transition succeeds and an interruption occurs before the terminal pointer swap, `commit.committed` remains false and `publish_candidate()` enters ordinary `_rollback`, contrary to v0.10's permanent B fail-stop. The new interruption test raises from `_commit_exact_guard` before a successful transition and does not cover B. `classify_pass_restart()` is also isolated: preflight still rejects existing evidence/guard as generic fresh-path failure and `main()` never invokes the classifier. Implement B fail-stop/no-rollback, wire restart classification into the real entrypoint, and directly test B/C restart and A same-candidate foreign-ref fail-closed semantics.

Formal tree/Gitlink is independently correct for this exact pair: `cosmos-framework` is mode `160000`, type `commit`, exact child `93a89ba61306d840a008813f62f26a34d54850f4`; child commit is independently reachable.

Reported `70/70` CPU tests and static checks are auxiliary evidence only.

Remediation remains strictly limited to the already approved four root tooling/test files and temporary directory/local bare-remote CPU/static tests. No real source/candidate/ref/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 are authorized.

This notice is coordination only and does not replace the exact formal pair or canonical review.