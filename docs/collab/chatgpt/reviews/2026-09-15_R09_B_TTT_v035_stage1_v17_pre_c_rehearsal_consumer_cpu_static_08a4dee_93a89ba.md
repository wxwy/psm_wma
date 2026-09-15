# ChatGPT independent review — Stage-1 v0.5 pre-C rehearsal CPU/static exact absence-closure remediation

- Date: 2026-09-15
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`
- Formal root: `08a4dee0e85084a110f1c642513dd32583efb72e`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:55)`
- Blockers: `1 HIGH`
- Design/Authority: `0`; Production/implementation: `1 HIGH`; child/runtime: `0`

## Scope / pair validity

The formal root resolves, is root-only CPU/static remediation, and its tree binds `cosmos-framework` mode `160000` exactly to the declared child `93a89ba61306d840a008813f62f26a34d54850f4`. The child resolves. This review does not authorize v0.5 request construction/C, real consumer invocation, materialization, source-evidence, real Git/network/source/data/cache I/O, child mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

## Positive remediation verified

The previous closure issue is partially corrected:

- the exact four V18 designated absolute paths are now frozen as `DESIGNATED_ABSENCES`;
- authority-ref query absence now requires empty stdout instead of the prior non-empty placeholder;
- local/remote authority-absence records carry explicit byte length/SHA-256 and validate them;
- the exact v0.5 pair, six-key Git isolation environment, pre-admission retirement, typed `ReadbackV1`, internal byte equality, canonical JSON/Markdown checks, producer-raw inverse patch witness, capability immutability and terminal no-retry behavior remain preserved.

## HIGH 1 — frozen observation identity is still incomplete

**Location:** `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:55` (`QueryFactV1` and the related closure schema/validation).

**Root cause:** the implementation still models several frozen live observations as raw values or pathname tuples rather than as the exact observation records frozen by the Stage-1 authority.

`QueryFactV1` stores `stdout`, `stderr` and optionally `advertised_v2`, but it does not store/validate the required byte-length and SHA-256 identity for each raw result or for the separately extracted advertised V2 value. Likewise `ClosureV1.output_absences` is only the two output path strings, and `designated_absences` is only the four exact pathname strings. The V18 frozen contract requires each designated absence to be an explicit `lexists=false` observation record including path, predicate, boolean/no-follow result and canonical raw-record byte length/SHA-256; the request closure also requires raw query/result identities, not just possession of immutable Python `bytes`.

The current `QueryFactV1.identity_ok()` only checks non-empty stdout plus timeout/return-code. That does not witness the frozen raw-result identity. The tests therefore can still construct a semantically foreign query/absence observation that has the correct argv/predicate/path shape but lacks the required frozen identity record and pass this layer.

**Contract violation:** V18 freezes the four exact designated paths *and their absence observation records/identities*, and inherited v1.7 closure requires complete raw-result identities for the two remote queries and the independently extracted advertised V2 value. V31 did not supersede those identity requirements; it only refroze when the observations may occur.

**Acceptance criterion:** replace the remaining reduced fields with typed frozen observation records that explicitly carry and validate the required raw bytes plus byte length/SHA-256 identities. At minimum:

1. both remote-query records bind timeout, return code, stdout raw + length/SHA, stderr raw + length/SHA, predicate, and for remote V2 the independently extracted advertised raw + length/SHA;
2. both v0.5 output absences are typed absence observations, not pathname-only tuples;
3. the four V18 designated absences are typed ordered records bound to the exact V18 absolute paths and `lexists=false` semantics, including predicate/result/boolean and canonical observation-record length/SHA;
4. direct CPU/static drift tests mutate each identity field and prove fail-close before consumer invocation.

Until that exact observation identity closure is implemented, the CPU/static Gate cannot close.
