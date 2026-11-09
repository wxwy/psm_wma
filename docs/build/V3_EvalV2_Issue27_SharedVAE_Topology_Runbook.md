# Issue27: configuration driven shared VAE topology

Status: candidate implementation; independent Code Gate required. No GPU run,
RoboCasa run, throughput/SR acceptance or official V3 merge is authorized here.

## Existing entry points and configuration

Use the existing `scripts/robocasa_eval_v2` CLI, Runtime, Registry, resource
reservation and Native Batch transaction executor. There is no second scheduler
or runtime. Keep the complete existing checkpoint, source, asset, VAE file/hash,
physical device, EGL and resource configuration.

For general shared-history operation set:

```yaml
execution_profile: phase_b
local_memory_mode: required
local_evidence_profile: sim_shared_vae
single_latency_arm: null
max_infer_batch_size: 8
batch_wait_ms: 0
# Existing sim_shared_vae fields, frozen file hashes and resource budgets required.
# sim_shared_vae.bmax: 1
# sim_shared_vae.wait_ms: 0
```

`single_latency_arm` remains an optional A/B/C single-instance measurement label.
Explicit measurement arms retain their original one Server/one Sim/Policy B1
validation and exact execution identity. General shared-history operation uses
the independent `execution.shared_vae` identity. An existing single-arm run cannot
be silently resumed under the new general identity. No-TTT/server_vae keeps its
original execution identity and creates no shared VAE Worker.

Server count comes from the used `gpu_ids`. `sims_per_gpu` and the existing
`physical_slots` plan determine Sim slots. `render_gpu_ids` maps each Policy GPU
to its Sim/render GPU and may map multiple Policy GPUs to the same render GPU.
One Worker is created per used physical render GPU and enrolled separately with
each Policy Server using it. There is no topology whitelist.

The existing round protocol retains its task-count slot cap and M<=8. The
existing `streaming_task_affinity_v2` protocol retains M<=32 and its own frozen
resource reservations and sampling semantics. Use that existing protocol when
more physical slots than Tasks are needed. Shared-history Policy batch accepts
1..8 independently of Worker B1; existing server_vae/No-TTT capacity is unchanged.
Actual active work is also bounded by pending Episodes and resource admission.

Representative acceptance configurations (not allowed-value enumeration):

| Servers | Total Sim slots | M per Server | Policy cap | VAE cap/wait |
| --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 1 | 1/0ms |
| 1 | 8 | 8 | 8 | 1/0ms |
| 2 | 32 | 16 | 8 | 1/0ms |

Correction from the Evidence-only review: `2x16` means two Policy Servers with
sixteen Sims each, thirty-two total. This representative uses the existing
streaming M16 protocol. The previous two/eight (sixteen total) tests remain
additional coverage; their original archived evidence is not relabeled as32.

Other legal shapes and boundaries are covered by parameter/property tests,
including three Servers, Policy caps2..7 and existing streaming M32 capacity.

## Transaction and lifecycle invariants

The same model executor prepares feature candidates and runs Native READY batches.
If a pump precedes already-admitted preparation tasks, it yields that executor;
it never waits on that executor for those tasks. With no admitted peer it executes
the available READY member immediately. Original request deadlines still fence
prepare, sealing, generation, commit, response and ACK. A cap8 configuration is
not an assertion that every runtime batch has eight members.

Native generation still runs once per actual Policy batch. Its existing encoder
iterates current images as independent B1 calls. Ordered boundary capture checks
each member's original RGB, lease, source, request, loaded tokenizer, deadline and
full pre-crop latent. It performs no extra Encode1 and no VAE B8 operation. A bad,
missing or extra observation prevents publication of the entire boundary group;
the existing transaction still owns atomic response/FastState/boundary commit.
Historical evidence remains exactly fifteen signed Worker features plus the
already committed current boundary, with sixteen causal T1 updates.

A Worker binds one run/manifest and a bounded set of Policy epochs derived from
the physical topology. Each slot still pins its original Policy epoch and
monotonic generation. Default standalone Workers retain one allowed Policy
epoch. Root supplies derived live Session/Policy capacities via private FD and
checks the actual READY limits. Existing queue, byte, per-session, clock, signing,
capability and resource bounds remain. End affects only its own Session; restart
requires fresh epochs/keys. Registry and private IPC owned-only cleanup remain.

Full M/B/execution and Worker resource identity remains frozen in Manifest and
Resume. This task does not relax source checking or resume compatibility.

## Author CPU evidence and reproduction

The review handoff identifies full Formal Root/Child SHAs and the immutable raw
evidence directory. Its archived `run_cpu_gate.py` requires both worktrees clean,
HEAD and Gitlink equal to that exact pair, and a new evidence directory. It checks
Ruff, formatting, syntax, native constructor/identity equality, original and new
CPU suites, zero JUnit failures/errors/skips, and before/after source hashes.

```bash
/workspace/.venvs/psm-wma-cpu/bin/python /path/to/archived/run_cpu_gate.py \
  --root /path/to/clean/root \
  --expected-root "$ISSUE27_FORMAL_ROOT" \
  --expected-child "$ISSUE27_FORMAL_CHILD" \
  --evidence-dir /path/to/new/evidence
```

Run from the clean Root. The runner sets CUDA visibility empty, model libraries
offline, pytest plugin autoload off, no Python bytecode, numeric threads1 and
external cache/temp directories. Inputs are synthetic CPU fixtures, with real
Local math, HMAC checks, Store, transaction state, original model method bodies,
Root supervisor, Worker subprocesses, private FDs, Unix IPC and Owner HTTP.
The CPU environment lacks Linux timens proc entries; the existing explicit kernel
identity fixture supplies only those records to exercise the production parser.
This is not a native deployment clock/physical-device attestation.

The two old-source RED tests inject only the final new test files into isolated
baseline worktrees. Old Root/Child production hashes must stay identical; both
old restrictions must fail at their documented guards. Final GREEN verifies
identical test-file hashes. Development/static/fixture failures remain archived
separately and are not counted as final passing runs.

Real GPU multi-session smoke, then performance acceptance, requires fresh GPT
Code Gate and separate authorization. Previous B1 hardware speedups are preserved
as historical evidence, not transferred to new topologies by these CPU tests.
No SR/900EP test is required by this code handoff.
