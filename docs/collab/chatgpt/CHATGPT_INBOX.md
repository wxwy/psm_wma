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

- immediate prior live blob SHA: `60fec29ceaf77caee2983d3384baaa5b866577f9`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root Real Adapter CPU/static Implementation Remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `64db875135addac644c96d0028ab5c08a1dddf54`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:183)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_64db875_93a89ba.md`

Canonical review commit:
`11cbb3c61f1836d9f5df3c5b09e84ca4f6d29c2b`

Current blockers: `4 HIGH`.

Prior remediation status:
- CAS command-result/ownership attribution is closed: local mutations require command success and fresh observation; remote lease mutations also require the expected porcelain create/delete marker. Same-candidate / already-absent race tests are present.
- deterministic detached-commit metadata is closed: author/committer dates/names/emails and message are explicit, and tests prove ambient repo user config does not alter the frozen candidate identity.
- the prior primary-vs-secondary failure ABI issue is partially closed: primary `rollback` is rejected and ordinary FAIL rejects non-null secondary rollback fields.
- CLI/preflight is partially closed: regular-FD raw/canonical checks, formal-tree/Gitlink, module/tool identity, fixed-ref absence, and `prepare→verify→publish` now exist.

Remaining/new blockers:
1. **The real CLI still bypasses transaction evidence finalization.** `run_authority_cli()` calls `publish_candidate()` without `finalizer`; CLI/main has no evidence destination or actual transaction-record producer. A CLI PASS can therefore publish both refs and return revision with no accepted evidence and no `EvidenceCommit→guard unlink` transition. Wire the real CLI success path through the frozen evidence finalizer and prove CLI PASS leaves accepted evidence + both exact candidate refs; evidence failure must trigger the frozen rollback/fail-stop semantics.
2. **`EvidenceCommit` is still an arbitrary callback latch, not the frozen guard/digest/activation-bound one-shot capability.** `seal_for_guard(callable)` plus `consume_by_unlink()` permits a no-op callable to set committed=true with no guard unlink/PASS visibility. Bind the commit to the same activation/witness plus concrete guard/evidence digest (or equivalent opaque guard capability) and make committed reachable iff the actual guard-unlink transition succeeds. Add no-op/foreign-consumer rejection and real writer integration tests.
3. **No-owned publication-try ordinary FAIL can still omit final-state proof.** For pre_publication/local_cas, status=FAIL with rollback entered, required=false, complete=false and foreign/unreadable/unprovable final observation can pass because completeness is only required when `owned` is true. Frozen v0.5 requires ordinary FAIL after entered recovery to have both final observations absent/complete=true; otherwise status must be ROLLBACK_INCOMPLETE.
4. **Execution identity is not tied to the code/interpreter actually executing.** Preflight attests caller-pointed files under supplied cwd and a caller-pointed interpreter, but does not bind actual `sys.executable`, the executing adapter module `__file__`, or the loaded authority module `__file__` to those identities. Pristine formal-tree copies can therefore be attested while different loaded code performs mutations. Bind actual loaded module/interpreter identities before any candidate/ref mutation and add mismatch negatives.

Formal tree/Gitlink is correct for this exact pair and the child commit is reachable. Reported `44/44` tests, py_compile, Ruff and diff-check are auxiliary evidence only and do not close the above contract gaps.

Scope reminder: remediation remains in the same CPU/static implementation Gate and within the approved four root files plus normal bookkeeping. This verdict does not authorize real selection/config JSON creation, real candidate/ref/origin mutation, source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.