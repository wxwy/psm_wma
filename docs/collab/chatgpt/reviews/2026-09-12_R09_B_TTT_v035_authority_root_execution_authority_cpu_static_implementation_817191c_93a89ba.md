# ChatGPT Review — Authority-root Execution Authority CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root implementation SHA: `817191c91ae8c8eb7e1a66f15055d2286d0b76c4`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is an actual submodule/Gitlink resolving to `93a89ba61306d840a008813f62f26a34d54850f4`; that child is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental implementation review against prior exact pair `a564e953aadc646daeed66e46115ecdb614e80b8 / 93a89ba...`. The effective remediation delta remains inside the approved root adapter/test scope plus bookkeeping.

## Prior blocker closure progress

### Prior HIGH — bootstrap common-config authority was not causally frozen before native Git observations: PARTIALLY CLOSED

The remediation materially improves the bootstrap authority boundary:

- common config is now opened with `O_NOFOLLOW|O_CLOEXEC` and retained on one FD;
- `(dev, ino, size)` and raw bytes are frozen from that FD;
- the raw allowlist is parsed from those exact bytes;
- before every bootstrap Git invocation, the current config pathname is required to still resolve to the original file identity and the retained FD bytes must still match;
- a pre-existing main-worktree `.git/config.worktree` is directly rejected before Git/project import.

Those changes close the prior simple path/read split and the previously missing main-worktree `config.worktree` witness.

## Current blocker

### HIGH-1 — linked-worktree config authority is still bound to the wrong path, and the effective config is not revalidated after Git consumes it

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:177`

The approved v0.4 contract is explicitly about both normal repositories and actual linked/detached worktrees. For a linked worktree, the bootstrap reads the worktree `.git` file into `gd`, but then does two non-equivalent things:

1. it sets `common = dirname(dirname(gd))` instead of binding the common directory through the linked worktree's actual `commondir` authority (or another exact equivalent);
2. it checks `wcfg = os.path.join(admin, 'config.worktree')`, where `admin` is the worktree's `.git` path. In a linked worktree that path is a regular file, not the per-worktree admin directory. The actual per-worktree config authority is under the resolved worktree Git dir (`gd/config.worktree`). Therefore the bootstrap can report `config.worktree` absent while never inspecting the real file the linked-worktree Git machinery would use if that layer became active.

The new direct witness only creates `root/.git/config.worktree` in a normal worktree, so it does not prove the required linked/detached-worktree case.

The same function also validates config path identity/bytes only **before** each `subprocess.run(...)`. Native Git then reopens the config pathname independently. A replacement after the precheck but before/during Git's read can still influence `rev-parse`, `status`, or `ls-tree`; there is no post-command same-path/same-bytes check to detect that the effective Git view was obtained under a different local-config authority. This remains weaker than the approved v0.4 raw/config-view drift contract and the production `verify_configuration_authority()` pattern.

### Exact acceptance

1. For linked worktrees, freeze the actual worktree Git dir separately from the worktree `.git` marker. If `.git` is a file, resolve and validate the referenced Git-dir as an absolute existing non-symlink directory and derive/bind the common Git dir through its authoritative `commondir` relation (or an equally exact no-config-dependent mechanism), not by assuming `parent(parent(gd))`.
2. Require the real `<git_dir>/config.worktree` to be absent before the first bootstrap Git observation. Add a direct actual linked/detached-worktree witness with `config.worktree` present under that real admin directory and prove rejection before project import/ref/evidence.
3. Keep the no-follow common-config FD, but revalidate the config pathname identity and FD bytes after each native Git bootstrap observation as well as before it; any replacement/path/bytes drift must fail closed before project import/ref/evidence/callback. An equivalent mechanism that guarantees Git can only consume the already-admitted immutable config bytes is also acceptable.
4. Add a direct isolated-bootstrap race witness that replaces the common config after the precheck but before/during the Git view and proves the operation is rejected rather than accepted under unaudited config.
5. Preserve all closed executable-identity, module-closure/symlink, endpoint/no-replace, Evidence ABI, production common-config, CAS and CPU/static contracts.

The reported CPU/static/static-check passes are supportive only; they do not replace the missing linked-worktree and post-consumption causal witnesses above.

## Blocker summary

- prior executable-identity HIGH: CLOSED
- prior common-config HIGH: PARTIALLY CLOSED
- current blockers: `1 HIGH`
- design blockers: `0`
- child/runtime blockers: `0`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:177)`

This verdict binds only exact formal pair `817191c91ae8c8eb7e1a66f15055d2286d0b76c4 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Scope remains temporary CPU/static only. This review does not authorize real materialization/source/checkpoint I/O, project origin/ref/evidence mutation, collection/receipt/publication, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1.
