# ChatGPT Review — Authority-root Execution Authority Implementation Design v0.4

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-EXECUTION-AUTHORITY-IMPLEMENTATION-DESIGN`

## Exact formal pair

- root design SHA: `9aba4460469ddab4640e90694e78968d497a9273`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink resolving to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental design review against prior exact pair `65836016ebc4fbcb73c50dc055cae206a690bc4f / 93a89ba...`. The formal delta is docs/status only and adds v0.4; no root tooling or child/runtime implementation changes are in this pair.

## Prior HIGH closure

### Prior HIGH — `git_dir/config` was not the effective linked-worktree local-config authority: CLOSED

v0.4 now freezes separate typed `git_dir` and `git_common_dir` identities using the already-frozen Git executable/env/prefix; both must resolve to absolute existing non-symlink directories. With `extensions.worktreeConfig` absent/false, it makes `<git_common_dir>/config` the sole local-config authority and requires per-worktree `config.worktree` to be absent.

The authoritative common config path, same-FD raw SHA-256, canonical parsed allowlist mapping and isolation fingerprint are all required to enter the invocation/Evidence exact-key ABI. The native `git config --no-includes --local --null --list` view must match the same frozen raw-config authority, with any path/bytes/view mismatch failing before the first object/ref/transport action.

The required direct witnesses now include actual linked/detached temporary worktrees: forbidden `url.*`/`remote.*`/include entries placed in the common config must reject even when the per-worktree admin directory has no config; the minimal accepted linked-worktree case is an explicit positive control. Symlink escape, `extensions.worktreeConfig=true`, `config.worktree` appearance and raw-vs-Git-view divergence are also fail-closed witnesses. This directly closes the previous exact acceptance criteria.

## Retained authority chain / scope

The v0.4 delta does not reopen or weaken the already-frozen v0.2/v0.3 contracts:

- process-level bootstrap observation still uses the actual Python 3.11 invocation before project import;
- adapter/authority/collection/audit remain the complete project-module closure to bind before import;
- production transport remains a canonical direct endpoint rather than `origin`/remote alias;
- no-replace, global/system config isolation, fixed Git command prefix, endpoint digest and isolation fingerprint remain required;
- local-config accepted-key/value policy from v0.3 remains fail-closed for every other key;
- direct native temporary-repository and temporary bare-remote CAS witnesses remain required;
- only `tools/psm_wma/materialize_immutable_source_authority_root.py` and `tools/psm_wma/test_materialize_immutable_source_authority_root.py` are authorized for the next CPU/static implementation Gate.

## Evidence / implementation boundary

This approval is design-only. The implementation review must verify the literal production parser/invocation/Evidence-v1 ABI, native Git path behavior, linked/detached worktree config resolution, direct adversarial witnesses, and unchanged PASS/FAIL/rollback semantics. Passing unit-test counts or static checks alone will not substitute for the direct causal witnesses frozen here.

No real materialization, real source/checkpoint I/O, project origin/ref/evidence mutation, collection/receipt, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized.

## Blocker summary

- prior HIGH: CLOSED
- current design blockers: `0`
- Evidence-only blockers: `0`
- total blockers: `0`

## Final verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC`

This approval binds only exact formal pair `9aba4460469ddab4640e90694e78968d497a9273 / 93a89ba61306d840a008813f62f26a34d54850f4` and only the two-root-file CPU/static implementation scope stated above.
