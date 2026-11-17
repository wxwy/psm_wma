# G2 Issue58 P0: one-shot Stage A production candidate

Date: 2026-11-17 CST. This is a code/runbook candidate, not a production
acceptance or a record of a server run. Implementation SHA is pinned in the
canonical Inbox handoff after commit. Parent reviewed core is Root
`4ad0fe7394cb62c4b5692fecaf6ce52963b8852c`, Child/Gitlink
`d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`, nav G2
`70eb7b447e65d793b0ebe18b258291ce46f057c1`. The candidate starts from the
docs-only A2 approval at `29f9993d2543b8bb638f135aac9dd7172b71baf0`.

Owner Issue58 supersedes the old 48-episode manual rotations. Codex implements
and runs CPU checks, GPT independently checks fixed code on the data server,
Owner alone deletes authorized old views and manually starts full production.
No automatic merge, environment creation/installation, GPU sample, server
access, private-file transfer, full production, state15 or training here.

## Implemented scope and reuse

The original `atomic_6views_run.schedule` still builds/reuses one immutable
plan and consumes its one queue across all 92 packages. The supervisor adds
admission, owned-process control, progress and final drain. It does not create
48-episode subruns. Full mode requires 9,126 episodes, all 18 supported Atomic
tasks, packages <=100, physical GPUs4–7 and eight renderer slots per GPU. One
resident consumer uses GPU7 alongside that renderer allocation; actual resource
viability and throughput require GPT's sample/A-B gate.

Existing B=1/T=1 preprocessing, encoder, recipe, builder, per-View storage,
legacy scanner and both post-hoc build/verify CLIs remain unchanged. All valid
Views and clean/robot variants are encoded, irrespective of selected_view_ids.
Full profile requires PNG, SG, metadata, task entities, selection, language,
pose, marker variants and VAE. No synthetic COMPLETE and no old-schema waiver.

New files: `ledger_archive.py`, `work_lifecycle.py`, `process_control.py`,
`full_production.py`, thin `tools/g2/run_stage_a_production.py`, repository
launcher/config template and three CPU test modules. Existing streaming,
consumer CLI and original producer receive the limited hooks. One existing
test keeps its identity but replaces the obsolete assertion of retained
private SQL rows with the durable receipt and zero active rows.

P1 microbatch is explicitly deferred. Issue23 B4/B8 latent maxabs
0.03125/0.0234375 failed exact parity; B8 visual approval remains valid only as
visual evidence. This P0 accepts no max_batch_size/max_wait_ms setting and
does not change B1 recipe `3ee9c48399143866b2a0061f3cee01bff35842228f639380d60602d6402e2fc1`.
Any later B>1 implementation needs actual batch context identity and a separate
numerical/performance gate. It must not postpone P0.

## Working ledger and publication protocol

New transient spool schema is `g2_final_pixel_spool_v3`. Start a fresh spool;
v1/v2 spools are rejected, never silently migrated or deleted. `max_records`
now bounds active events/jobs rather than lifetime history. Pending PNG BLOBs
and private numerical chunks retain their original finite budgets.

After final profile/source/cache validation and numeric input release:

1. Job remains active, done=2, while renderer lease prevents work cleanup.
2. Verify exact episode/source/profile/recipe, final six identity files and
   cache receipt. Refuse unknown, pending, failed or inconsistent inputs.
3. Safely clean that job's managed work (below).
4. Atomically fsync `completed/<job-prefix>/<job>.json`.
5. In one FULL-synchronous SQLite transaction, insert the compact completed
   index and remove only that job's acknowledged event rows and active job.

A crash before SQL commit leaves the active job and same retryable receipt;
after commit the same job resolves through its tombstone. No unconfirmed ACK
is deleted. The permanent index is O(episodes), not O(cumulative images).
The SQLite file reuses freed pages; this is not a VACUUM of a live database.
Receipts keep the exact scope, final source/cache hashes, event status counts
and work-cleanup evidence. Re-registering same source/recipe is idempotent;
another source/profile/recipe, damaged receipt or changed publication identity
rejects. Late events must exactly match declared final owner descriptors.

Stats include active_jobs/records, completed_jobs, cleanup_pending_jobs,
pending count/bytes, statuses, unfinished and failed jobs. Previously completed
SQL event rows are intentionally absent; use completed_receipt(job) for audit.
Reader payloads remain the final episode/view files, independent of this GC.

## Managed native/F27 work cleanup

Only a fresh explicitly managed work root can be claimed. Its guard binds the
spool/output roots; symlink traversal, overlap with inputs/code/output/spool
or a nonempty unowned root rejects. Each episode's exact existing work layout
gets a source-row/episode/profile/job lease and an external renderer flock.
The producer holds it until it returns, including the final publication gap.

Cleanup requires complete source/cache/profile proof, matching lease and an
exclusive work lock plus target lock. Busy work stays active for later retry.
Intent is durable before atomic rename into `.g2-trash/<job>`; only that owned
tree is removed, then cleanup receipt is written. Interrupted rmtree resumes
using the original intent even if the lease file was already removed. Missing
work without intent, modified lease, recreated paths or ambiguous live/trash
paths reject. Late producers cannot recreate completed work. Failed/unsealed
work, unrelated directories, private evidence and original assets are retained.
Normal supervised production has keep_work=false; legacy explicit keep-work
remains separate. Empty parent/lock directories and receipts are retained.

## Runtime contract and configuration

Template: `tools/g2/production/stage_a_9126.template.json`. Its Root and mapping
checksum placeholders deliberately fail validation. GPT must fill the **exact
reviewed Issue58 implementation SHA**, actual immutable mapping SHA256 and
verified local paths in a separate absolute config file, then freeze it.
Do not use the following docs-only HEAD as an implementation pin.

Reuse the existing PSM interpreter, currently documented as:
`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python`.
Noetic setup/native executables must already exist in the pinned nav checkout;
the launcher never builds or installs. Preflight checks clean exact Root/Child/
nav HEADs and Root Gitlink, interpreter, mapping hash, disjoint namespaces,
native existence/hashes, free disk and current selected GPU ownership. The
binary hashes are provenance records, not proof of a fresh native build; GPT
must independently establish binary/source identity. It never stops unowned
processes to acquire resources.

Controller/consumer PYTHONPATH contains selected Root/Child only, user site is
disabled. Only the F27 renderer subprocess gets optional existing
renderer_pythonpath dependency overlay(s). An overlay containing g2 or
cosmos_framework is rejected. The VAE descriptor preflight requires original
NumPy2.2.5 and exact approved recipe before any model load. The old renderer
overlay's NumPy2.5.4 must not contaminate the consumer. No GPU model is loaded
by preflight; full raw/depth/episode identities are checked by the original
planner when run starts.

Defaults: max_active_jobs32, pending PNGs32/256MiB, numerical chunks4GiB,
active SQL records100k; free-work reserve64GiB/free-spool reserve8GiB, bounded
admission600s and final drain1800s, producer attempts2. These are explicit
candidate limits, not measured peak promises. New jobs wait behind active
jobs/reservations and free-space gates; existing interrupted jobs may finish
and release work. Timeout/failure preserves work and reports nonzero. GPT's
resource sample must validate/tune before production; config cannot change
during a resume. Configuration changes require a new isolated run namespace.

Namespaces in the template are **proposed**, not created/inspected server paths:

- output: data1 `robocasa365-target-atomic-stageA-issue58` (fresh, never old root).
- work/spool/run: `.tmp_backup/g2_stageA_issue58_{work,spool,run}`, disjoint.
- run: immutable run_manifest/profile/plan, progress.json/.jsonl,
  vae_consumer.log, preflight/runtime hashes, resume receipt, result.json.

## Exact manual entry points (NOT RUN here)

After GPT sample/A-B approval, set these to actual frozen paths on the server:

```bash
G2_CODE=/absolute/clean/checkout/of/reviewed/issue58/sha
G2_PYTHON=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
G2_CONFIG=/absolute/frozen/stage_a_9126.json
G2_LAUNCH_LOG=/absolute/owned/logs/stage_a_9126.launch.log
cd "$G2_CODE"
bash scripts/g2/run_stage_a_full.sh "$G2_PYTHON" "$G2_CONFIG" preflight
# One Owner invocation, after the separately recorded approval:
tmux new-session -d -s g2-stage-a-9126 -c "$G2_CODE" \
  env G2_PYTHON="$G2_PYTHON" G2_CONFIG="$G2_CONFIG" G2_LAUNCH_LOG="$G2_LAUNCH_LOG" \
  bash -c 'exec bash scripts/g2/run_stage_a_full.sh "$G2_PYTHON" "$G2_CONFIG" run --manual-start > "$G2_LAUNCH_LOG" 2>&1'
```

The tmux command passes paths as arguments/environment, not interpolated shell
code. Log parent must already exist. The code does not launch production when
imported, planned or shown with --help. No automatic start follows preflight.

```bash
# Read progress; request stop from a second shell with the same exact config:
bash scripts/g2/run_stage_a_full.sh "$G2_PYTHON" "$G2_CONFIG" progress
bash scripts/g2/run_stage_a_full.sh "$G2_PYTHON" "$G2_CONFIG" stop
# Once the first controller exited (its flock prevents a concurrent controller):
bash scripts/g2/run_stage_a_full.sh "$G2_PYTHON" "$G2_CONFIG" resume --manual-start > "$G2_LAUNCH_LOG.resume" 2>&1
```

Stop records a durable request; SIGINT/SIGTERM also request it. Only process
groups carrying this run's exact inherited token and same uid may be stopped,
never caller/unowned/mixed groups. Resume terminates that run's orphaned
children, reuses immutable plan/config, clears only its own stop marker,
retries retained failed jobs explicitly, and continues producing/consuming.
It does not delete failed inputs. A changed source/recipe fails instead of
starting a new unreviewed namespace. Persistent source corruption needs GPT
diagnosis rather than an endless retry loop.

Producer75 means SOURCE_READY_VAE_PENDING, never DONE. Supervisor waits for
active jobs **including cleanup** to reach zero and strictly validates every
selected final episode. Only then result.json says DONE/complete=true/exit0.
Explicit stop returns75, failure2; partial source/cache data remain. Final
training_ready is always false. Progress records completed throughput, active
work/pending/SQL state, spool/native bytes and observed peaks, free space, CPU
times/load average, selected GPU memory/utilization and failures. JSONL/logs
grow for audit, not as a per-event payload queue.

## GPT independent gates before Owner full start

Use a new sample config/namespace, same fixed code/Child/nav/interpreter/recipe.
For the existing two representative episodes set sample_mode=true,
tasks=[CloseBlenderLid,CloseFridge], episodes_per_task=1,
expected_selected_episodes=2, expected_task_count=2,
expected_episode_ids=[0,502]. Smaller renderer allocation, e.g GPU4 x1 plus
VAE5/max_active_jobs1, is permitted only in sample mode; record resources.
Run the same preflight/run/progress/stop/resume commands, not server-local
temporary launch scripts. Recheck exact source/geometry/arrow/member/text
contracts, all valid views, compact owners, immutable final pixels, B1 stream/
posthoc/reencode maxabs0, real process overlap and receipts/cleanup after stop.

Prepare render-only A/B with the existing original producer, identical two
episodes/resources and render flags, new disjoint output/work/plan roots,
`tools/g2/profiles/stage_a_candidate_clean.json` (only view_vae=false), and no
spool/managed-work flags. This original-queue invocation derives the same flags
from the frozen **two-episode sample** config; it is a real GPU command for
GPT's separately authorized A/B only, **NOT RUN here**:

```bash
G2_SAMPLE_CONFIG=/absolute/frozen/two_episode_sample.json
G2_AB_ROOT=/absolute/new/disjoint/render_only_ab
export PYTHONPATH="$G2_CODE:$G2_CODE/cosmos-framework" PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
export COSMOS_TRAINING=0 COSMOS_INTERNAL=0 COSMOS_DEVICE=cuda
/usr/bin/time -v "$G2_PYTHON" - "$G2_SAMPLE_CONFIG" "$G2_AB_ROOT" <<'PY'
import sys
from pathlib import Path
from g2.offline.full_production import load_config, preflight, producer_args, validate_paths, ROOT
from g2.offline.atomic_6views_run import schedule
cfg = load_config(sys.argv[1]); cfg['_config_path'] = str(Path(sys.argv[1]).absolute())
assert cfg['sample_mode'] and cfg['expected_selected_episodes'] == 2
assert set(cfg['tasks']) == {'CloseBlenderLid', 'CloseFridge'}
assert cfg['expected_episode_ids'] == [0, 502]
preflight(cfg)  # fixed imports/recipe/native/resource check; no model load
ab = Path(sys.argv[2]).absolute()
if ab.exists(): raise RuntimeError('A/B root must be new; preserve prior evidence')
cfg.update(output_root=str(ab/'output'), work_root=str(ab/'work'), run_root=str(ab/'run'))
validate_paths(cfg)
args = producer_args(cfg)
args.output_profile = ROOT/'tools/g2/profiles/stage_a_candidate_clean.json'
args.vae_spool = None; args.managed_work_cleanup = False
raise SystemExit(schedule(args))
PY
```

Freeze concrete paths and collect raw process/disk monitoring in parallel.
Compare unchanged PNG bytes/owners/geometry; record total wall time, native
work/spool peaks, GPU/CPU, consumer rate, errors and resume. This comparison is
NOT_RUN here; no invented speedup or disk-peak acceptance. Then evaluate the
intended32-renderer resource layout before approving 9,126 production.

## Owner-only old-view cleanup

Issue58 permits deletion of the **old view images**, not flat/Depth/G1/VAE
caches/checkpoints or whole dataset roots. No launcher/preflight/stop/resume
performs this deletion. GPT/Owner should first list/hash the exact old PNG
files under state sixview/islands directories (excluding every vae_cache and
cache/checkpoint tree), save that private list on the server and review it.
After Owner explicitly confirms that exact list, Owner can execute:

```bash
# OLD_VIEW_LIST_NUL is an independently reviewed exact NUL-delimited PNG list.
# Manual Owner command only; never run by Codex or automatically by production.
xargs -0 -r rm -- < "$OLD_VIEW_LIST_NUL"
```

Do not rm -rf the old dataset/root. Retain the review/list/deletion receipt.
This document does not claim a list was prepared or a deletion occurred.

## CPU evidence and limitations

Replay with an existing CPU interpreter (no installation):

```bash
cd /absolute/issue58/checkout
ISSUE58_PYTHON=/absolute/existing/python ISSUE58_OUT=/absolute/fresh/evidence \
  bash docs/collab/codex/evidence/2026-11-17_issue58/commands.sh
```

Own gate/JUnit/logs/fingerprints preserve all478 prior case IDs and unchanged
A1 three-probe file. PyArrow/MuJoCo/Pandas-dependent cases are reported as
local skips, not pass; GPT previously passed them on the server. The SQLite
stress explicitly simulates101,101 acknowledged small rows over1,001 jobs,
with128 active cap and peak101; it tests GC residency, not VAE throughput.
Actual tiny synthetic source/cache validators are also used by the A2 and new
consumer stop/resume/cleanup integration tests. Crash points include receipt/
SQL before/after commit, source before seal, numerical before/after ACK and
partial rmtree; competing GC/writers, concurrent reads, low-disk admission,
owned-process stop and late-producer refusal have checks.

Author CPU evidence is not GPT independent approval. Real F27/Wan sample,
resource A/B, full9,126, P1 batch research, old-view deletion, state15/joint
alignment, training and merge remain explicitly NOT_RUN here. Fixed source
and Draft PR handoff request precede any independent server execution.
