# R02 NVIDIA EGL attribute — format-only author handoff

Status: REQUEST_FRESH_INCREMENTAL_CODE_REVIEW; author CPU PASS, independent
review/DS validation pending. No GPU or V3 promotion performed.

| Object | Exact SHA |
| --- | --- |
| New Formal Root | `46c08127b2a13155bb22204069a1456cb01424d7` |
| New Child / Gitlink | `1069fe78841228cadbbfbe6afbd767eaed6225da` |
| Root parent, latest request/review documents | `c4d0a4281fb57797484a91b9c47387997b967f31` |
| Previous Formal Root | `286573d2d592cbd7449930e6e93f188a3a9b037d` |
| Previous Child | `37558dcc71682304f3de1848923e6cedb9b77837` |

Both new isolated branches: `v3-eval-v2-r02-format-20261103`. Subsequent evidence
and Inbox commits are metadata and must not replace the Formal Root above.

## Exact remediation

Applied Ruff **0.12.7** `format` only to Child
`cosmos_framework/simulation/robocasa/render_devices.py` and Root
`tools/v3/eval_v2_batch_tests/render_devices_test.py`, using each file's discovered
project configuration (Child `.ruff.toml`, line length 120; Root defaults).
Child diff is 4 additions / 15 deletions, Root test 9 additions / 8 deletions.
Wrapping, parentheses layout and one quote style changed; both complete
`ast.dump(..., include_attributes=False)` strings are identical before/after.
Git-object AST comparisons independently match saved snapshots and fingerprints.
No assertion, CUDA/PCI mapping, context proof, refusal, model, Local-TTT or media
semantics changed. Child was committed first, Root test/Gitlink second.

The isolated checkout initially matched the previous Formal Pair exactly, with
both repositories clean. Both original source SHA256 values match the DS report.
Ruff format failure was reproduced on exactly two files before formatting.
The latest candidate's four docs-only successors were preserved by fast-forward
before the new Root implementation commit. Old failed ordinal-fallback branch,
historical results and old Evidence were not edited.

## Author checks on the new clean Pair

- **66 distinct tests passed**, zero failures/errors/skips, 0.95 seconds, running
  only `render_devices_test.py` and `render_mapping_test.py` with the mandated
  `--noconftest -c /dev/null -q -p no:cacheprovider` options.
- Ruff0.12.7 check and format --check PASS; both-repository committed diff checks,
  before/after AST equality and syntax compilation PASS.
- Root/Child identities and clean state match before/after CPU execution. Four
  source/config bindings record exact Git Blob and SHA256, including the unchanged
  mapping regression and Child formatter config. No further source edits.
- Author runtime: Python3.12.14, pytest9.0.2, NumPy2.2.6, scipy1.15.3,
  Pillow11.3.0, requests2.32.5, PyYAML6.0.3. Existing CPU environment reused without
  dependency installation. CUDA visibility disabled, offline model/cache settings
  and all cache/temp/JUnit outputs outside repositories.

This is author execution, **not DS or GPT independent PASS**. The original DS66
run used Python3.13.11 and passed functional/check/AST while format failed; its
report-supported provenance is preserved in
`docs/collab/chatgpt/reviews/2026-11-03_R02_NV_ATTRIB_286573d2_37558dcc_DS_CPU66_FORMAT_Gate_REQUEST_CHANGES.md`.
DS private raw logs were not accessed here. Old122/379/42 suites were not rerun.

## Reproduction and artifacts

Evidence directory:
`docs/collab/codex/evidence/2026-11-03_r02_nv_attrib_format_author_cpu/`.
`artifact_manifest.json` binds 55 artifacts, including the runner/packager,
before/after source and AST dumps, original expected format-RED logs/diffs,
`final/junit.xml`, test/stdout and command records, CPU environment, `gate.json`,
Git-object AST proof, minimal source patches and source bindings.

From a clean isolated checkout of the new Formal Pair, with Root and its scripts
and Child on PYTHONPATH and CPU/offline environment variables as in
`environment.json`, run:

```bash
python -m pytest --noconftest -c /dev/null -q -p no:cacheprovider \
  tools/v3/eval_v2_batch_tests/render_devices_test.py \
  tools/v3/eval_v2_batch_tests/render_mapping_test.py \
  --basetemp /ABS/NEW_EXTERNAL_EVIDENCE/pytest_tmp \
  --junitxml /ABS/NEW_EXTERNAL_EVIDENCE/junit.xml
ruff check cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py \
  tools/v3/eval_v2_batch_tests/render_devices_test.py
ruff format --check cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py \
  tools/v3/eval_v2_batch_tests/render_devices_test.py
```

Replace the placeholder with an owned new external directory; use Ruff0.12.7.
The recorded runner's paths refer to this author's cloud workspace. Adapt paths
for independent validation while preserving the two-file/66-test scope.

## Requested next Gate and STOP

Request GPT fresh incremental Code Gate for formatting/AST/static only on the
new Pair. Then DS independently revalidates the narrow CPU/static scope.
No real NVIDIA EGL, Action Server, GPU, FFmpeg or RoboCasa run was performed;
no GPU/process inspection, model/dataset/Checkpoint read or training change.
Do not infer R02 GPU1EP PASS from CPU doubles. Do not merge V3/v3-local-ttt,
start 1EP/900EP, edit out2/NoTTT/H2/H3, resume training or dispatch DS here.
STOP after isolated candidate publication and exact remote readback.
