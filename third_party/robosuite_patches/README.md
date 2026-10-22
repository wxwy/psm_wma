# RoboCasa 1.0.1 evaluation vendor

This is a reproducible patchset, not an upstream release or a patch for an existing
editable installation. `vendor.lock.json` is the version authority. The deterministic
patched robosuite commit is **`1ac174585293ed998ffc9cf73e47439798cf6f6c`**, parent
**`824ac14cefcfb7ec125fe5eb2e0bad7364466154`** (official v1.5.2). It is reconstructed
locally from this patch and fixed commit metadata; do not try to fetch that new SHA
from the official ARISE repository. `UPSTREAM_LICENSE` retains the upstream license.

RoboCasa is pinned at **`6f90063c0ec2b9916bbd977368b54c98d9c2d908`**, version1.0.1;
MuJoCo package/native library3.3.1 and NumPy2.2.5. No latest/master install is used.
The fixed reference `5ce6643f3092639d08f7b0f90ed1c6a84f50552c` is a **source reference
for selected backports**, not the installed runtime dependency.

## Changes from v1.5.2

Eight source files implement four contracts:

- Real `LegacyMobileBaseJointVelocityController`, factory dispatch and package export.
  The class is an exact AST backport of the fixed official reference. X-forward uses
  its +heading planar transform; historical Y-forward swaps the planar inputs and uses
  -heading. Yaw sign is preserved. The ordinary controller alias gives a different
  planar direction at nonzero heading and is not used.
- `ManipulationEnv → RobotEnv → MujocoEnv` passes `load_model_on_init` all the way down.
  Base constructor/reset are exact official-reference backports. False defers model,
  Sim, renderer and initial observable setup to first reset, including the first
  model/scene RNG draw. Default True retains eager initialization.
- `_destroy_sim` safely handles a missing Sim attribute and repeated destruction.
- `Task → MujocoWorldBase` forwards both physical options. The world changes the
  existing `<option><flag multiccd=...>` and actual compiled native enable bit.
  **MuJoCo3.3.1 does not support sleeping islands or the MJCF `sleep` attribute.**
  The target `enable_sleeping_islands=False` represents the actual unavailable/disabled
  capability; True raises instead of being silently ignored or triggering a version
  upgrade. The unrelated `mjENBL_ISLAND` bit is not a sleeping-islands control.

`source_provenance.json` gives the official reference blobs and exact class/method AST
hashes. DS's2096-byte stopgap diff was reported with a hash but its original bytes were
not available here. This is an independent full repair, not a claim to have verified or
approved those four temporary hunks.

## Offline construction

Use existing local Git caches that contain the exact base commits and all their tree
objects. These commands are **preparation templates**, not permission to deploy or run
the real simulator. Choose a NEW output directory; failed output is retained.

```bash
python tools/v3/build_robocasa_vendor.py \
  --robosuite-cache /path/to/local/robosuite-cache \
  --robocasa-cache /path/to/local/robocasa-cache \
  --output /path/to/NEW/vendor-build
```

Only committed Git objects are read from the caches; dirty cache working-tree bytes
are never copied. The script does not alter either cache. Fetch is local-file-only,
lazy network fetching and hooks are disabled, and a shallow destination avoids needing
unrelated historical blobs from a partial cache. The script verifies the patch SHA256,
resulting tree and deterministic commit. It creates clean independent robosuite and
RoboCasa checkouts plus `build.json`. It never installs Python packages, resets/cleans
an existing tree, edits a training path, downloads assets, or creates a Kitchen.

For later authorized deployment, install the built checkouts in a **new independent
simulator environment**, with `runtime-requirements.txt` pins, using the environment's
normal reviewed setup. Do not run pip against an active G1 environment or patch DS's
dirty editable tree. This file does not freeze every optional Python dependency; the
target host must still supply RoboCasa's complete compatible dependencies/assets.

## Runtime identity and assets

`scripts/robocasa_vendor.py` imports through the selected Simulator interpreter only
after checking package metadata, import origin and clean locked source. It validates
actual module versions/files, MuJoCo native version331/3.3.1 and native library hash,
compiles tiny XML to witness multiccd, and reads task horizons from the pinned official
registry **without another1.5× multiplication**. No environment, MjData, step or renderer
is created. Direct CLI invocations force CUDA off/MuJoCo rendering disabled and use
temporary external compiler/import caches; no source or training files are written.

```bash
CUDA_VISIBLE_DEVICES='' MUJOCO_GL=disable /path/to/sim/python -B \
  scripts/robocasa_vendor.py --tasks CloseFridge,NavigateKitchen \
  --asset-manifest /path/to/REVIEWED/asset-inventory.json
```

An inventory is optional only when there are no untracked assets. Its format is:

```json
{"robocasa": {"robocasa/models/assets/fixtures/example.xml": "<actual SHA256>"}}
```

Every untracked/ignored asset must be an explicitly listed regular file below the
package's `models/assets/`, with one of the versioned non-code suffixes and exact
SHA256. Extra/missing/changed inventory entries fail. Unknown scripts, native modules,
backups and symlinks reject even if gitignored. Existing `.pyc` is permitted only when
its magic, source location and compiled code match a tracked source under this Python;
poisoned/sourceless bytecode rejects. Numba caches belong outside the source checkout.
Do not delete or move DS files to force a clean result; build a new checkout instead.
An approved asset inventory binds bytes, **not proof of original dataset physics**.

`collect_runtime(sim_python=..., simulation_env=...)` runs the probe through that exact
interpreter with the intended Simulator environment, including PYTHONPATH. It deliberately
does not use `-I`, which would hide import overrides from the real launch. It validates
the interpreter binary/path, import environment, lock, probe and returned digest and keeps
raw stdout/stderr evidence. Probe failures are fatal; no user-supplied runtime JSON is
accepted as authority.

Batch C must call `build_verified_evaluation_identity` with the same frozen Simulator
environment used for Popen and repeat `probe_runtime` in the Simulator before env creation,
comparing the runtime digest. The returned bundle has a stable `manifest` and separate
`runtime_probe_evidence`; persist the latter as evidence, not as resume equality data.
The existing legacy Queue is deliberately **not** rewired in this isolated Batch B.

The new manifest separates `evaluation_runtime` from each dataset's recorded version
fields/JSON pointers/hash. Generation Git commit and capture-time commit remain UNKNOWN;
the dataset's0.5.1 string is never filled with evaluator1.0.1 or inferred as a tag SHA.
Runtime source verification does **not** close the physical compatibility Gate.

## CPU and deferred target-host acceptance

Build the exact checkouts first. Use a CPU Python with NumPy2.2.5, MuJoCo3.3.1, SciPy,
Numba, Pillow, requests, termcolor, pytest and Ruff0.12.7. Author exact versions/logs are
in the Batch B evidence directory. Tests never install into or modify the source trees.

```bash
CUDA_VISIBLE_DEVICES='' MUJOCO_GL=disable PYTHONDONTWRITEBYTECODE=1 \
NUMBA_CACHE_DIR=/path/to/NEW/external-numba-cache \
PSM_VENDOR_BUILD=/path/to/NEW/vendor-build \
python -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
  tools/v3/robocasa_vendor_test.py --junitxml=/path/to/NEW/evidence/vendor.xml
```

Controller/XML code and the native compiler are real. Lifecycle tests execute original
constructor/reset bodies through all three layers with counting simulation boundaries.
Runtime positive unit tests use explicit registration/import/metadata doubles around real
source Git checks, original registry data and actual MuJoCo. They do not claim a successful
complete RoboCasa import or real PandaOmron rollout on this cloud host.

Still required after independent code/CPU review and separate Owner execution authorization:
actual installed import/asset audit; real PandaOmron CloseFridge and NavigateKitchen
create/reset/step, forward/lateral/yaw against body axes and raw15/state15/camera ABI;
observed compiled Kitchen options, official target10 kitchens/object split, horizon/seed
and reset-scene evidence. Real0.5.1 generation physics remains unproven. Historical5% SR
is diagnostic only. A/B/C integration requires a new formal Root/Child/vendor Pair.
