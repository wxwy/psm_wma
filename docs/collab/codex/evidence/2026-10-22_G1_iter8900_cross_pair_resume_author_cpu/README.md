# G1 iter8900 Owner-authorized cross-pair resume — author CPU only

Isolated candidate Root `b910304dbf493eb5babe26cf1b055edc8477b386` / Child-Gitlink `61bfa94766d33d95a7fa9771857d0f2fb3f0b405`, branch v3-g1-cross-pair-resume-20261022. Not merged/executed; no real G1/DCP/model/optimizer/RNG load, GPU, torchrun or server access.

Final115 cases=68new+28F0+19Config-truth,32subtests PASS,0fail/error/skip,6.275s. JUnit147 includes subtests.20warnings from old imported cache test marker declarations. Ruff0.12.7/format/syntax/bash-n/diff PASS.

Synthetic canonical YAML hash replaces production pin only inside test fixture. Old source-pair constants are copied into original35b0 baseline solely so the same fixture can run: no new runtime logic copied; baseline.log is expected source equality failure. Recreate phase5_before.py via git show35b0:examples/psm_wma_robocasa_corrected_phase5.py before using baseline_probe.py. first.log is earlier55-casegreen, not final suite.

Original Local snapshot/restore/planner/core bodies execute with real Torch CPU at small dimensions and full world8/B8/GA2/T16/K4. Only heavy import wiring is isolated; callback base is object. All-rank collectives use8-element mocks, not distributed GPU/Gloo. Real preflight function uses synthetic external model/data-loading boundaries and supplied semantic fixture. Runtime generic code and old regression tests remain byte-identical; full target dependency/actual legacy digest and full-checkpoint validation are DS/Owner gates.

Original config/identity/latest/checkpoint bytes+mtime unchanged in every read-only test; lifecycle test appends only a new launch subdirectory in synthetic temp assets. witnesses.json and gate.json retain full evidence.
