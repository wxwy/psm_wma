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

- immediate prior live blob SHA: `4e69f0540469d4547857a827caea5210f1f1f81f`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root Real Adapter CPU/static Implementation Evidence Remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `2f9fd4bcaec0fd0ea0c6302aa69910e24ce9e378`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:128)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_2f9fd4b_93a89ba.md`

Canonical review commit:
`15e9b4c5bbbb721fbe47495014b3d57bbe8a2e97`

Current blockers: `4 HIGH`.

Prior `64db875...` blocker status:
- CLI PASS evidence transaction is now on the real subprocess execution path.
- every publication-try ordinary FAIL now requires entered recovery + complete final absent proof.
- actual `sys.executable` and loaded adapter/authority module `__file__` identities are bound before mutation.
- `EvidenceCommit` was improved to carry activation/path/digest state, but exact same-activation/guard-identity enforcement is still incomplete.

Current blockers:
1. **EvidenceCommit is not exact-current-activation / exact-guard-identity bound.** A stale uncommitted commit from activation A can be used by activation B's finalizer to seal/unlink B's guard; B's own commit remains uncommitted, so B then rolls refs back after PASS became visible. Guard binding is path-based rather than object identity, so guard replacement can also be unlinked and treated as committed. Bind an authority-verifiable opaque finalization token to the exact current activation/witness/commit, writer-owned guard identity, evidence-path identity and recomputed canonical record digest. Add stale/different activation and guard-replacement negatives.
2. **PASS finalizer does not re-observe fixed refs at the evidence commit point.** `_pass_evidence_record()` hard-codes both refs as candidate based on the earlier `publish_candidate()` post-observation. A ref can drift between that observation and guard unlink, leaving accepted PASS with non-candidate refs. Freshly re-observe local+remote immediately before seal/unlink and bind those actual observations into the evidence record; any drift must stay pre-commit and trigger frozen rollback/fail-stop behavior.
3. **Evidence writer cleanup/publication is not ownership-safe under filesystem races.** On any exception `_cleanup_pending_evidence()` blindly unlinks temp/final/guard paths, so raced/preexisting foreign state can be deleted; `os.replace()` can overwrite a final path created after the initial absence check. Track activation ownership per path and use no-overwrite atomic final publication; preserve all foreign/raced final/guard/temp state. Add direct race tests.
4. **The real CLI still produces no actual FAIL / ROLLBACK_INCOMPLETE evidence.** Failure schemas are only validated through manually constructed test fixtures; `publish_candidate()`/`_rollback()` expose no structured chronology and CLI failures only raise. Expose authority-owned structured terminal outcome data and write truthful canonical FAIL or ROLLBACK_INCOMPLETE records for the frozen phases. Add end-to-end temporary CLI failure tests including preflight, no-owned local-CAS/final-proof, remote-CAS, evidence-write and rollback-incomplete outcomes.

Non-blocking follow-up: before real execution, keep the remote credential-free and make the exact request's argv-token hashing convention explicit.

Formal tree/Gitlink is correct for this exact pair and the child commit is reachable. Reported `47/47` tests, py_compile, Ruff and diff-check are auxiliary evidence only and do not close the above production/contract gaps.

Scope reminder: remediation remains in the same CPU/static implementation Gate and within the approved four root files plus normal bookkeeping. This verdict does not authorize real selection/config JSON creation, real candidate/ref/origin mutation, source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.