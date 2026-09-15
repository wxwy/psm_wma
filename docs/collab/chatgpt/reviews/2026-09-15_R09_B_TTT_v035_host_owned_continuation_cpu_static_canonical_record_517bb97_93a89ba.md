# ChatGPT independent review — V27 host-owned continuation CPU/static canonical-record remediation

Formal pair:
- root: `517bb9790985a2001f6778ad64ccfbe7fe5bce3d`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-HOST-OWNED-CONTINUATION-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_host_boundary.py:17)`

Blockers: `2`
- Design/Authority: `0`
- Production/implementation: `1 HIGH`
- Evidence: `1 MEDIUM`
- Scope/child/runtime: `0`

## Re-lock / target validity

- Pre-review `V2` HEAD is request/bookkeeping commit `f57fa0891dbd8ce2c390440e953469527d751ed0`, whose parent is the declared formal implementation root `517bb9790985a2001f6778ad64ccfbe7fe5bce3d`.
- `CODEX_INBOX.md` explicitly requests this exact pair for the same fake-host CPU/static Gate.
- Formal root resolves `cosmos-framework` exactly to Gitlink `93a89ba61306d840a008813f62f26a34d54850f4`.
- Child `93a89ba61306d840a008813f62f26a34d54850f4` resolves independently in `wxwy/cosmos-framework`.
- Previous reviewed implementation pair was `c4a3b985cfd8a576ab114431f8ee2ae4df6f2681 / 93a89ba61306d840a008813f62f26a34d54850f4`, verdict `REQUEST_CHANGES(tools/psm_wma/stage1_host_boundary.py:42)`. Root changed, so this is a fresh incremental review.

## Frozen contract used

V24 + approved V27 remain binding. In particular the exact review authority must still cover:
- session/plan/lease identity and binding;
- consumer/guard/verifier provider/module/path/source-blob/callable/ABI/transport;
- sealed pair/patch identity;
- C01--C15;
- nine freshness identities;
- the two output paths;
- the exact six-key environment;
- remote/query facts;
- authority/designated absences;
- replay/frozen-target/descriptor/source/argv identities required by the later host-boundary design.

This Gate is only stdlib fake-host protocol conformance. Real host/IPC/pre-C/C is still forbidden.

## Positive closure from `c4a3b985...`

Two prior findings are materially closed:
- **private snapshot / aliasing is closed**: `_HostSnapshotV27` is stored in host state, `_record_from()` returns a detached value witness, privileged attestation revalidates the returned record against the private snapshot and canonical digest, and resume reads the private snapshot only;
- **exact approval + serialized admission remain closed**: exact Gate/root/child/session/binding/nonce/counter checks remain in place and `RLock` still serializes approval plus `APPROVED -> CONSUMING` before freshness/apply.

The new base-mutation tests are therefore meaningful progress and the previous aliasing HIGH is not carried forward.

## HIGH 1 — the fixed fake ReviewRecord schema is still not the inherited exact authority schema

Location: `tools/psm_wma/stage1_host_boundary.py:17-31, 42-58`.

The remediation freezes twelve category names and per-category field names/counts, but those shapes are not actually the frozen Stage-1 review-record shapes. Several fields are generic placeholders rather than the inherited authority contract:

- V24 explicitly requires the **six-key environment**; `_SCHEMA` has no environment category at all.
- `QueryFactV1` carries ordered argv, timeout, return code, stdout/stderr identities, predicate and advertised-V2 identity. The fake schema reduces `query_identities` to only `stdout`, `stderr`, `predicate` and does not model the two distinct remote queries.
- `DescriptorV1` has the exact fields `abi`, `operation`, `paths`, `encoding`, `transport`; the fake schema instead defines eight anonymous `descriptor_0..7` fields.
- the frozen target/replay authority in the rehearsal has named cwd/index/evidence/json_output/markdown_output and concrete replay/source/argv structures, while the fake schema substitutes synthetic names/counts such as four `frozen_targets` entries (`json`, `markdown`, `patch_text`, `patch_raw`) and eight anonymous source/argv slots.
- every value, regardless of semantic type, is forced through the same generic `identity:<token>` regex. The model therefore does not distinguish hashes, lengths/integers, paths, predicates, argv, provider/module/callable identifiers or ordered nested identities.

The public `create()` API also still accepts one free-form string and `_default_rows()` manufactures the entire allegedly reviewed authority surface from that token. That is acceptable as a fixture helper only if it builds the **exact frozen schema**; with the current invented/generic schema it remains a shortcut around the actual authority contract.

This means the host can accept a self-consistent record that is canonical relative to `_SCHEMA` but incomplete or structurally different from the authority that V24/V27 says was independently reviewed. A canonical digest over the wrong schema does not establish protocol conformance.

Violated frozen contract: complete detached exact ReviewRecord equality for V24/V27.

Acceptance:
1. derive the fake-host ReviewRecord schema directly from the inherited frozen authority instead of synthetic category/count choices;
2. explicitly model the six-key environment, exact two paths, both remote/query fact identities, exact consumer/guard/verifier provenance, C01--C15, nine freshness identities, authority/designated absences, sealed pair/patch identities, replay binding and named frozen targets/descriptor/source/argv identities;
3. for each field, freeze the appropriate canonical primitive type/format or freeze a named sub-record digest whose own canonical schema is explicit; do not treat every field as the same opaque string grammar;
4. remove the free-form-string shortcut from the host-facing `create()` contract, or move it to a test fixture builder that emits the exact schema and cannot stand in for arbitrary reviewed authority;
5. keep the host-private detached snapshot and current exact attestation/admission behavior unchanged.

## MEDIUM 2 — evidence proves snapshot isolation, but still tests the synthetic schema rather than the frozen authority

Location: `tools/psm_wma/test_stage1_host_boundary.py`.

The expanded `8/8` suite now causally covers returned-record base mutation, snapshot separation, approval drift, prior-session/prior-generation replay, parallel resume and terminal failure branches. Those portions are good.

The remaining evidence gap is specifically schema fidelity:
- `setUp()` still creates records through `host.create("review-a")`, so all passing tests exercise `_default_rows()` synthetic placeholders rather than an independently assembled exact frozen ReviewRecord;
- malformed-schema testing proves only the current `_SCHEMA` field list, not that `_SCHEMA` itself matches V24/V27;
- there is no witness for six-key ENV, exact DescriptorV1 field grammar, both query facts, two output paths, or the real nested replay/target/source/argv identity shapes.

Acceptance:
- build at least one explicit canonical fake ReviewRecord fixture matching the frozen authority schema without using the free-form shortcut;
- add malformed/partial/type-format drift witnesses for each real category/sub-record, including ENV and both query facts;
- make schema-fidelity tests fail if an inherited required category/field is omitted, renamed, collapsed, reordered or assigned the wrong primitive format.

## Blocker lifecycle

From the previous implementation review:
- exact per-category canonical ReviewRecord: `PARTIALLY CLOSED / STILL OPEN (HIGH)` — fixed names/counts exist, but the schema is not the inherited exact authority surface;
- client-visible record aliasing / private snapshot integrity: `CLOSED`;
- exact Gate/root/child + privileged attestation: `CLOSED`;
- serialized one-shot admission: `CLOSED`;
- Evidence: `PARTIALLY CLOSED`; snapshot/approval/concurrency/failure causality is substantially better, schema-fidelity evidence remains open.

## Scope reminder

This verdict binds only the exact formal pair above and `G0-R09-B-TTT-V035-HOST-OWNED-CONTINUATION-CPU-STATIC`. It does not authorize real Stage1Host process/OS identity, real IPC, privileged real attestation transport, real envelope/pre-C/C, real consumer or `apply_patch`, request pair/materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1.
