# PSM-WMA V3 — Formal30k Observability / Async Raw Prefetch Implementation Candidate

Date: 2026-10-10
**Verdict: IMPLEMENTED / NOT VERIFIED — RESUME HOLD.**
Source baseline: Root `32e254326a574bff45111415430a8c1170cdea9a`, Child/Gitlink `71e03c8501c94a2ad5fed60955af657d3f945b85`.
Candidate Child `98cb4fd0cc59e71f27543d67fa33cbf4f3703657` on `v3-local-ttt`; corresponding Root `V3` Gitlink is updated by the commit containing this review.
Production sync of the formerly separate but fully accepted Dataset Index/FSDP2 baseline was explicit per user instruction, not a new re-review of unchanged underlying data/model logic.

### Actual changed scope
Child baseline-to-candidate diff limited to:
- `cosmos_framework/model/generator/mot/robocasa_async_segment_prefetch.py` and test (new)
- `cosmos_framework/model/generator/mot/robocasa_exact_window_local.py`
- `cosmos_framework/trainer/local_memory_grouped.py` and test
- `examples/psm_wma_robocasa_formal_monitor.py` and test (new)
- `examples/psm_wma_robocasa_corrected_telemetry.py` and test
- `examples/psm_wma_robocasa_corrected_phase5.py` and test.
No checkpoint serializer, optimizer, scheduler, model or FSDP2 edits.

### Semantics to verify
- `--num-workers 0` exactly preserves synchronous ordered samples, rank-planned frontier and strict DCP contract.
- `--num-workers 2` genuinely does RAW window reads in background but ordered Transform, Local, optimizer and commit stay on main rank thread.
- Failure before commit drains the next-member prefetch and leaves committed Frontier/weight/optimizer intact.
- File log and CPU plotter cannot write or change DCP, do not claim performance evidence.
- `config_digest` remains frozen; implementation source SHA changes and **requires fresh Gate**.

### Evidence status
Github code changes inspected, new targeted regression tests committed. **No local project venv with LeRobot/pyarrow, no 8xH100 access, no actual DCP inspection, no Ruff/pytest result from DS, no performance measurements.** These are all OPEN, not implicitly accepted.
Read Gate A/B/C from `docs/build/PSM-WMA_V3_formal30k_observability_async_raw_prefetch_contract_2026-10-10.md`. DS_PRO executes only CPU/static/real read-only preflight at this stage. **Never resume, fresh-start, or promote diagnostic checkpoint absent separate explicit authorization and latest host evidence.**
