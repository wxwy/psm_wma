# ChatGPT formal review — Stage-1 v1.7 pre-C rehearsal consumer CPU/static

Formal pair:
- root: `c2174dd00e11b96f7ff1b187a2ea84853bfd8f42`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:118)`

Current blockers: `1 HIGH`; Design/Authority: `0`; Production/implementation: `1 HIGH`; Evidence/identity: `0`; child/runtime: `0`.

## Positive closure

The directly requested remediation from the prior pair is closed:
- both remote-query stdout/stderr and extracted advertised-V2 bytes now carry explicit length/SHA identities and are fail-closed;
- both v0.5 output absences and all four V18 designated absolute paths are typed ordered `lexists=false` observations with canonical raw bytes and length/SHA identities;
- `AUTHORITY_ARGV` is rebound to the frozen immutable-source ref literal;
- prior exact-once retirement, typed readback/core byte equality, exact v0.5 pair, six-key environment, patch inverse witness, capability sealing and terminal result behavior remain present;
- formal root resolves, scope is root-only tooling/tests/status, and its `cosmos-framework` Gitlink equals the declared reachable child exactly.

## HIGH 1 — the sealed rehearsal still omits required inherited closure inputs/identities

V31 requires one CPU/static implementation to cover all four rehearsal-input classes, including **all injected source objects and literal binding** plus the full live provenance/freshness closure. The inherited V1.7 authority is explicit that this closure is non-shrinkable.

The current `ClosureV1` at line 118 still contains only:
- opaque `git_identity: bytes`;
- bare `config_raw: bytes` and `local_v2_raw: bytes` with no explicit byte-length/SHA identity;
- the two now-correct query facts;
- local/remote authority-ref absence;
- output/designated absence observations.

It still does not model or validate the inherited required fields:
1. `.git` object/directory identity as a typed validated identity, plus `.git/config` raw length/SHA and local `V2` raw length/SHA;
2. `selection`, `config`, `bootstrap`, `bootstrap_contract`, replay outer and canonical parser argv/raw identities;
3. the full V1.0 P0 root/path/blob tuple, P1 injected-object identities and owner-FD flag/value;
4. the frozen cwd/index/evidence targets as explicit sealed targets;
5. V31's complete injected source-object set and literal `ReplayBinding` binding.

These are not optional diagnostics. V1.7 says the provenance closure must not be abbreviated into partial query blobs/ambient state/history, and V31 says PASS must seal every final object needed by C. Because the static core has no fields or validation for these items, a foreign/incomplete rehearsal can still PASS while violating the frozen authority.

## Acceptance criterion

Before closure:
- extend the typed rehearsal input/closure to represent every inherited V1.7/V31 item above;
- bind raw bytes/argv/targets with the exact frozen identities (including length/SHA where the authority requires them), exact ordering and allowlists;
- preserve the already-correct query/absence/capability/patch/readback/one-shot behavior;
- add direct CPU/static drift tests for every newly added identity/target/source-binding field, proving fail-close before consumer invocation;
- keep this Gate root-only and pure-memory; no real Git/network/source/data/cache I/O, v0.5 construction/C, materialization, child mutation, GPU or training.

No CPU/static closure is granted for this pair.