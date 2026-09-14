# ChatGPT review — Stage-1 v1.7 exact request instance v0.1

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`
- Formal root: `ad758f9589f4712ee97a169e1f4236aa59f158e6`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Requested verdict: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_V17_AUTHORITY_ROOT`
- Final verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.1.md:13)`

## Result

Blockers: **3 HIGH**.

- Request/Authority: 3 HIGH
- Production implementation: 0
- Evidence-only: 0
- child/runtime: 0

Formal Gitlink resolves exactly to reachable child `93a89ba...`; the formal technical delta is root docs-only request Markdown/JSON plus task/coordination records. No child/runtime bytes changed.

## HIGH 1 — moving `V2` observation makes the request stale by construction

The request binds construction-time remote `V2` to `bb99c6df4cf6ba615e09e3ff4c8c065509b4dc6e` and then states that drift of any observation is `BLOCKED_AUTHORITY_NOT_CLOSED`. But committing this request necessarily advanced `V2` to formal root `ad758f9589f4712ee97a169e1f4236aa59f158e6`, and review persistence/coordination advances it again. Therefore exact equality against the recorded `remote_v2` value is already false before any approved attempt can begin.

This differs from fixed authority-ref absence, which is intentionally a stable runtime freshness fact. The collaboration branch `V2` is expected to move when the request and its reviews are committed.

### Required remediation

Separate `V2` from runtime equality freshness. Bind it only as construction provenance, or freeze a relation that remains valid after request/review commits (for example an ancestry/provenance relation tied to the formal request root). Runtime pre-mutation fail-close may continue to require the fixed local/remote authority ref to remain absent and designated artifact paths to remain absent.

## HIGH 2 — canonical JSON does not satisfy the approved construction closure

The approved v0.2/v0.3/v0.4 design required the future canonical JSON to bind the complete same-round construction closure, including observation time, formal/base/replay identities, local and remote-ref observations, designated absences, selection/config/bootstrap bytes, parser argv, six-key environment, owner-FD insertion, replay output, cwd/index/evidence targets, and the whole canonical JSON bytes/SHA. v0.4 additionally requires each remote query to bind command, return code, stdout length/SHA, and stderr length/SHA.

Current JSON is materially incomplete. Among other omissions:

- no observation timestamp;
- no local `V2` observation;
- closed replay root is present, but the frozen replay module/test blob+raw identities are absent;
- no actual canonical parser argv array;
- only environment key names are present, not the frozen six key/value environment;
- no frozen remote-query timeout;
- `remote_v2` lacks stderr SHA;
- `remote_authority_ref` lacks stdout SHA and stderr SHA;
- no whole canonical JSON identity is bound inside the request closure; the Markdown only states an external `3054 / 2fffb82a...` identity.

As a result the exact request cannot mechanically reconstruct and authenticate the full authority program frozen by the approved design.

### Required remediation

Construct a new canonical request JSON with the complete frozen field set and exact identities. Preserve the strict v0.4 remote-query success contract. If whole-request identity is represented outside the JSON to avoid self-reference, the formal design/request must explicitly define that canonicalization rule rather than silently weakening the frozen v0.2 requirement.

## HIGH 3 — post-approval one-shot execution authority is contradictory and underspecified

The formal Markdown says same-pair approval may authorize one Stage-1 attempt, but immediately says `此前及此后均禁止 launcher/materializer执行`. Taken literally, that prohibits the launcher/materializer both before and after approval and contradicts the requested `APPROVE_TO_MATERIALIZE...` verdict.

The JSON also contains `one_request_only`, which is a construction property, not an execution-attempt property. It does not freeze the v1.6-style one-shot semantics required for safe materialization: one exact post-approval attempt only, zero-mutation preflight drift rejection, success hard-stop at authority tuple, failure or consumption exhausts authority, no second attempt/retry, and a new exact request + fresh independent approval for another attempt.

### Required remediation

Make the exact request itself unambiguous about its post-approval authority. A valid replacement should state the exact positive verdict literal and define one-and-only-one Stage-1 materialization attempt with explicit consumption/no-retry semantics. Before unanimous same-pair approval, execution remains forbidden. After the single attempt is consumed or fails, execution is again forbidden until a new exact request receives fresh approval.

## Preserved / closed controls

The following remain correct and should not be reopened absent regression:

- formal parent `08d5828...` and child `93a89ba...`;
- launcher base `18966 / 8b0fad...`;
- closed replay root `50b0bff...`;
- parser `2336 / 1a9543ec...` and outer `18875 / 658e9b9e...`;
- fixed local authority ref currently absent;
- fixed remote authority query reported `returncode=0`, empty stdout, empty stderr;
- designated clean/index/evidence/pending paths reported absent;
- no Stage-1 execution, source/checkpoint/manifest/data/cache I/O, child/runtime mutation, GPU, training, evaluation, inference, or LIBERO4IN1 occurred during construction.

## Scope

This verdict does **not** authorize materialization, execution, retry, launcher/materializer invocation, downstream collection/receipt/record/package/publication, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1. v1.6 authority remains consumed and cannot be reused.
