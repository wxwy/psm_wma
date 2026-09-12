# ChatGPT Review — Authority-root Execution Authority Implementation Design

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-EXECUTION-AUTHORITY-IMPLEMENTATION-DESIGN`

## Exact formal pair

- root design SHA: `569a34d50e5106f982c3ed111171d67ea3344bc9`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The current V2 head at review start was bookkeeping/request-delivery head `816e318386ef73c2c13a59574df8bdf6665842b7`; it is not the formal target. The formal root is independently reachable. Its `cosmos-framework` entry is an actual submodule/Gitlink and resolves exactly to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh docs-only design review. No production/root tooling file changes are part of this formal pair.

## Prior blocker disposition

### d3cd3c9 HIGH-1 — one-shot request not fully frozen: DEFERRED CORRECTLY TO THE NEXT EXECUTABLE REQUEST

The prior exact request remains unapproved and must not execute. This design does not falsely claim that the old prose request is executable; instead it proposes the root-tooling changes needed so the next request can contain every execution-significant value with no post-verdict substitution. That is consistent with the prior acceptance, which explicitly allowed reopening root tooling in a fresh implementation pair.

### d3cd3c9 HIGH-2 — closed production CLI/Evidence ABI cannot bind bootstrap + four-module closure: DIRECTIONALLY ADDRESSED, NOT YET DESIGN-CLOSED

The design correctly proposes extending parser/invocation/Evidence-v1 to include collection/audit module identities and bootstrap/argv/protocol fields, instead of trying to force the old two-module ABI to attest a stronger real-execution authority.

### d3cd3c9 HIGH-3 — remote alias / ambient Git semantics: DIRECTIONALLY ADDRESSED, NOT YET DESIGN-CLOSED

The design correctly removes `origin` as execution authority, binds a canonical endpoint digest, and introduces no-replace/config isolation. However the exact enforcement/evidence contract is still incomplete, below.

## Current blockers

### HIGH-1 — bootstrap identity is still declarative; the design does not specify a causal runtime observation of the actual `python -c` source that executed

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_execution_authority_implementation_design_v0.1.md:53-60` (§4)

The design says the inline bootstrap bytes are frozen in the next request and that their digest must equal the frozen argv field, adapter evidence field, and fixture-builder parity test. It also says runtime bootstrap bytes must equal the formal binding before step 1.

But it never defines how the running stdlib bootstrap obtains an independent observation of the exact `-c` source bytes that the Python process actually received. A caller-supplied `bootstrap_raw_sha256` field plus an adapter evidence field only proves that the same declared digest was propagated. It does not prove that the process-level `-c` source argument equals those bytes. Fixture-builder parity is build-time/static evidence, not a runtime causal witness.

This is the remaining core of the prior bootstrap-attestation blocker. Because the bootstrap itself is the trust root that runs before project import, the implementation contract must define what concrete runtime fact it measures before admitting the project namespace.

**Exact acceptance:**

1. Freeze one exact process-level bootstrap observation rule before project import. For Python 3.11 this may be an exact `sys.orig_argv` projection or an equivalently direct stdlib observation of the original process argv; if Linux `/proc/self/cmdline` is used, freeze that platform dependency and byte grammar explicitly.
2. Derive `observed_bootstrap_raw_sha256` from the actual observed `-c` argument bytes, not from a caller-declared hash, fixture builder, or reconstructed template.
3. Derive the bootstrap argv digest from the same observed process argv under one frozen canonicalization, and prove it matches the exact approved request values before `sys.path.insert`, `runpy`, project import, authority Git action, or evidence write.
4. Carry the observed bootstrap/source/argv digest into the typed invocation/Evidence-v1; reject any mismatch between declared and observed values.
5. CPU/static evidence must directly launch the production bootstrap form with a modified `-c` payload while keeping the declared digest unchanged and prove rejection before the runpy/import sentinel and before Git/evidence mutation.

Without an observed process-level source fact, the new Evidence-v1 would still attest a declared bootstrap identity rather than the bootstrap that ran.

### HIGH-2 — native Git isolation is underspecified and the planned Evidence uses injected seams where direct native-Git witnesses are required

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_execution_authority_implementation_design_v0.1.md:64-75` (§5–§6)

The design states that every Git invocation will use `--no-replace-objects`, a minimal environment and fixed `-c` options, and that local repo config may not act as endpoint/object-view authority. This is the right direction, but two contract gaps remain.

First, the actual Git authority is not frozen. The design does not enumerate the exact command prefix / fixed `-c` set, exact local-config admission rule, or exact canonical endpoint grammar. Saying fixed `-c` disables attributes/hooks/filter semantics is insufficient because local repository config can still influence transport and command semantics unless the implementation explicitly rejects or neutralizes the relevant config surface. In particular, endpoint execution must be defined against direct endpoint bytes rather than any alias or `url.*.insteadOf` rewrite, and the design must say how local `include*`, `url.*`, remote, protocol, hook/filter/attribute and other admitted config are handled before the first authority action.

Second, §6 explicitly limits the new tests to temporary fixtures plus injected subprocess seams and says they do not call real commit/ref/remote behavior. That does not satisfy the prior direct-witness acceptance for native Git semantics. A mocked subprocess can prove argument construction but cannot prove that the production `NativeAuthorityGit` path actually remains fail-closed under Git replacement refs, local config URL rewrites, or real `ls-remote` / `push --force-with-lease` behavior.

**Exact acceptance:**

1. Freeze an exact Git invocation contract: complete env allowlist, exact command prefix/options, exact fixed `-c` entries, canonical endpoint grammar/normalization, and an explicit rule for local repo config (either exact allowlist/fingerprint with fail-closed rejection of everything authority-relevant, or a mechanically isolated invocation that cannot consume it).
2. Explicitly cover `url.*.insteadOf` / endpoint rewrite, `include*`, remote aliases, replace refs, hook/filter/attribute/protocol-related config, and any other config that can change endpoint/object/ref semantics. The accepted mechanism may reject rather than normalize, but must be exact and testable.
3. Evidence-v1 `git_isolation_fingerprint` must be derived from the exact effective isolation contract, not a caller string.
4. Permit and require direct CPU/static tests using only temporary local repositories and a temporary local bare remote (never project `origin`): create actual replace refs/config rewrite/adversarial local config, run the production `NativeAuthorityGit` path, and prove either pre-action rejection or use of the exact approved endpoint/object view. Also prove remote create/delete CAS behavior through the real local bare remote.
5. Injected subprocess tests may remain for error injection, but they cannot be the sole witness for native Git semantics.

## Scope / non-blocking observations

- Reopening the root tooling implementation is authorized by the prior exact acceptance; this is not by itself an impermissible extra provenance Gate.
- The proposed two-file root implementation scope is narrow and does not touch child/runtime/training code.
- The four-module transitive closure remains the correct declared project import closure for the current formal adapter path.
- The next executable request must still satisfy the prior request-completeness acceptance: no placeholders or values filled after approval.

## Blocker summary

- current design blockers: `2 HIGH`
- production blockers in the already-closed `ad9e011...` pair: `0` (not reopened by this docs-only review)
- total blockers: `2 HIGH`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_execution_authority_implementation_design_v0.1.md:53)`

This verdict binds only the exact formal pair `569a34d50e5106f982c3ed111171d67ea3344bc9 / 93a89ba61306d840a008813f62f26a34d54850f4`.

No root-tooling implementation, real materialization, source/checkpoint I/O, candidate/ref/evidence mutation, collection/receipt, child/runtime change, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.