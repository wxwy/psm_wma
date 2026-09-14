# ChatGPT Independent Review — R09-B TTT v0.3.5 Rebound Stage-1 Authority-root Materialization Request v1.4

**Date:** 2026-09-14  
**Formal root:** `08cf3f7b15b743ba536bfc7f02b00e1d594e3e0d`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`

## 1. Pair / scope lock

- Fresh-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request is rebound Stage-1 v1.4 for the exact pair above.
- Verified formal root `08cf3f7...` resolves `cosmos-framework` exactly to reachable child `93a89ba...`.
- Incremental scope from the approved rebind-design pair is docs-only request construction: v1.4 Markdown/JSON plus ledger/review bookkeeping; no production or child/runtime change.
- Formal parent is rebound to `08d5828cdb4c12afa3b798ff01826c91ceb8755a`.
- Verified that new-parent launcher source path resolves to Git blob `af19a9eb66ecaf8bd0b92a48ab1867f105026658`; adapter path resolves to Git blob `4a51bddd15ec9a88883e3071cc550de85721599b`; child Gitlink remains unchanged.

## 2. Positive findings

1. v1.4 correctly abandons old parent `b359...` and binds the closed config-grammar parent `08d...`.
2. The canonical JSON includes the rebound launcher base identity (`base_path`, `base_blob`, `base_sha256`, `base_bytes`) and explicitly rejects old-base/fallback/mixed-parent reconstruction.
3. The request carries the rebound adapter identity and unchanged formal-tree authority/collection/audit closure.
4. FD3/4/5/8 ABI, `/proc/self/fd/8` cwd/index/bootstrap-root contract, fixed authority ref, fail-close code and authority-tuple-only stop remain present.
5. Formal scope is request construction only; no materializer/source/checkpoint/manifest/data/cache/child/GPU/training execution occurred in this formal pair.

## 3. Blocking findings

### HIGH-1 — ordered replay cannot reproduce the declared parser argv

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.4.json:1`

The exact rebound launcher base `08d...:docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py` contains **zero** occurrences of `--bootstrap-owner-root-fd`; its embedded `RAW[2]` therefore has no owner-FD pair to preserve.

However v1.4 freezes the replay step as:

> `within the parsed array ... preserve the single --bootstrap-owner-root-fd,8 pair ...`

There is no replay step that inserts that pair. Yet the declared final `inner_parser_argv` contains exactly one `--bootstrap-owner-root-fd`, `8` pair.

Therefore the declared parser bytes/SHA (`2336 / 1a9543ec...`) cannot be reproduced from the exact frozen new-parent base under the request's own ordered replay. This is the same class of authority break as the earlier non-reproducible replay issue: equivalent-looking final bytes are not enough when the frozen derivation does not produce them.

**Exact acceptance:** the next request must explicitly specify where/how one owner-FD pair is inserted into the parsed `RAW[2]` array before canonical serialization, reject any base that already contains an unexpected owner-FD pair, require exactly one final pair, and recompute parser/bootstrap/contract/payload/whole-request identities from that corrected replay.

### HIGH-2 — construction-round freshness is not explicitly bound in the formal request

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.4.md:31`

The frozen Stage-1 contract requires a new exact request to carry **same-round** route/ref/path freshness. v1.3 satisfied this by stating `构造时重新观察` and binding the exact `.git`, `.git/config`, local/remote fixed-ref, clean/index/evidence/pending observations.

v1.4 only says that the JSON freezes `freshness/absence`; neither its Markdown nor its construction note states that those values were re-observed during the v1.4 construction round. The `.git` / `.git/config` / ref values are byte-for-byte the historical values seen in v1.3, so the formal request bytes do not distinguish a fresh re-observation from copying the old snapshot.

**Exact acceptance:** for the replacement exact request, perform and explicitly record a new zero-mutation same-round observation of `.git`, `.git/config`, local fixed ref, remote fixed ref, clean root/index/evidence/pending paths, and bind those exact observations in the formal request. Any drift at later execution must still fail before mutation.

### HIGH-3 — canonical whole-request SHA is outside the formal request

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.4.md:31`

The controlling request contract requires the exact request itself to bind its canonical whole-request bytes/hash. The approved v1.3 formal Markdown carried:

`Canonical JSON=7775 bytes / 82f3103518ea953f6295e955f1d1f24e7945287dd19c1a47365647ca5fc22f7a`.

For v1.4, the reported canonical JSON identity (`8482 bytes / 831f9d8a246029333c07621debd197ff0ac8bdf1ccf7c9da4215ce8bf7c14b85`) exists only in SESSION/CODEX_INBOX bookkeeping added around the review request. The formal v1.4 Markdown itself does not bind it. Because review/ledger bookkeeping SHAs are not formal request authority, this regresses the previously frozen exact-request rule.

**Exact acceptance:** the replacement formal request Markdown must directly bind the canonical JSON byte length and SHA-256, and that identity must correspond to the exact sibling canonical JSON being reviewed.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.4.json:1)`

Current blockers: **3 HIGH Design/Authority**.  
Production implementation blockers: **0**.  
Evidence-only blockers: **0**.  
Child/runtime blockers: **0**.

## 5. Scope reminder

This verdict binds only exact pair `08cf3f7b15b743ba536bfc7f02b00e1d594e3e0d / 93a89ba61306d840a008813f62f26a34d54850f4` and this Stage-1 exact-request review.

No materialization/retry is authorized. No source/checkpoint/manifest/data/cache I/O, collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1 is authorized.

A corrected request should be a new exact pair (e.g. v1.5), freshly re-observed and fully re-derived from the rebound `08d...` launcher base, then reviewed independently before any single-attempt Stage-1 execution authority can exist.
