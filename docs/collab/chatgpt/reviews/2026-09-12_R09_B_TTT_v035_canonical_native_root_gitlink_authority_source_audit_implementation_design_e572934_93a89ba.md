# ChatGPT Independent Review — R09-B TTT v0.3.5 Root Gitlink Authority Source-audit Implementation Design v0.2

**Date:** 2026-09-12  
**Formal root:** `e572934e6bbe5cabf2085fdf23aece8e2f0f2c20`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read the live Codex request ledger.
- Independently verified formal root `e572934e6bbe5cabf2085fdf23aece8e2f0f2c20` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal target is docs-only remediation of the same implementation-design Gate; child remains unchanged.
- Review is limited to the two v0.1 HIGH remediations plus fresh internal-consistency audit. No implementation or real source-audit execution is authorized.

## 2. Findings

### Prior HIGH-1 — Git execution trust boundary: CLOSED

v0.2 now freezes `/usr/bin/git` as the only executable, hashes its bytes, records strict single-line `git --version`, forbids PATH/caller Git selection, uses `shell=False`, `text=False`, `close_fds=True`, freezes an explicit subprocess environment, disables replacement objects, and excludes caller Git repository/object/config environment variables. Root and child transport are selected only by validated absolute `-C` / `--git-dir` arguments.

The command identity is versioned and binds executable SHA-256, Git version, exact environment digest, and command-whitelist digest. Temporary-fixture witnesses explicitly inject hostile Git environment and require unchanged authoritative object resolution.

### Prior HIGH-2 — machine-readable per-step evidence: CLOSED

v0.2 restores deterministic machine-readable evidence. Successful output is exact `root_gitlink_source_audit_evidence_v1`; checks are fixed-order and carry exact `name/status/reason/observed`. Validation and operational failures use exact `root_gitlink_source_audit_failure_v1`, preserve pre-existing output bytes, and use deterministic exit codes. Non-canonical publication raw bytes are explicitly rejected by byte-for-byte reserialization comparison.

### HIGH-1 — Design/Authority — bootstrap operational failures require a command identity that cannot yet exist

The new Git execution contract says `/usr/bin/git` missing, non-executable, unreadable for SHA-256, or invalid/non-single-line `git --version` is an operational FAIL. The same section defines `root_gitlink_git_command_identity_v1` as an exact mapping containing `git_executable_sha256` and `git_version`, and says it "must enter every result". Section 2 then requires every validation or operational failure object to contain `command_identity`.

Those requirements are mutually inconsistent for failures that occur before executable SHA/version can be established. For example, if `/usr/bin/git` does not exist or cannot be read, a conforming implementation cannot both emit the required exact failure schema and supply the required exact command identity without inventing unspecified placeholder/null semantics. That leaves the bootstrap failure contract implementation-defined.

**Acceptance:** freeze an exact bootstrap-failure representation. One acceptable approach is to define a separate exact bootstrap identity/status schema, or make `command_identity` explicitly nullable only for named pre-identity operational reasons while freezing exact companion fields/reason codes. Another acceptable approach is to split Git identity establishment into a mandatory bootstrap record whose exact partial/error schema is defined before the full `root_gitlink_git_command_identity_v1` can exist. Add direct stdlib/unittest witnesses for missing/non-executable/unreadable Git and invalid `git --version`, proving exact failure stdout, exit 3, and zero output mutation. Once full command identity exists, retain the current rule that every subsequent result carries it.

## 3. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_root_gitlink_authority_source_audit_implementation_design_v0.2.md:10)`

Current blockers: **1 HIGH**.  
Design/Authority blockers: **1**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 4. Scope

No tooling implementation is authorized by this review. Real publication/source-audit execution, checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, forward/loss/backward, optimizer/scheduler stepping, sidecar, runtime integration, training, evaluation, inference and LIBERO4IN1 remain forbidden.
