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

- immediate prior live blob SHA: `1ce0072a27f9d463eb39f1d17b4fb14493d52273`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Authority-root config grammar CPU/static remediation design v0.2 APPROVED

Formal pair:
- root design SHA: `9a0d48efc59d6e50e3d0ed2e80f670779d3fad64`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CONFIG_GRAMMAR_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_authority_root_config_grammar_cpu_static_remediation_design_v02_9a0d48e_93a89ba.md`

Canonical review commit:
`5216bb62002073106bce55f7856d1c5b68d533af`

Current blockers: `0`; Design/Authority blockers: `0`; production implementation blockers: `0`; evidence-only blockers: `0`; child/runtime blockers: `0`.

Closure summary:
1. The v0.1 quoted-subsection authority ambiguity is closed. v0.2 preserves quoted subsection bytes/case exactly while lowercasing only section and variable names under the frozen ASCII grammar.
2. Parser output is an ordered tuple sequence `(section_name, subsection_or_none, variable_name, raw_value)`; subsection identity is never flattened into a dotted key, unescaped, interpolated or case-folded.
3. The allowlist is the exact complete 14-tuple current bound config. `[branch "V2"]` and `[branch "v2"]` are distinct; only exact `V2` is authorized.
4. Outer launcher and bootstrap adapter must each carry an inline stdlib-only equivalent parser. Same raw config must yield byte-identical serialized canonical tuples or the same failure category.
5. Raw config SHA binding, descriptor identity, no-symlink route, config.worktree/commondir absence and existing Git isolation flags remain independent fail-closed barriers.
6. Scope remains root CPU/static only. The consumed v1.3 execution authority is not revived.

Implementation acceptance reminder:
- v0.2 supersedes v0.1 only for the three same-pair findings; all other v0.1 acceptance obligations remain binding, including that the actual frozen current config must pass both parsers to the next non-config precondition.
- Implementation review should therefore directly verify real-format assignment whitespace/indentation handling as well as exact tuple semantics and the required negative cases.

Exact next allowed action: implement the frozen parser/allowlist remediation only in the root frozen payload source, `tools/psm_wma/materialize_immutable_source_authority_root.py`, and direct temporary CPU/static tests. Then submit that implementation for independent close review.

Scope reminder: this approval does **not** authorize Stage-1 materialization or retry, source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1. After implementation close, a new fresh-bound exact Stage-1 request and a new separate single-attempt materialization approval remain mandatory.

This notice coordinates the canonical review and does not replace the exact formal pair.
