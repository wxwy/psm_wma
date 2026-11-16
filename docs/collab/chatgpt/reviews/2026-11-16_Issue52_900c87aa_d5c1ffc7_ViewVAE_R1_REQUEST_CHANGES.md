# Issue52 / PR53 — independent R1 incremental CODE/CPU review

- Review date: 2026-11-16 CST (Asia/Shanghai).
- **Formal implementation Root: `900c87aa0ae643123477e985b6a051fb7535ee03`.**
- **Formal Child/Gitlink: `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`.**
- Previous implementation: `aa0450b8e36b2cb833beda96256a29c3db95db23`.
- Increment base / previous review-only commit: `25b49dba85ca12aad2a902786b927019329fa608`.
- Author bookkeeping HEAD inspected: `4ad1059195fae264f27b50a680eda5c7abea7b68`; it does not replace the fixed implementation.
- V3 observed: `55cc5181abf8ca4b1e2a3a6b415699c457cc080b`, unchanged.
- PR: https://github.com/wxwy/psm_wma/pull/53 — open, Draft, unmerged at inspection.

## Formal technical verdict: REQUEST_CHANGES

**The original F1 and F2 counterexamples are fixed. The independent 265-case CPU suite passes. One newly introduced P1 compatibility regression blocks CODE approval: the new origin checker rejects a legitimate namespace package required by the pinned native Wan import chain.**

This is a narrow incremental review of the two requested entry-boundary fixes. The already reviewed cache format, source/index semantics, per-View storage/reader and atomic/resume design remain unchanged and are not being redesigned.

| Finding | Result at the fixed R1 implementation |
|---|---|
| Original F1: foreign Cosmos parent/helper can mix checkouts | CLOSED for the reported mixed-source acceptance bug; unchanged reviewer probe now passes |
| Original F2: unsupported native canvas tier accepted by plan | CLOSED; unchanged 1024×1024 probe now returns exit 2 with no cache |
| R1-F3: valid selected-Child namespace package rejected | **OPEN, P1; independently reproduced on CPU** |

The current Issue52 owner handoff authorizes scoped independent CODE/CPU review and supersedes historical V2/MM/Kimi waiting rules for this task. No other reviewer's approval is inferred.

## Independent execution and source binding

All execution below was performed by the reviewer against the fixed candidate snapshot, not inferred from author logs. The environment was reused from the previous independent review: Python 3.12.14, Torch 2.15.0+cpu, pytest 9.2.0, NumPy 2.5.5, Pillow 13.0.0, Ruff 0.17.5. No network access occurred during tests.

| Check | Independent result |
|---|---|
| Scoped full regression | **265 passed; 0 failures, 0 errors, 0 skips**; console 11.73 s, JUnit 11.708 s |
| Original reviewer counterexamples, byte-for-byte unchanged script | **2 passed**; zero failures/errors/skips; JUnit 0.472 s |
| New native namespace acceptance regression | **1 failed** at the expected-acceptance assertion; zero errors/skips; JUnit 0.134 s |
| Retained baseline identities | All original **224** `classname::name` identities present; exactly **41** additional identities |
| Selected Ruff rules E4/E7/E9/F/I | PASS |
| Formatting | PASS; 14 product/test/CLI Python files already formatted |
| Candidate source manifest | 41/41 SHA256 values matched; same 41 before/after |
| Supplemental native package probe inputs | 45/45 before/after hashes unchanged, including four additional exact Child files |

The 2 replay cases and 1 new probe are separate evidence runs, not added to the 265-case suite. The original probe script SHA256 remains `3767287d3f30f365b0c9318fff0796ec180c845448cbae94bf72791b1df2e197`. Its previous RED evidence at aa0450b8 remains immutable in the prior review.

The 265 tests comprise builder 21, canvas 32, contract 18, encoding 61, source 31, storage 43, existing event-index 24, index-package 4 and compact-v3 31. The 41 additions are canvas 32 plus import-boundary 9. The older test definitions were preserved.

The snapshot reuses the previously verified exact source files for unchanged paths and obtains modified files through the GitHub plugin at the full new SHA. Every fetched file was checked against its Git blob SHA. The four native `env_parsers` source files were fetched from the exact Child to complete the supplemental package layout; no Child implementation was edited. This is a scoped source snapshot, not a claim of a complete local repository clone.

## Closed findings

### F1 — reject foreign or unverifiable loaded Cosmos sources

The new `g2/latent_cache/encoding.py:83–123` checks all loaded Cosmos modules/packages, their spec origins/files and both package search-path inventories. It runs before the controlled import (`:362–363`) and after it (`:444–445`), before new binding tokens are published (`:450–466`). The original five-file source hashes, preload binding tokens and source compilation rather than pyc behavior remain.

The unchanged original foreign-parent probe now observes:

```json
{
  "rejected": true,
  "error": "loaded Cosmos module/package belongs to another checkout or has unverifiable origin: cosmos_framework"
}
```

The original acceptance bug is closed. The valid-package false rejection described below is a distinct regression introduced by this fix.

### F2 — supported native canvas preflight before loading

`encoding.py:53–80` matches the pinned Child classifier, including all five special 768 shapes and the short-side tier boundaries, and checks the unchanged constructor's 256/480/720 tiers. It is called by the CLI, direct plan/build, and Encode1 before the corresponding scan/cache-write or image/model-loading operations.

The unchanged 1024×1024 probe now reports native tier `768`, `cli_exit=2`, `plan_returned=false`, and `cache_created=false`. Default/supported sizes and legitimate native long-narrow sizes remain covered. No new 768 support or automatic canvas substitution was introduced.

## R1-F3 — P1: native namespace package is falsely rejected

**Location:** [encoding.py:104–109](https://github.com/wxwy/psm_wma/blob/900c87aa0ae643123477e985b6a051fb7535ee03/g2/latent_cache/encoding.py#L104-L109). The affected post-import gate is [encoding.py:444–445](https://github.com/wxwy/psm_wma/blob/900c87aa0ae643123477e985b6a051fb7535ee03/g2/latent_cache/encoding.py#L444-L445).

The checker assumes every Python package is backed by an `__init__.py` and calls `_regular_file` on both `spec.origin` and `__file__`. A legitimate namespace package has neither file origin. The checker raises `TypeError` internally and converts it to the foreign/unverifiable-origin `RuntimeError`, even if every package search path belongs exactly to the selected Child.

This is present in the actual pinned dependency, not just a hypothetical module layout:

1. [The exact Child env_parsers directory](https://github.com/wxwy/cosmos-framework/tree/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/utils/env_parsers) has four Python modules and **no `__init__.py`**. Its tree SHA is `a466f72bc34349b9abc490171a77618bee26baa9`. The full Child tree API response was not truncated.
2. [wan2pt2_vae_4x16x16.py:23](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/tokenizers/wan2pt2_vae_4x16x16.py#L23) imports `VideoTokenizerInterface`.
3. [interface.py:11](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/tokenizers/interface.py#L11) imports `cosmos_framework.utils.env_parsers.cred_env_parser.CRED_ENVS`.
4. A successful native Wan module import therefore loads the `env_parsers` namespace package into `sys.modules`. The new post-import check then rejects it before the Wan constructor at `encoding.py:500`.

### Independent observed reproduction

`test_native_namespace.py` uses the actual pinned Child package layout and the unchanged R1 checker. It imports only the namespace package, not its credential modules, Torch or Wan. It confirms the directory entries and the absence of `__init__.py`, then verifies both package search-path lists are exactly the expected selected-Child directory.

Observed result:

```json
{
  "package": "cosmos_framework.utils.env_parsers",
  "spec_origin": null,
  "file": null,
  "loader": "NamespaceLoader",
  "all_paths_in_selected_child": true,
  "accepted": false,
  "error": "loaded Cosmos module/package belongs to another checkout or has unverifiable origin: cosmos_framework.utils.env_parsers",
  "cause": "TypeError",
  "torch_loaded": false,
  "wan_loaded": false
}
```

The acceptance assertion fails: **1 FAILED, shell exit 1**. Raw log, JUnit, exact probe and full observed paths are retained.

**Evidence distinction:** the valid-package rejection is directly executed and reproduced. Its effect on a native Wan load is inferred from the exact fixed Child's unconditional import chain and the adapter's post-import check. This review did not instantiate native Wan, load real weights or run a GPU, and does not report a native Wan execution result.

### Why 265 CPU tests do not cover it

The new import-boundary fixture writes an `__init__.py` into every parent directory at [test_view_vae_encoding.py:623–629](https://github.com/wxwy/psm_wma/blob/900c87aa0ae643123477e985b6a051fb7535ee03/g2/tests/test_view_vae_encoding.py#L623-L629). It covers ordinary packages and foreign/unknown origins, but not the legitimate namespace layout used by the pinned Child. Thus the 265-case PASS and this supplemental FAIL are consistent.

### Minimum correction and acceptance

Keep the existing ordinary-module/package origin protections. Distinguish a genuine namespace package with verifiable search locations from an ordinary module with a missing/unknown origin:

- Accept the legitimate selected-Child namespace only when its loader/spec/package shape and **all** search paths establish the expected local selected directory, retaining the existing no-symlink/source-bound constraints.
- Continue rejecting foreign, mixed, empty or unverifiable namespace search paths, and ordinary modules whose origins are unknown. Do not simply allow every `spec.origin is None`.
- Add the selected-Child namespace acceptance case plus foreign/mixed namespace rejection regressions. Preserve the original two reviewer assertions and all 265 test identities.
- Keep Child/Gitlink unchanged; adding a fabricated `__init__.py` to the dependency is not the requested fix.
- Submit the minimal adapter/test increment at a new fixed implementation SHA on this same Draft PR for narrow re-review.

No cache format/index/reader or importer redesign is requested.

## Scope verification

Relative to the previous review-only commit, the implementation changes only three production files: `g2/latent_cache/encoding.py`, the two preflight call sites in `builder.py`, and the build CLI. Tests add the canvas module and append nine encoding cases. The other changes are runbook/author evidence.

The later `4ad10591` commit changes SESSION, TODO, Inbox and `post_stage_scope.json` only. The contract/source/storage/reader, existing offline index/resolver, original reviewer evidence, Child/Gitlink and V3 are unchanged. The review publication itself adds only the new formal report and its evidence.

## Exact independent test commands

Working directory: `/workspace/scratch/720989c43529/pr53_r1_review/source`.
All input images/weight bytes used by the CPU suite/replayed probes are fixtures; the supplemental namespace probe does not use weights.

```bash
export CUDA_VISIBLE_DEVICES=''
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/cosmos-framework:$PWD"
set -o pipefail

/workspace/scratch/720989c43529/pr53_review/venv/bin/python -m pytest \
  g2/tests/test_view_vae_builder.py \
  g2/tests/test_view_vae_canvas.py \
  g2/tests/test_view_vae_contract.py \
  g2/tests/test_view_vae_encoding.py \
  g2/tests/test_view_vae_source.py \
  g2/tests/test_view_vae_storage.py \
  g2/tests/test_scene_view_event_index.py \
  g2/tests/test_scene_view_index_package.py \
  g2/tests/test_scene_graph_compact_v3.py \
  --junitxml=../evidence/pytest.xml -q 2>&1 | tee ../evidence/pytest.log

/workspace/scratch/720989c43529/pr53_review/venv/bin/python -m pytest \
  ../evidence/test_review_edges.py \
  --junitxml=../evidence/review_edges.xml -q 2>&1 | tee ../evidence/review_edges.log

/workspace/scratch/720989c43529/pr53_review/venv/bin/python -m pytest \
  ../evidence/test_native_namespace.py \
  --junitxml=../evidence/native_namespace.xml -q 2>&1 | tee ../evidence/native_namespace.log

/workspace/scratch/720989c43529/pr53_review/venv/bin/ruff check \
  --select E4,E7,E9,F,I \
  g2/latent_cache/{__init__,builder,contract,encoding,source,storage}.py \
  g2/tests/test_view_vae_{builder,canvas,contract,encoding,source,storage}.py \
  tools/g2/{build,verify}_spatial_view_vae_cache.py

/workspace/scratch/720989c43529/pr53_review/venv/bin/ruff format --check \
  g2/latent_cache/{__init__,builder,contract,encoding,source,storage}.py \
  g2/tests/test_view_vae_{builder,canvas,contract,encoding,source,storage}.py \
  tools/g2/{build,verify}_spatial_view_vae_cache.py
```

To reproduce in another checkout, place the exact Root and Child under a `source/` directory and these reviewer scripts in a sibling `evidence/` directory, or change only the source/output bindings. The original and supplemental assertions must remain intact.

## Evidence and remaining Gate

Evidence directory: `docs/collab/chatgpt/evidence/2026-11-16_issue52_900c87aa/`.

- `independent_gate.json`, `result_audit.json`, `environment.json`, `remote_scope.json`.
- `pytest.log/.xml`, `review_edges.log/.xml`, both unchanged original-probe observations.
- `test_review_edges.py` (unchanged), `test_native_namespace.py`, `native_namespace.log/.xml`, `native_namespace_observed.json`.
- `native_namespace_tree.json`, 41-file source before/after and supplemental 45-file source before/after, Ruff/format logs.

**NOT_RUN:** real VAE weights/native Wan numeric/decode/GPU/performance samples, server/private-data access, full-corpus encoding, simulation, training and merge.

Close R1-F3 through a new fixed source and independent narrow review first. The subsequent representative real-VAE sample/configuration Gate remains separate; no production or V3 promotion is granted by this review.
