# ChatGPT Review — Authority-root Launcher Procedure v0.4

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root docs SHA: `11950c953d7c3e781f821ab648d45af83e60d340`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink to the stated child, and the child commit is independently reachable in `wxwy/cosmos-framework`.

The delta from prior pair `17767c0c52cb2e5856a9c98baf29f520ce27fc5b` is docs/status/review bookkeeping plus the v0.4 annex/replacement request only. No production root tooling or child/runtime code is changed.

## Progress from the prior HIGH

The prior launcher-authority blocker is materially narrowed. v0.4 now freezes a canonical procedure descriptor with absolute Git worktree add/remove argv, backing paths, FD targets, close policy, final launch mapping, and explicit launcher-owned cleanup / `ROLLBACK_INCOMPLETE` semantics. This closes the earlier purely-natural-language ownership/rollback gap.

However, the object still does not yet constitute a complete auditable execution authority.

## Blockers

### HIGH-1 — the launcher payload bytes required by the annex are still absent

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.4.md:35`

Section 3 explicitly requires the launcher `payload` raw bytes, byte length and SHA-256 to be reviewed together with the new request. Neither the annex nor replacement request supplies those bytes, length or digest. The canonical descriptor still contains the literal placeholder `"payload"` in `launch.argv`.

Therefore the executable launcher code that performs worktree creation, backing-file creation, FD manipulation, cleanup and final `execve` would still be created for the first time after approval. That is exactly the post-approval authority-bearing choice the previous review prohibited.

**Exact acceptance:**
1. Freeze the exact stdlib launcher payload raw UTF-8 bytes in the annex/request, or freeze an immutable formal-tree launcher artifact with exact path/blob/raw-SHA identity.
2. Freeze its exact byte length and SHA-256 and bind `launch.argv[5]` to those exact bytes, not the string placeholder `payload`.
3. Demonstrate by independent/static reconstruction that those exact bytes implement only the approved descriptor/procedure and introduce no new runtime values.
4. The reviewed execution command must invoke only those approved bytes.

### HIGH-2 — the canonical descriptor and prose disagree on the final `execve.argv`

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.4.md:25`

The descriptor freezes `execve.argv` as the symbolic reference `v0.3.bootstrap_observation_json[1:]`. Under the approved v0.3 definitions, `bootstrap_observation_json` is the bootstrap-observed `sys.orig_argv[6:]` value, i.e. `["--", *actual_argv]`; slicing `[1:]` therefore yields only `actual_argv` and omits the Python executable, `-I -S -B -c`, bootstrap payload and literal `--`.

Section 3 step 5 instead says final `os.execve()` must receive the full argv `[python, -I, -S, -B, -c, <bootstrap raw>, --, *actual_argv]`. Those are different authorities. A canonical launcher descriptor cannot leave the final process argv dependent on which interpretation an operator chooses.

**Exact acceptance:**
1. Replace the symbolic `execve.argv` reference with an exact canonical array or an unambiguous derivation whose result is exactly `["/opt/conda/bin/python3","-I","-S","-B","-c",<frozen bootstrap raw>,"--",*actual_argv]`.
2. Freeze the canonical bytes/length/SHA-256 of that final argv representation or prove exact derivation from already-frozen bytes.
3. Make descriptor and §3 step 5 byte-for-byte semantically identical; no alternative interpretation may remain.

### HIGH-3 — the first native Git worktree mutation occurs before the launcher binds the parent repository routing/config authority

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.4.md:38`

The frozen procedure's step 1 checks that `/disk/rl/psm_wma/.git` is a non-symlink directory, then step 2 immediately runs the frozen `git worktree add` command. It does not, before that first native Git command, bind and revalidate the parent repository's exact Git routing/common-config authority (Git-dir/common-dir/config identity/raw bytes, `config.worktree` absence and strict accepted local-config view).

That is weaker than the already-closed execution-authority contract. The six-key environment and command-line prefix disable system/global config and several known hooks/filters, but they do not make arbitrary repository-local config disappear. A repository-local config/routing drift can therefore be consumed by the very `git worktree add` that creates the clean root, before the clean-root bootstrap has a chance to perform its own routing/config checks.

The replacement request itself still requires routing-authority revalidation before execution, so the exact payload/procedure must causally perform that check before the first worktree Git observation/mutation rather than leave it to an operator or to the later adapter bootstrap.

**Exact acceptance:**
1. Before `worktree_add_argv`, the frozen launcher payload must verify the frozen Git executable identity and bind the parent repository `.git`/Git-dir/common-dir/local-config authority with no-follow identities/raw bytes and the already-approved strict config policy (including `config.worktree` absence / `extensions.worktreeConfig` policy), or use a stronger demonstrably equivalent mechanism.
2. Revalidate that routing/config authority immediately before and after launcher native Git observations that consume it, including add/remove cleanup, so route/config replacement cannot switch authority mid-command.
3. Any drift must fail before worktree creation; if drift is detected after launcher-owned mutation, only the already-frozen ownership cleanup/`ROLLBACK_INCOMPLETE` path is allowed.
4. No new remote alias, shell, PATH, ambient config or caller authority may be introduced.

## Blocker summary

- docs/request blockers: `3 HIGH`
- implementation blockers: `0` (closed production adapter implementation remains authoritative)
- child/runtime blockers: `0`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.4.md:35)`

This verdict binds only exact pair `11950c953d7c3e781f821ab648d45af83e60d340 / 93a89ba61306d840a008813f62f26a34d54850f4`.

No materialization, JSON/worktree/index/candidate/ref/evidence creation, source/checkpoint I/O, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized by this review.