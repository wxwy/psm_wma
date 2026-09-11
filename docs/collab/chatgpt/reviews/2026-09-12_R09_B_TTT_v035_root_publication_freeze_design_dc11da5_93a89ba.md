# ChatGPT Independent Review — R09-B TTT v0.3.5 Root Publication Freeze Design

**Date:** 2026-09-12  
**Formal root:** `dc11da59495f41cea58ccf17225469fcf6183452`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-ROOT-PUBLICATION-FREEZE-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read the live Codex request ledger.
- Independently verified formal root `dc11da59495f41cea58ccf17225469fcf6183452` resolves `cosmos-framework` exactly to child `93a89ba61306d840a008813f62f26a34d54850f4`; child is reachable and unchanged.
- Formal commit is docs-only for this Gate: it adds `docs/build/PSM-WMA_Local_Memory_v0.3.5_root_publication_freeze_design_v0.1.md` plus normal SESSION/TODO bookkeeping. No publication target, child, runtime, real source audit, real checkpoint/data/cache I/O, GPU or training execution is part of this formal pair.
- The prior root Gitlink authority CPU/static tooling Gate is correctly treated as closed-only tooling; it does not authorize real publication or audit.

## 2. Findings

### HIGH-1 — Design/Authority — input-package witness authority is not frozen

Section 2 says the publication input package contains only the two nested objects `canonical_model_config` and `checkpoint_source_descriptor`, while also requiring recomputed nested digests to match an independently predeclared witness. Section 4 then exposes `verify_publication_bytes(raw_bytes, expected_witness)`, but this design does not freeze the witness object's exact schema/key set, canonical digest semantics, source-evidence record identity, or the rule that prevents a caller from supplying an arbitrary self-consistent witness.

As written, a future caller can choose both a candidate package and a matching expected witness unless a later design invents additional authority semantics. That defeats the purpose of this Gate, which is specifically to freeze the publication inputs before implementation/materialization.

**Acceptance:** freeze now the exact machine-readable publication-input package and witness contracts. If the witness is separate, define its schema/version, exact keys/types, canonical JSON/SHA-256 relationships, and the exact digest/identifier that binds it to a future independently-approved immutable source-evidence record. State explicitly that materializer/verifier callers, environment, working tree and publication bytes cannot author or select the expected witness. Also place the source-evidence producer/closure Gate explicitly in the mandatory sequence before any real materialization execution.

### HIGH-2 — Design/Authority — child Gitlink is incorrectly promoted to future audit invocation input

Section 3 item 2 requires the index Gitlink SHA to be recorded as a full child revision in an independent future audit invocation input. That conflicts with the already-frozen source-audit design v0.3: the authoritative child revision must be derived only from the locked formal root tree's `cosmos-framework` Gitlink; caller/audit-input child revision is explicitly non-authoritative and must not replace the root-tree lookup.

The current implemented source-audit interface likewise does not accept an expected child SHA; it receives a formal root revision plus child object transport and derives the child revision from the root tree.

**Acceptance:** remove `child_git_revision` from any authoritative future audit invocation input. A pre-commit index Gitlink observation may be retained only as a non-authoritative mutation guard proving that the materialization commit does not stage/change `cosmos-framework`. The post-commit read-only audit must receive the new formal root revision, derive the child Gitlink from that formal root tree, and use the child Git directory only as object transport.

### HIGH-3 — Design/Transaction — zero-mutation failure contract contradicts post-stage verification order

Section 3 requires the publication bytes to be written/staged and then immediately re-read from the index blob for byte-for-byte verification. The same section later requires every pre-commit validation failure to leave target and index completely unmodified: no created/replaced target and no staged target.

Those requirements cannot both hold for failures discovered after the live target/index has already been mutated, unless an exact transactional mechanism/rollback boundary is frozen. The current design freezes neither an isolated temporary-index verification path nor an exact snapshot/rollback protocol, so the promised fail-closed state is not implementable from the text.

**Acceptance:** freeze an executable transaction boundary. Preferred safe pattern: perform all fallible package/schema/digest/path/staged-set/blob-byte validation in isolated temporary state (for example, a temporary file plus isolated temporary Git index/tree) before touching the live publication path/index; only after all checks pass may one controlled commit phase mutate the live target/index. If live state must be touched before the final check, instead freeze exact pre-state snapshots, rollback semantics, post-failure byte/index equivalence checks, and distinguish pre-mutation from post-mutation failure. The design must no longer claim unconditional zero target/index mutation while verifying only after live staging.

## 3. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_root_publication_freeze_design_v0.1.md:23)`

Current blockers: **3 HIGH**.  
Design/Authority blockers: **3**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 4. Scope

No publication creation/write, no real root source-audit execution, no production `root_gitlink_authority_v1` creation/consumption, no runtime integration, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1 is authorized. The next remediation should remain docs-only for this Gate.