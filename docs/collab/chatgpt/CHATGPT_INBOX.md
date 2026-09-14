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

- immediate prior live blob SHA: `a3ef47ef67280be6d83aea85b93f9750c23e1553`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Authority-root config grammar CPU/static remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `f709832e523cc250e9b751594bee5e4bb086f0d2`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8_witness_test.py:34)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_authority_root_config_grammar_cpu_static_remediation_f709832_93a89ba.md`

Canonical review commit:
`ccc0e0e3b40ffede7b5f844f8944172b495e8743`

Current blockers: `1 HIGH Evidence`; Design/Authority blockers: `0`; Production/Authority blockers: `0`; child/runtime blockers: `0`.

Closure summary:
1. The prior Production/Authority HIGH is closed. Outer launcher, isolated bootstrap inline parser and runtime adapter now use the same frozen config-parser category vocabulary: `config-utf8`, `config-section`, `config-grammar`, `config-duplicate`, `config-allowlist`.
2. The exact 14-tuple grammar remains intact; quoted subsection identity stays byte/case-preserving and exact `V2` remains distinct from `v2`.
3. Existing raw-config digest, descriptor/no-symlink/route, config.worktree/commondir and Git-view drift barriers remain unchanged.
4. The outer witness fixture is now the exact frozen 14-tuple config and directly proves outer/runtime valid tuple byte equivalence plus the required `V2/v2`, escaped, dotted and path subsection category equivalence.

Remaining HIGH — bootstrap is still outside the direct cross-parser witness:
1. The frozen v0.2 acceptance and prior ChatGPT remediation review require a three-parser witness: outer frozen launcher, isolated bootstrap inline parser, runtime adapter.
2. `test_outer_and_adapter_config_parser_are_byte_equivalent` invokes only outer `P.parse_config_raw()` and runtime `ADAPTER._parse_config_raw()`.
3. The isolated bootstrap source now appears statically aligned, but no direct witness drives the same corpus through it and compares canonical tuple bytes / normalized failure category. Static similarity and aggregate `69/69` + `17/17` PASS do not substitute for the frozen direct witness.

Exact acceptance:
- Add one temporary CPU/static cross-parser witness over all three actual parser seams.
- For the exact 14-tuple valid config, compare serialized ordered canonical tuples byte-for-byte.
- For at least `V2/v2`, escaped, dotted and path subsection negatives, compare the exact frozen failure category; include duplicate/unknown tuple classes if practical.
- The test harness may extract/execute the isolated bootstrap parser, but production parsers must remain inline and non-importing as frozen.
- Do not change the 14-tuple authority or weaken any route/digest barrier.

Scope reminder: this verdict does **not** authorize Stage-1 retry/materialization, source/checkpoint/manifest/data/cache I/O, downstream collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1. After implementation close, a new fresh-bound exact Stage-1 request and separate single-attempt materialization approval remain mandatory.

This notice coordinates the canonical review and does not replace the exact formal pair.
