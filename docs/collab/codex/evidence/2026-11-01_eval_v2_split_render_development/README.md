# Split render mapping — development evidence only

Stage code commits: Root91896fac2140f6c77dfb440c32253626051eb8f2 /
Childf1439ac3a83bf3f7c32d3be204f2723f90231996. This is not a Formal Code Gate.
The complete task also includes Media/EBADF repair, awaiting Owner traceback.
No media production files have changed and no review verdict is requested yet.

render_development_1 stopped at import sorting before pytest. Logs retained.
render_development_2:118 passed,0fail/error/skip; scoped Ruff and AST checks PASS.
The execution used development (dirty) source, hashed after formatting; all10
watched code files match the later stage Git objects byte-for-byte as recorded
in committed_source_equivalence.json. Full committed diffs are supplied because
the earlier development git diff did not include untracked new files.

CPU-only: real config/runtime/worker/slot and parser paths with driver/NVML/sysfs,
environment/model/encoder boundaries replaced. No true EGL, GPU, simulator,
FFmpeg, actual model/DCP or active Run was accessed or started. Includes69 existing
relevant tests,46 new render tests and3 Worker-source tests. The Worker fixture
adds an explicit CPU backend and its new required source witness; no assertions
were relaxed. Do not call this independent acceptance or measured GPU capacity.

Final exact combined Root/Child and author Gate follow the pending Media fix.
No canonical V3/official Child promotion, live directory update or runtime.
