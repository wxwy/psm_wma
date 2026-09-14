# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Config Grammar CPU/static Remediation

**Date:** 2026-09-14  
**Formal root:** `f709832e523cc250e9b751594bee5e4bb086f0d2`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective technical request binds exact pair `f709832e523cc250e9b751594bee5e4bb086f0d2` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Verified formal root `f709832...` resolves `cosmos-framework` exactly to reachable child `93a89ba...`.
- Compared incrementally against rejected implementation pair `cb4760ba050a05edd18ed08e1e33b2ea12dfc11c / 93a89ba...` and the approved v0.2 design `9a0d48ef... / 93a89ba...`.
- Scope remains root CPU/static implementation + temporary witnesses only. No Stage-1 retry/materialization, source/checkpoint/manifest/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training/eval/inference/LIBERO4IN1 is authorized.

## 2. Prior blockers — disposition

### Prior HIGH Production/Authority — CLOSED

The three parser implementations now use the same frozen category vocabulary for the config grammar seam:

- `config-utf8`
- `config-section`
- `config-grammar`
- `config-duplicate`
- `config-allowlist`

The runtime adapter exposes `ConfigParseError.category`; the outer launcher emits the same category strings; the isolated bootstrap inline parser also uses the same category literals. The exact 14-tuple allowlist, case-preserving quoted subsection identity (`V2` distinct from `v2`), one-ASCII-space quoted-header separator rule, raw-digest/route/no-symlink barriers and Git-view drift check remain intact.

No new Production/Authority blocker was found in this remediation delta.

### Prior HIGH Evidence — PARTIALLY CLOSED, one blocker remains

The new outer witness now directly compares:

- valid canonical tuple bytes from `P.parse_config_raw(exact)` vs runtime `ADAPTER._parse_config_raw(exact)`;
- failure categories for `[branch "v2"]`, escaped, dotted and path subsection variants.

This closes the previous absence of any direct outer/runtime equivalence witness and the stale outer 14-tuple fixture problem.

However, the approved v0.2 design and the immediately preceding ChatGPT review froze a **three-parser** equivalence obligation: outer frozen launcher parser, isolated bootstrap inline parser, and runtime adapter parser. The new witness only invokes the first and third. The isolated bootstrap parser is changed by inspection to the same taxonomy, but there is no direct witness that drives the same valid/invalid corpus through it and compares its canonical tuple bytes / rejection category against the other two.

Passing `69/69` adapter tests plus `17/17` outer witness therefore does not yet prove the frozen cross-parser contract for the bootstrap seam.

## 3. Blocking finding

### HIGH-1 Evidence — isolated bootstrap parser is not included in the byte-identical cross-parser witness

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8_witness_test.py:34`

The current direct witness `test_outer_and_adapter_config_parser_are_byte_equivalent` compares only outer `P.parse_config_raw()` and runtime `ADAPTER._parse_config_raw()`. It never executes/extracts the isolated bootstrap inline parser on the same corpus.

Static similarity of bootstrap source is not a substitute for the v0.2 acceptance requirement that parser equivalence be witnessed directly.

**Exact acceptance:** add a temporary CPU/static witness that, for one shared corpus:

1. drives the exact 14-tuple real-format config through all three parser seams;
2. compares the serialized ordered canonical tuple sequence byte-for-byte for the valid case;
3. compares the exact frozen failure category for at least the already-required `V2/v2`, escaped, dotted and path subsection negatives, and preferably the duplicate/unknown tuple classes as well;
4. does not import one parser implementation into another production seam merely to make the test pass; the witness may extract/execute the isolated bootstrap parser under a test harness;
5. preserves all current grammar authority and route barriers unchanged.

No redesign of the 14-tuple authority is requested.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8_witness_test.py:34)`

Current blockers: **1 HIGH Evidence**.  
Design/Authority blockers: **0**.  
Production implementation blockers: **0**.  
Child/runtime blockers: **0**.

## 5. Scope reminder

This verdict binds only exact pair `f709832e523cc250e9b751594bee5e4bb086f0d2` / `93a89ba61306d840a008813f62f26a34d54850f4` and the config-grammar CPU/static implementation-close Gate above.

It does **not** authorize Stage-1 retry/materialization, source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.
