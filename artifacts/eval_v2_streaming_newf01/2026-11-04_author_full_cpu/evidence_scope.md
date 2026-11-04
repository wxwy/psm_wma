# Interpretation of the original CPU evidence

The exact-pair author CPU Gate passed869 unique cases; DS independently executing
the same Pair is still pending. Raw Gate/JUnit/log files remain unmodified.

The two M32/B8 and M32/B16 pipeline cases each completed900 unique Core and900
Session across64 Slot state machines, with at most64 simultaneous occupied Slots.
Physics, model and large process boundaries are CPU doubles. Small OS cases use
real subprocesses/HTTP/Worker/Registry and verify owned cleanup/outsider isolation.
Their observed maximum native B was3 and2 respectively, not saturated B8/B16.
This evidence supplies no H100/GPU speed or actual64OS-Sim throughput claim.

The dual-mode tests call `torch.distributed.checkpoint.save` with tiny CPU modules
and temporary generated state: Child `inference/robocasa_dual_mode_test.py`
lines268,300,353. This is actual CPU DCP API testing, with no real training DCP,
model weights or datasets loaded. The original Gate boilerplate field
`gpu_native_model_simulation_dcp_training=NOT_RUN` must not be interpreted as
"no DCP API was invoked at all". Its raw value is preserved; this scope statement
and the actual source/test calls provide the precise interpretation.

Budget/server-death fixtures intentionally record runtime faults. Expected
SIGTERM/BrokenPipe cleanup diagnostics remain present. Zero JUnit failures/errors
means those safety assertions passed, not that all negative fixtures had graceful
zero-fault episodes. NEW-F01 cases have0 Core and unresolved failure evidence,
with all owned processes reclaimed and unrelated processes protected.

Only locally generated CPU evidence is archived. No remote Desktop/server files,
real model/checkpoint/dataset, runningR04 orG2 workspace was accessed or changed.
No V3 promotion, DS execution, GPU/real evaluation or training run occurred.
