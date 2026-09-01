# R09-B2 P4 Interpreter Provenance design v0.8 review

- Request commit: `176166832874a826a2f61ac99ca3c766b5e317f6`
- Design commit: `d8934dc0c75b4d9ad833eec0e088943b15b65bcc`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Design: `docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.8_2026-09-01.md`
- Verdict: **REQUEST_CHANGES**

## Scope

Design-only review. This review checks the remediation of ChatGPT review `2026-09-01_R09_B2_P4_interpreter_provenance_design_v07_8a1bbf5_e4dbea6.md`. It does not authorize implementation, P4 record regeneration, P5 compose/export, torchrun, CUDA/GPU, model/data access, training, evaluation, inference, P5 closure, or B2-T.

## Findings

### Previous HIGH closed — ambient native-loader injection is now fail-closed

`docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.8_2026-09-01.md:7-29` adds a verifier-owned native-loader environment and, more importantly, constructs the child environment from an empty environment rather than inheriting the caller environment. `LD_PRELOAD`, `LD_AUDIT`, `LD_LIBRARY_PATH`, `GLIBC_TUNABLES` and the other listed loader controls are absent; dependency resolution and actual child spawn are required to use the same effective environment.

That closes the previous pre-Python injection path. The late child assertion is diagnostic only; the security boundary correctly sits in parent preflight plus `subprocess env=` before ELF loading.

### HIGH — the native dependency closure is still seeded too narrowly for the actual P4 runtime

`docs/build/PSM-WMA_R09_B2_P4_interpreter_provenance_design_v0.8_2026-09-01.md:25-27,33` says to recompute the child ELF/dynamic-loader transitive dependency closure while otherwise retaining the v0.7 host-native TCB unchanged.

The inherited v0.7 contract only explicitly roots native resolution at the child Python executable and bootstrap-used base-prefix extensions. That is insufficient for the actual D005 training process. After bootstrap, the approved staging payload can import many additional ELF objects, including PyTorch/native wheel extensions and package-owned shared libraries. Those objects can have their own `DT_NEEDED`, `RPATH/RUNPATH/$ORIGIN`, CUDA/system-library dependencies, or explicit runtime-loaded native libraries. Their installed bytes may already be bound by the wheel/source payload contract, but the identities of the native libraries they subsequently load are not proven merely by binding the Python executable's dependency closure.

False-PASS example:

1. lexical/base Python, loader environment, child executable closure, request, staging manifest, and `torch` extension bytes are all unchanged;
2. a system/CUDA shared library used only when a staged torch/native extension is imported changes at the same canonical path;
3. the current host-native TCB check does not seed dependency resolution from that staged ELF, so pre-spawn provenance can still PASS while later training executes different native code.

Required design fix:

1. Define the verifier-owned **native closure seed set** as every ELF regular file that may become executable native code from the approved runtime payload, not only the child executable/bootstrap base extensions. At minimum this includes:
   - child/base interpreter ELF;
   - approved base `lib-dynload` ELF payloads;
   - every ELF/native extension and package-owned `.so` in the copy-only staging manifests from registry/editable/VCS sources;
   - any separately approved native executable invoked by the bootstrap/runtime.
2. Under the exact v0.8 sanitized native-loader environment, resolve each seed's `PT_INTERP`/`DT_NEEDED` dependency graph with `RPATH/RUNPATH/$ORIGIN` semantics and take the deterministic union closure. Bind canonical path + SHA256 for every resolved external native object.
3. Runtime-native libraries loaded outside the static `DT_NEEDED` graph (for example an explicitly `dlopen`ed driver/plugin) must either be represented by a verifier-owned explicit native-runtime allowlist with canonical path/SHA, or the Gate must fail closed if such a dependency is required but cannot be proven. Do not silently classify such libraries as already covered by the child executable closure.
4. Add CPU/static negatives where the child Python and staged native extension remain byte-identical but one dependency used only by that extension changes path/SHA; pre-spawn verification must FAIL. Also cover a second staged ELF with a disjoint dependency to prove the verifier is taking the union over the entire native seed set rather than checking one representative extension.

This is a provenance-scope correction only. The v0.8 empty-environment/native-loader grammar should be retained unchanged.

## Positive observations

- The previous `LD_PRELOAD` / `LD_AUDIT` / `LD_LIBRARY_PATH` / `GLIBC_TUNABLES` blocker is correctly closed.
- Dependency resolution and spawn now share one effective environment instead of checking one environment and executing in another.
- Ambient loader/rank variables are not inherited into the child.
- The v0.7 out-of-band request digest, direct lexical `--no-python` worker, `-I -S -B -c` loader, verified bootstrap bytes, parent Python-install manifest, and copy-only mode-specific staging remain intact.
- The request remains design-only and does not attempt to run P4/P5/torchrun/GPU.

## Gate decision

**REQUEST_CHANGES**.

`APPROVE_TO_IMPLEMENT_P4_INTERPRETER_PROVENANCE` is not granted yet.

A next design revision should preserve v0.8 and only make the host-native dependency closure seed set complete across all approved runtime ELF payloads, with explicit handling for native runtime loads not captured by `DT_NEEDED`.

Still unauthorized:

- root P4/P5 tooling implementation;
- creating/modifying a Gate venv or external source checkout;
- P4 static record regeneration;
- P5 export/retry/compose or `load_experiment_from_toml`;
- torchrun/distributed execution;
- CUDA/GPU;
- model/dataloader/optimizer/checkpoint construction;
- weights/data/MP4 access;
- training/evaluation/inference;
- P5 closure;
- B2-T or any later gate.
