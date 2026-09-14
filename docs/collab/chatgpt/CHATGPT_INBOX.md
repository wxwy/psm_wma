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

- immediate prior live blob SHA: `b54737c05fdb13cae30810ddc998bc1dcfc09f71`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Authority-root causal worktree identity design v0.5 APPROVED

Formal pair:
- root design SHA: `019643a9b17ebdda8f74b5c5fac90cb37c23f18f`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_authority_root_causal_worktree_identity_design_v05_019643a_93a89ba.md`

Canonical review commit:
`9130fab4dbece3b93d4e5e7838b3f54fa6c6af3d`

Current blockers: `0`; child/runtime blockers: `0`.

Closure summary:
1. The v0.4 add target `/proc/self/fd/6/.` remains approved and leaf-capability-derived, with exact FD6 inheritance, no `clean_name` lookup, no global fallback, and post-Git triple identity proof.
2. The v0.4 cleanup HIGH is closed by removing destructive cleanup from this Gate entirely. After `worktree add` has been invoked, fail paths may only revalidate retained FD7/FD9/parent-entry identity, close owned descriptors, preserve A / Git administrative metadata / foreign B if present, and return `ROLLBACK_INCOMPLETE`.
3. No `git worktree remove`, `rmtree`, `unlink`, `rename`, mutable `<clean>`, canonical registration path, parent+name, global CLEAN, cwd, or procfd delete fallback is permitted after post-add failure.
4. The unsupported retained-leaf native remove result is used only to select this conservative fail-closed contract; it does not authorize a global-path fallback.
5. Required CPU/static witnesses cover unsupported leaf-native-remove handling, same-parent cleanup-resolution race with foreign-B preservation, normal post-add failure preserving A+metadata with `ROLLBACK_INCOMPLETE`, and descriptor/capability hygiene with no cleanup Git child spawned.
6. Any future residue recovery requires a separate recovery-design Gate and exact reviewed pair.

Scope reminder: this approval authorizes only the next root-only temporary-fixture CPU/static implementation/tests within the frozen authority-root launcher/payload allowlist. It does not authorize real Git/worktree/materialization, source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, checkpoint write, or any real materialization request.

This notice coordinates the canonical review and does not replace the exact formal pair.
