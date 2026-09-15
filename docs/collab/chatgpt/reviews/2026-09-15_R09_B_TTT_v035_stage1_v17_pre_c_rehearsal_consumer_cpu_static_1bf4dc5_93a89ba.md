# ChatGPT formal review — Stage-1 v1.7 pre-C rehearsal consumer CPU/static

Formal pair:
- root: `1bf4dc5315ac37a360e850dc5d0baf799287b58c`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:116)`

Blockers: `1 HIGH`.
- Design/Authority: `0`
- Production/implementation: `1 HIGH`
- child/runtime: `0`

## Positive closure

This pair materially closes the prior structural full-closure finding:
- `.git`/config/local-V2 are now typed raw facts with length/SHA self-consistency;
- P0 root/path/blob tuples, P1 named injected-source records, ReplayBinding, owner-FD, frozen targets, query identities and typed output/designated absence observations are present in the sealed closure;
- exact v0.5 tuple, six-key environment, exact authority-ref literal, canonical JSON/Markdown/patch witnesses, admission retirement, typed readback, byte-exact postcondition and terminal no-retry remain preserved.

## HIGH 1 — typed source/literal records are self-consistent but are not bound to the frozen authority identities

Location: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:116` (`SourceObjectV1.identity_ok()`), with the same root cause in `ReplayBindingV1.identity_ok()`.

Root cause:
The new typed records validate their own shape/hash, but do not prove that the bytes/literals are the exact frozen authority objects.

### Direct P0 witness

`SourceObjectV1` carries `(name, root, path, blob_oid, raw)`, but `identity_ok()` only returns:

`self.raw.name == self.name and self.raw.identity_ok()`

It never computes the Git blob OID of `raw.raw` and compares it with the frozen `blob_oid`.

The current test fixture demonstrates the hole directly: for every frozen P0 tuple it constructs `raw_fact(name, name.encode())` while retaining the authoritative blob OID, and the success path passes. Those bytes are not the frozen Git objects, so a foreign but self-consistent payload is admitted.

### ReplayBinding / P1 witness

`ReplayBindingV1.identity_ok()` checks the formal parent/path/blob, `base_bytes`, owner-FD, row counts and non-empty row shape, but it accepts any 64-character `base_raw_sha256` and arbitrary non-empty eight parser/source rows. The test fixture uses `"a" * 64` plus synthetic `--key-N / old-N / new-N` rows and still passes. That is not the required **complete literal ReplayBinding**.

Likewise the P1 records are accepted when their names match `P1_OBJECT_NAMES` and each `RawFactV1` is internally self-consistent; there is no comparison against the exact frozen injected-object identities/literals.

Contract violation:
- V1.7 requires P0 to use the three allowlisted Git objects and the complete literal ReplayBinding, and requires P1 injected-object identities to be explicitly bound rather than reconstructed or substituted.
- V31 requires `rehearse_v05()` to seal **all injected source objects and literal binding** before C.
- A record that only proves “these arbitrary bytes hash to the hash supplied next to them” is not an authority binding.

Why current evidence is insufficient:
- `8/8` CPU/static tests currently certify the permissive behavior: their success fixture deliberately uses synthetic P0 bytes and synthetic ReplayBinding rows.
- Drift tests mutate declared metadata, but do not prove that accepted bytes/literals equal the frozen authority values.

Acceptance criterion:
1. **P0 object binding:** for every `SourceObjectV1`, require exact frozen `(name, root, path, blob_oid)` and require `git_blob_oid(raw.raw) == blob_oid` in addition to raw length/SHA self-consistency. Add a negative test where raw bytes change while the declared frozen blob OID remains unchanged; rehearsal must fail before consumer invocation.
2. **P1 injected-object binding:** freeze the exact expected identity for each of the eight P1 objects (exact literal/raw length+SHA or the controlling canonical identity) and compare against it. Names + self-hash alone are insufficient. Add foreign-but-self-consistent raw tests for every P1 category.
3. **ReplayBinding literal binding:** compare `base_raw_sha256`, parser rows and source rows to the exact frozen ReplayBinding values/identity, not merely length/shape/non-empty predicates. Add tests for a different valid-looking 64-hex base SHA and different same-shape rows.
4. Preserve all already-closed behavior: full typed closure categories, exact query/absence identities, exact authority ref, six-key environment, noncopyable/nonserializable plan/capability, canonical byte witnesses, admission retirement before freshness, typed readback and terminal no-retry.

No CPU/static closure is granted for this pair. This verdict does not authorize v0.5 request construction/C, materialization, source-evidence, real Git/network/source/data/cache I/O, child mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.
