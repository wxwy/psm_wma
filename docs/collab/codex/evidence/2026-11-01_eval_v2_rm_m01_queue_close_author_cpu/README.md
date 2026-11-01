# RM-M01 focused author CPU evidence

Formal Root `6484dd83efc512e6801470790eb84ac7349c127a` / Child-Gitlink `9a8cd6183424bfce245fbca393ca25ed59919ea6`.
Old reviewed implementation `46d3a604e66ca139e2f060fd4caaaa0583a1035f` / `d3b2a29b978ff4abef800b9e71fab4422b7a0d23`.
Only Child media.py changes in production:2 insertions/1 deletion across two
assignments. Root adds the fault tests and updates Gitlink; renderer, ownership,
Adapter, model, Local-TTT, Store/Scheduler, training, DCP and Vendor are unchanged.

`old_red/`:14 cases,10 expected failure assertions+4 controls pass,0error/skip,
old committed Child clean. New test bytes/hash frozen before the first RED and
unchanged in final. `development_green/` is development evidence; `final/` is
the clean exact-Pair author Gate:29 passed/0failure/error/skip.14new+13existing
Media lifecycle+2Core regressions; Python3.13.5, Ruff0.12.7 check/format and
six-file syntax PASS. Do not add development counts to29 or claim full192 rerun.

Faults cover cancel_join_thread and queue.close EIO/ValueError, later tolerated
writer EBADF that must not clear an existing failure, healthy controls,
idempotence, and real Adapter/diagnostics forwarding with Core/Local Reset ACK
preservation. Existing tests exercise CPU-only fake encoders/real Queue lifecycle;
new native tests use fake Env/model via loopback HTTP. No actual FFmpeg/model/
simulator/EGL/GPU or DCP/active Run access. No independent DS execution.

Exact commands/cwd/environment: each run's invocation.json and commands.json.
CPU caches are external under /tmp/psm-eval-render-media-rm01-20261101/.
Raw stdout, JUnit, frozen RED test, source bindings and zero-context source diffs
are retained. Original192/53 artifacts remain byte-identical at their old Pair.
This evidence requests fresh GPT incremental review, not approval or V3 merge.
