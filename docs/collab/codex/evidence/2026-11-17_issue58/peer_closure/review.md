# Issue58 local narrow peer closure

Reviewed exact Root `a3e0048b40e1392d0ff92d4fce8da4dc278447f6`, unchanged
Child/Gitlink `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`.
Verdict: **LOCAL_NARROW_REVIEW_PASS**. Original one P1 is closed; no new
P1/P2 found in the scoped correction. This is not GPT server acceptance or
permission to start full production. No code/test/ledger/ref edits by peer.

Compared product delta from rejected local3b13e6a5: only full_production.py
and the two existing new test modules. prepare_plan now returns fresh run-mode
args, preserving explicit manual-start/experimental guards. Original plan
build/queue, archive and B1 encoding core are not bypassed. The revised CPU
child-consumer integration keeps real prepare_plan/build/original schedule;
only source discovery/native compute/resource preflight/VAE compute are fake.
The test mapping fixture now resides under its protected flat root, obeying
the existing planner policy. Small same-P0 additions enforce an output free
space reserve and test an open ViewReader across verified work/archive GC.

## Unchanged original probe and focused execution

Original final probe copied byte-for-byte from peer/ into peer_closure/ so its
__file__-relative observation does not overwrite original RED evidence.
SHA256 before replay:
`0fcb570fc6b34a2d7ea6a1e019c4be2f99adb91498b6f2ce2966d466b974f788`.

Working directory `/workspace/psm_wma_issue52`; existing CPU interpreter only,
no checkpoint, real/native source, network, install, server or GPU:

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 COSMOS_DEVICE=cpu \
PYTHONPATH="$PWD/cosmos-framework:$PWD" \
/workspace/.venvs/g2-view-vae-52/bin/python -m pytest -q -p no:cacheprovider \
docs/collab/codex/evidence/2026-11-17_issue58/peer_closure/test_review_dispatch.py \
g2/tests/test_one_shot_supervisor.py::test_one_run_stop_resume_real_consumer_ack_cleanup_and_final_audit \
g2/tests/test_one_shot_supervisor.py::test_low_disk_and_active_job_admission_backpressure_preserve_work \
g2/tests/test_one_shot_work.py::test_completed_work_waits_for_renderer_lease_then_reclaims \
--junitxml=docs/collab/codex/evidence/2026-11-17_issue58/peer_closure/closure.xml \
> docs/collab/codex/evidence/2026-11-17_issue58/peer_closure/closure.log 2>&1
```

Exit0, **4PASS/0fail/error/skip**,14.90s. dispatch_observed.json now records
prepared_action=run,worker_calls=1,selected=1. Original same probe at rejected
3b13 recorded actionplan/0workers and RED; those files remain unchanged.
Stop/resume performs actual synthetic source/cache verification, managed-work
and ledger cleanup with the original queue and real CPU consumer child;
reader data remains equal across archive; low output space blocks new work
without deleting retained evidence. These focused cases overlap author
totals, so they are not added to487PASS/13 inheritedSKIP.

After run, HEAD remains exacta3e0048b; git diff for g2/tools-g2/scripts-g2 is
empty, and ls-tree confirms unchanged Child/Gitlink. No additional full-suite
run was needed for this narrow closure. Author revision2 raw evidence remains
separate from this peer result. Actual F27/Wan/resource A/B/full32-slot layout,
full9126/old-view deletion/P1microbatch/training/merge remain NOT_RUN by peer.
