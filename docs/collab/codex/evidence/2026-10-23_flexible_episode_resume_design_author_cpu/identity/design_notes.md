# Flexible Episode Resume: model identity design and legacy bridge notes

Date: 2026-10-23. Base contract: Root cc7820bee1a73bd2bb2078cb7f00239944f66d37.
Scope: read-only CPU prototype, not production wiring, not GPT verdict or GPU authorization.
Owned source: `tools/v3/episode_resume_prototype/model_identity.py` and `model_identity_test.py`.

## API and sequencing

1. `build_model_identity(*, checkpoint: Path, num_steps: int, action_horizon: int, guidance: float) -> dict`: inspect current model bytes without importing torch, executing pickle or loading a model. No output writes.
2. `compare_model_identity(old: dict, new: dict) -> dict`: validate both self-digests/schemas and compare exactly the four model parameters. No filesystem writes or new baseline creation.
3. `legacy_ingest(manifest: dict, current_identity: dict, *, current_provenance: dict | None = None) -> dict`: validate original strict manifest digest, bridge its historical checkpoint observation to the freshly read strong current baseline, retain its identity and original protocol unchanged. No manifest writes.

Future integration must first build and compare the model identity (or perform the legacy bridge for a historical manifest) BEFORE creating an invocation/attempt or loading a model. After a successful comparison, validate complete historical Episodes against their ORIGINAL manifest and construct a current-plan view. A bridge decision is not an Episode validity decision. Runtime/ABI/path/resource safety preflight remains mandatory but is independent of historical model-parameter equality. Missing or corrupt model/manifest input is an input error, not an invitation to silently begin a new experiment.

## Strong new identity schema

```json
{
  "schema": "psm_eval_model_identity_v1",
  "parameters": {
    "checkpoint": {
      "path": "/canonical/actual/job/checkpoints/iter_000004000",
      "scope": "full_model_sha256_v1",
      "metadata_sha256": "<64 lowercase hexadecimal digits>",
      "shards": [
        {"name": "__0_0.distcp", "bytes": 123, "sha256": "<64 lowercase hexadecimal digits>"}
      ]
    },
    "num_steps": 30,
    "action_horizon": 16,
    "guidance": 1.0
  },
  "digest": "<SHA256 of canonical schema+parameters only>",
  "observed_checkpoint_stats": [["__0_0.distcp", 123, 1700000000000000000, 1700000000000000001]],
  "validation_scope": "full_byte_hash_plus_nonexecuting_headers_not_tensor_load_or_DCP_completeness"
}
```

- `parameters` contains exactly checkpoint, num_steps, action_horizon and guidance. Root, Child, config SHA, vendor/runtime identity, tasks, Episode count, seed, GPUs, ports, timeouts, media and progress MUST NOT be inserted as additional equality fields.
- `checkpoint` is one compound hard parameter, not an extra fifth parameter. It binds canonical actual root path, `.metadata` full SHA256, sorted unique shard names/byte counts/full SHA256. A different canonical actual path is a hard mismatch even when all bytes match; aliases that resolve to the same actual root produce the same identity. Root is the iteration directory containing `model/`.
- Hash input is UTF-8 JSON with sorted keys, no whitespace, ensure_ascii=false and finite JSON numbers only, containing `schema` and `parameters`. Shard ordering is canonical. guidance is normalized to float, including signed zero to 0.0. Integers/bools do not get silently accepted as each other for num_steps/action_horizon; bool and NaN/Inf guidance are rejected.
- `observed_checkpoint_stats` is outside the model digest and exists only as a fresh current legacy-bridge observation. A timestamp-only change to byte-identical model files does not change a NEW full-hash identity. The legacy bridge is intentionally stricter on its historical stat witnesses; see below.
- These self-digests detect accidental corruption and establish content identity; they do not cryptographically authenticate an untrusted external manifest producer.

## Explicit diagnostics

```json
{
  "status": "MODEL_MISMATCH",
  "errors": [
    {
      "parameter": "action_horizon",
      "reason": "hard model parameter changed",
      "old": 16,
      "new": 8
    }
  ],
  "warnings": []
}
```

Each changed one of the four parameters receives its own old/new entry; checkpoint changes include the complete old/new checkpoint observations rather than hiding the changed bytes. Successful comparison is `MATCH` with no errors. Invalid/unreadable input raises `IdentityInputError(code, message)`; examples are `CHECKPOINT_INPUT_INVALID`, `CHECKPOINT_HEADER_INVALID`, `CHECKPOINT_CHANGED_DURING_READ`, `MODEL_IDENTITY_INVALID`, `LEGACY_MANIFEST_INVALID`, and `CURRENT_OBSERVATION_INVALID`. Future integration must propagate these before scheduling and must preserve all historical files.

## Source, runtime, invocation, and safety separation

Keep source/runtime/config observations outside the four hard parameters. Suggested invocation envelope (future design, not written by this prototype):

```json
{
  "invocation_id": "<unique append-only id>",
  "model_identity_ref": "<strong model identity digest>",
  "invocation_plan": {
    "tasks": ["CloseFridge"], "episodes_per_task": 5, "requested_seed": 1,
    "media": {"save_rollout_mp4": true, "save_generated_video": "all", "save_init_png": true},
    "execution": {"gpus": [2,3], "base_port": 9000, "progress": true}
  },
  "source_provenance": {"root_sha": "<actual>", "child_sha": "<actual>"},
  "runtime_provenance": {"evaluation_runtime": "<actual pinned runtime object>"},
  "config_provenance": {"config_sha256": "<actual bytes>"},
  "comparability": "UNASSESSED_CONVENIENCE_AGGREGATE_NOT_SAME_CONDITION_BENCHMARK"
}
```

- The prototype legacy adapter emits SOURCE/RUNTIME/CONFIG_PROVENANCE_CHANGED or _UNKNOWN warnings with actual old/new values, `reuse_blocked: false`, and explicit convenience-aggregate qualification. It does not infer that a SHA change is harmless or that unchanged SHA proves unchanged physical execution; no single-condition benchmark claim is established by identity matching alone.
- Tasks/episodes/seed/media/resources are invocation controls. Old protocol is retained but not compared as one equality blob. Current selected-task evidence still needs per-task original data-source/config metadata preserved and comparability warnings from the Episode/plan layer; a changed task set must not become a mismatch merely because a legacy task-metadata list differs.
- ABI validity (raw15/state15/required/H16, supported action horizon and server interface), version/runtime availability, ordinary files/paths, external-process ownership, output lock, timeout bounds and cleanup protections remain safety/integrity checks. A present runtime may be invalid for execution and rejected as unsafe; a historical runtime difference alone is not a fifth model identity condition. Preserve both facts in diagnostics.
- Future append-only invocation/resource locking and output mutations belong to subsequent reviewed implementation. This read-only prototype neither implements a new writer lock nor opens output directories for writes.

## Legacy bridge schema and strength

Supported original manifests: `psm_v3_eval_identity_v1` and `psm_v3_eval_identity_vendor_v1`. Recompute the original digest using its original identity JSON, not a new digest from projected fields. Read original protocol.num_steps/R/guidance, checkpoint, model_metadata_sha256, and model_shard_stat_witnesses. The original checkpoint path, metadata SHA and complete sorted shard `(name,size,mtime_ns,ctime_ns)` inventory must all match the fresh strong observation. Any changed stat is rejected, EVEN if current full hashes are byte-identical. A weaker historical observation cannot be upgraded by silently substituting new payload hashes.

```json
{
  "schema": "psm_legacy_episode_ingest_decision_v1",
  "status": "LEGACY_STAT_BRIDGE_MATCH",
  "errors": [],
  "warnings": [{
    "code": "LEGACY_PAYLOAD_HASH_NOT_RETROSPECTIVELY_AVAILABLE",
    "reuse_blocked": false,
    "scope": "legacy_metadata_sha256_and_shard_stats_not_payload_hash",
    "message": "Only historical metadata SHA and shard size/mtime/ctime match; current full hashes are a NEW baseline."
  }],
  "original_manifest_digest": "<unchanged historical digest>",
  "original_identity": {"<original full strict identity>": "<deep copy>"},
  "legacy_model_parameters": {"<four historical parameters>": "<original binding strength retained>"},
  "current_model_identity_ref": "<new strong baseline digest>",
  "checkpoint_binding_scope": "legacy_metadata_sha256_and_shard_stats_not_payload_hash",
  "historical_payload_sha256": null,
  "original_provenance": {"root_sha": "<old>", "child_sha": "<old>", "config_sha256": "<old>", "evaluation_runtime": null},
  "original_invocation_plan": {"<original full protocol>": "<deep copy>"},
  "episode_validation": "REQUIRED_USING_ORIGINAL_MANIFEST_NOT_RELABELED_WITH_CURRENT_DIGEST"
}
```

The legacy bridge is only as strong as previously recorded stat evidence plus metadata SHA. It cannot retrospectively prove old tensor bytes, detect a pre-manifest replacement, authenticate fabricated history, or turn unknown old runtime into a known current runtime. A normal same-path rewrite is caught by ctime/mtime/stat changes, but stat matching is not a full historical cryptographic payload attestation. No old payload SHA is invented. Preserve original manifests/actions/predictions/media byte-for-byte and preserve per-Episode original digest/attempt references. Current strong hashes establish only the NEW baseline for subsequent invocations.

## Hashing, race, and header limitations

- Hashes stream every model shard, so total I/O is proportional to complete model size once per fresh observation. Model-only identity deliberately excludes optim/ and training state. No GPU or tensor memory is required; metadata bytes are collected to check structural opcodes. Real capacity/throughput planning is still needed before a future production implementation. Do not silently downgrade to prefix hashes or size-only checks for speed.
- Before/after snapshots include device, inode, size, mtime and ctime, and require unchanged complete model inventory through the read. O_NOFOLLOW, ordinary nonempty files and no model-file symlinks prevent incidental unsafe inputs. Mutation detected during hashing fails closed. This is a point-in-time observation, not an ongoing immutable lease; future execution must preserve an immutable input or independently verify the actual model loaded by the Action Server. A previously serialized observation is not a substitute for a fresh current read.
- `.metadata` is parsed with pickletools opcodes without executing GLOBAL/REDUCE/imports. Shards get bounded ZIP local-header checks. These guards catch clearly absent/corrupt/truncated header inputs but do NOT validate DCP metadata classes, tensor storage offsets, full ZIP CRC, every required distributed shard, architecture compatibility, or successful torch DCP load. Synthetic fixtures are structurally valid tiny pickle/ZIP files, deliberately not real loadable DCPs. Full-byte identity must not be advertised as DCP completeness/load proof.
- A future alternative checkpoint serialization requires an explicit parser/version design; do not accept arbitrary headers by guessing. None of these checks permits reading real training DCP in this prototype exercise.

## Focused CPU evidence

`45 passed`, 0 failed / 0 skipped, pytest 0.25s; Ruff 0.12.7 check and format --check pass; py_compile and git diff --check pass. Initial Ruff identified a test-only unused import that was removed before the focused pytest run; initial log retained.

Evidence directory: `/tmp/psm-v3-episode-resume-design-20261023/identity/`
- exact commands: `commands.txt`
- pytest full log: `pytest.log`
- JUnit: `junit.xml`
- Ruff: `ruff-check.log`, `ruff-format-check.log`, initial `ruff-check-initial.log`

Tests cover each old/new hard mismatch, same-path payload replacement with same size/restored mtime, canonical full-hash stability after timestamps change, stricter legacy stat rejection, malformed/missing metadata and shards, no symlink/model execution, changed-during-read rejection, unknown/mixed source/runtime/config warnings, mutable invocation plan fields, preserved legacy identities, and an adapter test that calls the UNMODIFIED actual production legacy identity helper in tiny clean synthetic Git Root/Child repositories. Original old manifest bytes/inode/timestamps are asserted unchanged; no real DCP, model, simulator or GPU is accessed. This is author CPU design evidence, not DS independent acceptance or a production/GPU Gate.
