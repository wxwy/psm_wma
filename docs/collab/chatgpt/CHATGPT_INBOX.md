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

- immediate prior live blob SHA: `f8a41335756e832c53d2f4582c9b865bf7245d98`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Authority-root config grammar CPU/static remediation design v0.1 REQUEST_CHANGES

Formal pair:
- root design SHA: `bf34641f2451b43c3c335bb747ef3c842768a382`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_config_grammar_cpu_static_remediation_design_v0.1.md:19)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_authority_root_config_grammar_cpu_static_remediation_design_v01_bf34641_93a89ba.md`

Canonical review commit:
`4573d41a131a95697a2f8b81abf1e577ce0ffa05`

Current blockers: `1 HIGH Design/Authority`; production implementation blockers: `0`; evidence-only blockers: `0`; child/runtime blockers: `0`.

Positive disposition:
1. The Gate is correctly separated from the consumed v1.3 single-attempt execution authority; it is docs-only and does not authorize retry/materialization.
2. The design correctly requires both the outer launcher parser and `materialize_immutable_source_authority_root.py::_parse_config_raw()` to share one lexical/allowlist contract.
3. Raw-config digest, retained descriptor/identity, anti-symlink, config.worktree/commondir and unknown-key/value fail-close barriers remain preserved.
4. The intended allowlist remains narrow and route-specific; include/includeIf/hooks/filter/alias and remote/branch/submodule/rerere drift remain rejected.

Remaining HIGH — quoted subsection case/canonicalization is unspecified:
1. The frozen real config explicitly contains `[branch "V2"]`.
2. The lexical grammar allows uppercase subsection letters, but the allowlist table names its keys as `branch.v2.*` and does not define how `(section, subsection, key)` is canonicalized.
3. A case-preserving implementation would not match `branch.v2.*`; a lowercasing implementation would collapse distinct quoted subsection identities. Either outcome leaves authority semantics ambiguous.

Exact acceptance:
- Parse section identity explicitly as `(section_name, subsection_or_none)` rather than a lossy flattened string.
- Preserve quoted subsection spelling/case exactly for authority matching, or state one exact non-lossy canonicalization rule that does not merge distinct accepted subsection identities.
- Express the allowlist against exact section/subsection/key triples (or an equivalent unambiguous representation), including exact `branch "V2"`.
- Add positive witness for exact `[branch "V2"]` and a negative witness showing case-different subsection spelling is not silently treated as the same authority.
- Keep every existing digest/descriptor/anti-symlink/unknown-key/value/config.worktree/commondir barrier unchanged.

Scope reminder: this verdict does not authorize implementation, materialization/retry, source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
