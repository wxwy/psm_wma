# R09-B2 P1 production manifest closure review

- Request: `3527c7de9a772a76c925ad5aec0523e7dfc29423`
- Evidence commit: `4b087be0c0e58a6471f7f62eed526eedac4cca84`
- Source root: `4177e83088e6c2e0a2b620bfdf8593e325fc375b`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **APPROVE_TO_CLOSE_P1_PRODUCTION_MANIFEST**

## Independent findings

### PASS — production budget and provenance are frozen in the committed header

`artifacts/g0/r09/b2/p1_production_manifest_100x16x128/header.json` records the exact matched-run stream budget:

- `optimizer_updates=100`
- `grad_accum=16`
- `max_samples_per_batch=128`
- `record_count=204800`
- `world_size=1`
- `num_workers=0`
- `shuffle_seed=42`

The same header records source root `4177e83`, submodule/Gitlink `21d064f`, the recipe TOML hash, builder/verifier hashes, dataset source/wrapper hashes, per-suite dataset-info/parquet hashes, cache-manifest hashes, records SHA256, and four suite-record SHA256 values.

This closes the earlier blocker where P4 only had the tiny 4-record CPU P1 summary rather than a production-sized stream identity.

### PASS — committed verifier result covers the full production manifest contract

`verification.json` is `PASS` with all 14 checks true. I independently inspected the verifier source at source root `4177e83`; these checks are not summary-only assertions. The verifier:

1. reads all `records.jsonl` entries and requires `len(records) == optimizer_updates * grad_accum * max_samples_per_batch`;
2. requires contiguous and unique ordinals;
3. checks exact record schema and optimizer-update/microbatch/sample arithmetic;
4. checks suite round-robin selection from the frozen suite order;
5. reloads the referenced latent-cache episode and requires every referenced `windows[start_frame]` value to be a dict;
6. recomputes each suite JSONL SHA and reconstructs the global record list from the four suite partitions;
7. recomputes builder/verifier/dataset/wrapper/TOML and dataset metadata/parquet hashes;
8. reconstructs the four LIBERO datasets and checks every record's `(task_index, episode_index, start_frame)` against `dataset_flat_index` in both directions.

Therefore the verifier PASS covers the complete 204800-record structural/cache/provenance contract rather than merely accepting the header metadata.

### PASS — artifact files are committed as immutable evidence

The evidence commit contains the production `header.json`, `records.jsonl`, four suite JSONL files, and `verification.json`. The large records blob is beyond the GitHub connector's single-response payload limit, so I could not independently stream all 43.9 MB into this review process for a second local SHA pass. This is not treated as a blocker because the audited source-controlled verifier recomputes the records and suite hashes from the actual files and its committed result is tied to the frozen source/provenance above.

No evidence in this review authorizes or demonstrates GPU, model/VAE/MP4 access, `torchrun`, training, evaluation, or inference.

## Gate decision

**`APPROVE_TO_CLOSE_P1_PRODUCTION_MANIFEST` is granted.**

This closes only the production P1 stream-manifest prerequisite for P4. It does **not** close P4 Launch D005 and does not waive the remaining P4 verifier hardening around canonical P3 ownership, production budget/job identity/environment/output binding, or actual D005 artifacts.

This review does not authorize P5, B2-T, `torchrun`, GPU, training, evaluation, inference, closed-loop, or broader scope.
