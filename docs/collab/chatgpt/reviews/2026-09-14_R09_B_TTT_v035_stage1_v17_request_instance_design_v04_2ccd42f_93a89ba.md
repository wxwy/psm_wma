# ChatGPT review — Stage-1 v1.7 request-instance design v0.4

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`
- Formal pair: root=`2ccd42fadc325c10d072f236b9b5805c732446b3`; child/Gitlink=`93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`
- Blockers: 0 (Design/Authority 0; Production/Authority 0; Evidence/Scope 0; child/runtime 0)

## Incremental review

The immediately prior same-Gate review of v0.3 had one HIGH Design/Authority blocker: the fixed authority-ref remote absence could be inferred from empty stdout without requiring that `git ls-remote` itself succeeded.

v0.4 closes that blocker. For both permitted exact remote queries, construction must now complete within the frozen timeout with `returncode == 0`. The future canonical request must bind, separately for each query, the exact command, return code, stdout raw-byte length/SHA-256 and stderr raw-byte length/SHA-256. Empty stdout is explicitly insufficient as a success signal.

The fixed authority ref `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1` is remote-absent only when the exact second query succeeds and has zero stdout bytes, zero result lines and zero stderr bytes. Nonzero return code, timeout, transport/auth/DNS error, diagnostics, malformed response or nonempty stdout fail closed as `BLOCKED_AUTHORITY_NOT_CLOSED` and cannot establish absence. The V2 query likewise only becomes advertised-identity authority after successful completion.

Previously closed boundaries remain intact: exactly two remote queries, zero mutation, fixed docs-only request output paths, frozen formal parent/base/replay identities, v1.6 consumed/non-reusable, one future request only, and independent same-pair three-party review of that exact request before any single Stage-1 attempt can be authorized.

Formal delta from v0.3 is docs-only v0.4 plus coordination/review bookkeeping. The root Gitlink resolves exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`; child/runtime production bytes are unchanged.

## Authorized consequence

This exact design may be used to construct exactly one fresh root docs-only Stage-1 v1.7 request-instance Markdown/JSON pair under the frozen construction allowlist. This approval does not authorize launcher/materializer execution, Stage-1 materialization/retry, source/checkpoint/manifest/data/cache/runtime I/O outside the allowlist, downstream collection/receipt/record/package/publication, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.
