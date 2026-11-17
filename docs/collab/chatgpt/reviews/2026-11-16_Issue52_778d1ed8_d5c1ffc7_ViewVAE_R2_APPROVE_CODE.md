# Issue52 / PR53 — independent R2 namespace compatibility review

- Review date: 2026-11-16 CST (Asia/Shanghai).
- **Formal implementation Root: `778d1ed8a031429fd857c980fc872d4c85123cd1`.**
- **Formal Child/Gitlink: `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`.**
- Previous implementation: `900c87aa0ae643123477e985b6a051fb7535ee03`.
- Increment base / previous review-only commit: `49374cb343d02bf2e3ca4d13dc89c5dfe55a8480`.
- Author bookkeeping HEAD inspected: `fe6a8b426b1df45aafb5cab07ea3a5a1fa988d8b`; it does not replace the formal implementation.
- V3 observed: `55cc5181abf8ca4b1e2a3a6b415699c457cc080b`.
- PR: https://github.com/wxwy/psm_wma/pull/53 — open, Draft, unmerged at inspection.

## Formal technical verdict: APPROVE_CODE

**R1-F3, the legitimate native namespace-package rejection, is CLOSED at this exact pair. The independent full scoped CPU suite passes 283/283 and all three unchanged original reviewer probes pass 3/3. No new blocking issue was found in this narrow increment.**

This approves the submitted View VAE cache implementation within the established CODE/CPU scope, incorporating the previous review of cache organization/index/reader and the closed F1/F2 corrections. It does not certify a complete native Wan load, real-weight numerical/decode quality, GPU behavior, throughput, complete-corpus readiness, training, or V3 merge.

| Finding | Final CODE/CPU status at R2 |
|---|---|
| F1: foreign Cosmos parent/helper acceptance | CLOSED; original rejection probe passes |
| F2: unsupported native canvas tier accepted by plan | CLOSED; original 1024×1024 plan probe passes |
| R1-F3: selected-Child native namespace falsely rejected | **CLOSED; unchanged original native namespace acceptance probe passes** |

The owner-authorized Issue52 handoff is scoped independent CODE/CPU review. The current SESSION/Inbox explicitly overrides historical V2/MM/Kimi waits for this scope; no other reviewer verdict is inferred.

## Independent validation

The reviewer executed these tests against a separately prepared fixed-source snapshot using Python 3.12.14, Torch 2.15.0+cpu, pytest 9.2.0, NumPy 2.5.5, Pillow 13.0.0 and Ruff 0.17.5. Test execution used CPU only and no network access.

| Check | Result |
|---|---|
| Full scoped regression | **283 PASS, 0 failures, 0 errors, 0 skips**; 14.14 s |
| Three original reviewer assertions | **3 PASS, 0 failures, 0 errors, 0 skips**; JUnit 0.522 s |
| Prior test identities | All **265** retained; exactly **18** additional identities |
| Prior test source | All nine previous test files byte-for-byte unchanged |
| Selected Ruff E4/E7/E9/F/I | PASS |
| Formatting | PASS; 15 product/test/CLI files already formatted |
| Source binding and stability | **48/48 SHA256 matched**, unchanged before/after execution |
| Encoding scope | AST outside `_check_cosmos_origins` unchanged |
| Original probe integrity | Both original script files byte-for-byte unchanged |

The three probe cases are separate overlapping evidence, not added to the 283-case suite. The previous independent RED evidence remains immutable: F1/F2 at aa0450b8 and namespace rejection at 900c87aa. Their unchanged assertions are now GREEN on R2; the reviewer did not overwrite or rerun those old evidence files.

The 283 cases comprise builder21, canvas32, contract18, encoding61, namespace18, source31, storage43, event-index24, index-package4 and compact-v3 31. Test identity comparisons use JUnit `classname::name`; no original case was dropped or skipped.

Source retrieval uses the GitHub plugin at the exact implementation SHA, checked Git blob hashes for newly fetched files, and the previously independently verified source snapshot for unchanged files. All 48 author-bound hashes were then recomputed independently. The local snapshot is scoped rather than a full git clone. A missing copy of an unchanged reviewer script was populated and all 48 hashes verified **before** project test execution.

Original probe SHA256 values:

- `test_review_edges.py`: `3767287d3f30f365b0c9318fff0796ec180c845448cbae94bf72791b1df2e197`.
- `test_native_namespace.py`: `41c1c4365d78c5e8bdd56356b378af6f2061fea1588e266025f13882d4211405`.

## Why the namespace fix closes R1-F3

The only production change is inside [`_check_cosmos_origins`](https://github.com/wxwy/psm_wma/blob/778d1ed8a031429fd857c980fc872d4c85123cd1/g2/latent_cache/encoding.py#L83-L146). The new branch at lines109–129 handles a package with absent file/origin through all of the following checks:

- Standard `NamespaceLoader`, with the module loader identical to `spec.loader`, and `spec.has_location=False`.
- A real expected directory under the selected Child, with no symlink in it or its parents.
- No `__init__.py` or dangling `__init__.py` symlink disguising an ordinary package.
- Identical package/spec search-path inventories, with absolute paths.
- The common check at lines135–141 still requires **nonempty** inventories and **every** path to equal the expected selected-Child directory.

Ordinary source modules/packages continue through the original file-origin checks at lines130–134. This is not a blanket acceptance of `origin=None`. The previous `unknown_origin` case in `test_view_vae_encoding.py:656–659` still clears only an ordinary module's spec origin, preserving its file, and remains passing.

The actual pinned Child `cosmos_framework.utils.env_parsers` namespace is now accepted. The unchanged reviewer probe reports:

```json
{
  "package": "cosmos_framework.utils.env_parsers",
  "spec_origin": null,
  "file": null,
  "loader": "NamespaceLoader",
  "all_paths_in_selected_child": true,
  "accepted": true,
  "torch_loaded": false,
  "wan_loaded": false
}
```

This directly closes the CPU-reproduced false rejection. It establishes compatibility of that actual package and guard; it is not a claim that a complete native Wan import/model construction was executed.

## Retained rejection behavior and lifecycle

The 18 added namespace cases at [`test_view_vae_namespace.py`](https://github.com/wxwy/psm_wma/blob/778d1ed8a031429fd857c980fc872d4c85123cd1/g2/tests/test_view_vae_namespace.py) consist of:

| Coverage | Cases |
|---|---:|
| Actual selected Child namespace, no Torch/Wan import | 1 |
| Namespace present before / first loaded during controlled import, each checking cross-encoder reuse | 2 |
| Foreign/mixed paths; empty paths; module/spec path disagreement; unknown/mismatched loader; inconsistent file/origin/location; ordinary missing origin/file; symlink/missing directory; namespace changed to ordinary package | 15 |

The negative namespace fixtures use real Python namespace specs/loaders and isolated subprocesses. They require the checker's `RuntimeError`, preserve the loaded module object, and verify no binding token was published.

The origin checks still run before import (`encoding.py:385–386`) and after import (`:467–468`). Verified binding tokens are published only after the existing source/loader checks (`:473–489`). The five bound source modules, hashes, pyc safeguards, preloaded-bound-module protections and reuse behavior are unchanged.

All three original probes also confirm:

- A foreign parent from another checkout is still rejected.
- 1024×1024 is still native tier768 and is rejected with CLI exit2; no plan is returned and no cache is created.
- The valid selected-Child namespace is accepted while Torch/Wan remain absent.

No additional importer or cache redesign is requested.

## Scope verification

The exact increment from review-only parent49374cb3 contains one production function change, a new namespace test file, a runbook appendix and author evidence. The following author commit fe6a8b42 changes only SESSION, TODO and canonical Inbox.

Cache contract/schema/source/index/storage/reader, builder, both CLIs, canvas preflight, original assets, existing G0/G1/Local/model/nav_sg, Child package layout/Gitlink, V3, and previous independent review reports/evidence are unchanged. Local protected-source comparisons and the exact remote commit file list are retained in the evidence.

This review publication adds only its formal report and independent evidence. The formal implementation remains778d1ed8 regardless of later review/bookkeeping commits.

## Exact independent execution

Working directory: `/workspace/scratch/720989c43529/pr53_r2_review/source`.
Inputs: fixed source, synthetic CPU fixtures/identity-only weight bytes, and actual pinned Child namespace directory. No real weights were used.

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
  g2/tests/test_view_vae_namespace.py \
  g2/tests/test_view_vae_source.py \
  g2/tests/test_view_vae_storage.py \
  g2/tests/test_scene_view_event_index.py \
  g2/tests/test_scene_view_index_package.py \
  g2/tests/test_scene_graph_compact_v3.py \
  --junitxml=../evidence/pytest.xml -q 2>&1 | tee ../evidence/pytest.log

/workspace/scratch/720989c43529/pr53_review/venv/bin/python -m pytest \
  ../evidence/test_review_edges.py ../evidence/test_native_namespace.py \
  --junitxml=../evidence/review_probes.xml -q 2>&1 | tee ../evidence/review_probes.log

/workspace/scratch/720989c43529/pr53_review/venv/bin/ruff check \
  --select E4,E7,E9,F,I \
  g2/latent_cache/{__init__,builder,contract,encoding,source,storage}.py \
  g2/tests/test_view_vae_{builder,canvas,contract,encoding,namespace,source,storage}.py \
  tools/g2/{build,verify}_spatial_view_vae_cache.py

/workspace/scratch/720989c43529/pr53_review/venv/bin/ruff format --check \
  g2/latent_cache/{__init__,builder,contract,encoding,source,storage}.py \
  g2/tests/test_view_vae_{builder,canvas,contract,encoding,namespace,source,storage}.py \
  tools/g2/{build,verify}_spatial_view_vae_cache.py
```

For another environment, preserve the fixed Root/Child under a `source/` directory with the reviewer scripts in sibling `evidence/`, or rebind only source/output paths. The assertions must remain unchanged.

## Evidence and next stage

Evidence directory: `docs/collab/chatgpt/evidence/2026-11-16_issue52_778d1ed8/`.

It contains `independent_gate.json`, `result_audit.json`, `remote_scope.json`, `environment.json`, full and probe raw logs/JUnit, all three probe observations, both original scripts, source before/after fingerprints, Ruff/format logs.

**CODE/CPU gate is closed at this exact pair.** Next is the separately authorized representative real-VAE sample/configuration gate: complete native import and real-weight load, independent T1 spatial output, actual cache write/read/index checks on representative Views, and measured numerical/decode/resource behavior. The existing 256×256 white fit/pad and FP32-storage defaults remain candidate settings until that gate.

**NOT_RUN:** complete native Wan import/construction, real weights, GPU encoding/decode/numerical/performance samples, server/private-data access, full-corpus encoding, simulation, training and merge. This report does not authorize those actions or change PR Draft status.
