# G2 spatial-View independent Encode1 cache — Issue52

Date: 2026-11-16. This is the code/CPU implementation candidate for
[Issue #52](https://github.com/wxwy/psm_wma/issues/52), pending independent review.
Baseline Root: `55cc5181abf8ca4b1e2a3a6b415699c457cc080b`.
Unchanged Cosmos Child/Gitlink: `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`.
The fixed implementation SHA and actual CPU evidence are recorded in the final
handoff; these baseline SHAs are not an implementation approval.

## Scope and reused entry points

Encode **every valid spatial View**, regardless of current task selection.
Within each Episode, save one numeric file per logical View, containing all of
that View's physical PNG versions and logical-state reference indices. This
explicitly supersedes earlier proposals to encode only selected task images,
write one Episode-wide tensor file, or write one tensor file per PNG.

The source is an already completed G2 v1/v2/v3 package. Reuse
`scene_view_event_index.resolve_indexed_png`; do not recompute 1mm/1° events,
sample rate, memberships, SG, MuJoCo state, nav_sg or rendered images. Logical
view IDs preserve the complete relative PNG path, minus `.png`, so equal
basenames under different Room/Island paths never collide.

Actual dependencies are kept in this direction:

```text
tools/g2/build_spatial_view_vae_cache.py
  -> g2.latent_cache.builder
       -> source -> existing safe PNG resolver
       -> encoding -> existing Cosmos normalizer + Wan VAE
       -> contract + storage
tools/g2/verify_spatial_view_vae_cache.py
  -> builder verification -> contract + storage (+ explicit source audit)
future training adapter
  -> storage only
```

`source.py` isolates input/index validation from scheduling. It checks the
original manifest/completion identity and all physical PNG owners; it does not
reconstruct SG to build an image cache. The source validation scope is declared
in cache metadata. Existing complete v2/v3 validators remain separate and need
no relaxation for the new side directory. Their fixture compatibility is
tested alongside this candidate.

`encoding.py` reuses `vision_encoder.normalize_uint8_item` and
`Wan2pt2VAEInterface` from the pinned local Child. It does not call Local's
`encode_current_composite_visual96`, import an online daemon or Policy, copy a
VAE network, build G1 17-frame windows, combine left+wrist images, or average
the spatial latent grid into Visual96.

## Candidate preprocessing and encoding ABI

`preprocessing_recipe(height=256, width=256, interpolation="lanczos")` describes
one uint8 RGB image: aspect-preserving fit, deterministic half-up resized
dimensions, centered white `[255,255,255]` padding and a fixed explicit canvas.
The candidate permits explicit canvas/interpolation choices; Wan canvases must
have dimensions divisible by16. There is no automatic bucket fallback.

`preprocess_rgb(rgb_uint8_HWC, preprocessing)` returns the padded RGB canvas and
metadata: original/resized/canvas H/W, four padding widths, half-open content
rectangle, interpolation/library versions and RGB layout/range. White source
pixels remain valid image content. The valid rectangle is geometric evidence;
no latent receptive-field/patch-validity mask is invented from pixel colors.

`WanSingleFrameEncoder(weights_path, device="cuda", cosmos_root=None)` is lazy.
Its `descriptor()` binds local weight bytes, adapter/Child computation sources,
effective constructor, normalization/scale/precision and software versions
without instantiating Wan or touching GPU. `encode(rgb, preprocessing)` loads
the existing local Wan once and returns `(latent_CHW_cpu_fp32, metadata)`.

The adapter establishes its pinned Cosmos module provenance on the first
actual `encode` call. Modules already imported externally before that binding,
without registration by this adapter, are conservatively rejected. The adapter
does not reload or rewrite those modules to present them as its own pinned
imports. The fresh-process CLI follows this lifetime requirement; future online
integration must explicitly arrange the same import/provenance lifecycle.
Reusing this preprocessing/Encode1 interface does not itself certify integration
into an already initialized Policy or service process. `descriptor()` remains
lazy and does not establish a model runtime or access GPU.

Each invocation is independent input `[1,3,1,H,W]`, frozen eval/no-grad, eager,
non-streaming, with no retained encoder state. Existing Wan BF16 computation
and internal mean/inverse-standard-deviation scaling are used; no extra scale
or pooling is applied. Actual output rank and T=1 are checked before storing
`[C,H_z,W_z]`. `H_z/W_z` come from actual encoder output, not a canvas-size guess.
The current candidate deliberately supports B=1 only. Different View/episode
batch ordering and B>1 performance/numerical parity are not approved by fake
CPU tests.

The preprocessing/encoder dependencies and storage dtype form `recipe_id`.
FP32 storage is the initial no-additional-quantization baseline. Float16 or
bfloat16 storage is an explicit candidate conversion requiring a real error
measurement; existing BF16 computation does not prove storage quantization
lossless. These defaults do not freeze the eventual production recipe.

## Storage and identities

```text
tasks/<task>/episodes/episode_NNNNNN/
  episode_manifest.json             # existing, unchanged
  COMPLETE.json                     # existing, unchanged
  state_.../                        # existing materialized state directories
  vae_cache/
    manifest.json                   # new cache identity + complete view index
    COMPLETE.json                   # cache's own completion record
    .build.lock                     # persistent local writer lock
    sixview/<logical-path>.pt
    islands/<island-id>/<direction>.pt
```

The diagram is illustrative: actual relative View paths are retained, including
additional Room directories. Absent views have no payload and no valid latent.
Views appearing/disappearing midway are indexed from every state, not only the
first. Current logical state/frame and physical owner state/frame are separate;
an old image reference never changes the current sample's identity. A state
with no materialized directory can still reference an older physical owner.
No previous image is implicitly filled into an absent current View.

The per-View `.pt` representation contains a CPU tensor `[U,C,H_z,W_z]`, exact
episode/View/source/recipe binding, every physical owner PNG path/hash,
preprocessing provenance and state-to-record mapping. Physical owner references
reuse one record. No approximate content deduplication or cross-Episode
registry is introduced. Image reuse is not geometric/member-version reuse;
unavailable world geometry or robot pose fields remain explicitly unknown.

Each numeric file is written through a private same-directory temporary file,
validated, and atomically published without overwriting an existing file.
A same-target nonblocking local writer lock prevents competing publishers.
Resume can reuse only complete files with matching source and recipe. Temporary,
corrupt or mismatched files do not count as complete. No mixed recipe silently
replaces the same target namespace. Only after all expected Views and references
are covered does the builder publish the cache's own completion marker. Source
manifest/completion/PNG fingerprints are checked across the build; original
input bytes and original completion records are not rewritten.

## Reader ABI and efficiency

```python
from g2.latent_cache.storage import open_episode_index, ViewReader

index = open_episode_index(episode_root, expected_recipe_id=recipe_id)
reader = ViewReader(index, max_views=4, max_bytes=256 * 1024 * 1024, mmap=True)
sample = reader.read_view("sixview/floor_top", logical_state_id)
samples = reader.read_many(logical_state_id, selected_view_ids)
```

The index binds the Episode, so callers need not supply a second ambiguous
episode key to each method. `read_many` keeps selection order, including repeated
requests; absent results retain current identity with `present=False` and
`latent=None`. A present result contains the selected CHW tensor plus owner and
preprocessing provenance.

Opening an index reads only small cache/source identity files. Payload access
uses CPU `torch.load(weights_only=True, mmap=True)` and file-level bounded LRU.
Only selected files are opened; a selected record's data integrity is checked
without cloning or moving its entire history. Full file/content inspection is
an explicit offline verification operation, not a per-sample training step.
Reader import/index opening do not import Wan, builder, MuJoCo, ROS, EGL,
Policy, daemon or network services. The reader's mapping/cache budget is not a
hard process-RSS bound and cannot cap tensors retained by its caller.

## CLI and exact commands

Run from the Root checkout. Dataset root and local weight path are explicit.
Repeat `--task` or `--episode`; omitted selectors cover all completed Episodes
under the dataset's standard task/episode layout. There is deliberately no
view/task-candidate filter that could trim cache coverage.

```bash
python -m tools.g2.build_spatial_view_vae_cache --help
python -m tools.g2.verify_spatial_view_vae_cache --help

# Read-only plan; no VAE/GPU or cache output.
python -m tools.g2.build_spatial_view_vae_cache \
  --dataset-root /path/to/robocasa365-target-atomic-6views \
  --task CloseBlenderLid --episode 0 --weights /path/to/local/wan_vae.pth \
  --device cuda --height 256 --width 256 --interpolation lanczos \
  --storage-dtype float32 --batch-size 1 --dry-run

# Complete cache/schema/payload/source audit, without VAE construction.
python -m tools.g2.verify_spatial_view_vae_cache \
  --dataset-root /path/to/robocasa365-target-atomic-6views \
  --task CloseBlenderLid --episode 0 --recipe-id <sealed-recipe-sha256>
```

`--dry-run` (alias `--plan`) and `--execute` are mutually exclusive explicit
actions. Only the latter performs real encoding. Its implementation is supplied
now, but real sample execution is **NOT_RUN** in this task and requires the
subsequent authorization described in Issue52. In that separately authorized
sample command, replace `--dry-run` with `--execute`; add `--resume` only to
reuse the same source/recipe namespace.

Ordinary verify defaults to a source audit as well as numeric integrity;
`--skip-source` omits the full source PNG audit while retaining cache-internal
identity, physical-owner provenance and logical-state-to-record validation.
`--recipe-id` enforces expected cached configuration. `--reencode` is the
independent real-VAE comparison action and
requires `--weights`; it uses the sealed cache preprocessing and matches the
encoder identity. `--atol/--rtol` default to strict zero, are explicit and
nonnegative, and have no effect on ordinary verification. A tolerance is a
declared comparison criterion, not evidence that a proposed production precision
was approved. Weight/model/tolerance flags without `--reencode` are rejected so
ordinary verification cannot silently become model execution.

## CPU fixtures, pass/fail and evidence

Example CPU-only reproduction, using a prepared environment with CPU Torch,
NumPy, Pillow and pytest and the pinned Child checkout:

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0 \
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m pytest -q \
  g2/tests/test_view_vae_*.py --junitxml=/tmp/g2-view-vae-cpu.xml
```

Fixtures cover absent/multiple Island Views, mid-Episode appearance/disappearance,
noncontinuous logical IDs and original frames, physical and reused owners,
states without directories, selected-only payload access and bounded LRU,
T=1/preprocessing/fake-tokenizer state guards, round-trip dtype/shape/finite,
changed source/weights/recipe, corrupt data, bad paths/symlinks/references,
interruption/resume, competing writers, unchanged input bytes and compatibility
with the original completed-package validators. CLI help/dry-run and ordinary
reader imports must not load a model or contact services.

Passing CPU fixtures proves the format/index/lifetime/IO contract under those
fixtures. It does not prove native Wan numeric parity, reconstructed arrow or
small-object quality, B>1 isolation, quantization accuracy, real GPU sample
throughput, storage optimum, training utility or complete corpus readiness.
Actual command output/JUnit and fixed source identity are recorded in the
code/CPU evidence and final handoff below.

## Independent real Gate and stop condition

After code review, separately authorize representative real samples such as
CloseBlenderLid/000000 and CloseFridge/000502 plus missing-direction/multiple-
Island cases. Compare native independent Encode1 and cached readback, owner vs
logical indices, preprocess/decode visual quality, file sizes, encode time,
selected/all-view read P50/P95, CPU occupancy and concurrency effects. Keep
original source images, arrows, SG and manifests on the server. Only then freeze
the production canvas/precision/batch settings and request a full-corpus plan.

This candidate does not add Global Reader/KV, language enhancement, task recall,
state15/Pose5 changes, training Dataset integration, Agent or online services.
No real VAE/GPU sample, full encoding, production data operation, simulation
evaluation, training, Child/Gitlink change or merge is performed by its CPU
delivery. Stop at a fixed Root SHA and independent Draft PR for GPT review.


## Recorded code/CPU candidate results

The final source-stable run on 2026-11-16 passed **224/224**, with zero failures,
errors or skips: 165 new cache fixture cases and 59 existing event-index,
index-package and compact-v3 regressions. This is an author CPU result, not
GPT independent acceptance. Environment: Python 3.12.14, Torch 2.15.0+cpu,
Pillow 13.0.0, NumPy 2.5.5, pytest 9.2.0. No native Wan weights were loaded.

Exact final reproduction from the Root checkout in the prepared CPU venv:

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH="$PWD/cosmos-framework:$PWD" \
  /workspace/.venvs/g2-view-vae-52/bin/python -m pytest \
  g2/tests/test_view_vae_*.py \
  g2/tests/test_scene_view_event_index.py \
  g2/tests/test_scene_view_index_package.py \
  g2/tests/test_scene_graph_compact_v3.py \
  --junitxml=artifacts/g2_view_vae_issue52/pytest.xml -q
```

Evidence is in `artifacts/g2_view_vae_issue52/`: `gate.json` contains exact
commands and actual results; `pytest.xml`/`pytest.log` preserve the final run;
`source_sha256.json` binds the 13 new Python files, three baseline regression
files and five unchanged Child sources. `environment.json`, CLI help, selected
Ruff (`E4,E7,E9,F,I`), format and diff-check logs are included. The development
`pytest_fix.xml` overlaps the final suite and is not added to its count.

Prepublication peer review closed the reusable-output buffer alias, mutable
reader metadata, skip-source internal identity/preprocessing and encoder loaded
source issues. Bound Cosmos modules compile verified source bytes without
reading or writing Child bytecode caches. Negative controls include a stale
same-size/same-timestamp `.pyc`, external preload, transitive stale dependencies,
re-signed mismatched cache headers and changed preprocessing dimensions.

Source hashes were unchanged across the final run. Original G0/G1/Local/model
implementations, original G2 producers/validators, nav_sg, Child and Gitlink were
not modified. Real VAE/GPU samples, production recipe freeze, complete-corpus
encoding, training and merge remain **NOT_RUN**. The fixed implementation SHA
is listed in the canonical Inbox handoff and Draft PR.
