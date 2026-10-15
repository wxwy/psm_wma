# DS_PRO — E1 independent CPU acceptance request

Date: 2026-10-15 (Asia/Shanghai). Author: Codex implementation side.
Status: **CANDIDATE_PUBLISHED / DS_GATE_PENDING / GPT_FRESH_REVIEW_PENDING**.
This is a request, not a DS result or GPT verdict. Owner authorized E1 only and instructed stopping here after publication.

## Exact candidate identity

- Root Implementation: `afd615e4b2fc7610aef950b4c2ea80a494abfd5d`.
- Child and Gitlink: `1d56320c08c56b0f8dd248919d152d81ae12ea7b` (UNCHANGED).
- Root source parent: `72aeb3767b6123de0358d5d148d5c2c788179d3c`.
- Branch: `v3-e1-evaluation-reliability-20261015`; later docs-only branch HEAD must not replace the implementation SHA.
- Production V3 remains at its existing authorized source; E1 branch is NOT merged. B1 diagnostic a3239591 / 8f3672d1 and frozen Index8/Packed128 comparisons unchanged.
- Frozen Contract: `docs/build/PSM-WMA_V3_E1_evaluation_reliability_contract_2026-10-15.md`; Git blob `0df5438868cd9adf190631457dcf4c2866de4a27` at the implementation SHA.
- Source/test diff ONLY: `scripts/eval_robocasa_18task_queue.py`, `tools/v3/eval_robocasa_queue_e1_test.py`. Other source commit paths are this contract, author evidence, SESSION/TODO notes; no identity module or Child changes.

## Author observations (not independent acceptance)

Python3.12.14, pytest9.0.2, Ruff0.12.7. Two-file syntax/Ruff check/format PASS. Focused suite exit0: **26 passed, 15 parameter subcases passed**, 16.76 seconds; JUnit includes **41 cases total**, not 41 independent test methods. CPU tiny subprocesses/mocks only. Full stdout, JUnit, source hashes and exact commands are in `docs/collab/chatgpt/evidence/2026-10-15_V3_E1_author_cpu/`. No real simulator/server/GPU/DCP/robot data or training used.

## DS allowed actions and fail conditions

Use a clean detached independent validation worktree pinned to the exact implementation SHA with the exact clean Child. Preserve original training directory, other agents' work, all notes and historical evidence. No reset/clean/force, production edits, source/test/config/SESSION/TODO modifications, package installation, GPU, torchrun, data scans, model/DCP loads, official screening, Fresh/Resume, B0 rerun, B1 or Gate M action. Use existing DS Python, Ruff0.12.7 and pytest. Missing environment/capability is BLOCKED, not permission to modify production.

Linux PR_SET_CHILD_SUBREAPER capability is required for owned-descendant reaping. Tests deliberately create only fake Python servers/simulators, send SIGTERM to their scoped coordinator handler, test ignoring TERM/spawned-child KILL and waitpid. This is not real GPU cancellation evidence. Read contract limitations (no daemonizing/escaping owned process groups). Return failures as-is; stop on first failed stage, no automatic retry or test weakening.

## Reproducible CPU commands

After safe exact checkout, run from its Root. Choose a NEW external evidence directory; this example creates one under /tmp. Environment package installation is not part of this request.

```bash
set -euo pipefail
EXPECTED_ROOT=afd615e4b2fc7610aef950b4c2ea80a494abfd5d
EXPECTED_CHILD=1d56320c08c56b0f8dd248919d152d81ae12ea7b
EVIDENCE_DIR="$(mktemp -d /tmp/psm-v3-e1-ds-XXXXXX)"
export CUDA_VISIBLE_DEVICES=""
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="$EVIDENCE_DIR/pycache"
test "$(git rev-parse HEAD)" = "$EXPECTED_ROOT"
test "$(git -C cosmos-framework rev-parse HEAD)" = "$EXPECTED_CHILD"
test "$(git rev-parse HEAD:cosmos-framework)" = "$EXPECTED_CHILD"
test -z "$(git status --porcelain --untracked-files=all)"
test -z "$(git -C cosmos-framework status --porcelain --untracked-files=all)"
git rev-parse HEAD > "$EVIDENCE_DIR/root.txt"
git ls-tree HEAD cosmos-framework > "$EVIDENCE_DIR/gitlink.txt"
git diff-tree --no-commit-id --name-status -r HEAD > "$EVIDENCE_DIR/diff.txt"
ruff --version > "$EVIDENCE_DIR/ruff-version.txt"
test "$(ruff --version)" = "ruff 0.12.7"
python -m py_compile scripts/eval_robocasa_18task_queue.py tools/v3/eval_robocasa_queue_e1_test.py > "$EVIDENCE_DIR/syntax.log" 2>&1
ruff check --config cosmos-framework/.ruff.toml scripts/eval_robocasa_18task_queue.py tools/v3/eval_robocasa_queue_e1_test.py > "$EVIDENCE_DIR/ruff-check.log" 2>&1
ruff format --check --config cosmos-framework/.ruff.toml scripts/eval_robocasa_18task_queue.py tools/v3/eval_robocasa_queue_e1_test.py > "$EVIDENCE_DIR/ruff-format.log" 2>&1
python -m pytest --noconftest -q -o addopts='' -p no:cacheprovider tools/v3/eval_robocasa_queue_e1_test.py --junitxml="$EVIDENCE_DIR/pytest.xml" > "$EVIDENCE_DIR/pytest.log" 2>&1
test "$(git rev-parse HEAD)" = "$EXPECTED_ROOT"
test "$(git -C cosmos-framework rev-parse HEAD)" = "$EXPECTED_CHILD"
test "$(git rev-parse HEAD:cosmos-framework)" = "$EXPECTED_CHILD"
test -z "$(git status --porcelain --untracked-files=all)"
test -z "$(git -C cosmos-framework status --porcelain --untracked-files=all)"
```

Preserve commands, cwd, versions, each stage returncode and first failure traceback, before/after Root/Child/Gitlink/status. Produce an external DS gate.json or consolidated report binding these facts to the exact Pair. Include test counts with subcase distinction, no owned orphan survivors, unaffected unrelated process, errors retained even with complete tasks, null official SR on infrastructure failure, partial files retained, finite deadline/cancel/reap, atomic summaries and prior execution preservation. Do not run broad repository/GPU gates to compensate for an E1 failure.

## Stop and Fresh Review

DS returns independent E1 CPU Evidence only. Codex/GPT then inspect exact source/test/contract + Evidence, and GPT issues a separate pair-bound Fresh Incremental verdict in reviews/. No gate closure or merge follows from these author results. Do not proceed to E2, T1, P1, training, official eval or any other Gate without its own authorization.

## Publication limitation

Native Git branch publication works. GitHub CLI GraphQL and REST PR APIs returned `Forbidden`; no PR was created or merged. Review candidate through its exact SHA/branch. Optional manual PR URL: https://github.com/wxwy/psm_wma/compare/V3...v3-e1-evaluation-reliability-20261015 . No branch protection or authorization bypass attempted.
