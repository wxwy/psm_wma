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

- immediate prior live blob SHA: `179c27f40bb839cb35e8858a318399da4a8552a4`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Authority-root causal worktree identity design v0.2 REQUEST_CHANGES

Formal pair:
- root design SHA: `c6ac4639d2abb6bb19263e1ee923902419844fd5`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.2.md:26)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_authority_root_causal_worktree_identity_design_v02_c6ac463_93a89ba.md`

Canonical review commit:
`dbd591d4088f2dc7b13c0f2aafda8990597f0266`

Current blockers: `1 HIGH Design/Authority`; child/runtime blockers: `0`.

Blocking summary:
1. v0.2 correctly removes the mutable global absolute CLEAN target and freezes an inherited parent FD6, exact `close_fds=True` / `pass_fds=(6,)`, CLOEXEC handling, and `/proc/self/fd/6/<clean_name>` with no global fallback. This closes global-parent-path redirection.
2. However `/proc/self/fd/6/<clean_name>` still re-resolves the mutable `clean_name` entry inside the retained parent. If that entry is replaced after the pre-call identity check but before Git resolves the target, Git can populate a foreign replacement B while retained `clean_fd` still names owner A; post-Git triple revalidation only detects the mutation afterwards.
3. This directly contradicts v0.2's own required `target-resolution race` witness, which requires clean-entry replacement to leave the foreign inode untouched.

Exact acceptance:
- Bind Git's actual mutation target to the retained clean-root **leaf inode**, not only to its parent directory. Prefer a dedicated inherited duplicate of `clean_fd` with an exact procfd leaf target if temporary real-Git fixtures prove it works, or another primitive with equivalent immutable-leaf semantics.
- Freeze exact inherited-FD lifetime, `close_fds` / `pass_fds`, CLOEXEC, collision rules, and no fallback to parent+name/global CLEAN.
- Add an actual temporary local-Git race witness that replaces `parent_fd/clean_name` within the same retained parent before Git target resolution and proves Git either populates only the retained owner inode or fails before touching the foreign replacement.
- Separately retain the global-parent replacement witness, owner-limited cleanup, and administrative metadata validation without dependence on ephemeral procfd names after the target capability lifetime.

Positive retained points: docs-only scope, `mkdirat` + immediate no-follow `clean_fd`, FD6 exact inheritance constraints, no PATH/shell/ambient fallback, and `ROLLBACK_INCOMPLETE` for unprovable ownership are directionally correct and should be preserved.

Scope reminder: this verdict authorizes only another docs-only redesign. No real Git/worktree/materialization, source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
