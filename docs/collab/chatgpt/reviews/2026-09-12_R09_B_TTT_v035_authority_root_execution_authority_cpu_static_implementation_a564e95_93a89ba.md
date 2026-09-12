# ChatGPT Review — Authority-root Execution Authority CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root implementation SHA: `a564e953aadc646daeed66e46115ecdb614e80b8`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is an actual submodule/Gitlink resolving to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental implementation review against prior exact pair `5efcbdf8954f65da9c7dfd1d0f34c96204c5ddf6 / 93a89ba...`. The effective implementation delta remains confined to the approved root adapter/test files plus collaboration bookkeeping.

## Prior blocker closure

### Prior HIGH-1 — pre-import interpreter/Git executable identity: CLOSED

The bootstrap now verifies, before project import:

- the declared interpreter path is absolute, regular and non-symlink;
- interpreter raw SHA-256 matches the frozen invocation field;
- exact interpreter version output matches the frozen field under the isolated environment;
- Git remains regular/non-symlink with frozen raw SHA-256 and now also has its exact version checked before project import.

Direct isolated-bootstrap witnesses were added for interpreter path/hash/version and Git-version drift. This closes the prior split executable-identity contract.

### Prior HIGH-2 — unaudited local config before bootstrap Git observations: PARTIALLY CLOSED

The remediation correctly tightens `extensions.worktreeconfig` to exact `false` when present, so the previously active worktree-specific config layer is no longer enabled before the bootstrap Git commands. The hostile-config witness now also covers `extensions.worktreeConfig=true`.

However the bootstrap still does not establish the same causal common-config authority frozen by the approved v0.4 design before executing `rev-parse`, `status`, and `ls-tree`.

## Current blocker

### HIGH-1 — bootstrap common-config admission is still TOCTOU/path-authority incomplete before the first native Git observation

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:165`

The approved v0.4 contract requires, before the first object/ref/transport action, a deterministic `git_dir` / `git_common_dir` authority, `<git_common_dir>/config` as the sole local-config authority, `config.worktree` absent, and a same-authority raw/config-view contract that fails closed on path/bytes/view drift.

The current stdlib bootstrap improves policy parsing but still performs this sequence:

1. `lstat()` `.git` / derived paths;
2. separately `open(...).read()` the `.git` pointer and common config;
3. manually derives the common directory for linked worktrees;
4. then executes native Git commands.

There is no same-FD open with `O_NOFOLLOW`, no retained `(dev, ino)` identity, no re-read/revalidation immediately around the first Git observation, and no proof that the manually derived common directory itself is an absolute existing non-symlink directory inside the frozen repository authority. A safe config can therefore be replaced after admission but before `git status`/`ls-tree`, letting those commands consume bytes that were never the admitted authority. This is the same class of raw-vs-effective-config gap that v0.4 explicitly froze against.

The bootstrap also does not require the worktree admin directory's `config.worktree` to be absent. `extensions.worktreeConfig=false` means that file should be inactive, but the approved production contract is stricter: the alternate file must be absent before the authority boundary is considered closed.

**Exact acceptance:**

1. Before the first bootstrap Git command, derive and freeze exact absolute `git_dir` and `git_common_dir` identities without consuming unaudited Git config; prove each existing directory is non-symlink and that the derived paths remain within the frozen repository authority.
2. Require `<git_dir>/config.worktree` absent even when `extensions.worktreeConfig` is false.
3. Open `<git_common_dir>/config` with no-follow semantics; bind the actual opened file identity `(dev, ino)` and raw bytes from that same FD, parse the allowlist from those bytes, and reject any unsupported key/value.
4. Immediately before and after the first Git authority observations, prove the same config path still resolves to the same identity and bytes; any replacement/path/bytes drift must fail before project import, ref/evidence mutation or project callback. An equivalent mechanism that makes native Git consume only the already-admitted immutable config bytes is also acceptable.
5. Add direct isolated-bootstrap witnesses for: common-config replacement after read/before Git view, symlink/common-dir escape, and pre-existing `config.worktree`, proving no project-import sentinel/ref/evidence is reached.
6. Retain all newly closed executable identity, module closure/symlink, endpoint/no-replace, Evidence ABI, common production preflight and temporary-CAS contracts.

The reported CPU/static passes and static checks remain supportive only; they do not replace this missing causal config-authority witness.

## Blocker summary

- prior HIGH-1: CLOSED
- prior HIGH-2: PARTIALLY CLOSED
- current blockers: `1 HIGH`
- design blockers: `0`
- child/runtime blockers: `0`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:165)`

This verdict binds only the exact formal pair `a564e953aadc646daeed66e46115ecdb614e80b8 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Scope remains temporary CPU/static only. This review does not authorize real materialization/source/checkpoint I/O, project origin/ref/evidence mutation, collection/receipt/publication, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1.