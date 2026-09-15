# ChatGPT formal review — Stage-1 v0.5 pre-C rehearsal consumer CPU/static remediation

Formal pair:
- root: `bc7857492dec64a629ecb7684e6d307d146aca24`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:203)`

Current blockers: `1 HIGH`; Design/Authority: `0`; Production/implementation: `1 HIGH`; Evidence/identity: `0`; child/runtime: `0`.

## Positive closure

- formal root resolves and its tree binds `cosmos-framework` exactly to `93a89ba61306d840a008813f62f26a34d54850f4`;
- prior exact-once/freshness retirement defect is closed: `_retirement.consumed` is set before freshness comparison, so freshness failure is terminal;
- post-write verification now returns typed `ReadbackV1` and the core performs byte-exact equality plus canonical JSON/Markdown revalidation;
- patch bytes are reconstructed from producer `json_raw`/`markdown_raw` and compared exactly, closing the prior arbitrary patch-shape gap;
- exact v0.5 output tuple and exact six-key Git isolation environment are enforced;
- capability mutation/copy/serialization and plan copy/serialization are rejected in ordinary API use.

## HIGH 1 — live closure observation schema/semantics still do not match frozen authority

The remediation remains under-specified and in one place semantically inverted:

1. `designated_absences` is accepted whenever it contains any four unique strings. The inherited V18 authority freezes exactly these four ordered absolute paths and their absence-observation records:
   - `/disk/rl/psm_wma/.authority-root-materialization-08d5828`
   - `/disk/rl/psm_wma/.authority-root-materialization-08d5828/.authority-root.index`
   - `/disk/rl/psm_wma/artifacts/g0/r09/authority_root_materialization_evidence_v1.json`
   - `/disk/rl/psm_wma/artifacts/g0/r09/authority_root_materialization_evidence_v1.json.pending`
   Each requires the exact path, `lexists=false` predicate/boolean and canonical raw observation identity; arbitrary labels such as `clean_root/index/evidence/pending_evidence` are not equivalent.

2. `output_absences` is only the two pathname strings, not typed absence observation records with raw result/predicate/identity.

3. `QueryFactV1` now carries argv/timeout/rc/stdout/stderr and advertised V2 raw bytes, but it does not seal the required explicit byte length/SHA-256 identities for stdout/stderr/extracted advertised V2. `AuthorityAbsenceV1` similarly lacks raw length/SHA-256 identity. The inherited construction closure requires raw bytes plus explicit identities, not only storage of opaque bytes.

4. The `authority_ref` query is declared with predicate `authority_absent`, but `_validate_closure()` currently requires `authority_ref.stdout` to be non-empty (`not closure.authority_ref.stdout` causes failure). The inherited absence rule is the opposite: a non-empty/unqualified authority-ref result fails closed. The current unit fixture uses `b"absent"` stdout and therefore proves the wrong behavior.

This is one root cause: the CPU/static closure model still does not represent the exact frozen live-observation authority. A later real adapter could satisfy this synthetic schema while violating the actual Stage-1 closure.

## Acceptance criterion

- replace designated absence labels with the exact four ordered V18 absolute-path observation records and validate exact equality;
- represent both v0.5 output absences as typed observation records with exact predicate/result identity, not names only;
- bind explicit byte length and SHA-256 for every required raw query/absence result and separately extracted remote-V2 advertised raw value;
- correct remote authority-ref absence semantics so an empty qualified result is the valid absence case and any non-empty/unqualified result fails closed;
- add direct CPU/static rejection tests for foreign designated paths, missing/incorrect raw identities, non-empty authority-ref stdout, and malformed output-absence records.

No CPU/static closure is granted for this exact pair.

Still NOT authorized:
- v0.5 request-pair construction or C;
- real consumer invocation;
- materialization or source-evidence;
- real Git/network/source/data/cache I/O;
- child/runtime/config mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.
