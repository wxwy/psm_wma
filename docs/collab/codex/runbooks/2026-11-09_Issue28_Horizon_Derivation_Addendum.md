# Issue28 — Owner Horizon correction addendum

Supersedes the prior fixed-K/default16 requirements only. Authority: Owner's
2026-11-09 correction, latest Issue28 body and exact050e45d8/59746af0 review
`2026-11-09_Issue28_050e45d8_59746af0_HistoryK_HorizonDerivation_REQUEST_CHANGES.md`.
Previous631 tests/207subtests and CPU dense parity remain valid historical
evidence, not acceptance of this new increment.

`local_ttt_history_k` defaults to None/omitted. Resolve it to H, the actual
Action Chunk length. Explicit K must be an exact positive integer dividing H;
reject bool/float/zero/negative/non-divisors. Select original source T+j when
`j % (H//K)==0`, always including j0. K=H is dense, K=1 selects only j0. Helpers
accept positive H, including H12/K3 and H24; no fixed K enumeration exists.

H is not the Task Episode rollout horizon. The existing frozen Native protocol
Action Chunk size is now named ACTION_CHUNK_SIZE in its authoritative contract
and used by the existing Manifest/model identity. It remains16. Root configuration
resolves default K from that protocol; runtime compares actual Policy INFO H to
its frozen Manifest. Policy Owner receives resolved model cfg.action_chunk_size;
the existing consumer receives Owner H. Sparse Worker bootstrap/READY/assignment
carry H with K, and Sim binds it to the original Actor/native settings. Native
Worker/Owner/Sim still reject a horizon outside the existing model protocol.
This introduces no public Horizon knob and no H12 model/simulator support.

Default dense H16 retains prior Feature/receipt wire, request fingerprint and
canonical Manifest omission of K. Sparse selection/completion/skip authority,
T1 prepare/commit/abort, original source IDs, cached j0, Session isolation and
full M/B/source Resume restrictions remain. Model/training/Native scheduler and
actual H16 action flow are unchanged; no new engine/runtime.

CPU acceptance: positive H/divisor/relative-source properties, H12/H24 examples,
invalid K/H types and non-divisors, config None/omitted/dense identity, Episode
horizon distinction, Model/Worker/Sim/Session H mismatch rejection, current H16
all-K and relevant No-TTT/transaction/topology/End regression. Compare separate
old59746af0/new CPU processes with the same dense probe and fixed seed, requiring
Feature/FastState/Prefix/syntheticAction hashes equal. Hardware/model numerical
equivalence, performance/SR and any merge need separate authorization.

Continue existing RootPR30/ChildPR9. Freeze a new exact pair, preserve raw JUnit,
logs, command/environment and source fingerprints outside the source worktrees,
then archive immutable evidence and request fresh GPT incremental review. Do
not relabel previous counts or rerun old965/900EP. No GPU/real Sim/training/V3.
