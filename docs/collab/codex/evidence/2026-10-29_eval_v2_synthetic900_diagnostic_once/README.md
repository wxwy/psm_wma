# Original synthetic900 single diagnostic — INCONCLUSIVE

Formal Root `9657fb6ab590f228d760362e506d5dd1b626880a`; Child/Gitlink `0ae313e329d290fc6b8a50fda1112820fb7ac485`. This publication commit is evidence bookkeeping, not a new Formal Pair.

Single original case: 1 PASS, 0 FAIL, 0 errors, 0 skipped; shell 0. The only diagnostic invocation did not reproduce the exception. Runtime.run returned error=None. No internal exception stack exists for this invocation; this does not establish the throw-site of the previous failure, close the source risk, or overturn the author unified Gate FAIL. No retry was launched.

The external plugin delegates the original `robocasa_eval_v2.runtime.Runtime.run` exactly once, observes only after it returns or raises, returns the same result object, and restores the method afterward. It introduces no scheduler/thread/timing hooks and captures no frame locals. The single original nodeid and assertions remain unchanged. Full plugin, launcher and before/after checker are in `instrumentation/`.

`raw/source_before.json` and `raw/source_after.json` independently establish the same clean Pair, all 53 watched source hashes unchanged, and the original author FAIL top-level artifacts unchanged. These are diagnostic-only checks; they do not supply a missing final field in the earlier FAIL Gate JSON. `raw/os_before.txt`/`os_after.txt` contain PID/PPID/PGID/state/command-name snapshots, not GPU or real owned-process acceptance. This case uses CPU process/model/physics doubles, real local HTTP/Slot/Store paths and synthetic inputs; no real 900-episode evaluation.

Original author full434 remains **257 PASS / 1 FAIL / 176 not run, REQUEST_CHANGES**. This single-case result is not added to that count. DS independent CPU remains not started. No full Gate retry, production/test/Gitlink change, V3 merge, Issue reply, GPU, Canary or training action followed. Original failed evidence remains at commit `f65ac07d3fc3e56117dd9192ba77e4b58b5c9934`; governing Evidence Review at `cb361421c2b3a545f8f17fce1fa0f1e6a5d3f423`.

`derived/result.json` is interpretation; `raw/` is copied byte-for-byte with source-to-published hashes in `derived/original_to_published.json`. Only selected public scheduler/case records are archived. Whole temporary trees, caches, assignment/capability configs and checkpoints are excluded. `artifact_sha256.json` hashes every published artifact except itself.
