# ChatGPT Review — Authority-root Launcher v0.8 Static Witness Closure

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root docs SHA: `5ff4df58cc8e17644aab945de3de6d74b8b2967c`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink to the stated child, and the child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh formal pair relative to the prior reviewed `bf852c233b2c2e31eb33dc859188a9a4b41c50df / 93a89ba61306d840a008813f62f26a34d54850f4` pair. The v0.8 formal request correctly narrows this round to **docs-only/static-witness closure** and requests only `APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_WITNESS_CLOSURE`; it does not request or authorize materialization.

The exact formal-tree launcher blob is `f41b9e7d797d879d72f448bb2fae077d38288102`. The v0.8 annex freezes the launcher as 13,620 UTF-8 bytes with SHA-256 `8103e504d3e0e7398e487227466e247e6e96d3a70f8fe688d01b749344d3cb9a`.

## Authority chain used

The review applies the inherited v0.2/v0.3 frozen runtime bytes/FD ABI/tool identities, the v0.4 launcher mutation/cleanup semantics, the prior v0.7 exact-pair review, and v0.8 only where it explicitly supersedes the launcher artifact/static witness closure. v0.8 does not supersede the post-mutation fail-stop rule, exact ownership requirement, or direct causal Evidence requirement.

## Prior blocker disposition

- v0.7 HIGH-1 (`/proc/self/fd` self-enumeration): **CLOSED**. `durable_fds()` lists first and then `fstat`-validates candidates, so the transient directory FD is excluded after `os.listdir()` closes; the forked direct payload witness exercises `close_to_keep({3,4,5})` with an injected extra FD.
- v0.7 HIGH-2 (post-add ownership-capture gap): **PARTIALLY CLOSED / STILL BLOCKING**. v0.8 correctly converts lookup/open/bind failure in `capture_owned()` to `ROLLBACK_INCOMPLETE` and retains a no-follow CLEAN directory FD after binding. However the binding still occurs only after `run(... worktree add ...)` returns and is not anchored to the inode actually created by that Git command.
- v0.7 HIGH-3 (Gate/Evidence matrix): **PARTIALLY CLOSED**. The formal request now correctly asks only for static-witness PREPARE closure, and the 11-case suite directly exercises substantially more exact payload seams. But the decisive successful-add → foreign replacement → ownership-capture seam from prior HIGH-2 is still absent.

## Blocker

### HIGH-1 — post-add capture can still bind a foreign CLEAN inode; the exact replacement seam is not causally witnessed

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py:90-102` (`bind_owned`, `capture_owned`, `add_and_capture`).

`add_and_capture()` performs the native `worktree add` through `run()` and only after that call returns invokes `capture_owned()`. `capture_owned()` calls `bind_owned()`, which starts by `lstat(CLEAN)`, opens the current pathname with `O_DIRECTORY|O_NOFOLLOW`, and only proves that the pathname and the newly opened FD refer to the same current inode.

That is not a proof that this inode is the CLEAN directory created by the preceding Git mutation. If the just-created CLEAN is removed/renamed and another directory is installed at the same pathname between successful `run()` return and `bind_owned()`'s first observation, `bind_owned()` can successfully bind the replacement. The later `assert_worktree()` rejects a simple non-worktree replacement, but it still has no pre-replacement inode authority: a foreign replacement that reproduces the expected Git worktree/admin semantics can satisfy HEAD/status/worktree-list checks because the launcher never retained an identity for the object actually created by the add command.

This leaves the exact ownership claim in annex v0.8 stronger than the implementation. The annex states that any post-add replacement becomes `ROLLBACK_INCOMPLETE` and that post-add ownership is captured as the newly created authority; the code only turns *binding failure* into `ROLLBACK_INCOMPLETE`, not replacement that remains bindable and semantically Git-valid.

The current 11-case Evidence does not close this. It directly tests missing CLEAN via `capture_owned()`, foreign replacement **after ownership has already been captured** via `cleanup()`, nonzero add, and post-add `commondir` drift. It does not inject successful `worktree add` followed by CLEAN replacement before the first ownership bind. Therefore the exact regression class from the prior review remains unproven as well as not fully prevented.

**Violated frozen contract:** inherited v0.4 launcher-owned mutation/cleanup semantics; prior v0.7 HIGH-2 exact acceptance requiring successful-add followed by CLEAN disappearance/replacement before ownership capture to fail closed; direct causal Evidence principle; v0.8 annex claim that post-add replacement cannot become accepted owner authority.

**Exact acceptance:**
1. Make the first accepted CLEAN owner identity causally attributable to the worktree created by this exact add, rather than merely to whatever directory happens to occupy `CLEAN` after `run()` returns. A replacement inode in the add→capture interval must not be accepted as owner authority.
2. If the implementation cannot prove continuity from the add-created object to the retained FD, it must terminate `ROLLBACK_INCOMPLETE` before treating CLEAN as owned or creating backing files.
3. Preserve the existing no-force-remove rule for foreign replacements and the conservative `ROLLBACK_INCOMPLETE` terminal semantics.
4. Add a direct temporary native-Git witness against the exact payload seam: successful add, inject CLEAN rename/replacement before the first ownership capture, and prove the replacement is never accepted/removed and the terminal result is `ROLLBACK_INCOMPLETE`. Include a replacement that is sufficiently Git-valid to ensure the witness does not pass merely because `rev-parse` fails on an empty directory.

## Blocker summary

- current blockers: `1 HIGH`
- child/runtime production blockers: `0`
- launcher/static-closure blockers: `1 HIGH`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py:90)`

This verdict binds only exact pair `5ff4df58cc8e17644aab945de3de6d74b8b2967c / 93a89ba61306d840a008813f62f26a34d54850f4`.

No materialization is authorized. No source/checkpoint I/O, worktree/backing/index/candidate/ref/evidence creation on project paths, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized by this review.