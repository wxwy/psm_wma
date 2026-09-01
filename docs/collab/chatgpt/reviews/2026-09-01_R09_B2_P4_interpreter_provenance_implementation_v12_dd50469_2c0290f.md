# R09-B2 P4 interpreter-provenance implementation v1.2 review

- Request commit: `dd5046941fe93fc3c2649a7feb16698a311c578f`
- Request-declared implementation commit: `2c0290fc9cfa3ca375e1b7b6c3f56fd6df8701bd` (**unresolvable Git object**)
- Actual request parent / implementation inspected: `2c0290fc3c2f3953d3809c34598f2377ad092664`
- Design anchor: `476a5ddfa8beb89315234819e1e1a917ea227bc6`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Scope

Root-only static implementation review. No P4 record regeneration/refreeze, P5 export/compose/retry, torchrun/distributed execution, CUDA/GPU, model/data/weights access, training, evaluation, or inference was authorized or performed by this review.

## Findings

### HIGH — formal request is not bound to the implementation Git object that was actually reviewed

`docs/collab/chatgpt/CODEX_INBOX.md` in request `dd50469` names implementation `2c0290fc9cfa3ca375e1b7b6c3f56fd6df8701bd`, but GitHub cannot resolve that SHA. The request's actual parent is `2c0290fc3c2f3953d3809c34598f2377ad092664`.

This is the same provenance class already rejected for the v1.2 design SHA typo: a matching short prefix is not an acceptable substitute for an exact Git object.

Required: submit a request-only correction that explicitly binds the exact implementation object actually intended for review. This does not by itself close the implementation blockers below.

### HIGH — the approved P4/P5 execution-chain provenance was not implemented; verifier/tests still freeze the old direct-Python launch

Approved design v0.6+ requires the outer agent and every torchrun worker to enter the reviewed lexical interpreter through `-I -S -B -c <FROZEN_STDLIB_LOADER>`, with the worker launched by `torch.distributed.run --no-python`, request path + out-of-band request SHA + mode bound in argv, and no root-owned Python file executed before the verified loader.

Actual implementation still does the opposite:

- `tools/g0/verify_r09_b2_p4_d005.py:136-147` freezes `[lexical-python, -m, torch.distributed.run, ..., -m, cosmos_framework.scripts.train, ...]`; there is no `-I/-S/-B`, no `-c` loader, no `--no-python`, no `p4-agent/p4-worker`, and no worker-request digest.
- `tools/g0/test_verify_r09_b2_p4_d005.py:62-80` constructs that same old direct torchrun argv as the *valid* fixture, so the reported 17/17 PASS actively validates the obsolete contract.
- `tools/g0/export_r09_b2_p5_resolved_config.py:255-290` launches P5 as `[lexical-python, exporter_script, --child-request, ...]`, directly executing a root-owned Python file; it does not use the reviewed `-I -S -B -c` verified-bytes loader or an argv-carried expected request SHA.
- no bootstrap/loader implementation corresponding to the approved v0.6-v1.2 process tree was added in the implementation diff.

False-PASS: a v3 D005 using the old normal-site torchrun process tree can satisfy `_argv_ok()` and the unit fixture even though it violates the approved interpreter-provenance design.

Required: implement and machine-bind the complete outer/agent/worker/P5 launch contract from the approved design, including the frozen stdlib loader, exact worker `--no-python` command derivation, request digest token, mode/rank grammar, and permanent negatives rejecting direct `python -m cosmos_framework...` / direct exporter-script startup.

### HIGH — static D005 verification is incorrectly bound to an already-existing non-final staging path

Approved v1.0 contract says the **future separately authorized execution parent** creates the final copy-only staging under the previously absent D005 run root, then computes native `RPATH/RUNPATH/$ORIGIN` closure from that final canonical layout before spawning the agent. The run root must remain absent before that execution preflight.

The implementation instead makes `native_load_contract.staging_root` a static D005 field and immediately dereferences it during `verify_native_load_contract()`. `tools/g0/test_verify_r09_b2_p4_d005.py:75-80` proves the static pair by creating `root/staging`, while the D005 output `run_root` remains a different, absent path.

That cannot prove the final runtime native closure: moving identical ELF bytes to the future `<run_root>/import_staging/<token>` can change `$ORIGIN`/RUNPATH resolution. Conversely, creating the final run-root staging during P4 static refreeze would violate the frozen `fresh` contract.

Required: separate static D005 provenance from execution-time final-staging provenance. Static P4 may bind source/install/payload manifests and the staging grammar; only the future authorized execution preflight may materialize the final staging and derive the path-dependent native closure/request before spawn. P5 remains independently attempt-staged.

### HIGH — `verify_native_load_contract()` does not independently prove all-staged Python coverage

`tools/g0/r09_b2_interpreter_provenance.py:165-174` contains the correct primitive `analyse_all_staged_python()`, which compares the supplied manifest with every discovered staged `*.py`.

But `tools/g0/r09_b2_interpreter_provenance.py:250-275` does not use it. `analyse_python_contract()` trusts `approved_payloads`; `verify_native_load_contract()` then calls it with caller-owned `contract["python_payloads"]`. Therefore the verifier can be given a staging tree containing `hidden.py` plus a contract that simply omits `hidden.py`; direct/wrapper/allowlist candidate sets can all omit the same file and remain self-consistent.

The current test only calls `analyse_all_staged_python()` directly; it does not test this omission through the real `verify_native_load_contract()` path.

Required: verifier must independently derive or exact-check the Python payload universe from the verified staging/source manifest before any direct/wrapper analysis. Add a permanent shared-forgery negative where an extra staged Python file contains a native-load trigger and both `python_payloads` and all candidate sets omit it; full verifier must FAIL.

### HIGH — wrapper-chain implementation has multiple false-PASS holes and does not implement the approved v1.2 grammar

`tools/g0/r09_b2_interpreter_provenance.py:120-151` skips **every** call whose ancestor is a `FunctionDef`. The wrapper pass at `:195-250` then:

- only admits module-level `ast.FunctionDef` from `tree.body`; approved class-method wrappers are not analyzed;
- skips every invocation occurring inside any function definition;
- does not implement the required wrapper-object escape checks for alias/container/callback/return/reflection usages.

The claimed PyTorch-style regression is not an actual `torch.classes` class-method case; the test uses module-level functions. A concrete false-PASS is:

```python
import ctypes

def load(path):
    ctypes.CDLL(path)

alias = load
alias("evil.so")
```

The direct pass skips the function body, the wrapper pass can record `load` as an unused generic definition, and `alias(...)` is neither rejected as a wrapper escape nor counted as a wrapper invocation.

Required: implement the approved definition→invocation analysis for both module functions and class methods, scan invocation/escape uses in all executable AST contexts, fail on alias/container/callback/reflection/return/decorator escapes, and add the actual PyTorch `_Classes.load_library -> torch.ops.load_library -> ctypes.CDLL` shape plus wrapper-alias/shared-forgery negatives.

### HIGH — ELF/native evidence is caller-owned and self-certifying, not independently derived from bytes

`tools/g0/r09_b2_interpreter_provenance.py:281-325` accepts `closure_objects[*].undefined_symbols`, `elf_loader_records`, `target`, and `target_sha256` as supplied structures. It does not independently parse the ELF files, prove the closure object exists/is the bound file, derive the undefined loader symbols/callsites from bytes, or recompute the target file SHA.

`verify_native_load_contract()` simply feeds those caller-owned rows back into this schema gate. Thus a forged pair can remove `dlopen` from `undefined_symbols`, remove its record, and still be internally consistent. A nonexistent/fake target can also carry an arbitrary `target_sha256` string.

Required: root-owned verifier must derive the ELF seed/closure universe from verified payloads/final staging, parse the approved ELF bytes itself (PT_INTERP/DT_NEEDED/RPATH/RUNPATH/$ORIGIN plus loader symbols/callsite records), canonicalize targets, and recompute target SHA from actual files. Add shared-forgery negatives where both closure metadata and loader records omit the same real ELF site.

### MEDIUM — source cleanliness still ignores untracked files

`tools/g0/verify_r09_b2_p4_d005.py:66-70` implements `_git_clean()` as `git diff --quiet HEAD --`, which ignores untracked files. The approved provenance contract explicitly requires tracked **and untracked** clean source roots to prevent untracked import/source shadowing.

Required: use an exact full-clean check such as empty `git status --porcelain=v1 --untracked-files=all` for production root, submodule, and any VCS source root participating in provenance, with a permanent untracked-shadow negative.

## Positive observations

- Gitlink remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`; no submodule change is present.
- `lexical_interpreter()` correctly preserves lexical launcher path separately from resolved base interpreter, and P5 was at least changed to prefer the lexical `path` rather than directly using `realpath`.
- schema v3 requiring `native_load_contract` correctly makes legacy v2 records fail schema validation.
- `analyse_all_staged_python()`, candidate-set exact equality, and several CPU-only negative-test primitives are useful building blocks; the blocker is that they are not wired into an independently derived end-to-end contract.
- submitted tests are root-only/CPU-oriented and do not themselves perform the prohibited P4/P5/GPU/training execution.

## Gate decision

**REQUEST_CHANGES**.

`APPROVE_TO_CLOSE_P4_INTERPRETER_PROVENANCE_STATIC` is **not granted**.

The existing narrow implementation authorization remains sufficient for remediation: root-owned P4/P5 provenance tooling, loader/bootstrap/verifier/exporter code, and standard-library CPU tests may be modified and tested. No broader runtime authorization is implied.

Still unauthorized:

- creation/modification of the actual Gate venv or external production/VCS checkout;
- P4 record regeneration/refreeze;
- P5 export/retry/compose or `load_experiment_from_toml`;
- torchrun/distributed execution;
- CUDA/GPU;
- model/dataloader/optimizer/checkpoint construction;
- weights/data/MP4 access;
- training/evaluation/inference;
- P5 closure;
- B2-T or later gates.
