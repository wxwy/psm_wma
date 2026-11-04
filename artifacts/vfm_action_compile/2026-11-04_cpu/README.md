# Independent R04 Action compile narrow CPU evidence

Formal Root **c9fa60b7134fda8fb848c29c148f25c7a8901892** /
Child **4e9c8104ffd15a373b576bc35ee608de1b60eea1**.
BaselineV39635cefe /Child1069fe78; Issue17 source is not included.

[Full Code Gate handoff](../../../docs/collab/codex/reviews/2026-11-04_R04_VFM_Action_Compile_c9fa60b7_4e9c8104_Code_Gate_Request.md).

- [Summary](final_summary.json), [exact-pair JUnit](formal-targeted/junit.xml),
  [original log](formal-targeted/pytest.log), [CPU command](formal-targeted/command.json):
  **51/51 PASS**,19 new+32 existing,0fail/error/skip,8GPU/L1 explicitly deselected,
  exit0/source unchanged1227entries/clean execution Pair.
- [Old RED](old-red/junit.xml):4 actual FailOnRecompileLimitHit after8graphs;
  [new long witnesses](formal-targeted/long_witnesses.json):4×1024requests/1graph,
  cap8 unchanged; [real CPU Inductor](formal-targeted/inductor_witnesses.json):2graphs/dtype.
- [Old/new exact numeric comparison](formal-eager/summary.json):12 cases of
  output/input and parameter gradients/statekeys bit-equal to old eager reference.
- [Static proof](formal-static/static.json), [four-file Child delta](formal-static/child_delta.patch),
  [read-only peer audit](peer_review.md).
- [Raw archive](cpu_evidence.tar.gz), [SHA256SUMS](SHA256SUMS):709061bytes/81entries,
  SHA256`ca0b7bfe2f974ad4db03fe19af28f8969b4f84d2b4c1f1f33227bdbee574f45c`.

Only local synthetic CPU evidence. Archive includes original traces/counter data,
source fingerprints, old source, tiny generated numeric-reference tensors and
transparent external scripts; caches/bytecode/current symlinks omitted. No remote
server files or real weights/data were accessed/copied. First postprocessor's
empty-JUnit-classname assumption and its file-attribute correction are preserved;
project test assertions/source/raw results were not changed for that correction.

GPU grouped_mm, CUDA capture/replay/FSDP/CUDA backward, full Local-TTT trajectories
and real-model latency are unvalidated. CPU local=True covers only Action head.
GPT Code Gate pending; no V3/G2/Issue17 merge or R04 Resume. Existing648 Core were
not accessed/rewritten, and no final900EP SR is claimed. Later ledger/evidence
commits are not new implementation targets.
