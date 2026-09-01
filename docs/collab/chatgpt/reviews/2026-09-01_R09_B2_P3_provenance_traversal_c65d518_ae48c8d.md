# R09-B2 P3 provenance/traversal re-review

- Review request root: `c65d518302109a8e753998db5a5d804c31c593c4`
- Reviewed implementation root: `ae48c8d9de17a7ece228d9512c0aab323171c416` (main provenance binding introduced at `8578736ce1eaff2622cb0d9422f0de565561a00e`)
- Submodule/Gitlink: `0af5d53900ec169f43104d4fdf1827ad6691600d`
- Scope: root-side static verifier/provenance hardening only; no GPU/model/processor authorization.

## Verdict

**REQUEST_CHANGES**

The previous blocker — provenance fields being merely non-empty — is substantially improved: the verifier now derives Gitlink from `root_revision`, checks frozen source hashes, binds D005 SHA/content, command/cwd/environment/GPU/world-size/resource cap, and checks the exact run token. The traversal exception also now fails closed instead of raising.

However, the current provenance gate still does not prove that the code executed from the claimed committed revisions.

## HIGH — source hashes are taken from the mutable working tree, not from the claimed commits

`tools/g0/verify_r09_b2_p3_gpu_inventory.py:72-75` computes `source_hashes_valid` using `_sha256(root / relative)`.

At the same time `root_gitlink_valid` only proves:
- `provenance.root_revision == git rev-parse HEAD`, and
- the Gitlink recorded in that commit equals the artifact-declared submodule revision.

It does **not** prove that:
- the root working tree is clean;
- the checked-out submodule HEAD equals `submodule_revision`;
- the submodule working tree is clean;
- the hashed root/submodule files are the blobs from `root_revision` / `submodule_revision`.

Therefore this can still PASS:
1. HEAD remains at the reviewed commit;
2. modify `collector.py`, `verifier.py`, model/optimizer/DCP source, or submodule files without committing;
3. place the hashes of those modified files into artifact provenance;
4. all current source-hash checks pass while the artifact still claims the old committed root/submodule revisions.

That violates the required execution-provenance binding.

### Required fix

Before any PASS can be accepted, hard-gate at least:

1. root tracked-clean status;
2. actual `cosmos-framework` HEAD == `submodule_revision` == root Gitlink;
3. submodule tracked-clean status;
4. source SHA validation against **commit blobs**, not only current filesystem bytes. For example:
   - root-owned files: hash `git show <root_revision>:<path>` content;
   - submodule-owned files: hash `git -C cosmos-framework show <submodule_revision>:<path>` content;
   - optionally also require current filesystem bytes equal those committed blobs.
5. Add negative regression: keep root HEAD/Gitlink unchanged, modify one frozen source file in the worktree, provide matching modified-file SHA in the artifact, and require FAIL.

## MEDIUM — D005 containment should use resolved-path containment, not only `..` syntax rejection

Current guard rejects absolute paths and any literal `..` path component, which is useful, and `ae48c8d` correctly catches the resulting `ValueError`. But `root / relative` may still follow a symlink under the repository to a location outside the verified root.

For a run-authorization record, use resolved containment such as `d005_path.resolve()` and require it to remain under `root.resolve()` before reading. Add a symlink-escape negative case if D005 paths are allowed to reference filesystem files outside committed Git blobs.

## Accepted from this round

- non-empty provenance fields are no longer the sole PASS criterion;
- exact run token is verifier-owned;
- root revision -> Gitlink derivation exists;
- D005 SHA and root/submodule/Gitlink identity cross-check exists;
- command/cwd/environment/GPU/world-size/24GiB binding exists;
- path traversal via literal `..` now produces structured provenance FAIL rather than traceback;
- BLOCKED artifacts still do not have to fabricate execution provenance;
- current root tree still points to Gitlink `0af5d53900ec169f43104d4fdf1827ad6691600d`.

## Scope

Continue only CPU/static verifier/test hardening. Do **not** authorize GPU execution, processor/model construction, checkpoint I/O, forward/backward/optimizer/scheduler step, B2-T, P4/P5, training/eval/inference/closed-loop, multi-GPU, long training, backend freeze, Global/Agent/RL.
