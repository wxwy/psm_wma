# R09-B2 P1 stream-manifest design review — root 350b83d / submodule+Gitlink eaa0f97

## Verdict

**APPROVE_TO_IMPLEMENT_B2_P1**

Scope is limited to implementing and CPU-only validating the enforceable data-stream manifest contract. This does **not** authorize B2-T, GPU, model loading, optimizer/training execution, evaluation, inference, closed-loop, or backend freeze.

## Why the design is acceptable

P1 correctly addresses only the first P0 blocker: same seed is insufficient to prove recurrent and TTT consume the same windows. The proposed contract turns the future B2 stream into a globally ordered, machine-auditable sequence rather than relying on RNG equivalence.

The following design choices are approved:

- canonical ordered records with `ordinal` plus readable window identity;
- source/header binding to root/submodule/Gitlink, dataset/cache/config hashes and frozen budget;
- single-process deterministic consumption for B2 (`world_size=1`, `num_workers=0`, ordered delivery);
- fail-closed manifest-aware replay with no random replacement/retry;
- requested-vs-observed ordinal-by-ordinal verification;
- resume by manifest offset rather than RNG fast-forward;
- CPU-only negative tests and deterministic regeneration before any B2-T review.

## Required implementation hard gates

1. **Identity naming must match the actual dataset contract.** The current source exposes `task_index`; implementation may call the external field `task_id` only if it proves and records an explicit deterministic mapping. Otherwise use `task_index` in the canonical identity. Never silently rename one into the other.

2. **Record-count arithmetic must be derived from the actual B2 packer/joint-loader semantics, not assumed.** The implementation must machine-prove the mapping from `optimizer_update`, `microbatch`, suite scheduling and `sample_in_microbatch` to global `ordinal`. If the four-suite joint loader means the approved formula differs from `100 × grad_accum_iter × max_samples_per_batch`, the builder must fail until the formula is corrected and frozen; do not preserve an incorrect formula for documentation consistency.

3. **Manifest generation must reproduce the exact intended episode-block shuffle semantics without consuming mutable training RNG state.** Store the effective shuffle seed/epoch semantics and make two independent builds byte-identical. Do not infer equality merely from a configured seed.

4. **`dataset_flat_index` must be checked bidirectionally.** For every record, resolve flat index -> `(task/episode/start_frame)` and also prove the identity maps back to the same unique flat index. Duplicate/ambiguous window identities must fail.

5. **Cache-window existence must be hard-gated per record before PASS.** A suite-level manifest hash alone is insufficient; every requested `(episode_index,start_frame)` must resolve to the exact-window cache entry expected by the current cache contract.

6. **Observed replay must preserve the record IDs through the real B2 data/packing path while remaining non-mutating.** For P1 validation this may instantiate/read dataset metadata and samples on CPU, but must not load the model, optimizer, VAE, or execute training. Any observer that advances a second independent iterator instead of observing the actual consumed iterator is invalid.

7. **Source provenance must bind implementation, generated manifest, and verifier.** Header must include builder/verifier SHA256 (or equivalent tracked source identity), root/submodule/Gitlink, exact relevant source-file hashes, and the final JSONL SHA256. Verification must reject a manifest generated against different source provenance.

8. **Negative tests are mandatory and machine-readable.** At minimum: swapped ordinal, modified suite/task/episode/start frame, wrong flat index, duplicate ordinal, missing ordinal, missing cache window, source-hash change, worker/world-size mismatch, and record-count mismatch must all FAIL.

## Allowed implementation surface

Approved:
- root `tools/g0` manifest builder/verifier/test artifacts;
- the minimal manifest-aware data wrapper in `cosmos-framework` needed to consume exact records;
- B2-specific launcher/config plumbing only insofar as required to select this wrapper and enforce `world_size=1`, `num_workers=0`, ordered delivery;
- CPU-only manifest build/replay/negative tests.

Not approved:
- changes to Local/TTT/recurrent model algorithms;
- model/VAE/optimizer loading;
- CPU/GPU training;
- B2-T or any 100-step run;
- evaluation/inference/closed-loop/SR;
- P2-P5 implementation unless separately reviewed.

After implementation, stop at REVIEW and submit the exact root SHA, changed submodule/Gitlink SHA, generated manifest/header/verifier outputs, and negative-test evidence for a separate closure review. No B2-T authorization is implied by P1 PASS.
