# V3 Packed128 Gate B0 — isolated CPU comparator candidate

Owner decision 2 (2026-10-13): approved implementation + CPU-only verification.

Files:
- `tools/gates/v3_packed128_gateb_compare.py` — read-only two-window/8-rank consumer & sidecar CPU plan, isolated RNG witnesses, CPU Native payload hash mode and fail-closed unimplemented B1.
- `tools/gates/v3_gateb_numerics.py` — proposed per-FQN numerical comparison formulas; thresholds NOT Owner-frozen.
- `tools/gates/test_v3_packed128_gateb_compare.py` — CPU synthetic fixture and negative tests.
- `docs/DS_PRO_V3_GATEB_B0_CPU_VALIDATION_2026-10-13.md` — DS execution instructions and evidence request.

This is **not** a GPU Gate B1 numerical implementation or a persisted checkpoint migration. No production code was changed. Do not run `--mode paired-run` (blocked in code).

Use the project's validated V3 Python environment and run:

    python -m py_compile tools/gates/*.py
    python -m pytest -q tools/gates/test_v3_packed128_gateb_compare.py

Local isolated result at authoring: 21 passed; no real RoboCasa/8-rank source DCP/GPU used.
