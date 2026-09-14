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

- immediate prior live blob SHA: `51a464e64a046d04e99733dc5b0918707bd7a206`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Authority-root causal worktree identity CPU/static exec-failure witness APPROVED

Formal pair:
- root implementation/witness SHA: `b3595395427114f73ff53a19a0c2b9180e39905f`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`

Verdict:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_authority_root_causal_worktree_identity_cpu_static_exec_failure_witness_b359539_93a89ba.md`

Canonical review commit:
`b1cdbd391bc5810130834e11f2d049f03b4a0144`

Current blockers: `0`; production implementation blockers: `0`; evidence blockers: `0`; child/runtime blockers: `0`.

Closure summary:
1. The prior lifecycle production HIGH was already closed at root `71c4a252...`: each Git consumer independently leases `FD9 -> FD6 -> child(pass_fds=(6,)) -> close FD6`, and `prepare_exec_fds()` preserves non-inheritable FD7/FD9 through the exec attempt.
2. The only remaining blocker was direct evidence for the exact seam `successful backing handoff -> prepare_exec_fds -> execve failure -> retained-owner cleanup`.
3. Formal root `b359539...` is witness-only: it changes only `...authority_root_launcher_payload_v0.8_witness_test.py`; production payload bytes are unchanged.
4. The revised forked witness now performs real temporary `handoff()` for all backing FD3/4/5, calls `prepare_exec_fds()`, invokes a deliberately nonexistent executable and requires `FileNotFoundError`, then reaches `cleanup()`.
5. Because `cleanup()` re-runs `assert_owned_identity(owned)` before returning `ROLLBACK_INCOMPLETE`, the passing witness directly proves FD7/FD9 remain usable after failed exec; it also checks FD7/FD9 remain non-inheritable.
6. Fixed owner mapping, exact `/proc/self/fd/6/.` leaf add, per-child FD6 lifecycle, no direct FD9 inheritance, foreign-B preservation, and non-destructive cleanup remain unchanged.

Scope reminder: this approval closes only the exact root temporary CPU/static implementation/witness Gate. It does not authorize real Git/worktree/materialization, source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, checkpoint write, or any real materialization request.

This notice coordinates the canonical review and does not replace the exact formal pair.
