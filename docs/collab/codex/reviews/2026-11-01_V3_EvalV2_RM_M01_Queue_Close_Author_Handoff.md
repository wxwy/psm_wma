# RM-M01 — unknown Queue shutdown failures, narrow author handoff

Status: **REVIEW**, fresh GPT incremental Code Gate requested. Author CPU PASS
does not close the old REQUEST_CHANGES or constitute independent DS acceptance.

| Object | SHA |
|---|---|
| New Formal Root | `6484dd83efc512e6801470790eb84ac7349c127a` |
| New Formal Child / Gitlink | `9a8cd6183424bfce245fbca393ca25ed59919ea6` |
| Previous Formal Root | `46d3a604e66ca139e2f060fd4caaaa0583a1035f` |
| Previous Child | `d3b2a29b978ff4abef800b9e71fab4422b7a0d23` |
| Preserved GPT review / Inbox head | `f6ada8822f597d0ce4ee7928282fd690ca652ec0` |
| Independent branch, both repos | `v3-eval-v2-render-media-20261101` |

Evidence/Inbox/receipt successors are not new implementation SHAs.

## Minimal production change

Only `cosmos_framework/evaluation/robocasa_v2/media.py` changes in Child:
**2 insertions,1 deletion across two assignments**.

- At `media.py:226`, unknown `OSError/ValueError` from
  `queue.cancel_join_thread()` / `queue.close()` sets `fd_failed=True`.
- At `media.py:245`, later descriptor errors OR into the existing failure state.
  A tolerated descriptor EBADF cannot clear an earlier unknown Queue error.

Root adds one focused test file and updates Gitlink. Existing scripts/configs,
render mapping, EGL helper/Context verification, process ownership, Adapter,
model, Local-TTT, Store/Scheduler, inference deadlines, training, Checkpoint and
Vendor code are unchanged. The frozen design and GPT review are byte-identical.
No timeout, assertion, numerical criterion or default configuration was relaxed.

## Frozen RED and clean-Pair GREEN

New tests were formatted, copied and SHA256-frozen **before the first old-code
run**. The same bytes are committed in the new Formal Root:
`2ff48caeb197c5a4e04a04a686ebcdb28944d3e12c4d0968629726b774c56c5c`.

| Check | Result |
|---|---|
| Old committed Child,14 new cases |10 expected failures,4 controls PASS,0error/skip |
| New clean exact Pair |29 PASS,0failure/error/skip |
| Breakdown |14 new +13 existing Media lifecycle +2 existing Core regressions |
| Python / Ruff |3.13.5 /0.12.7 |
| Ruff check / format / syntax / production diff-check |PASS, scoped |
| Formal watched source bindings |6/6 |
| New raw artifact hashes |48 |
| Original192 evidence |53/53 artifact hashes preserved; not rerun |

The old RED asserts the actual missing authority flag, not a fixture exception:
eight stopped-encoder/feeder cases cover both Queue operations, EIO/ValueError,
and subsequent healthy/tolerated-EBADF descriptor closure; two further failures
prove the real Adapter/diagnostic record also missed the flag. Four controls
separate healthy Queue shutdown, diagnostic-only EBADF and successful forced
reap. GREEN keeps the exact same test/assertion bytes. Idempotent close retains
the failure without repeating operations. Core success/steps, immutable result,
Local Reset ACK and optional-media independence remain valid in the native
loopback HTTP/Env controls.

Final exact command:

```bash
# cwd: /workspace/psm-wma-eval-render-media
/tmp/psm-eval-render-media-20261101/python313/bin/python \
  /tmp/psm-eval-render-media-rm01-20261101/run_cpu.py formal \
  /tmp/psm-eval-render-media-rm01-20261101/final
```

Explicit CPU/offline flags and external HF/Matplotlib/XDG/Ruff caches are in
`final/invocation.json`; full commands, logs, JUnit and syntax records are retained.
Both repositories were clean, Gitlink matched Child and watched source hashes
were unchanged before/after the final run. Development GREEN29 remains separate.

Evidence:
`docs/collab/codex/evidence/2026-11-01_eval_v2_rm_m01_queue_close_author_cpu/`.
Includes the frozen pre-RED test, all raw RED/GREEN results, six Git-blob bindings,
zero-context Root/Child source diffs, protected-tree/history proof and original
192 evidence preservation. No full192 rerun, GPU performance repetition or
reinterpretation of historical acceptance.

## Requested review and boundaries

Please review only RM-M01's two assignments and focused tests on this new Pair.
The original report is preserved at
`docs/collab/chatgpt/reviews/2026-11-01_V3_EvalV2_Split_Render_Media_46d3a604_d3b2a29b_Incremental_Code_Gate_REQUEST_CHANGES.md`.

No actual GPU, EGL/OSMesa simulation, model, Action Server, FFmpeg, training,
formal DCP, active out2/NoTTT/shared worktree, results or server logs were accessed.
The Queue/encoder regressions use CPU fake encoder targets; new fault injection
uses stopped-process/Queue/fd doubles; native reporting uses a fake Env/model
through loopback HTTP. No V3/official Child promotion or old out2 Resume.
After candidate publication/readback, STOP for GPT incremental review. Independent
DS CPU and separately authorized real EGL/FFmpeg hardware tests remain required.
