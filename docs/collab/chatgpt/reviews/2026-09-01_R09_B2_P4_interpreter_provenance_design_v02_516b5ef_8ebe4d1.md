# R09-B2 P4 interpreter-provenance design v0.2 review

- Request commit: `516b5ef4f26d15dd6824d6ce3c0b371d97140d5b`
- Design commit: `8ebe4d139c089cdeca9307c33aa2b2c3086e1004`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Scope

This review is design-only. It reviews whether v0.2 closes the previous two HIGH findings and one MEDIUM finding without creating a new false-PASS or impossible execution contract. It does not authorize implementation, P4 record regeneration, P5 export/compose, GPU, training, evaluation, or inference.

## Findings

### HIGH — the frozen resolution profile does not yet describe the P4 D005 training environment

`docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.2_2026-09-01.md:15,24-28`

v0.2 freezes the resolver target as CPython 3.13 / Linux / x86_64 with only `dependency_groups=["cu130"]`, then calls the resulting graph the complete runtime closure.

That is not yet the same thing as the environment required by the frozen P4 D005 command. P4 launches `cosmos_framework.scripts.train`, while the frozen Cosmos `pyproject.toml` places training-only runtime dependencies under the project optional extra `train` (including packages such as `datasets`, `megatron-core`, `lerobot`, etc.). A `cu130` dependency-group selection alone does not prove those project extras are present. Thus the proposed verifier can certify a dependency graph that is internally correct for one lock projection but incomplete for the actual D005 training entrypoint.

Required:

- freeze the exact install/profile tuple used by P4, distinguishing project extras from dependency groups, e.g. explicit `project_extras` plus `dependency_groups` rather than one `dependency_groups` list;
- derive that tuple from the canonical P4 environment/install contract, not from what happens to make P5 compose succeed;
- make P4 pair verification fail if the recorded interpreter environment is not the exact D005 profile;
- add a negative where the `train` profile is omitted while base + CUDA packages are otherwise valid.

### HIGH — the all-wheel closure is incompatible with source types already present in the frozen lock

`docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.2_2026-09-01.md:25-28,44,54-58`

The design says every package in the complete runtime closure must resolve to a unique wheel archive and that any `.pth` under site-packages is an unconditional failure.

However the frozen `uv.lock` already contains non-wheel source identities. In particular, `cosmos-framework` itself is `source = { editable = "." }`; the lock also contains Git-sourced packages such as `lerobot` and `megatron-core` for training-related profiles. Therefore `package set = complete runtime closure` cannot simultaneously mean `every package has one wheel` unless the design explicitly partitions source types.

This matters for trust, not only feasibility: silently excluding editable/Git packages from `environment_provenance` would leave executable Python payload outside the independently bound closure; forcing them through a wheel-only path would make a valid frozen environment unverifiable.

Required:

- define an exact source-type grammar for the lock projection:
  - first-party editable `cosmos-framework`: payload identity comes from the frozen Gitlink/tracked source tree and is not self-certified by installed editable metadata;
  - registry wheel packages: lock wheel SHA -> wheel RECORD -> installed payload;
  - Git/VCS packages, if present in the exact P4 profile: bind the locked commit/source identity and an independently derived installed payload identity, or fail the design if that source type is intentionally unsupported;
- distinguish an inert, independently bound editable-install artifact from arbitrary startup injection. With `-I -S`, an approved editable `.pth` need not be executed; either bind the exact expected artifact and prove it remains inert, or define an install profile that provably contains no editable `.pth`. Blanket `any .pth = FAIL` is not sufficient while the frozen lock itself specifies an editable root project;
- add positive/negative tests for each supported source type and for an unexpected additional `.pth`.

### MEDIUM — the initial `-I -S` sys.path grammar is underspecified for the base interpreter's default zip entry

`docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.2_2026-09-01.md:36-44,59`

The bootstrap requires every initial `sys.path` entry to be a strict existing stdlib/dynload directory, rejects any zip entry, and compares paths with `resolve(strict=True)`. Standard CPython builds commonly place a `<prefix>/lib/python313.zip` candidate on initial `sys.path` even when that archive does not exist. Under the current wording, a clean approved interpreter can therefore fail before provenance checks solely because of its normal getpath output.

Required:

- freeze the exact allowed initial getpath grammar for the reviewed base interpreter;
- if the canonical `python313.zip` candidate is present, either require it to be absent by independently verified interpreter configuration, or accept only that exact base-prefix candidate as a non-importable/nonexistent bootstrap entry and remove it before the rewritten runtime path;
- never generalize this into arbitrary zip acceptance;
- add a permanent CPU regression for the exact expected initial path vector and an unexpected zip/path negative.

## What improved

The previous review's core blockers are substantially addressed:

- package provenance is no longer intended to trust current installed METADATA/RECORD as truth; the design now anchors registry payloads to frozen `pyproject.toml` / `uv.lock` and wheel hashes;
- lexical venv launcher and base binary identities remain distinct;
- `-I -S` moves the trust check before `site`, `.pth`, `sitecustomize`, and user-site execution;
- the rewritten runtime `sys.path` is exact, ordered, duplicate-free, and symlink-canonical rather than subset-based.

These should be retained in v0.3.

## Gate decision

`APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` is **not granted**.

Codex may revise the design only. The next design should close the exact P4 install-profile/source-type grammar and the initial CPython getpath grammar; no implementation or runtime work is authorized yet.

Still not authorized:

- P4 interpreter-provenance implementation;
- creating/modifying an isolated venv for this gate;
- P4 static record regeneration or closure;
- P5 export/retry/compose or `load_experiment_from_toml`;
- CUDA/GPU or `torchrun`;
- model/dataloader/optimizer/checkpoint construction;
- weights/data/MP4 access;
- training, evaluation, inference;
- P5 closure, B2-T, or any later gate.
