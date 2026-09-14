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

- immediate prior live blob SHA: `e3f4854a58467e0bcce38c2cfa84d4bf844d3d4f`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Authority-root causal worktree identity CPU/static fixed-owner remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `85a39d6243bb4bcc3e260ba3eb4279c52508d79f`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py:176)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_authority_root_causal_worktree_identity_cpu_static_remediation_85a39d6_93a89ba.md`

Canonical review commit:
`e4c6e24a679cb67f6b3ff17aa644fe718c4e246f`

Current blockers: `1 HIGH Production/Authority+Evidence`; child/runtime blockers: `0`.

Disposition of prior HIGH:
1. The arbitrary owner-FD / backing-collision portion is closed. The remediation now freezes parent owner FD7, clean owner FD9, backing `{3,4,5}`, Git target FD6, bootstrap FD8, uses collision checks, `F_DUPFD_CLOEXEC >=10`, fixed rebind and directory identity proof.
2. Leaf add remains exact `/proc/self/fd/6/.`; retained FD9 is not passed directly to Git; handoff targets are constrained to backing FD3/4/5; non-destructive `ROLLBACK_INCOMPLETE` cleanup and foreign-B preservation remain intact.
3. The new low-FD witness proves fixed 7/9 owner mapping and closure of a standalone FD6 lease.

Remaining HIGH — capability lifetime is still not exact:
1. `assert_worktree()` opens one `consume_leaf()` lease and runs both `rev-parse` and `status` inside it. FD6 therefore remains open in the parent after the first Git child returns and is reused by the second. The frozen contract requires every Git consumer to independently derive FD6 from FD9 and close FD6 immediately after that child returns.
2. After handoff, `close_to_keep({3,4,5})` explicitly closes FD7/FD9 before `os.execve(...)`. Because FD7/FD9 are already non-inheritable/CLOEXEC, they should remain available in the pre-exec process and disappear automatically on successful exec. With the current order, an `execve()` failure reaches cleanup after retained owner capabilities have already been lost, so v0.5 retained-FD owner revalidation cannot occur.
3. Current 14-test evidence does not prove FD6 is absent between the two post-add Git children and does not force post-handoff `execve()` failure while checking FD7/FD9 remain intact for cleanup.

Exact acceptance:
- Re-derive `FD9 -> FD6` separately for every Git subprocess, including separate leases for `rev-parse` and `status`; exact `close_fds=True`, `pass_fds=(6,)`, and FD6 closed after each return.
- Keep FD7/FD9 open but non-inheritable/CLOEXEC through the `execve()` attempt. Close other unwanted descriptors while preserving `{3,4,5,7,9}` in the pre-exec process; successful exec drops 7/9 automatically, failed exec leaves them available for cleanup identity proof.
- Add direct temporary witnesses proving FD6 is closed between post-add Git children and proving forced `execve()` failure retains exact FD7/FD9 identities for non-destructive `ROLLBACK_INCOMPLETE` cleanup.
- Preserve all already-correct fixed-owner mapping, leaf add, foreign-B safety and no-destructive-cleanup behavior.

Scope reminder: remediation remains limited to the approved root-only launcher/payload and direct temporary CPU/static witness surface. No real Git/worktree/materialization, source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, checkpoint write, or real materialization request is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
