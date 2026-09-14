# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Config Grammar CPU/static Implementation

**Date:** 2026-09-14  
**Formal root:** `cb4760ba050a05edd18ed08e1e33b2ea12dfc11c`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective implementation-close request binds exact pair `cb4760ba050a05edd18ed08e1e33b2ea12dfc11c` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified the formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Compared against the approved v0.2 design root `9a0d48efc59d6e50e3d0ed2e80f670779d3fad64`; technical implementation changes are limited to the frozen outer launcher payload source, `tools/psm_wma/materialize_immutable_source_authority_root.py`, its direct CPU/static test, plus task/review bookkeeping. No child/runtime/GPU scope change is present.
- The consumed v1.3 materialization authority is not revived by this Gate.

## 2. Positive implementation disposition

The core grammar correction is materially aligned with the approved v0.2 design:

1. The exact 14-tuple allowlist is present in the outer launcher, isolated bootstrap payload, and runtime adapter.
2. Section and variable names are ASCII-normalized to lowercase while quoted subsection bytes/case are preserved; exact `("branch", "V2", ...)` is authorized and case-different `v2` is rejected.
3. Quoted headers require exactly one ASCII space between section and opening quote; escaped/dotted/path subsection spellings are rejected.
4. The runtime adapter now parses to ordered `(section, subsection, variable, value)` tuples and projects them only after exact tuple validation.
5. Existing raw-config bytes, Git-view comparison, no-symlink/descriptor/route checks, `config.worktree` / `commondir` barriers and Git isolation remain in place.
6. The submitted CPU/static suite reports `py_compile` PASS, `69/69` unittest PASS and `git diff --check` PASS, with temporary local-Git fixtures only.

Those changes close the original quoted-subsection/case ambiguity. They do not by themselves close the implementation Gate because two explicit v0.2 acceptance contracts remain unmet.

## 3. Blocking findings

### HIGH-1 — Production/Authority: frozen cross-parser failure-category contract is not implemented

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:342`

The approved v0.2 design requires that, for the same raw config, the equivalent parsers either produce the same canonical tuple sequence or **fail with the same category**.

The current implementation does not expose one common frozen failure taxonomy:

- the outer launcher classifies failures as strings such as `config section`, `config grammar`, and `config allowlist`;
- the isolated bootstrap parser still calls a generic `fail()` whose externally visible classification is its bootstrap invocation/line location rather than those same config categories;
- the runtime adapter raises a different set of `NativeGitError` categories such as `Git config section 无效`, `Git config syntax 无效`, `Git config key 无效`, `Git config 不允许duplicate key`, and `Git config 含未授权或缺失 tuple`.

These are not merely cosmetic message differences: under the frozen v0.2 contract, category equivalence is part of the authority semantics and is what allows the two independently inlined parsers to be proven behaviorally identical on invalid input. The implementation therefore does not yet implement the approved production contract.

**Acceptance:** define one finite frozen category set for config parsing/authority rejection and make outer launcher, isolated bootstrap, and runtime adapter map the same invalid raw config to the same category. Preserve the no-import/inline constraint and every existing fail-closed route barrier.

### HIGH-2 — Evidence: required byte-identical cross-parser witness is absent

**Location:** `tools/psm_wma/test_materialize_immutable_source_authority_root.py:268`

The approved v0.2 design explicitly requires a witness comparing equivalent-parser canonical output / failure category byte-for-byte.

The formal diff adds one direct `_parse_config_raw()` grammar test and updates the temporary fixture to the 14-tuple real-config shape. Existing bootstrap/CLI tests exercise some valid and hostile configs, but the submitted evidence does **not** contain a direct cross-parser witness that:

1. feeds the same valid raw configs to the frozen outer parser and runtime/bootstrap parser and compares serialized ordered tuple bytes;
2. feeds the same invalid corpus and compares the normalized failure category;
3. covers at least exact current config, `V2` vs `v2`, escaped/dotted/path subsection, unknown key, duplicate triple, remote/submodule URL drift, include/includeIf, and quoted-header spacing.

`69/69 PASS` therefore cannot substitute for the direct witness frozen by the design.

**Acceptance:** add a temporary CPU/static equivalence witness over the actual frozen parser implementations (not a third reimplementation), assert byte-identical canonical tuple output or identical frozen failure category, and run it in the formal evidence command. No real source/checkpoint/materialization activity is needed.

## 4. Formal verdict

`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:342)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **0**.  
Production/Authority blockers: **1 HIGH**.  
Evidence-only blockers: **1 HIGH**.  
Child/runtime blockers: **0**.

## 5. Scope / next action

This verdict binds only exact pair `cb4760ba050a05edd18ed08e1e33b2ea12dfc11c` / `93a89ba61306d840a008813f62f26a34d54850f4` and this CPU/static remediation Gate.

The 14-tuple grammar, case-preserving subsection identity, exact `V2` authority and existing route/digest barriers should remain unchanged. The remediation should only normalize cross-parser failure categories and add the missing direct equivalence witness.

No Stage-1 materialization or retry is authorized. After implementation close, the workflow still requires a new freshness observation, a new exact Stage-1 request and a new separate single-attempt materialization approval. No source/checkpoint/manifest/data/cache I/O, downstream collection/receipt/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1 is authorized by this verdict.
