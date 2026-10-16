# F0 REG-01 / TEST-02 author CPU evidence

Root implementation `9e51c94a6d5dba41bd37423b9db8e634ca433789`; Child/Gitlink `7cae7c3049310ccc3b7e44ce9769534e152d1f26`.

Minimal CPU author verification only. Full established V2 dependency environment is absent; DS full-environment validation is mandatory and PENDING. No GPU, torchrun, real model/DCP/data access.

`gate.json` gives exact commands/return codes and source hashes matched against committed Child. Pytest9: 28 methods +32 subtests =60 JUnit cases, all green/no skips. Direct unittest runs the same 28 methods; do not add counts across runners.

`scoped_probe.py/json/log` extracts the unchanged existing Index regression function/helper AST with original pytest assertions, compares production AST (guard reorder only), and runs the original nine TrainerTests before/after with an explicit external module whose import body evaluates torch.dtype. Old fixture: 9 errors; new fixture: 9 pass, unchanged names and assertion ASTs. This is a controlled import-collision reproduction, NOT the actual V2 dependency stack. The intentionally failing baseline traceback is in before_trainer9.log; after_trainer9.log confirms the corrected fixture. Full original-module collection still awaits DS.

Prior DS Gloo/configuration/storage evidence was accepted by GPT on the previous Pair. This patch does not re-execute or relabel that evidence; unchanged-core reuse is subject to DS/GPT diff verification.
