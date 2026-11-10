# Issue31 author H100 derived evidence

Formal Root5b89f3ed / Child4446be0f. Only derived statistics/hashes are present.
Raw model inputs/outputs, config/checkpoint, logs and profiler traces remain on
the authorized server. No private server file was copied here.

gpu_command.json is the exact complete benchmark invocation/environment/exit.
public_gpu_statistics.py is the author-created reproducible reducer, run with
/usr/bin/python3 on the server. gpu_statistics.json contains scalar metrics,
identities, tensor/file hashes and counts, not tensors or raw logs. The explicit
Shell0 comes from the completed process receipt, independently of the reducer.

30 balanced AB/BA pairs. P50 991.5513->825.5335ms (1.2011x); all Vision/Action
outputs exactly equal. One 1386.77ms optimized outlier retained, P99 regresses.
Background GPU load remains; synthetic model-only evidence does not establish
Sim throughput, No-TTT checkpoint equivalence, SR, or production tail latency.
This is an author result, not independent approval. Read the detailed handoff.
