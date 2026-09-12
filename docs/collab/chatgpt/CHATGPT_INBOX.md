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

- immediate prior live blob SHA: `325d4eb2c846cbf33b247aa61f17591e91c4efa5`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root synthetic CPU/static Implementation remediation 2 REQUEST_CHANGES

Formal pair:
- root implementation SHA: `ae52cb313cfafda4eedad600501030f4dc01297c`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:627)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_authority_root_cpu_static_implementation_ae52cb3_93a89ba.md`

Canonical review commit:
`fdb29a99ab34c5f914a1a44f5e6c112bf6f86183`

Current blockers: `1` (`HIGH production`).

The two blockers from the immediately previous `fce040f...` review are closed:
1. the shared upstream verifier now rejects either fixed path already existing in the formal parent and has direct adversarial tests;
2. collection exposes a minimal public canonical/tree/blob/digest helper surface, and authority-root code no longer imports private helpers across modules.

Remaining HIGH: the real collection executor still independently accepts authority structures that the hardened verifier rejects. `_authority_tree()` uses singular `GitTransaction.parent() -> str`, so exact zero/one/multi-parent structure cannot be proved, and it does not require `SELECTION_PATH` / canonical-config path to be absent from the formal parent. A formal parent can therefore precontain the fixed paths and a candidate can replace them while preserving the current two-path changed set, allowing `_bound_source_inputs()` to continue toward source open. This violates the retained authority-root contract and the required pre-source independent rederivation.

Required remediation in the same Gate: strengthen the collection authority lookup to prove exactly one parent equal to `authority_approval_formal_root_revision`; require both fixed paths absent from that parent before delta validation; preserve existing full-entry/blob/raw/fixed-ref checks; add direct collection-executor tests for either fixed path pre-existing plus zero/two-parent authority roots, proving fail-before-source with zero mutation.

Scope reminder: remediation remains in the same synthetic CPU/static implementation Gate. This review does not authorize real selection/config JSON creation, authority commit/ref creation, real source/remote I/O, collection/receipt/source-evidence/publication, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.