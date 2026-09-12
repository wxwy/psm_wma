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

- immediate prior live blob SHA: `97c11c92e3e52228ceebcf7153b0495ea6d57cae`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root Real Adapter CPU/static Remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `8879742c4ea99bf2676903d4085a77aee91cd4e1`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:930)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_cpu_static_implementation_8879742_93a89ba.md`

Canonical review commit:
`0eb6d58f1c752cd1f5fa7bba2df1d95d82317083`

Current blockers: `1 HIGH`.

Prior `2249fdd3...` findings:
- H1 activation/stale capability: CLOSED. Witness+commit now share an opaque active activation and stale retained capabilities are rejected after the originating finalizer returns.
- H2 ref-race at commit point: CLOSED. The authority-owned consume transition now performs the final local+remote exact-candidate re-observation immediately before guard removal; direct local/remote post-seal drift tests remain pre-commit.
- H4 real terminal evidence producer: CLOSED. Verify retains prepared candidate; pre-input/request failures can emit preflight Evidence-v1; publication/cleanup failures preserve real chronology; cleanup uncertainty is serialized as ROLLBACK_INCOMPLETE/EVIDENCE_CLEANUP_INCOMPLETE.
- H3 filesystem object ownership: PARTIALLY CLOSED and remains the sole HIGH.

Remaining HIGH:

**Identity check and destructive unlink are still separate pathname operations.** `_unlink_owned()` performs `lstat(path)`, compares `(st_dev, st_ino)`, then calls `path.unlink()`. If the pathname is replaced after the successful identity check but before unlink, the activation deletes the foreign replacement. The PASS commit guard has the same class of defect: `EvidenceCommit.consume_by_unlink()` verifies the sealed guard identity, then performs the local/remote ref recheck, and only afterwards calls `os.unlink(self._guard)`; a guard replacement during that interval can be deleted and followed by `_committed=True` even though the exact sealed guard object was not consumed.

Exact acceptance: destructive evidence-path removal must be identity-safe at the actual mutation boundary, not only checked beforehand. Guard commit must mark committed only when the exact sealed guard object is removed; guard/temp/final cleanup must never remove a replacement inode; replacement injected specifically between final identity proof and unlink must preserve foreign bytes and fail-stop. Add direct boundary-race tests for both commit guard removal and cleanup.

Formal tree/Gitlink is independently correct for this exact pair and the child commit is reachable. Reported `58/58` tests, py_compile, Ruff and task-scoped diff-check are auxiliary evidence only.

Scope reminder: remediation stays in the same four-file temporary CPU/static Gate. This verdict does not authorize real selection/config JSON creation, real candidate/ref/origin mutation, source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.