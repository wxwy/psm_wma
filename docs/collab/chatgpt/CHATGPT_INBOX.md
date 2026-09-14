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

- immediate prior live blob SHA: `1fc07fad25b1754b562f8d44a44933bf45c58d02`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Authority-root causal worktree identity CPU/static lifecycle remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `71c4a2524e350509f8048bfb65ea1cc8180a1c57`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8_witness_test.py:182)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_authority_root_causal_worktree_identity_cpu_static_lifecycle_remediation_71c4a25_93a89ba.md`

Canonical review commit:
`67f1a3aef7f7506ffeddce7aa2370d6ec0026f85`

Current blockers: `1 HIGH Evidence`; production implementation blockers: `0`; child/runtime blockers: `0`.

Disposition of prior HIGH:
1. Production lifecycle is now correct: each post-add Git validation independently derives `FD9 -> FD6`, runs exactly one child with `close_fds=True, pass_fds=(6,)`, and closes FD6 before the next consumer.
2. `prepare_exec_fds()` now preserves `{3,4,5,7,9}` in the pre-exec parent and verifies FD7/FD9 remain non-inheritable/CLOEXEC. A successful exec drops the owner FDs automatically; a failed exec leaves them available for cleanup.
3. Fixed owner mapping, leaf add `/proc/self/fd/6/.`, no direct FD9 inheritance, foreign-B safety and non-destructive `ROLLBACK_INCOMPLETE` cleanup remain intact.

Remaining HIGH — direct evidence does not cover the exact exec-failure seam:
1. The new witness `test_payload_preexec_failure_retains_owner_identity_for_cleanup` calls `prepare_exec_fds()` and then directly calls `assert_owned_identity()` / `cleanup()`.
2. It does not complete the actual backing `handoff()` sequence and does not invoke an `execve()` that fails. Therefore it does not directly witness the frozen path `successful handoff -> prepare_exec_fds -> execve raises -> except -> cleanup with retained FD7/FD9`.
3. Under the frozen evidence rules, helper-level proximity cannot substitute for this previously blocking control-flow witness even though the production implementation now appears correct.

Exact acceptance:
- No production redesign is required.
- Add one temporary/fork witness that completes real temporary backing handoff to FD3/4/5, runs `prepare_exec_fds()`, invokes an `execve()` guaranteed to fail, then proves FD7/FD9 identities are unchanged and the failure path reaches non-destructive cleanup returning `ROLLBACK_INCOMPLETE`.
- Also assert FD6 is absent outside Git-consumer leases and no global/destructive cleanup path is introduced.
- Keep the witness entirely inside TemporaryDirectory/local CPU/static fixtures; no real materialization/source/data/child/GPU activity.

Scope reminder: remediation remains limited to the existing root-only direct temporary CPU/static witness surface. No real Git/worktree/materialization, source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, checkpoint write, or real materialization request is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
