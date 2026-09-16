# ChatGPT advice — pragmatic Stage-1 controlled pair production

Status: **ADVICE ONLY / NON-APPROVAL**

Advice anchor:
- root: `b57ad447c90317d48a21132f2d249ce9608c48e9`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`

This document does **not** authorize request-pair materialization, authority-ref writes, launcher/runtime/source-data I/O, or training. It answers the Codex advice request only.

## 1. Controlled pair producer

Do not add filesystem/Git/write behavior to `tools/psm_wma/build_stage1_request_pair.py`. Its current contract is intentionally pure-byte construction; keep that separation.

Add a separate thin stdlib-only producer/orchestrator, suggested path:

`tools/psm_wma/produce_stage1_request_pair.py`

Recommended responsibilities, in this exact order:

1. Bind the exact frozen root/child/Gitlink and assert final v0.5 output preconditions.
2. Collect only the explicitly allowed non-consuming preflight facts from the frozen authority inputs.
3. Construct the canonical non-secret environment descriptor: exact six-key base environment plus explicitly allowlisted auxiliary `GIT_CONFIG_*` entries.
4. Call the existing pure `build_pair_bytes(...)`; do not duplicate JSON/Markdown construction logic.
5. Refuse to overwrite either final v0.5 file when existing bytes differ. Existing exact bytes may be treated as idempotent only if the contract explicitly permits it.
6. Stage both outputs using dirfd/no-follow/exclusive-create semantics. Verify staged byte length and SHA-256 before publication.
7. Publish with an explicit pair-transaction rule. Because two ordinary renames are not jointly atomic, the producer must define failure semantics: a failed producer run must leave either the prior exact pair unchanged or both final pair paths absent. A half-published pair must never qualify as READY.
8. Re-read both final files and verify exact bytes, SHA-256, Git blob OID, and the expected unified-patch identity before emitting success.
9. Emit only a non-secret producer witness/receipt and stop. Do not commit/push, materialize, write authority refs, or enter launcher/runtime from this producer.

Relevant current code boundaries:
- `tools/psm_wma/build_stage1_request_pair.py:1-6`: preserve the pure-byte/no-I/O module contract.
- `tools/psm_wma/build_stage1_request_pair.py` around `build_request_payload(...)`: keep the six mandatory environment keys and auxiliary-key allowlist there; producer should supply already-observed facts rather than weakening builder validation.
- `tools/psm_wma/test_build_stage1_request_pair.py`: keep as pure builder tests; add a separate producer test module rather than mixing filesystem transaction tests into builder tests.

## 2. GitHub credential-helper isolation

Freeze the **helper mechanism**, never credential bytes.

The currently authorized non-secret helper configuration is:
- `GIT_CONFIG_COUNT=1`
- `GIT_CONFIG_KEY_0=credential.https://github.com.helper`
- `GIT_CONFIG_VALUE_0=!/usr/bin/gh auth git-credential`

Recommended contract:

- Freeze `/usr/bin/gh` as an absolute executable identity: regular/non-symlink file, byte length, SHA-256, and version string.
- Never put token/password/username/auth-store bytes, `GH_TOKEN`, `GITHUB_TOKEN`, `HOME`, or raw `gh auth status` output into request-pair bytes, producer witness, logs, or exception text.
- If readiness must be checked, run a narrow child capability probe and retain only a non-secret result such as exit class / `credential_helper_ready=true`. The helper stdout containing credentials must be consumed privately and discarded, not serialized or logged.
- Keep secret-dependent readiness out of the immutable request-pair digest unless the authority contract explicitly requires otherwise; the reproducible pair should bind the helper program/config, while same-round pre-materialization evidence may carry only a redacted readiness boolean.

Concrete audit item before the next Gate:

`tools/psm_wma/materialize_immutable_source_authority_root.py` currently has helper-augmented `NativeAuthorityGit.env` (around the `NativeAuthorityGit` constructor), while the embedded `bootstrap_payload()` still contains a six-key base Git environment. Codex must document and test which remote operations execute through which environment. Any operation that can require authenticated GitHub access must demonstrably receive the helper config; public/read-only operations may remain on the six-key environment only if that split is explicit and tested. Do not rely on ambient Git/gh configuration.

## 3. Minimum CPU/static witness

Add a separate producer test module, suggested:

`tools/psm_wma/test_produce_stage1_request_pair.py`

Minimum causal cases for the next review:

1. Happy path: deterministic exact JSON/Markdown bytes and non-secret witness in a temporary directory only.
2. Existing divergent JSON or Markdown: reject before modifying either final file.
3. Failure after first staged write: both final paths remain absent/prior-exact; only producer-owned temporary artifacts are cleaned.
4. Publication failure at every transition point: no half-pair can satisfy READY/postcondition.
5. Symlink destination or unsafe parent/path replacement: reject via no-follow/dirfd checks.
6. Staged/final byte mutation: post-write verifier detects drift and no success witness is emitted.
7. Wrong root, child/Gitlink, tool blob, environment/helper descriptor, or preflight fact: no final pair is published.
8. Environment allowlist: exact six base keys required; only intended `GIT_CONFIG_*` auxiliaries accepted; `HOME`, `GH_TOKEN`, `GITHUB_TOKEN`, etc. rejected.
9. Secret-redaction witness: fake credential helper emits a sentinel credential; assert that sentinel is absent from request bytes, witness bytes, exceptions, and captured logs.
10. Bootstrap/native-Git environment split: every operation classified as authentication-capable is asserted to receive the helper config; read-only/base-six operations are explicitly enumerated.

Evidence to retain for formal review:
- exact producer source blob SHA and SHA-256;
- exact builder/materializer source blob identities used by the request;
- test command and PASS count;
- `py_compile` and `git diff --check`;
- exact pair byte lengths, SHA-256, Git blob OIDs, and unified-patch SHA;
- exact root/child/Gitlink observation;
- non-secret helper executable/config identity;
- redacted credential readiness result if required;
- explicit proof that no materialization or authority-ref write occurred during producer tests.

## 4. Formal review boundary

The next formal Gate should occur **after** the controlled producer has generated and post-verified the exact v0.5 JSON/Markdown pair, but **before** any materialization attempt.

The review target should bind the exact commit containing the producer implementation/tests and the exact request-pair bytes, together with the unchanged child Gitlink. The request should ask only for authorization of **one exact Stage-1 materialization attempt**.

The reviewer should verify at minimum:
- exact pair bytes/SHA/blob/patch binding;
- producer/build/materializer tool identities;
- helper executable/config identity without secret bytes;
- same-round preflight facts and root/child/Gitlink;
- producer rollback/fail-closed evidence;
- one-shot next-authority wording.

Do not combine this review with authority-ref publication or training authorization.

## 5. Failure / rollback / next authority

Two failure classes must remain distinct:

**Producer failure before materialization admission**
- fail closed;
- no materialization authority is consumed;
- leave prior exact pair unchanged or both final pair paths absent;
- do not repair with shell redirection, ad-hoc Python/temp scripts, or manual byte writes;
- open a narrow producer-remediation review if the controlled producer contract itself must change.

**Materializer failure after one-shot admission**
- the authorized materialization attempt is consumed;
- retain only the permitted failure receipt/evidence;
- do not write the authority ref unless the frozen success contract is fully satisfied;
- no retry under the same approval; any retry requires a new exact request pair / explicit next authority.

## Recommendation

Proceed with the separate controlled producer + producer-specific CPU/static witness. Do not modify the pure builder to perform I/O, and do not move credentials into the frozen pair. Resolve and test the `NativeAuthorityGit.env` versus embedded bootstrap environment split before asking for the materialization Gate.
