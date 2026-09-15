# ChatGPT formal review — Stage-1 runtime-failure diagnosis

- Formal root: `5e59eb06dc323cdcf71fb4fbc3092071648dae30`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-RUNTIME-FAILURE-DIAGNOSIS`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v0.5.json:1)`
- Scope: diagnosis/minimal repair only; no real materialization was executed by this review.

## Finding — HIGH: bootstrap interpreter identity guard is internally inconsistent with the frozen launcher path

The frozen launcher reaches `os.execve(PYTHON, exec_argv, ENV)` with `PYTHON=/opt/conda/bin/python3`, and the observed runtime reached the printed `bootstrap exec argv`, proving the outer launcher got to the exec boundary. The bootstrap then immediately uses the same `--interpreter=/opt/conda/bin/python3` but requires:

```python
ip=os.lstat(interp)
if not stat.S_ISREG(ip.st_mode) or stat.S_ISLNK(ip.st_mode) ...: fail()
```

This rejects a symlinked interpreter path even though `execve()` and the raw-byte hash via `open(interp,'rb')` legitimately follow that path. Conda installations commonly expose `bin/python3` as a symlink to the concrete versioned interpreter. The current request freezes interpreter bytes/hash/version but does not freeze the `lstat` kind or resolved executable pathname. This exactly explains the observed pattern: outer exec succeeds, bootstrap exits with generic `bootstrap-invocation` before module execution/evidence publication.

The FD handoff is not the leading root cause from the static evidence: backing FDs 3/4/5 are explicitly made inheritable, CLEAN owner fd 9 is duplicated to bootstrap fd 8, and `dup2` gives the exec-facing fd an inheritable descriptor. There is currently no equally direct indication of an FD-loss defect.

## Minimal repair

Do not merely delete the interpreter guard. Refreeze interpreter identity consistently:

1. During non-consuming preflight, resolve `/opt/conda/bin/python3` to its concrete `realpath` and freeze both the invoked-path identity and resolved executable identity/type/hash/version.
2. Prefer executing the resolved regular executable path and pass that exact resolved path as `--interpreter`; bootstrap then `lstat`s the resolved path, checks regular/non-symlink, exact raw SHA-256, and exact version.
3. If retaining the symlink invocation path is required, explicitly freeze symlink pathname + link target + resolved regular-file identity and validate the complete chain; do not simultaneously allow exec-through-symlink and reject that same pathname by `lstat`.
4. Replace the generic default `bootstrap-invocation` at the early guards with specific fail categories (`bootstrap-argv-shape`, `bootstrap-contract-fd`, `bootstrap-owner-fd`, `bootstrap-interpreter-kind`, `bootstrap-interpreter-hash`, `bootstrap-interpreter-version`) so a future failure is causally attributable.

## Acceptance

Before another real materialization attempt, provide CPU/static/non-materializing evidence that:

- a subprocess harness using a symlinked Python entrypoint reproduces the old guard failure and the repaired canonical identity path passes;
- FDs 3/4/5/8 survive the actual `execve` boundary with exact type/identity/content while 7/9 do not leak;
- interpreter kind/hash/version drift each fails with its own category before `runpy.run_module`;
- argv/bootstrap contract hashes remain byte-exact after retargeting;
- no authority evidence/ref/materialization is produced by the diagnosis tests.

No retry/materialization authority is granted by this diagnosis verdict; the repaired exact pair requires a fresh Gate.
