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

- immediate prior live blob SHA: `aa5a6731725d8153d12159154a188779dde8f3e6`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Authority-root config grammar bootstrap witness remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `8aa5e519d9778a94f228a1050433327c00433020`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/test_materialize_immutable_source_authority_root.py:1035)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_authority_root_config_grammar_bootstrap_witness_8aa5e51_93a89ba.md`

Canonical review commit:
`0ef7f94c96ee521741fdaabaed67f05cd30521d2`

Current blockers: `1 HIGH Evidence`; Design/Authority blockers: `0`; Production/Authority blockers: `0`; child/runtime blockers: `0`.

Closure summary:
1. Production/Authority remains closed. Outer launcher, isolated bootstrap and runtime adapter retain the same frozen category taxonomy: `config-utf8`, `config-section`, `config-grammar`, `config-duplicate`, `config-allowlist`.
2. The exact 14-tuple authority remains unchanged; quoted subsection identity is byte/case preserving and exact `V2` remains distinct from `v2`.
3. This remediation adds a real isolated-bootstrap witness for two previously uncovered invalid inputs: `branch "v2"` → `config-allowlist`, and escaped subsection `branch "V\\2"` → `config-section`; each is compared directly with runtime parser category.
4. Formal root still resolves `cosmos-framework` exactly to reachable child `93a89ba...`; technical remediation is test-only.

Remaining HIGH — bootstrap is still not in the full frozen equivalence corpus:
1. The approved v0.2 design requires the equivalent parsers to produce the same ordered canonical tuple sequence for valid raw config or the same failure category for invalid raw config, with direct byte/category witnesses.
2. The new bootstrap test covers only two invalid inputs. It does not expose/capture bootstrap ordered canonical tuple output for the exact valid 14-tuple config, so no byte-identical valid-output comparison exists across outer/bootstrap/runtime.
3. Bootstrap category equivalence is also not directly compared for dotted/path subsection, unknown key, duplicate triple, remote/submodule URL drift, include/includeIf, or quoted-header spacing. Existing reject-only bootstrap tests do not compare normalized category to the other parser seams.

Exact acceptance:
- Extend the temporary CPU/static harness so the actual isolated bootstrap config parser is observably exercised over the same frozen corpus as outer/runtime.
- For the exact valid current config, capture/derive bootstrap ordered canonical tuples and compare serialized bytes across all three parser seams.
- For invalid cases, compare exact category across all three for at least `V2/v2`, escaped/dotted/path subsection, unknown key, duplicate triple, remote/submodule URL drift, include/includeIf, and quoted-header spacing.
- Preserve the current production parser bytes/authority semantics unless a witness demonstrates an actual production defect; no production grammar redesign is requested.

Scope reminder: this verdict does **not** authorize Stage-1 retry/materialization, source/checkpoint/manifest/data/cache I/O, downstream collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1. After implementation close, a new fresh-bound exact Stage-1 request and separate single-attempt materialization approval remain mandatory.

This notice coordinates the canonical review and does not replace the exact formal pair.
