# Issue24 Stage3A H1 — OmegaConf startup compatibility: incremental Code Gate request

Date: 2026-11-08. Author: Codex. **Independent verdict requested, not granted.**

Actual Wan/DCP C startup failed because the loaded tokenizer exposed ListConfig
to the identity JSON seam. This increment normalizes those effective containers;
it does not redesign Stage3A or infer real-model functional acceptance from CPU.

| Source authority | Exact SHA |
|---|---|
| New Formal Root | `ea64c26f7738f2efba5c33c78f18eab475230a61` |
| New Child / Gitlink | `90ac5e91c5919cdb1d228aebd797e40327900981` |
| Previous approved Formal Root | `ef82fe02ee73e3c804b83ffbd68c5123c1377fa2` |
| Previous Child | `6842b329f71fff8b9813b2d00b83edfc61e3e505` |
| Root parent including all latest reviewer docs | `1882959a9ba88a00f4914a4657c07dc203d573a2` |

Root Draft [PR25](https://github.com/wxwy/psm_wma/pull/25), Child Draft
[PR7](https://github.com/wxwy/cosmos-framework/pull/7) carry this new Pair after
publication. Root evidence/Inbox successors never replace the Formal Root.

- [Narrow Child diff](https://github.com/wxwy/cosmos-framework/compare/6842b329f71fff8b9813b2d00b83edfc61e3e505...90ac5e91c5919cdb1d228aebd797e40327900981)
- [Narrow Root diff](https://github.com/wxwy/psm_wma/compare/1882959a9ba88a00f4914a4657c07dc203d573a2...ea64c26f7738f2efba5c33c78f18eab475230a61)
- H1 authority: `docs/collab/chatgpt/reviews/2026-11-08_Issue24_Stage3A_RealWanDCP_ListConfig_REQUEST_CHANGES.md`, and Issue24 comment6718159464.

## Production change

Only Child `cosmos_framework/inference/robocasa_vae_daemon.py` changes production
behavior. Lazy OmegaConf conversion uses the original ListConfig/DictConfig
parent context with resolve=True/throw_on_missing=True/enum_to_str=False. It
creates ordinary primitive containers before canonical serialization, preserving
duration order/duplicates, None vs empty, field values and the existing64KiB bound.
No stringification, coercion, ignored identity fields or disabled guard.

Duration lists require positive exact integers; bool/float/string/nested/set or
unresolved/missing values fail closed. Chunk maps retain the actual Wan
constructor's string-key/positive-integer/multiple-of-four semantics. Constructor
dimensions and causal flag retain exact integer/boolean types. Actual temporal
window and optional supplied-value comparison receive the same container
normalization. Tensor/scale hash sources, hash domains, class binding and internal
actual-duration set sorting are unchanged. Valid native constructor canonical
bytes and every loaded identity field exactly match the old-code baseline.

No Root production source, model math, transaction, source/Manifest/Resume,
M/B consistency, GPU ownership, training config/weights or Stage3B change.
Other edits are new daemon tests, a real-helper Policy C-init AST regression,
the real-Omega variant of the existing Root Registry test, Gitlink and bookkeeping.

## Author evidence

Archive: `docs/collab/codex/evidence/2026-11-08_issue24_stage3a_h1_omegaconf/`.
Machine result: `author_result.json`; raw final gate: `author-02/gate.json`.

**696 top-level tests +207 subtests PASS**, zero failures/errors/skips. JUnit
suite tests attributes total903 includes subtests; actual testcase elements696.
Ruff check/format PASS on4 changed Python files. Shell0, gate.status PASS,
source_unchanged=true; both repositories were clean at exact Pair gate entry.

| Group | Top-level / XML testcase elements | Subtests |
|---|---:|---:|
| Stage3/Stage1 plus new H1 |400|207|
| Root lifecycle/config |153|0|
| Existing A/B/Local-TTT/Session/batch/Sim protections |143|0|

Real OmegaConf2.3.0 (not a stand-in), same synthetic frozen BF16 CPU tensor state
and tokenizer class test both constructor and loaded identity. Coverage includes
order/copy isolation, None/empty, parent interpolation, missing/invalid/oversize,
config mutation digest and old-identity rejection, and Worker load_real_encoder
control flow with only its Wan constructor/encoder backend replaced by CPU doubles.
Actual Policy C-init source block calls the real identity helpers; Root supervisor
compares its frozen config against those real-helper results and starts/reaps a
real synthetic CPU peer via private FD. These tests do not load real Wan/DCP or
prove physical GPU attestation. Root lifecycle raw process/close records are
included with provenance, not mislabeled Root IPC CLOSED receipts.

Controlled RED: the same two new ListConfig tests failed on old6842 production
with original ProtocolError, pytest exit1. Old daemon source was byte-identical;
new tests were injected, so that worktree was not a clean old Formal Pair. The
three test files have identical RED/final SHA256. Original red log/JUnit, native
identity baseline, source/test hashes and exact runner are preserved.

Author-01 stopped after static/native-probe success: the external runner parsed
a warning-prefixed log as one JSON record. No pytest group ran; source unchanged.
Only the external parser was corrected to require exactly one JSON record with
the exact expected fields. Author-02 reran the same clean Formal Pair and passed.
Both original runner versions and failure artifacts remain; no source/test change
or suppressed warning was used to obtain PASS. This is author evidence, not a
new independent CPU approval.

Executed final command:

```bash
cd /workspace/work/psm-wma-stage3a-h1-formal
/workspace/.venvs/psm-wma-cpu/bin/python \
  /workspace/work/issue24-stage3a-h1-evidence/run_cpu_gate.py \
  --root /workspace/work/psm-wma-stage3a-h1-formal \
  --expected-root ea64c26f7738f2efba5c33c78f18eab475230a61 \
  --expected-child 90ac5e91c5919cdb1d228aebd797e40327900981 \
  --evidence-dir /workspace/work/issue24-stage3a-h1-evidence/author-02
```

CUDA disabled, HF/transformers offline, numeric threads1, Python3.12.14 /
torch2.10.0+cpu / pytest9.0.2 / Ruff0.12.7. Exact overrides/versions/argv/logs/XML
and source fingerprints are archived; artifact_sha256.json inventories raw bytes.

## Gate handoff and retained original GPU failure

Request independent GPT **APPROVE_CODE / REQUEST_CHANGES** only for this exact
H1 increment. Historical old-Pair CPU APPROVE_CODE remains historical and is not
carried over to this new Pair. The original real-H100 H1 failure review and raw
data-server evidence remain untouched. No remote server accessed or raw server
file copied; exact directory/hash provenance is in the machine result.

Real H100/Wan/DCP retry, B1 Visual96/FastState/Prefix/Action comparison and real
closed-loop smoke are **NOT_RUN here** and require the next authorized Gate after
independent CPU approval. P0 SR/cost, B8 admission, V3 merge and training are
outside scope. No real-model equality, performance gain or success-rate claim.
