# R04 Action encoding — narrow compile boundary repair

Owner report: iter27700 R04 stopped with648/900 valid results after the Action
Server hit Dynamo's default recompile_limit8 in `_encode_action`; one recorded
guard was `len(packed_seq.action.domain_id) == 1`. Other guards were not captured.
These runtime facts are Owner-provided; no remote files/processes are accessed.

Independent baseline: Root9635cefe3208ab6320ba5fa70b0e0d68fd444790 /
Child1069fe78841228cadbbfbe6afbd767eaed6225da. Issue17 code is not included.

The existing VFM head policy already uses `fullgraph=True,dynamic=True` except
intentional static whole-forward CUDA-graph capture. Dynamic tensor dimensions
do not make Python list length polymorphic: packing and noisy-frame loops still
specialize whole `_encode_action` on each list/metadata structure.

Keep `_encode_action` as orchestration, running list packing, noised-frame index
assembly and scatter in the ordinary execution layer. Extract only the existing
cast → domain action projection → optional modality addition into
`_project_action_tokens(packed_tokens, per_token_domain_id, target_dtype)`. Apply
the unchanged head compile policy to that Tensor-only method instead. This keeps
the Action projection compiled without presenting lists/PackedSequence metadata
to Dynamo. Other encode/decode heads and all tensor equations/order stay intact.
No parameter, checkpoint schema, algorithm, Session, Batch or Resume changes.
No compile limit increase, global eager fallback or exception-to-success path.

Regression plan: real CPU `torch.compile` with default limit8, controlled B1–8
plus clean/noisy metadata variants (not claimed as the complete original R04
guard history), long alternating sequences; count graphs and compare output and
gradients with eager execution. Verify dtype/domain isolation, no-action and
checkpoint keys, preserve existing CUDA-graph-scope options. Controlled oldRED /
newGREEN uses identical test bytes and actual production function bodies.
CPUInductor is checked separately where the CPU environment supports it;
hardware numerics/latency remains a separate GPU review/execution stage.

This closes only the reported Action-head boundary risk; other compiled heads
still need end-to-end hardware observation. Keeping timestep/index orchestration
eager may affect latency, so no H100 performance claim is made from CPU evidence.
Preserve source/Manifest guards and all648 results; this patch does not authorize
replacing frozen R04 sources or resuming it. Publish isolated Child then Root
exactSHA plus focused evidence for GPT Code Gate. No full EvalV2 Gate rerun,
DS dispatch, real checkpoint/model/data access, GPU, G2 or canonical merge.
