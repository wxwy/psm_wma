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

- immediate prior live blob SHA: `8862ac210882194f5e992896e6b529ec957214a1`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter CPU/static descriptor-stable remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `99bafeb060054da29052fcc4bd1121f075e85ad5`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:153)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_immutable_source_collection_real_adapter_cpu_static_99bafeb_93a89ba.md`

Canonical review commit:
`13060e61ba55db0a8d7946be1fb138e3cd44f97e`

Current blockers: `2 HIGH Production/Authority+Evidence`; `0 child/runtime`.

Blocking summary:
1. `NativeRootFd._open_regular()` now traverses intermediate components with retained no-follow directory FDs, but it never revalidates that an opened component still occupies the source-root pathname. If an ancestor is renamed/replaced after its FD is opened, the final file open proceeds inside the detached old subtree and returns a readable source FD. This violates the frozen race-rejection requirement and also affects `NativeCollectionGit.snapshot()`, which now reuses this traversal primitive. The required causal intermediate-component replacement witness remains absent.
2. `AtomicFileEvidenceSink.emit()` binds the parent FD but closes the staged file FD before publishing by the mutable `<name>.pending` pathname. A concurrent replacement of that staging entry can therefore be hard-linked as accepted evidence without any staged-inode/post-link byte proof. The submitted parent-replacement witness also treats disappearance of the frozen evidence pathname as a successful emit, although the current contract freezes a request-bound destination path rather than an independently frozen parent-FD/leaf ABI.

Prior blocker disposition:
- snapshot leaf/file pathname TOCTOU: CLOSED by same-FD hashing;
- direct actual `NativeCollectionGit` + actual `NativeRootFd` through canonical `collect_synthetic()`, native rollback equality, tracked modes and final symlink/directory matrix: CLOSED;
- parent-FD-relative staging/publication: materially improved but not fully closed due staging-inode and frozen-destination continuity above;
- NativeRootFd component replacement race: still OPEN.

Exact acceptance is detailed in the canonical review. Remediation remains limited to the approved two-file CPU/static allowlist and temporary fixtures.

Scope reminder: no real source/checkpoint/manifest/data/cache I/O, live collection/receipt/publication execution, execution request activation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
