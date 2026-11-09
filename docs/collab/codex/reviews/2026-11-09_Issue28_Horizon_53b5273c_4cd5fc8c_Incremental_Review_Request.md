# Issue28 Horizon-derived K — incremental Code Gate request

Formal Root `53b5273c7907e2d7a8fb1831ac0e0ec8b9fa973a` / Child-Gitlink `4cd5fc8c43d6793745dbc4cac51c59ee8a020dbe`.
Review only the increment from prior050e45d87fe5faf3a830bcaf4629fd7d16ba47a7 /
59746af006748488a678aa9a55dfc3e200668219. Latest REQUEST_CHANGES review was
fresh-fetched/read and preserved via c622ac19. Same independent Draft RootPR30 /
ChildPR9; their qualified #27 bases and official V3 are unchanged by this work.
Later evidence commits are not new implementation targets.

## Correction

Root/Child public K defaults are None. Unified validate_history_k(K,H) resolves
None to H and accepts exact positive integer divisors only; selected_history_step
uses H//K and chunk-relative j, always j0, without source renumbering. Helpers
cover arbitrary positive H/relative anchors, including H12/K3 and H24 cases.
There is no fixed K enumeration or K sampling calculation16//K in production.

H comes from the existing frozen Native protocol Action Chunk size, not Episode
rollout horizons. Its original16 is named ACTION_CHUNK_SIZE in the authoritative
contract and reused by Manifest/model identity. Root resolves K from it and
compares actual Policy INFO.action_chunk_size to the frozen Manifest. Policy
Owner receives resolved model cfg H; the existing Local consumer receives Owner
H and freezes it per Session. Sparse Worker bootstrap/READY/assignment carry H
with K; Sim compares it to Actor/native settings. Native Worker/Owner/Sim retain
the current model H16 restriction. This adds no public H knob or real H12 model/
simulator capability, architecture, engine, scheduler, training or model change.

K=H uses the original dense wire/fingerprint/canonical Manifest omission of K.
Strict K/H/M/B/source Resume, all actual completion receipts, cached j0, original
T1 transactions and No-TTT/sharedB1/native batching/Session/End remain. Relative
helper anchors can be arbitrary; real Native chunk authority still requires its
original valid H16 boundaries.

## Exact clean-pair author evidence

**566 top-level tests +22subtests PASS =588 JUnit,0failed/error/skipped**;
shell0, gate.status=PASS, source_unchanged=true. Ruff/format/AST22 changed Python
files PASS. Raw `docs/collab/codex/evidence/2026-11-09_issue28_horizon/author01/`; immutable index `docs/collab/codex/evidence/2026-11-09_issue28_horizon/archive_manifest.json`;
exact Root/Child incremental patches and source before/after inventories included.

Covers H1..48/default/divisors/K1/dense/j0/true IDs and boundary rejection,
H12/H24 pure helper/T1 consumer cases, invalid types/non-divisors, omitted/None/
explicit dense canonical config/Manifest identity, Episode horizon distinction,
actual Policy H mismatch before Worker start, Worker/Sim/Session H fences,
current H16 all-K/0→16→32/partialEnd/retry/abort/late/No-TTT/Native transactions,
existing shared FD/OwnerHTTP/UnixIPC/topology/32Session/B8+B8/owned cleanup.
Model/physics/kernel/device/current-boundary boundaries are CPU doubles.

Same unchanged probe/seed28/CPU processes on old Child59746 and new4cd5fc8c:
Feature wire/cached boundary/actual Local FastState/Prefix/synthetic Action hashes
are identical for default H16. This is not real Wan/DCP/diffusion/GPU evidence.

Dev01 raw558PASS+22subtests/8FAIL preserved: one legacy Registry fixture lacked
the protocol Manifest and Policy INFO H required by the new identity check;
explicit fixture H was supplied, no production fallback/bypass. Final clean
author run includes all8. Original631+207/dense evidence and every349 archived
file remain unchanged and are not added to new counts. No old965/900EP rerun.

## Reproduce and review

Use archived dev_gate.py with its exact --formal-root/--formal-child above,
--run NEW-directory-name (external directory, no --format for a Formal run),
same CPU venv and a clean baseline Child59746. As-executed paths/commands/env
are in author01/commands.json/environment.json; probe is archived adjacent.
The script's fixed worktree/evidence/probe paths reflect this execution; change
only those paths to a new isolated checkout when reproducing elsewhere.

Please independently review this exact H-derivation increment and raw evidence;
author PASS does not close the existing MEDIUM or claim APPROVE_CODE. Do not
infer GPU/real model/performance/SR/merge authorization. No server files, active
jobs, training, GPU/realSim/SR/900EP or V3/#27 operations occurred.
