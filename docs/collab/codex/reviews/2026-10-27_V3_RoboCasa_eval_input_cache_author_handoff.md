# Issue #6 — cached input verification author handoff

2026-10-27 Asia/Shanghai. **Candidate code + synthetic author CPU Evidence; not GPT/DS approval or runtime authorization.**

| Object | Exact SHA |
| --- | --- |
| Root implementation | `9cb8b60dccf4ac2520f8d862b723d7bc94fe3813` |
| Child/Gitlink unchanged | `746c5cf2f2324104a62fb71510343aa40d3976c5` |
| Base production Root | `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9` |
| Parent docs HEAD | `eafef76f324964cb400b12e73dea2b4241c2baf7` |
| Candidate branch | `v3-eval-input-cache-20261027` |

Following docs/Evidence commit is not the implementation SHA. Candidate only; no V3/Child remote promotion. Owner frozen request: `docs/collab/chatgpt/requests/2026-10-27_Codex_V3_RoboCasa_eval_cached_input_verification.md`. [Design/cache schema/trust/runbook](../designs/2026-10-27_V3_RoboCasa_eval_input_verification_cache.md).

## What changes

RunStore accepts a four-parameter request from the production Resume CLI. Cold model validation hashes all metadata/shard bytes once; acquired original `.run.lock` rechecks live stat/inventory, with actual races forcing full rehash + unchanged strict identity comparison. After safe admission/full bundle checks, `begin_invocation` atomically publishes only a new verification record using the existing fsync/replace helper, bound to original strong anchor. No success cache on a failed Cold bundle; old manifests/anchors/episodes remain original.

Warm lookup verifies bounded ordinary JSON/schema/checksum/namespace/anchor-file SHA/four parameters/canonical checkpoint/30-day expiry/live ordinary file inventory and dev/ino/size/mtime_ns/ctime_ns. It reuses **the identical original strong digest**, with `cache_hit=true, model_payload_bytes_read=0`; not a stat-derived substitute digest. Miss/damage/expiry/path or parameter change rehashes then follows original strict admission, or refuses. Legacy relocation grants remain unchanged. Dry-run can read but cannot publish cache or create namespace/lease. No new command-line options; existing manual Resume command works after future deployment approval.

Config/Task validation stays full at each invocation's initial real bundle, with original hashes persisted in source manifests. Pre/post observations bind those hashes only if input files stayed stable. Batch pre_model_load/post_model_load/pre_commit and final guards use stat+manifest checks, no repeated full reads. Cross-invocation metadata cache was optional and is not introduced. Actual runtime/vendor probe, task discovery and server `/info` remain intact; do not call all startup I/O zero.

Necessary small shared helper change: optional verified-model argument to `v3_evaluation_identity.build_evaluation_identity` checks live observation/path/protocol and reuses already known `.metadata` SHA. It avoids another metadata read during bundle construction; default callers retain original behavior and manifest identity stays equal for equal inputs. No general hash monkeypatch, Child or model change.

Trust is **Owner-trusted readonly storage + reliable filesystem stat**, not fresh cryptographic proof or protection against malicious same-stat replacement/cache+anchor rewriting. Cache checksum is not a MAC. Warm does not renew full-validation age. Record schema/atomicity/invalidations and error codes are documented in the runbook.

## Frozen author CPU result

**Five direct modules:227 passed,0 failures/errors/skips,4.05s;53 new cache/CLI cases.** Ruff0.12.7 check/format and syntax9Python;10 frozen source/test SHA and committed blobs verified. Not whole-repository pytest. New cases execute actual Root model identity, RunStore/lease/atomic writes, CLI/plan/report wiring, with synthetic tiny DCP containers and no-execution runtime/server boundaries.

- Actual tiny fixture cold188bytes,1 full pass (metadata+one shard); Warm0 model bytes and0 `_read_hash` calls, equal strong digest. Full bundle helper test also forbids any metadata/model byte read when a validated observation is supplied. Not a13GB/H100 benchmark.
- Cache missing/truncated/duplicate/checksum/schema/expiry/future/namespace/identity errors; absent/corrupt anchor and symlink/control paths; inode/size/mtime/ctime/inventory/malformed headers/nonordinary directory; same-size changed byte with restored mtime fails; legitimate same-byte rehash updates witness without changing original anchor.
- Preview→lease mutation strictly rehashes/refuses, separate competing CPU process gets RUN_LOCKED, publish I/O failure and actual child exit23 before replace leave no partial success cache; bounded retry preserves original anchor. Dry-run cold/miss/hit stays read-only.
- Synthetic old22-of50 completed Episode prefix remains validated/reused with original evidence bytes/mtime; warm model cache does not skip any source/Episode validation. Legacy relocation still requires original opt-in. No existing real22 files were accessed.
-20batch×3metadata guard checks read0bytes; each mutation phase rejects, initial-bundle race cannot become trusted, altered job hashes reject. Actual CLI with two Tasks/batches cold/warm retains guard boundaries, no repeated full config/task hashes; stubbed execution produces **PARTIAL/zero completion**, never invented COMPLETE. Config/task initial full verification and real source revalidation paths stay present.

One pre-existing regression assertion was reproduced using exact49df7f3c original model-identity source: old isolated prototype lacks the later Owner `owner_accepted_relocated_legacy_checkpoint=False` field. Fixture now explicitly requires that field False **and every old field equal**. The old two-cold-hash assertion is intentionally one-hash+locked-stat under this task; race and changed-model refusal assertions remain. Earlier fixture failures (summary path, synthetic runtime schema, relocation basename) and original baseline RED are preserved separately, not added to final PASS.

## Evidence and reproduction

`docs/collab/codex/evidence/2026-10-27_eval_input_cache_author_cpu/`: actual final JUnit/stdout/command+env/source SHA, committed Git blob bindings, STATUS, cache I/O witness, static logs, full baseline patch/path list, protected-path proof, initial attempts and exact baseline RED, actual synthetic cache/anchor/tiny-container examples, artifact SHA256SUMS. Examples retain original test namespace and **are not trust authority for another run**. Follow-on docs commit contains these artifacts; code remains above formal Root.

Use clean detached Root9cb8b60dccf4ac2520f8d862b723d7bc94fe3813 and Child746c5cf2f2324104a62fb71510343aa40d3976c5, existing CPU dependencies and new external cache/Evidence directories. Exact argv/environment in command.json. Author command:

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  HF_HOME=<WRITABLE_CACHE>/hf MPLCONFIGDIR=<WRITABLE_CACHE>/mpl XDG_CACHE_HOME=<WRITABLE_CACHE> \
  PYTHONPATH=<ROOT>/scripts:<ROOT> <CPU_PYTHON> -m pytest --noconftest -c /dev/null \
  --rootdir=<ROOT> -p no:cacheprovider -q -s \
  tools/v3/robocasa_input_verification_test.py tools/v3/robocasa_input_verification_cli_test.py \
  tools/v3/robocasa_resume_store_test.py tools/v3/robocasa_resume_components_test.py \
  tools/v3/robocasa_eval_config_test.py --junitxml=<NEW_EXTERNAL_DIRECTORY>/junit.xml
```

No servers (including synthetic HTTP), real model/DCP hashes, GPU, Kitchen, training or real output mutation performed. CPU subprocesses only test lock ownership and interrupted cache writes. Full vendor/physics and HTTP/simulator process suites not executed on this authorization; their production paths are unchanged, not claimed independently accepted. Real host filesystem/stat/permissions behavior and safe deployment need later authorization.

## Review request / stop

Request **GPT fresh incremental Implementation Gate** for exact Root/Child above, then DS_PRO detached independent CPU. STOP after publication/readback. No V3 merge, no upgrade/restart current900-episode evaluation, no production22 Episode edits, no model/server/GPU/simulator/training execution. Existing commands need no new flags after approval; cache adoption on a legacy run occurs through full validation, never manual editing/copying trust records.
