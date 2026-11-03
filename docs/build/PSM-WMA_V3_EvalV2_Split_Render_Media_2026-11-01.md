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
Normalized effective rendering is bound into the new Run Manifest/digest and
saved in existing invocation records. Different backends or ordered render maps
therefore have different Run identities. Legacy manifests without this optional
field remain readable; new public launches always bind it. Runtime
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

The Owner supplied DS's Python3.13 traceback: QueueFeederThread fails in
`reader_close()` with EBADF, then `queue_sem.release()` raises semaphore
over-release. DS references the frozen iter20000/out2 resume log
`logs/GPU7_S0_simulator.log:18-95` and the original ep006
`tasks/PickPlaceDrawerToCounter/episodes/ep_006/media_diagnostics.json`.
These are accepted DS-reported observations, not server files read by Codex.
No current Run or historical result is opened, migrated or resumed here.

CPython3.13 source places sentinel `reader_close()` inside the normal error
handler, not a finally block. A reader-close exception can reach the handler's
semaphore release even though the sentinel did not acquire a message permit.
The CPU control injects EBADF into that real stdlib path and checks the secondary
ValueError; it does not establish every cause of the server's descriptor failure.
The pre-existing parent reader close before feeder join exposes a close race,
but merely swapping two lines does not handle a feeder blocked on a full pipe.

MediaSink now waits boundedly for the feeder before closing descriptors on the
normal path. A parent-only serialized close callback is installed after spawn,
before the first put; both the parent and feeder share it. If the consumer died
with a full pipe, this same callback closes the reader and the parent again waits
boundedly for the feeder. EBADF is retained as an optional media diagnostic and
cannot escape the sentinel callback into semaphore error handling. Unknown close
errors, a live encoder, or a feeder that cannot stop remain cleanup failures.
There is no global stdlib patch and no independent encoder process group.

`forced_encoder_cleanup` remains diagnostic history. The separate
`process_cleanup_failed`, `encoder_alive` and `feeder_alive` fields express actual
cleanup status. A successful forced reap no longer turns a scientifically valid
Core result into a process fault. EBADF alone never proves that a child exited.
Local end/reset and environment-authoritative SR keep their existing semantics.

After Core commit, the coordinator allows bounded normal late exit/zombie reap,
then targeted TERM/KILL for verified descendants of the registered Actor. Signal
delivery pins the PID with pidfd and rechecks session/start identity. Actor,
unrelated processes and a verified resource tracker are protected; ambiguous
ownership, an unavailable safe signalling API or actual survivors still block.
Cleanup actions are retained in existing runtime proof records. A reported live
feeder or server media fault still blocks even if the OS group has become empty.

## Evidence and stopping point

The earlier renderer development check has 118 passed, zero failure/error/skip, with
scoped Ruff and AST checks. Driver/NVML/sysfs/Env/model boundaries are CPU doubles;
no true EGL, GPU, FFmpeg or simulation was executed. This ran on hashed development
source, not a formal clean-pair Gate. Initial Media development tests have 29
passed on Python3.13.5, using fake CPU encoder targets and real Queue lifecycle.
Combined development regression has 192 passed, zero failure/error/skip, with
Ruff0.12.7 check/format and syntax PASS. The CPU process-group test uses an actual
owned orphan, actual TERM/KILL and reap, and a separate surviving foreign process.
Final combined results are recorded separately against a clean Root/Child Pair;
only that exact Pair is submitted for a fresh GPT Code Gate. Do not auto-merge V3
or update any active shared worktree, Run, YAML, media/results, DCP/log or process.

Only after separate Owner authorization: M1/B1 real hardware Canary, then M8/B2,
then B4/B8. Record real device identity, CUDA conflict checks, memory peaks and
throughput; do not interrupt NoTTT training or recover the old out2 namespace.
