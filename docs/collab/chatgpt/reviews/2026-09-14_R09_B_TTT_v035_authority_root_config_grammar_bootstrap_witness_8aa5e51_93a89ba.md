# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Config Grammar Bootstrap Witness Remediation

**Date:** 2026-09-14  
**Formal root:** `8aa5e519d9778a94f228a1050433327c00433020`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION`

## 1. Pair / scope lock

- Fresh-relocked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `8aa5e519d9778a94f228a1050433327c00433020` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified the formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Technical delta from prior reviewed implementation pair `f709832e523cc250e9b751594bee5e4bb086f0d2` is test-only: one direct isolated-bootstrap category witness added to `tools/psm_wma/test_materialize_immutable_source_authority_root.py`.
- Production parser / 14-tuple authority bytes are unchanged in this remediation.

## 2. Prior blocker disposition

The prior exact-pair review left one HIGH Evidence blocker only. Production/Authority had already closed because outer launcher, isolated bootstrap and runtime adapter all used the same frozen category taxonomy:

- `config-utf8`
- `config-section`
- `config-grammar`
- `config-duplicate`
- `config-allowlist`

The remaining acceptance required a direct temporary CPU/static witness that places the isolated bootstrap parser into the same equivalence corpus as the outer and runtime parsers, including canonical valid-output equivalence and normalized invalid-category equivalence.

## 3. Positive observations

The new test is useful and correctly narrows the previous gap:

1. It runs the actual isolated bootstrap payload over a temporary Git fixture rather than merely inspecting source text.
2. It demonstrates `branch "v2"` maps to `config-allowlist` in bootstrap and runtime.
3. It demonstrates escaped subsection `branch "V\\2"` maps to `config-section` in bootstrap and runtime.
4. Existing outer-vs-runtime witness already covers valid exact-config tuple bytes and subsection variants, so these two cases now have pairwise evidence spanning all three parser locations.
5. Scope remains temporary CPU/static only; no production materialization/retry, source/checkpoint/manifest/data/cache I/O, child/runtime mutation, GPU or training is introduced.

## 4. Blocking finding

### HIGH-E1 — bootstrap is still not in the full frozen cross-parser equivalence corpus

**Location:** `tools/psm_wma/test_materialize_immutable_source_authority_root.py:1035`

The new witness checks only two invalid bootstrap inputs (`v2` and escaped subsection) and compares only their failure category to the runtime parser. It does not close the full frozen acceptance from the approved v0.2 design and the prior ChatGPT review:

- the isolated bootstrap path does not expose/capture the ordered canonical tuple sequence for the exact valid current config, so there is still no byte-identical valid-output comparison across outer / bootstrap / runtime;
- dotted/path subsection variants are not included in the bootstrap equivalence assertion;
- unknown key, duplicate triple, remote/submodule URL drift, include/includeIf, and quoted-header spacing are not driven through bootstrap and compared to the same frozen category produced by the other parser implementations.

Existing bootstrap tests that merely reject hostile config are useful fail-close witnesses, but they do not compare normalized category against the outer/runtime parser for the same raw bytes. Likewise, source-level similarity of the three parsers cannot substitute for the explicitly frozen direct equivalence witness.

**Exact acceptance:** extend the temporary CPU/static witness/harness so the actual isolated bootstrap config parser is observably exercised over the same corpus as the other two parser implementations. At minimum:

1. exact current 14-tuple config: capture/derive the bootstrap parser's ordered canonical tuples and compare their serialized bytes with outer and runtime parser output;
2. invalid corpus: compare the bootstrap failure category against outer/runtime for `V2` vs `v2`, escaped/dotted/path subsection, unknown key, duplicate triple, remote/submodule URL drift, include/includeIf and quoted-header spacing;
3. keep the existing frozen `config-*` taxonomy, 14-tuple authority, raw-digest / route / Git-view / anti-symlink / config.worktree / commondir barriers unchanged;
4. remain temporary CPU/static only.

No production grammar redesign is requested.

## 5. Formal verdict

`REQUEST_CHANGES(tools/psm_wma/test_materialize_immutable_source_authority_root.py:1035)`

Current blockers: **1 HIGH Evidence**.  
Design/Authority blockers: **0**.  
Production/Authority blockers: **0**.  
Child/runtime blockers: **0**.

## 6. Scope reminder

This verdict binds only exact pair `8aa5e519d9778a94f228a1050433327c00433020` / `93a89ba61306d840a008813f62f26a34d54850f4` and the CPU/static remediation Gate above.

It does **not** authorize Stage-1 retry/materialization, source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1. After implementation close, a newly fresh-bound exact Stage-1 request and a separate one-shot materialization approval remain mandatory.
