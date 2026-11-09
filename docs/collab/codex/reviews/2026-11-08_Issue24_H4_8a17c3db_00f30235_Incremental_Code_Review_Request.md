# Issue24 Stage3A H4 — Actor source-witness contract: incremental Code Gate request

2026-11-08. Author: Codex. **Independent verdict requested, not granted.**

| Source authority | Full SHA |
|---|---|
| New Formal Root implementation | `8a17c3db6a2e571b67e6a149638f9d7922a704d5` |
| New Child / Gitlink | `00f30235da6ffb085a9304ef6501ede509203092` |
| Previous approved Formal Root | `599e7ce9d0e9ee5bb1cf96fe687bb28e35b6f77e` |
| Previous Child | `11e1855d58cb9f017243a08d610fb33a4443b773` |
| Root parent with latest review/Inbox | `878f1bb6d6f61996850d57c75f1d70502e04886b` |

Maintain isolated Draft [Root PR25](https://github.com/wxwy/psm_wma/pull/25) and
[Child PR7](https://github.com/wxwy/cosmos-framework/pull/7). Later Root
evidence/Inbox/receipt commits do not replace the Formal Root.

- [Child narrow source diff](https://github.com/wxwy/cosmos-framework/compare/11e1855d58cb9f017243a08d610fb33a4443b773...00f30235da6ffb085a9304ef6501ede509203092)
- [Root narrow diff](https://github.com/wxwy/psm_wma/compare/878f1bb6d6f61996850d57c75f1d70502e04886b...8a17c3db6a2e571b67e6a149638f9d7922a704d5)
- Authority: H4 formal report `docs/collab/chatgpt/reviews/2026-11-08_Issue24_C1S1_RealH100_H4_ActorSourceWitness_REQUEST_CHANGES.md` and Issue24 comment6720302846.

## Minimal production change

Child `simulation/robocasa/eval_v2_worker.py` adds25 lines only. For explicit
phase_b + sim_shared_vae + required, a fixed source-owned map imports the exact
ten extra Root C modules and obtains their actual imported __file__ origins:
shared_client, local_client, transaction_client, feature_trace, feature_evidence,
session_transactions, batch_transactions, vae_protocol, vae_worker, vae_client.
Unknown evidence profiles or inconsistent C execution/memory mode fail closed.

Original exact set equality and each imported absolute path/SHA256 comparison
remain unchanged, now covering all18 C labels. The allowlist never derives from
cfg.source_files and accepts no arbitrary superset. No Root witness removed,
sealed config rewrite, source bypass or server_vae fallback. Legacy valid A/off
and B/server_vae remain exact8; unprofiled PhaseA7/factory path unchanged.

No Root production edit. Other edits are new cross-repository test, Gitlink and
bookkeeping. No model/Local-TTT/VAE/transaction/Batch/Resume/H1/H2/H3 changes.

## Controlled old-code RED and exact-pair author GREEN

**821 top-level tests +207 subtests PASS**, zero failures/errors/skips, Shell0,
gate.status PASS, source_unchanged=true. Ruff check/format PASS on2 changed Python
files. JUnit suite tests1028 includes subtests; actual testcase elements821.

| Group | Top-level / testcase elements | Subtests |
|---|---:|---:|
| Original Stage3/Stage1/H1/H2/H3 |429|207|
| Root/H4/default Actor source/lifecycle/config |249|0|
| Original A/B/Local-TTT/Session/batch/Sim protections |143|0|

New80 H4 cases call actual Runtime._setup_actor under Store.locked, capture its
actual sealed config and verify its CLI config SHA. The test calls actual Child
serve(factory=None), retaining real module imports/origins/source/package-version
checks and socket wire protocol. Only unavailable execution boundaries are
doubled: Policy/Worker launch, rendering/vendor/environment. No environment is
created and no reset/step or real hardware functionality is claimed.

Actual Root-produced C18 and legacy A/B configurations (8source labels each)
all reach READY and close.
Each of18 labels has missing/hash/path negatives; all10 C imports have foreign
checkout origins with identical content, plus missing import, extra/renamed
labels, absent/server/unknown evidence profile, incompatible phase/memory mode
and library drift. Every negative fails before renderer/vendor/environment and
the original sealed file stays byte-identical. Source proof files contain only
labels/path/hash and bounded startup metadata, never raw Actor capabilities.
Original3 default-Actor regressions also run, protecting the PhaseA7 path.

First RED harness attempt lacked Store.locked and failed missing lease_id before
Actor. Its raw failure/JUnit/test+runner snapshots are retained; only that new
fixture was corrected. Successful controlled red-old-code-02 uses byte-identical
old Root runtime and old Child11e1855d Actor, then rejects actual C18 with exact
incomplete native source witnesses (pytest1FAIL/exit1 expected). That isolated
old worktree had an injected test and was not a clean old Formal Pair. The final
RED/GREEN test file SHA256 is identical. No production-source rewrite between
runs or weakened assertion was used to obtain GREEN.

Exact clean Pair final command:

```bash
cd /workspace/work/psm-wma-stage3a-h4-formal
/workspace/.venvs/psm-wma-cpu/bin/python \
  /workspace/work/issue24-stage3a-h4-evidence/run_cpu_gate.py \
  --root /workspace/work/psm-wma-stage3a-h4-formal \
  --expected-root 8a17c3db6a2e571b67e6a149638f9d7922a704d5 \
  --expected-child 00f30235da6ffb085a9304ef6501ede509203092 \
  --evidence-dir /workspace/work/issue24-stage3a-h4-evidence/author-01
```

CUDA disabled, HF/transformers offline, numeric threads1; Python3.12.14 /
torch2.10.0+cpu / pytest9.0.2 / Ruff0.12.7 / OmegaConf2.3.0. Native constructor
canonical bytes/full loaded VAE identity still equal the original archived
baseline. No old-Pair PASS count is inherited as this new-Pair evidence.

## Evidence and next Gate

Archive `docs/collab/codex/evidence/2026-11-08_issue24_stage3a_h4_actor_sources/`
contains original logs/XML/argv/env/version/source fingerprints, successful RED
and initial fixture failure, source/OS lifecycle proofs and external runner
snapshots as.py.txt. author_result.json is the machine summary and
artifact_sha256.json inventories bytes. Raw Actor configs/private bootstrap,
caches and full inherited environment are excluded.

Request fresh independent **APPROVE_CODE / REQUEST_CHANGES** only for exact H4
increment. Author CPU is not reviewer approval or a real C1S1 loop PASS. Previous
H2/H3 CPU and genuine hardware startup/fixed-input B1 parity remain historical.

Original hardware failure report and data-server evidence remain untouched;
summary SHA f8298ac777b4edad7f6187c061ac5c0e6f83aeaef56abeb95755fca33b4727ad and
directory provenance are in the machine summary. No remote server or original
server files accessed/copied. No GPU, real model/Sim, SR/900EP, B8 Action,
training/old-job operation or official V3 merge. Same real C-B1 1Server×1Sim smoke
comes only after independent Code Gate and authorized execution handling.
