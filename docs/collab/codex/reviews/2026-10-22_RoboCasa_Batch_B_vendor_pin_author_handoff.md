# Batch B — RoboCasa 1.0.1 vendor source / CPU author handoff

Date:2026-10-22. Result: **AUTHOR_SOURCE_CPU_PASS; independent review pending**.
**Physical compatibility / real benchmark Gate remains OPEN.** No actual Kitchen,
MjData, reset/step, renderer, GPU, Action Server, model or training was started.

## Exact isolated source identity

| Item | Exact value |
|---|---|
| Root Implementation | `2b14ef1a6b13be0c0dea405231506323594d81f2` |
| Child / Gitlink, unchanged | `35b0ea1ccee9ee26653ed6589c484f0997d1c586` |
| Root candidate ref | `v3-robocasa-vendor-b-20261022` |
| Root baseline | `d6b2484fa9f4ff5775ea1f13f3fcaf973ce499e8` |
| robosuite patch base | `824ac14cefcfb7ec125fe5eb2e0bad7364466154` |
| Reconstructed patched vendor commit | `1ac174585293ed998ffc9cf73e47439798cf6f6c` |
| Patched tree | `195e30cfd5d37289d227a89234bd8bb069792905` |
| RoboCasa evaluator1.0.1 | `6f90063c0ec2b9916bbd977368b54c98d9c2d908` |
| MuJoCo Python/native; NumPy | `3.3.1`; `2.2.5` |

This uses the Owner-authorized **patchset alternative**: the full patch, SHA256, fixed
base, expected tree/commit, commit metadata, license and local-only build tool live in
Root. The vendor SHA is actually reconstructed and checked, **not claimed to exist on
the upstream ARISE remote**. Two independent builds reproduced it. See
[vendor lock](../../../../third_party/robosuite_patches/vendor.lock.json) and
[build/runtime runbook](../../../../third_party/robosuite_patches/README.md).

Batch B is independent of the G1 cross-pair and Batch A candidates. No Child source,
existing Queue, legacy identity helper, Local-TTT, training, optimizer, RNG, checkpoint,
Config, datasets or historical evaluation results were changed. No source merge into
V3 or environment deployment is included. A/B/C combination needs a new formal Pair.

## Implementation and contract evidence

1. **Legacy controller:** full official `LegacyMobileBaseJointVelocityController`, its
   package export and factory dispatch. Reference commit
   `5ce6643f3092639d08f7b0f90ed1c6a84f50552c` is frozen for selected backport provenance,
   not installed as master. The Legacy class AST matches it exactly. CPU tests use the
   actual class's set_goal with synthetic Sim state for both X- and Y-forward definitions,
   signed forward/lateral/yaw and four headings. X-forward uses +heading; historical
   Y-forward swaps planar inputs and uses -heading. Ordinary-controller alias fails the
   nonzero-heading golden convention. Input arrays remain unchanged. Original raw15→env12
   decoder bodies retain all six base directions and mode-off masking. The pinned Omron
   XML axes and Kitchen's Legacy selection are checked directly.
2. **Deferred initialization:** official constructors through ManipulationEnv→RobotEnv→
   MujocoEnv and base reset are exact AST backports. A counting-boundary harness executes
   original constructor/reset bodies to show no load/Sim/renderer/scene-RNG draw before
   first reset when False, and proper first/later soft/hard-reset behavior. It is not a
   real Kitchen test. Default eager initialization remains available.
3. **Destruction:** `_destroy_sim` handles absent, None, live and already-destroyed Sim.
4. **Physics options:** Task forwards both flags into the real MujocoWorldBase/XML.
   Native3.3.1 compiles that actual model with CCD disabled→enableflags0 and enabled→16.
   One `<option>` is updated; no conflicting duplicate is inserted. Booleans are typed.

Important runtime boundary: **MuJoCo3.3.1 has no sleeping-islands capability / MJCF sleep
attribute**; the native parser rejects even `sleep="disable"`. Thus the required False
means actual absent/disabled capability and is recorded; True explicitly rejects. No
version upgrade, ignored True or false mapping to unrelated `mjENBL_ISLAND` is introduced.
This differs deliberately from the later upstream World's optional sleep feature.

The four behavior repairs touch eight vendor files (factory, mobile exports/controller,
base, robot env, manipulation env, Task, World). Full source origin/blob/AST hashes are in
[source provenance](../../../../third_party/robosuite_patches/source_provenance.json).
The DS-reported2096-byte diff/hash remains **attested, original bytes unavailable**;
this work does not claim to have checked/replayed those exact temporary patches.

## Runtime provenance component and integration boundary

New `scripts/robocasa_vendor.py` provides a standalone read-only source/version probe and
`build_verified_evaluation_identity` integration API. It:

- Uses the chosen Simulator interpreter and intended launch environment, including
  PYTHONPATH. `-I` is deliberately avoided because it would hide real import overrides.
  Actual module `__file__`/version, installed metadata, locked HEAD, clean tracked/index
  state, ignored/untracked source, native MuJoCo version/library hash and interpreter/
  probe/lock hashes are verified. No config-supplied runtime JSON substitutes for this.
- Permits normal fixture assets only through an explicit per-file SHA inventory below
  the package's `models/assets/`; unknown scripts/backups/native code/symlinks reject.
  Existing bytecode must match tracked source code, source location and interpreter magic.
  Changes/missing/extra inventory entries reject. Probe/compiler caches stay external.
- Reads official registry horizons once: **CloseFridge900, NavigateKitchen450**; no extra
  1.5× multiplication. Target split/source contains10 paired target kitchens. These are
  source/protocol facts, not a claim to have observed a running Kitchen or simulator.
- Returns immutable `manifest` separately from raw `runtime_probe_evidence`; variable
  import logs cannot break same-identity resume equality. Dataset SHA/recorded version
  fields and original JSON pointers are separate from `evaluation_runtime`. Missing
  generation/capture Git commits remain UNKNOWN; no version string implies an official
  capture-time tag. Ambiguous version claims reject; absent ones stay NOT_RECORDED.

**Not wired into the legacy Queue in this batch.** Batch C must pass the exact shared
Simulator environment, persist the stable manifest and raw probe evidence separately,
and repeat the probe inside the actual Simulator before env creation, comparing its
runtime digest. Only the later integrated Pair may claim the runtime is enforced across
the full real launch. The old manual launcher command is still not implemented here.

## Author CPU results and limitations

[Evidence directory](../evidence/2026-10-22_RoboCasa_Batch_B_vendor_author_cpu/) contains
gate.json, exact Root patch, vendor build/behavior witnesses, raw logs/JUnit, package and
source hashes, source-protection proof and expected-red baseline probe.

| Check | Result |
|---|---|
| Final focused cases | **109 passed**, 0 failures/errors/skips,16.24s |
| Original v1.5.2 baseline | Expected RED:4 failures, exit1 |
| Two independent local builds | Same clean vendor commit/tree |
| Ruff0.12.7 check/format | PASS for all3 new project Python files |
| Syntax | PASS for3 project files and8 patched vendor files |
| Source diff checks / hashes | PASS |
| Actual complete runtime CLI on author CPU venv | **Expected BLOCKED**: vendor distributions/full simulator environment not installed |
| Real Kitchen/reset/step/GPU / generation physics equality | **NOT EXECUTED / NOT PROVEN** |

Positive runtime unit tests explicitly double registration/import/metadata boundaries
while retaining real vendor Git/source checks, real native3.3.1 and original registry
data. Controller/XML modules are real code loaded without eager environment registration.
The actual CLI rejects this incomplete CPU environment instead of treating a source
checkout/version string as a valid installed runtime. Do not describe these unit tests
as target-host import acceptance or real PandaOmron physics verification.

Failure history: the first offline build requested unnecessary historical blobs from a
partial cache; local shallow fetch fixes that without network or edits to caches. Initial
two XML tests lacked the original `models.assets_root` package constant in the registration
fixture; restoring that constant fixed the fixture. Intermediate77/92/107-case runs are
superseded by109, not added to the total. No skip/xfail or weakened physics assertion.
Canonical unified-patch context whitespace and verbatim upstream license bytes are exempt
from Root plain-text whitespace normalization; actual vendor/source diffs pass separately.

## Exact reproduction / DS handoff

Use a clean independent detached worktree of the exact Root/Child above, an external NEW
evidence directory and a CPU interpreter with the fixed requirements. Do not reset/clean
existing work, install into an active G1 environment or mutate a dirty vendor checkout.
Use local caches for the exact upstream objects, then:

```bash
set -euo pipefail
cd "$EXACT_ROOT_WORKTREE"
git rev-parse HEAD
git ls-tree HEAD cosmos-framework
git -C cosmos-framework rev-parse HEAD
export CUDA_VISIBLE_DEVICES='' MUJOCO_GL=disable PYTHONDONTWRITEBYTECODE=1
export NUMBA_CACHE_DIR="$NEW_EXTERNAL_EVIDENCE/numba"
export HF_HOME="$NEW_EXTERNAL_EVIDENCE/hf" MPLCONFIGDIR="$NEW_EXTERNAL_EVIDENCE/matplotlib"
"$CPU_PYTHON" tools/v3/build_robocasa_vendor.py \
  --robosuite-cache "$ROBOSUITE_LOCAL_CACHE" --robocasa-cache "$ROBOCASA_LOCAL_CACHE" \
  --output "$NEW_VENDOR_OUTPUT" > "$NEW_EXTERNAL_EVIDENCE/build.log" 2>&1
export PSM_VENDOR_BUILD="$NEW_VENDOR_OUTPUT"
"$CPU_PYTHON" -m pytest --noconftest -c /dev/null -p no:cacheprovider -q -s \
  tools/v3/robocasa_vendor_test.py \
  --junitxml="$NEW_EXTERNAL_EVIDENCE/vendor.xml" > "$NEW_EXTERNAL_EVIDENCE/vendor.log" 2>&1
"$CPU_PYTHON" -m ruff check --config cosmos-framework/.ruff.toml \
  scripts/robocasa_vendor.py tools/v3/build_robocasa_vendor.py tools/v3/robocasa_vendor_test.py
"$CPU_PYTHON" -m ruff format --check --config cosmos-framework/.ruff.toml \
  scripts/robocasa_vendor.py tools/v3/build_robocasa_vendor.py tools/v3/robocasa_vendor_test.py
```

Author actual cwd `/workspace/psm_wma`, CPU Python
`/workspace/.venvs/psm-robocasa-vendor-cpu/bin/python`, scratch/log root
`/tmp/psm-v3-vendor-b-20261022`, input caches `robosuite-upstream`/`robocasa-upstream`,
successful build `locked-build-2`. Complete native/package versions are in versions.json.
Build is offline from those caches; initial public source clones were read-only HTTPS.
All subsequent unit inputs are synthetic state/tiny XML/local source, no G1/DS assets.

For the separate baseline probe (must yield exactly4 failures/exit1), set
`PSM_ROOT_WORKTREE` to the exact source worktree and `PSM_ROBOSUITE_CACHE` to a local cache
containing824ac14, then explicitly pytest the archived `vendor_baseline_probe.py`.
It is not an automatic `*_test.py` filename. Baseline failure is not final-green failure.

Request GPT **fresh incremental source/CPU review of this B-only Root/Child/vendor Pair**,
then DS independent focused CPU. Missing dependencies/objects are BLOCKED, never skipped.
Real installed runtime/asset audit and PandaOmron CloseFridge/NavigateKitchen env/controller/
camera/state/seed/target/reset witnesses remain a separate Owner-authorized Gate. The
data-generation0.5.1 commit and equivalence remain unknown; historical5% SR stays diagnostic.
Stop after publication; no deployment, A/G1/C merge, GPU/simulation or training authorization
is inferred from this handoff.
