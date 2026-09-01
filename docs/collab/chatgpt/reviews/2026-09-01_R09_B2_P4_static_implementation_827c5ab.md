# R09-B2 P4 static D005 implementation review

- Request / implementation: `827c5ab9b65552ae1dbad42d6dc42531887bc1f3`
- Reviewed Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Findings

### HIGH — argv verification is presence-based, so later production overrides can silently defeat the frozen 100-update contract

`tools/g0/verify_r09_b2_p4_d005.py:22-38` checks only that the expected launcher prefix matches and that tokens `trainer.max_iter=100` / `trainer.save_zero_checkpoint=true` occur somewhere in `argv`. It does not require an exact argv grammar, reject duplicate override keys, or compute the effective last override.

The production entrypoint applies trailing Hydra-style overrides after the TOML, so an argv such as:

`... trainer.max_iter=100 trainer.max_iter=5000`

still satisfies the current verifier while production runs with `max_iter=5000`. The same false-PASS class applies to `trainer.save_zero_checkpoint`, optimizer/scheduler settings, job identity, and other production overrides.

Required change:
- parse/freeze the exact allowed argv structure;
- require exactly one `--sft-toml` at the frozen position/value;
- reject duplicate override keys and any unapproved extra override;
- derive the effective values from argv and require exactly `trainer.max_iter=100` and `trainer.save_zero_checkpoint=true`.
- add a permanent negative regression where `trainer.max_iter=100` is followed by `trainer.max_iter=5000`; verifier must FAIL.

### HIGH — approved P1/P3 and environment/input contracts are not independently verified

The approved design required the verifier to independently read/bind the P1 stream manifest and P3 attempt-6 inventory, but `verify_pair()` accepts only the two D005 dictionaries plus `root`; it never receives or reads P1/P3 evidence. `TTT_KEYS` is unused, and `membership_sha256()` is never used by the verifier (`tools/g0/verify_r09_b2_p4_d005.py:12-13,47-53`; `tools/g0/write_r09_b2_p4_d005.py:22-31`).

Consequently the current permanent positive fixture passes with `source={"x":1}` and `inputs={"x":1}` and with no `backend_contract` at all. The verifier also checks only three required environment values (`PSM_R09_B1_TTT_ENABLED`, `LIBERO_NUM_WORKERS`, `CUDA_VISIBLE_DEVICES`) and does not enforce the approved required bindings for local history, stream manifest, cache root/verify ratio, LIBERO/base checkpoint/Edge/WAN assets, offline HF/Transformers, PYTHONPATH, external-asset hashes/realpaths, environment unset/inherit allowlists, or root/submodule/Gitlink provenance.

This permits a D005 pair that is internally matched but is not the approved production input stream / optimizer membership / offline launch contract to PASS.

Required change:
- verifier CLI/API must take the frozen P1 manifest evidence and P3 attempt-6 inventory/verifier evidence and independently derive/check their hashes, count/schema and recurrent/TTT optimizer membership;
- require exact root/submodule/Gitlink provenance;
- enforce every required production env/input field from the approved design and reject missing/extra hazardous inherited environment;
- validate canonical realpaths and file/directory manifest hashes for all external assets;
- add negative regressions for missing P1 binding, wrong P3 membership, missing cache/offline env, and provenance mismatch.

### HIGH — interpreter binding remains self-reported instead of verifier-owned

`tools/g0/verify_r09_b2_p4_d005.py:23-35` builds `expected_prefix` from `command.interpreter.realpath` supplied by the D005 itself. It does not require `<root>/cosmos-framework/.venv/bin/python`, does not resolve/check that path, and does not verify the interpreter SHA256. The positive test deliberately uses a fake `<framework>/python` file and still PASSes (`tools/g0/test_verify_r09_b2_p4_d005.py:14-20`).

That does not implement the approved interpreter hard gate.

Required change:
- verifier-owned expected interpreter = canonical `<root>/cosmos-framework/.venv/bin/python` realpath;
- require it exists as a regular executable file and its SHA256 equals the D005 interpreter/external-asset record;
- require argv[0] exactly that verifier-owned path;
- add wrong-realpath and wrong-SHA negative regressions.

## Additional hardening required by the approved design

- `command.sha256` and `environment.sha256` are not checked.
- required schema fields are not exact/fail-closed; arbitrary omissions/extras can pass.
- output paths are only checked for inequality, not ancestor/descendant overlap or Git tracking.
- `write_record()` is not actually a builder: it accepts arbitrary prebuilt JSON and checks only status/non-executable before writing. Either make it construct the record from reviewed inputs, or ensure it refuses to write unless the complete static verifier contract succeeds.

## Gate decision

`APPROVE_TO_CLOSE_B2_P4` is **not granted**.

No GPU or training rerun is needed. This is a root-only static correction. Do not start P5/B2-T, `torchrun`, GPU, training, evaluation, or inference under this review.
