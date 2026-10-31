# Issue #14 — optional per-Task rollout MP4 limit

Owner contract: https://github.com/wxwy/psm_wma/issues/14 .
Base Root `9ba1dd110a4e3e99e717937c2f8d044fa077cdbf`, Child
`6c83596d6a259e89c4cd3e79424024983426ac3d`. Implement only on the independent
`v3-eval-v2-rollout-first-n-20261101` Root and Child branches, then stop for a
fresh GPT incremental Code Gate. No automatic V3 promotion or runtime action.

## Configuration and behavior

```yaml
save_rollout_mp4: true
rollout_mp4_first_n_per_task: 3
save_generated_video: first
```

The optional limit defaults to null. Null preserves the existing boolean:
true records every Episode, false records none. A non-null value must be an
exact integer (not bool), between zero and the resolved episodes_per_task
inclusive (at most 50). False plus any non-null limit is rejected, including zero.
CLI episode-count overrides are applied before checking the bound.

The runtime passes the limit unchanged to every reusable Sim actor. Each
`NativeEpisode.execute` creates its own MediaSink with rollout enabled exactly
when the boolean is true and its logical Episode index is below the limit.
The choice is per Task, independent of completion order, success or retry count.
N=3 includes ep_000, ep_001 and ep_002 even when an Episode is a behavioral failure.
Retry/Resume of the same index preserves the choice. N=0 records none; N=50
records all fifty. Generated media retains its independent none/first/all policy.

The existing CLI already records the full resolved configuration before Runtime
construction. Runtime checks the new limit against the first Fresh invocation,
before process setup. A rejected Resume snapshot cannot become the anchor.
Old snapshots without the field mean null; they cannot adopt a non-null limit.
With a null limit, legacy boolean/generated Resume choices remain unchanged.
Non-null limits require a Fresh record. No new manifest/schema/service is added;
scientific and source identity checks remain strict. This is not permission to
resume an old Run under different Root/Child code.

Per-Episode media diagnostics record the configured limit and actual
`rollout_requested`. Existing invocation/actor configuration and source witnesses
retain the actual Root/Child provenance. No old media or Core Result is altered.

## Scope and CPU verification

Production changes: Root config.py and runtime.py; Child eval_v2_adapter.py.
MediaSink, Scheduler, Store, SR, Local-TTT, model/server and training are unchanged.
No missing or broken optional media changes environment outcomes or Local cleanup.
Limiting saved videos is not a claim of reduced OSMesa rendering cost.

Focused tests exercise strict config boundaries; actual CPU dry-run; new and old
invocation snapshots, rejected Resume recovery; production actor-config creation;
reused NativeEpisode with two Tasks and logical indices 0/1/2/3/49 plus repeated
indices; independent generated policies; and media faults with valid Core commit
and Local reset. Environment/model and encoder are synthetic boundaries. The
native HTTP codec/Local client use a loopback fixture; no real Action Server,
RoboCasa, model, GPU, FFmpeg or MP4 encoding runs. Keep the existing 17 config
regressions and two focused Core/media regressions; do not rerun broad Gates.

Freeze the new Root/Child pair before the author Gate. Retain the full command,
safe CPU/offline/cache overrides, JUnit/logs, scoped Ruff 0.12.7 check/format,
syntax checks, source bindings and minimal Diff. PASS requires no failures,
errors or skips and clean unchanged source before/after. Any failure stops the
Gate and retains its raw evidence. Author PASS is not independent acceptance.

The current Local-TTT out2 900-Episode evaluation and NoTTT training, their shared
worktree, YAML, outputs, MP4s, checkpoint/config identities and GPU processes
must not be accessed or updated. Publish candidates and request review, then stop.
