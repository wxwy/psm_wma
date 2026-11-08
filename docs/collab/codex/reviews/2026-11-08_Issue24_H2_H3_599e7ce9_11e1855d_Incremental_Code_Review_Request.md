# Issue24 Stage3A H2/H3 — C-B1 startup compatibility: incremental Code Gate request

Date: 2026-11-08. Author: Codex. **Fresh independent verdict requested.**

**Publication status: BLOCKED_ACCOUNT_EMAIL_VERIFICATION.** Git push and connected
GitHub API both returned403 requiring a verified email. New source/evidence/Inbox
commits are local; PR25 remains5e45b020 / PR7 remains90ac5e91. This prepared
request has not been delivered. See publication_blocked.json; tested Pair below
is intact, and no new code Gate or GPU result is claimed.
Only H2 private-bootstrap timeout representation and H3 actual CUDA UUID format
are changed. No Stage3A redesign, new hardware execution or Gate closure claim.

| Authority | Exact SHA |
|---|---|
| New Formal Root implementation | `599e7ce9d0e9ee5bb1cf96fe687bb28e35b6f77e` |
| New Child / Root Gitlink | `11e1855d58cb9f017243a08d610fb33a4443b773` |
| Previously approved Formal Root | `ea64c26f7738f2efba5c33c78f18eab475230a61` |
| Previous Child | `90ac5e91c5919cdb1d228aebd797e40327900981` |
| Root parent preserving all latest reviews | `5e45b02027d18b368751f1b22ea6d292c93e77bc` |

Continue isolated Draft [Root PR25](https://github.com/wxwy/psm_wma/pull/25) /
[Child PR7](https://github.com/wxwy/cosmos-framework/pull/7). Root docs/evidence/
Inbox successors never replace the implementation SHA. Official V3 is untouched.

- [Narrow Root diff](https://github.com/wxwy/psm_wma/compare/5e45b02027d18b368751f1b22ea6d292c93e77bc...599e7ce9d0e9ee5bb1cf96fe687bb28e35b6f77e)
- [Narrow Child diff](https://github.com/wxwy/cosmos-framework/compare/90ac5e91c5919cdb1d228aebd797e40327900981...11e1855d58cb9f017243a08d610fb33a4443b773)
- Authority: `docs/collab/chatgpt/reviews/2026-11-08_Issue24_C_B1_1x1_RealStartup_H2_H3_REQUEST_CHANGES.md` and Issue24 comment6719277972.

## Two production changes only

H2 — Root `scripts/robocasa_eval_v2/shared_vae.py`: C preflight (called by public
config.resolve) requires positive whole seconds; 10.0/15.0 remain legal and map
to exact integer10/15 **only in private FD bootstrap**. Fractional seconds fail
before fresh namespace/model/Worker startup, with no rounding or new time unit.
The same guard runs at serialization. Resolved config values/types, deadlines,
full Resume/config comparison and A/B/default behavior remain unchanged. Global
Child strict_json still rejects floats. No field removal or timeout extension.

H3 — Child `inference/robocasa_vae_daemon.py`: actual CUDA property UUID must have
full standard8-4-4-4-12 hexadecimal syntax, optionally prefixed by exact `GPU-`.
Only an absent prefix is added; an already prefixed value is retained. Compare
the resulting UUID exactly with Root expected, then still call actual nvidia-smi
using canonical UUID and verify physical index, UUID and normalized PCI. Unique
visible CUDA, concrete loaded parameter device and same-device checks are
unchanged. No ordinal mapping, config substitution, fallback or skipped guard.

Other changes are CPU tests/fixture, Gitlink and bookkeeping. No model math,
H1 normalization/hashing, transaction/15+1/session semantics, scheduling, M/B
Resume, strict JSON schema, training config/weights or Stage3B admission changes.

## Controlled RED and exact-pair author GREEN

**Final author-01 PASS:738 top-level tests +207 subtests**, zero failures/errors/
skips; Shell0, gate.status PASS, source_unchanged=true. Ruff check/format PASS on5
changed Python files. JUnit suite tests total945 includes subtests; actual XML
testcase elements738. Both worktrees were clean at exact Pair Gate entry.

| Group | Top-level / testcase elements | Subtests |
|---|---:|---:|
| Stage3/Stage1/H1/H3 |429|207|
| Root lifecycle/config/H2 |166|0|
| Existing A/B/Local-TTT/Session/batch/Sim protections |143|0|

Three selected new regressions failed on byte-identical old production:

1. Default10.0 via actual Root private FD → actual daemon strict_json failure.
   Original Worker log retains float/non-finite JSON token forbidden, not a fake
   model identity mismatch. Owned-process cleanup records are retained.
2. Public resolve failed to reject C10.5 before fresh namespace (DID NOT RAISE).
3. Matching bare actual CUDA UUID was rejected before NVML.

RED pytest exit1 each /3expected failures; tests/fixture were injected, so that
old worktree was not a clean old Pair Gate. All3 test/fixture file SHA256 values
are identical in RED and GREEN; no weakened assertion or temporary production-source
rewrite between those runs was used to obtain GREEN.

H2 positive evidence includes8 real synthetic CPU Registry/FD/READY/close cases:
3seconds, default10.0, explicit15.0, integer15, each with native and real-OmegaConf
constructors. Worker reads the actual strict private FD and reports parsed integer
duration; resolved type/value remain original. Worker survives Sim End; owned
exit0, sockets removed, external process survives and is then reaped by fixture.
Fractional C preflight rejects before namespace; A/B/default10.5 remain accepted
with unchanged execution identity. Raw lifecycle/process/process_closed records
are supplied with provenance; Registry close records are not mislabeled IPC proofs.

H3 CPU descriptors/mocks cover bare/prefixed valid UUID; malformed, truncated,
missing, duplicate/MIG/wrong prefix and wrong GPU; forged matching malformed UUID;
wrong NVML index/UUID/PCI, empty/multiple rows, unavailable/timeout; zero/multiple
visible CUDA; empty/CPU/mixed or split-device weights. Valid cases require the
NVML query by canonical UUID. All physical checks use synthetic CPU stand-ins,
not new hardware measurements. Original real-H100 proof remains reviewer evidence.

Native constructor canonical bytes and all loaded VAE identity fields also match
the previously archived old-code baseline. Original Stage3A/H1/A-B regressions
remain in this run; no old-Pair test count is inherited as new-Pair PASS.

Executed command:

```bash
cd /workspace/work/psm-wma-stage3a-h2h3-formal
/workspace/.venvs/psm-wma-cpu/bin/python \
  /workspace/work/issue24-stage3a-h2h3-evidence/run_cpu_gate.py \
  --root /workspace/work/psm-wma-stage3a-h2h3-formal \
  --expected-root 599e7ce9d0e9ee5bb1cf96fe687bb28e35b6f77e \
  --expected-child 11e1855d58cb9f017243a08d610fb33a4443b773 \
  --evidence-dir /workspace/work/issue24-stage3a-h2h3-evidence/author-01
```

CUDA disabled; HF/transformers offline; numeric threads1. Python3.12.14 /
torch2.10.0+cpu / pytest9.0.2 / Ruff0.12.7 / OmegaConf2.3.0. No real checkpoint,
model, simulation, remote server, GPU query or vendor/cache operations performed.

## Raw evidence and next Gate

Archive: `docs/collab/codex/evidence/2026-11-08_issue24_stage3a_h2_h3_startup/`.
Original logs/XML/argv/version/env/static scope/source fingerprints, RED Worker
failure log, OS lifecycle records and exact external runners as.py.txt are
retained; artifact_sha256.json inventories bytes; author_result.json provides
counts/provenance. Raw cache/bootstrap/actor config/inherited environment omitted.

Request **APPROVE_CODE / REQUEST_CHANGES** only for this exact H2/H3 increment.
Prior H1 CPU and real fixed-input B1 parity PASS remain historical; they do not
provide fresh approval of this Pair or real C-B1 closed-loop acceptance.

Original H2/H3 review and data-server failure evidence are untouched. Original
summary SHA6eefae77600f910050d0078b947f078e7879ae8ddfae2e69bd3eaf9c221c213a and
directory provenance are recorded; server files were not accessed/copied. No
GPU retry here. After independent Code Gate, the same separately authorized
C-B1 1Server×1Sim real post-step/IPC/commit/ACK/End smoke can be considered.
P0 SR/cost, B8 Action admission, V3 merge, training/900EP remain outside scope.
