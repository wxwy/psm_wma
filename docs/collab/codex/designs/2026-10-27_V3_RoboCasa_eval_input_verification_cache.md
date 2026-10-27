# Issue #6 — RoboCasa verified-input cache candidate

2026-10-27 Asia/Shanghai. Owner task `docs/collab/chatgpt/requests/2026-10-27_Codex_V3_RoboCasa_eval_cached_input_verification.md`. Baseline production Root `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`, docs HEAD `eafef76f324964cb400b12e73dea2b4241c2baf7`, unchanged Child/Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`. Root candidate branch `v3-eval-input-cache-20261027`; no automatic V3 merge or runtime authorization.

## Trust and identity

Warm verification assumes **trusted readonly model storage plus reliable Linux stat witnesses**. Reusing an earlier SHA under unchanged `(dev, ino, size, mtime_ns, ctime_ns)` is change detection, **not a new cryptographic proof of model bytes**. An attacker capable of malicious same-stat replacement or rewriting/resealing both cache and authorities is outside this fast-path guarantee. JSON integrity SHA is unkeyed corruption detection, not a signature/MAC.

Four hard model parameters remain exactly checkpoint/num_steps/action_horizon/guidance. No stat-derived substitute model digest is created. Strong identity SHA and all original legacy relocation/admission checks remain authoritative. Existing source Config/Task metadata and seed/runtime provenance retain their existing roles; cache is not a fifth result-reuse invariant and never rewrites old identities or results.

## Durable model record

Path: `<RUN>/_resume_v2/input_verification.json`. Schema `psm_eval_verified_model_cache_v1`. Exact fields: schema, absolute run_root, original strong-anchor file SHA256, verified_at_ns, full previously validated model identity/observation, integrity_sha256. Identity includes ordinary `.metadata` and `*.distcp` five-stat witnesses plus complete model-directory names. All directory entries must be ordinary files, not links/directories; headers are validated on full reads. Unknown ordinary non-model notes affect inventory and invalidate cache; only metadata/shards are model-payload hash scope, unchanged from the strong identity contract.

The record is bound to original `_resume_v2/model_identity.json`, requested canonical checkpoint path and three scalar parameters, schema/checksum and a **30-day maximum age**. Future timestamps and expired records conservatively miss. Warm hits do not extend this full-validation age. Every hit checks current inventory/stat and strong-anchor equality before reuse. No record or missing/corrupt anchor can bootstrap trust from stat alone.

Cold: full model read once outside lease; lock acquisition rechecks stat/inventory rather than blindly hashing again. If an actual race changed the observation, full rehash and strict old/new comparison occur; changed payload still fails. Original `.run.lock`, nonblocking exclusive ownership and admission execute before persistence.

Publication happens inside `begin_invocation`, after the CLI has completed safe history/plan and (when executing new episodes) full bundle/runtime/Config/Task validation, while holding that same lease. Strong anchor/legacy migration witnesses retain their original publication rules. Only the new cache is atomically replaced using existing bounded JSON `_write`: exclusive temporary file, file fsync, replace, parent-directory fsync, cleanup on exceptions. Original manifests/configs/episode evidence/checkpoints are never replaced by cache publication. Interrupted `.pending-*` files cannot become cache authority; an existing valid previous cache can remain valid, otherwise rehash. An incomplete fresh namespace is not silently admitted as a successful run.

Warm: read bounded non-symlink cache+anchor JSON, validate checksum/schema/namespace/age/parameters/strong identity, check live stat/inventory, reuse **the identical original strong digest**; no `_read_hash`/model bytes. Lock acquisition performs another stat guard and strict admission. Invalid record/stat/path/params/anchor causes full validation or explicit refusal; same-byte legitimate rehash may refresh cache witness under lease without changing original anchor. A new checkpoint cannot be accepted merely by deleting cache. Legacy path relocation still requires its existing explicit authorization and all original metadata/shard restrictions; cache cannot grant it.

Dry-run: read-only preview can hit cache or full-hash without it, but never creates or repairs run namespace, lease, anchor or verification cache. New internal RunStore `model_identity_request` selects cache behavior; production CLI supplies it automatically, no user flag or Resume command change. Other readers remain supported with full reads and stat lease guard.

## Config and Task metadata

Cross-invocation metadata caching is deliberately not added. Their original hashes remain persisted in original manifests and freshly verified at each invocation's initial real bundle when new episodes are planned. Vendor/runtime probe, dataset provenance and task discovery remain intact. Before that validation, capture original input observations; only bind resulting hash/manifest if all observations are still stable afterwards. This prevents assigning a verified old hash to a newly replaced file.

`InvocationInputGuard` then checks original Config/Task hashes in each source manifest and current canonical target plus five stat fields at pre_model_load/post_model_load/pre_commit and final input verification. It reads no file bytes. A changed/missing/nonregular input or changed source-manifest hashes fails, not silently rebaselines. Original model guard remains at each boundary. This is invocation-local trust; prior-result provenance and four-parameter result reuse continue under their existing contract.

The shared `v3_evaluation_identity.build_evaluation_identity` has an optional verified-model observation, supplied only by current Resume CLI through existing vendor API. It checks protocol/path/stat and reuses the known metadata SHA instead of reading `.metadata` again; returned legacy manifest is identical for equal inputs. Its default behavior remains unchanged for other callers. Actual vendor/native-library/runtime attestation is not replaced with stat-only claims.

## Scope and observability

Unchanged: Action Server `/info` and listener ownership/free ports; native model/Local-TTT/Child/No-TTT training/DCP; Episode-major sampler/seed/pending recovery/failure policy; actual Episode/actions/progress/cleanup/video decoding/source scans and final original-source revalidation. No global hash monkeypatch or process-name operation.

`checkpoint_reads` and terminal log now describe `verification_events`, including cache_hit, model_payload_bytes_read, actual full-read counters, reason/validation elapsed time and explicit trust scope. Warm validation timing is not model loading or total invocation time. Report records invocation guard count/zero subsequent bytes and whether an initial Config/Task bundle was validated. This excludes initial discovery/vendor/HTTP-info reads; it never claims all startup I/O is zero.

## CPU contract and later Gates

Five directly related synthetic modules cover cache cold/warm, explicit byte/call counts, invalid/missing/expired/checksum/namespace/duplicate-key records, ordinary file/anchor/path safety, same-size restored-mtime byte mutation, legitimate same-byte stat changes, four-parameter mismatch, preview/lease races, actual competing CPU process lease, atomic publish I/O error and process exit before replace, old Run22-episode prefix reuse, metadata mutations/manifest binding, real CLI/store/plan wiring and dry-run. CLI execution/runtime boundaries are explicit no-server stand-ins; missing execution remains PARTIAL, never fabricated completion. One stale original legacy-prototype regression assertion was independently reproduced at49df7f3c and now explicitly asserts the later Owner relocation flag False, preserving all old fields; expected two cold hashes is intentionally updated to one with stat safety tests preserved.

Author frozen result:227PASS,0skip/fail/error;53new cases, Ruff0.12.7 check/format and syntax9Python. Actual tiny model fixture:188bytes cold read once (metadata+one shard), Warm0bytes, identical strong SHA. These are not real DCP/loadability, server, simulator, GPU, independent DS or performance evidence.

After candidate publication: GPT fresh incremental code/Evidence review → DS clean detached CPU replay. Real checkpoint/stat/permissions/filesystem behavior and any actual900-episode evaluation deployment require separate Owner authorization. Do not touch existing22 episodes or running training/evaluation. STOP after author delivery.
