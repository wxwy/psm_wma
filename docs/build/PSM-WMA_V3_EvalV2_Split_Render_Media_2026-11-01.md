# Configurable Server / Render GPU separation and media lifecycle candidate

Owner scope: independent candidate only. Base Root
`7e2be5ca40891915a1e86eea935ed054ec1984dd`, Child
`8664267704da3206e719f3c7eef2b5ed86e2a417`. No canonical promotion, real GPU,
simulator, model, FFmpeg or evaluation / out2 Resume is authorized.

## Renderer mapping

The target example is `configs/eval/robocasa_eval_v2_split_render.example.yaml`:
Server GPUs [4,5], Render GPUs [6,7], M=8 and B=2. Each ordered render entry serves
the corresponding Server's slots. Counts, devices, M/B/wait and budgets are
configurable. Duplicate render IDs are permitted for intentional sharing; their
memory reservations accumulate. OSMesa uses `render_backend: osmesa` and
`render_gpu_ids: null` (or []). Omitted backend inherits MUJOCO_GL (default egl);
omitted EGL device mapping uses the Server's physical devices.

The existing Server/Slot scheduler, model, Local Session and Batch paths stay
unchanged. The CPU dry-run displays both inference and rendering slot maps.
Normalized effective rendering is saved in existing invocation records. Runtime
rejects changed roles/backend against the initial Fresh record before process
setup. Old Runs cannot silently adopt explicit new rendering policies; source
identity and existing scientific/Resume guards are not weakened.

Only Server processes get the inference CUDA device. Sim processes have no CUDA
visibility and receive the chosen GL backend before vendor imports. The worker
matches nvidia-smi's physical PCI identity to the EGL device's DRM/sysfs PCI
identity, then sets the actual EGL enumeration index. Missing or ambiguous physical
proof is blocked; numeric CUDA/EGL ordinal equality is never a fallback. The
pinned robosuite EGL context honors this environment variable. After each valid
Reset, verify the actual current EGL display/device before any policy action.
Device and Context proofs are retained using existing runtime evidence records.

This path requires EGL device-query extensions plus accessible DRM/sysfs PCI
identity. Their availability, correct H100 Context and rendering speed remain a
target-host Canary requirement. Enumeration itself initializes no GPU Context.
The target config allocates no work to GPU0–3; device IDs remain configurable.

Resource checks cover the union of inference and render GPUs. The configurable
Server and per-Sim reservations are admission estimates, not measured peaks.
Actual memory fraction/RSS checks remain. A foreign CUDA process on a selected EGL
render device blocks admission; no foreign process is stopped or reconfigured.
Native B1/B2/B4/B8 acceptance is not a claim that all fit a 10 GiB model budget.

## Media lifecycle

Inspect EBADF, bounded encoder/feeder reclamation and diagnostic versus actual
residual flags. Retain fail-closed for surviving owned processes/threads and keep
media independent of Core/SR and Local cleanup. Owner traceback is pending;
production media changes are deferred until it is available.

## Evidence and stopping point

The renderer development check has 118 passed, zero failure/error/skip, with
scoped Ruff and AST checks. Driver/NVML/sysfs/Env/model boundaries are CPU doubles;
no true EGL, GPU, FFmpeg or simulation was executed. This ran on hashed development
source, not a formal clean-pair Gate. A final exact Root/Child and focused author
Gate will follow the media fix, then a fresh GPT Code Gate. Do not auto-merge V3
or update any active shared worktree, Run, YAML, media/results, DCP/log or process.

Only after separate Owner authorization: M1/B1 real hardware Canary, then M8/B2,
then B4/B8. Record real device identity, CUDA conflict checks, memory peaks and
throughput; do not interrupt NoTTT training or recover the old out2 namespace.
