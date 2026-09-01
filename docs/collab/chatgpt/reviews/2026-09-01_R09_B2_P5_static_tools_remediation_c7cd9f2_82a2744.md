# R09-B2 P5 static tools remediation review

- Request: `c7cd9f2225c7e8cf469cde8432a1629a18630eef`
- Implementation: `82a2744243e743ce65c99785aa508188590e6094`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Findings

### HIGH — reviewed tool still has no controlled parent export / envelope assembly path

`tools/g0/export_r09_b2_p5_resolved_config.py:123-184`

`build_pair_requests()` now correctly gates both records through the frozen P4 pair verifier and derives D005-bound child requests. However, the reviewed tool stops there. There is still no parent function that:

1. writes the two verified requests,
2. launches two fresh canonical-interpreter subprocesses with the exact D005 cwd/environment,
3. reads the two child resolved-config outputs,
4. assembles the approved `effective_launch + resolved_config + provenance` envelopes,
5. records exporter/tool provenance and input hashes, and
6. invokes the P5 pair verifier.

`_child()` still writes only the bare canonicalized `config.to_dict()` tree, and the CLI only exposes the child path. A future P5 export therefore still requires ad-hoc, unreviewed orchestration outside the frozen tool to produce the envelope expected by the verifier.

Required: implement the complete parent orchestration as reviewed code. It may remain non-exposed / execution-disabled until a later run approval, but the exact execution path that will generate P5 artifacts must already be statically reviewable.

### HIGH — per-envelope binding remains incomplete; common omission/forgery can still PASS

`tools/g0/verify_r09_b2_p5_full_config_diff.py:92-116`

`_bound()` checks only:

- top-level key set,
- `production_source`,
- command argv/cwd,
- `environment.set`,
- budget,
- P3 launch binding,
- one P4-record digest.

It does not require or independently bind the full approved nested envelope. In particular, it does not bind exact values/schema for items including:

- command interpreter + interpreter SHA,
- parsed TOML + exact trailing overrides,
- environment `unset` / `inherit_allowlist` / `effective`,
- derived `world_size`,
- P1 binding,
- derived job path/output binding,
- P4 verification SHA,
- P3 verifier identity in provenance,
- exporter source/tool SHA.

The current positive CPU fixture omits many of these fields and still passes, demonstrating that the approved v0.2/v0.3 envelope contract has not yet been implemented fail-closed. If both sides omit or forge the same common field, pair diffing sees no difference.

Required: define and enforce exact nested schemas for `provenance` and `effective_launch`, and compare every verifier-owned field against independently loaded P4/P1/P3 evidence or derived production values, not only against the peer envelope.

### HIGH — common P3 provenance identity is still only cross-compared, not verifier-bound

`tools/g0/verify_r09_b2_p5_full_config_diff.py:44-53`

`_p3_checks()` only requires recurrent and TTT to have equal `p3_inventory_path`, `p3_inventory_sha256`, and `p3_verifier_sha256`. Both envelopes can therefore report the same forged provenance values while the actual launch-side P3 contract remains valid, and the verifier can still pass.

This contradicts v0.3, which requires common P3 evidence identity to be independently bound to the frozen P3 artifact/PASS verifier.

Required: bind provenance P3 path/SHA to the actual frozen P3 input and bind `p3_verifier_sha256` to the verifier-owned frozen value; add a regression where both sides are changed to the same bogus value and the pair must FAIL.

### HIGH — backend-derived resolved selector/local-backend values are not checked per side

`tools/g0/verify_r09_b2_p5_full_config_diff.py:55-85`

The verifier checks `resolved_config.optimizer.keys_to_select` and `local_history_backend` only when those fields appear in the pair diff. If both sides are changed to the same wrong value, there is no diff and no check. The same issue exists for same-length selector mutations handled by the per-index union-membership allowance.

Required before diff allowlisting:

- recurrent `resolved_config.optimizer.keys_to_select` must exactly equal verifier-owned recurrent selector keys;
- TTT must exactly equal verifier-owned TTT selector keys;
- recurrent `local_history_backend` must be exactly `recurrent`;
- TTT must be exactly `ttt_fast_weight`;
- any other approved backend-derived resolved field must be validated per side against its verifier-owned expectation.

After these per-side checks, per-index selector permissiveness should be unnecessary or strictly subordinate to the full-list checks.

## What improved

The remediation correctly removed caller-owned `--contracts`, internally derives P3 contracts from frozen P3 evidence, gates child-request construction through the P4 pair verifier, and binds several P4 record fields per side. These are meaningful improvements but do not yet close the trust boundary for an actual static-export request.

## Decision

`APPROVE_TO_REQUEST_P5_STATIC_EXPORT` is **not granted**.

No config export, `load_experiment_from_toml`, launch/validate/instantiate, CUDA, torchrun, GPU, training, evaluation, inference, P5 closure, or B2-T is authorized by this review.
