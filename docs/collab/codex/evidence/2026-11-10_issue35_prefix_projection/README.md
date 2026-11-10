# Issue35 request-local native Prefix projection reuse — CPU evidence

2026-11-10 Asia/Shanghai. Formal Root `1b184204e301a51a7a20ed4dde1a11689589cf2d`; Child/Gitlink `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`. These are author CPU results, not independent approval or real H100 parity/performance.

## Exact clean author Gate

```bash
cd /workspace/work/psm-wma-attention-issue35
/workspace/.venvs/psm-wma-cpu/bin/python \
  docs/collab/codex/evidence/2026-11-10_issue35_b1_assembly/probes/cpu_gate.py \
  --root "$PWD" \
  --out /workspace/work/issue35-prefix-projection-evidence/author01 \
  --expected-root 1b184204e301a51a7a20ed4dde1a11689589cf2d \
  --expected-child d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2 \
  --expected-tests 314
```

The inherited B1 wrapper and scoped Gate are unchanged. A byte-identical wrapper is copied under `probes/`; its title still describes its original B1 task. Use a new evidence directory for any future execution. The command above ran on the exact clean committed Pair before these evidence files were added. Subsequent documentation HEAD is a ledger, not the Formal Root.

- `raw_cpu/author01/gate.json`: PASS; 314 tests, zero failures/errors/skips, 1,487 source fingerprints unchanged, 11 static files. `author01/scoped/focused.xml`: the raw complete JUnit (49.236s). Underlying scoped shell exit 0 is recorded in `author01/existing_scoped_gate.command.json`; the wrapper returns 0 exactly when its recorded final status is PASS.
- `raw_cpu/author01/scoped/`: original JUnit, commands, stdout/stderr, environment, source before/after and identity. No pytest temporary directory or Ruff cache is included. CPU-only/offline: CUDA_VISIBLE_DEVICES empty, BLAS/OMP threads1; no checkpoint or RoboCasa.
- The pre-existing W0 assertion is explicitly deselected and is not counted as PASS. Existing I001 exclusions on attention.py/inference_text_kv_memory.py/unified_mot.py are unchanged; no new exclusions.
- The final 59 focused tests overlap with the complete 314; do not add the counts.

## Controlled regression and development history

- `red01.*`: original Child4be production, only test/harness added. One expected assertion failure: each of three layers projects K/V/KNorm30 times instead of once. It is a controlled dirty-test experiment, not a clean Formal Gate.
- `red_identity.json`, `red_fixture.py`: old production identities and exact test fixture. `regression_provenance.json` proves the decisive regression function AST matches the final test (SHA256 c530333cc1434f21c3801a775716178a0775ed165792e078274e8d8948d15223).
- `green01.*`: same regression passes with each per-layer count1.
- `focused01.*`, `focused01_fixture.py`: preserved first broad run, 55 PASS/3 FAIL. One test attempted binding outside no-grad; two fullgraph tests used a Python data-dependent CPU Attention stub. Fixes were confined to the fixture's scope and tensorized causal/sample mask stub; no numeric tolerance was loosened.
- `focused02.*`, `focused02_source.patch`: intermediate 59 PASS version returning a stacked projection buffer; retained for provenance, not the final candidate.
- `focused03.*`: final actual native-buffer capture version, 59/59 PASS; FP32/BF1630-step equality, real buffer identity, invalidation, cleanup, request isolation, opt-out/training/inference-tensor fallback, CPU fullgraph dynamic=False/True. This is not CUDA Inductor validation.

`evidence_index.json` lists every other evidence file's size and SHA256 (including failed logs unchanged). No server tensor, DCP/checkpoint, profiler trace or private remote data was copied. Real K16/source64 30-step velocity/Action/Vision/raw15 strict parity and native-model timing remain for GPT's independent H100 Gate; no K1 rerun, no No-TTT/Sim/SR/900EP or V3 merge.
