# ChatGPT formal review — Stage-1 v1.7 pre-C rehearsal consumer CPU/static remediation

Formal pair:
- root: `e870b903c570359fb7641837ea9b5e64c2aed9e3`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Final verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:48)`

Current blockers: `3 HIGH`; Design/Authority: `0`; Implementation: `3 HIGH`; Evidence/identity: included below; child/runtime: `0`.

## Positive closure

- formal root resolves and its tree binds `cosmos-framework` exactly to the declared child;
- exact v0.5 JSON/Markdown pair and the literal six-key Git isolation environment are now frozen;
- JSON canonicalization, Markdown five-field sibling binding, patch strict UTF-8/line witness and add-only path headers are validated internally;
- an internal `_consumed` latch now blocks second invocation after APPLIED and after consumer-result/post-write failures;
- copy/pickle rejection exists for capability and plan; explicit APPLIED / REJECTED_NO_WRITE / PARTIAL_OR_UNKNOWN branches exist;
- scope remains root-only stdlib CPU/static and does not authorize real consumer/Git/network/source/data/cache I/O, v0.5 request construction, materialization, child mutation, GPU or training.

## HIGH 1 — live closure schema is still reduced

Location: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:48-63`, `_validate_closure`.

Root cause:
- `QueryFactV1` contains only `argv`, one undifferentiated `raw` blob and `predicate`;
- the frozen Stage-1 closure requires the exact remote-query execution record: argv/order/count, timeout, return code, stdout raw identity and stderr raw identity, plus the separately extracted remote `V2` advertised raw identity;
- local/remote fixed-authority-ref absence also require explicit observed ref/path, raw result identity and success/absence predicate, not opaque bytes alone.

Why this violates the frozen contract:
- V31 refreezes lifecycle placement, not the inherited closure contents; moving observations into pre-C does not permit reducing their schema;
- the current static core therefore cannot prove the sealed plan contains the complete facts later required by C.

Acceptance:
- model the two exact remote query records with frozen timeout, rc, stdout/stderr bytes plus length/SHA identities;
- model separately extracted remote-V2 advertised raw value and its identity;
- model local and remote authority-ref absence with explicit target/ref, raw result identity and exact absence predicate;
- fail closed on omission, extra fields, wrong order/count/argv/timeout/rc/predicate or identity drift.

## HIGH 2 — sealed plan/capability/verifier identity is mutable after rehearsal

Location: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:66-81`, `:98-113`, `rehearse_v05`.

Root cause:
- `OpaquePatchCapabilityV1` uses mutable slots and allows rebinding `apply_opaque_v1`, identity fields and token after rehearsal;
- `SealedPreCPlanV1` is a mutable dataclass and allows rebinding `capability`, `descriptor`, `closure`, `post_write_verify`, raw values and identity metadata;
- post-write verification is still an arbitrary injected boolean callable: the static core validates only its qualname, then trusts its boolean result instead of consuming explicit observed readback bytes and performing the byte comparisons itself.

Why this violates the frozen contract:
- V31 requires a sealed same-process plan whose capability/callable identity, final bytes and post-write verifier are closed before C;
- a caller can mutate the plan/capability/verifier after PASS, so `consume_once_v05()` can execute a different callable or verify under different semantics than rehearsal approved;
- a boolean callback is not direct evidence of the required byte-for-byte JSON/Markdown postcondition.

Acceptance:
- make sealed data structurally immutable except for an internal one-shot retirement cell that cannot alter frozen authority fields;
- freeze capability/callable identity so it cannot be rebound after rehearsal and verify exact object identity at consume admission;
- replace the opaque boolean post-write verifier with a typed observed-readback result or equivalent sealed fake adapter whose returned bytes/identities are checked by the core itself against sealed `json_raw`/`markdown_raw`, JSON canonical reserialization and Markdown five-field binding;
- add mutation/drift tests proving fail-close before any callback.

## HIGH 3 — freshness failure does not retire the one-shot plan

Location: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py:190-194`, `consume_once_v05`.

Root cause:
- `_consumed` is set only after `current_closure == plan.closure` succeeds;
- on a freshness mismatch, the function raises while `_consumed` remains false, allowing the same plan to be called again later with a matching closure.

Why this violates the frozen contract:
- V31 states that once v0.5 C starts, any failure is terminal and permanently consumes the one-shot construction authority;
- freshness comparison is the first step of C, so a mismatch cannot be a reusable precondition failure.

Acceptance:
- retire/consume the plan atomically at C admission before freshness evaluation, or use an equivalent one-shot admission capability whose first attempt is irreversible;
- add a direct test: freshness mismatch followed by a second call with matching closure must fail as already consumed and must never invoke the consumer.

No closure authority is granted for this exact pair. v0.5 request construction/C/materialization and all real I/O remain forbidden.
