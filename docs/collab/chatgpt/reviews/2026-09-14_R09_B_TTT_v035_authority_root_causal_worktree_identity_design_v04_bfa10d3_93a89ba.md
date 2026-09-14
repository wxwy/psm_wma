# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Causal Worktree Identity Design v0.4

**Date:** 2026-09-14  
**Formal root:** `bfa10d345f2003a3a123f69dc836462fe05959d9`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`

## 1. Pair / correction / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`.
- The immediately preceding v0.4 request contained a transcribed root `bfa10d34a130a3616e351ccd1aaecaa6a3dc0e95`; the live Inbox explicitly corrects the sole valid formal root to `bfa10d345f2003a3a123f69dc836462fe05959d9`. This review binds only that corrected pair.
- Independently verified formal root `bfa10d3...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Relative to prior approved same-Gate pair `56acad8f39241c8c03fa770aa39468a3e71a2349` / same child, the formal authority change is docs-only v0.4 design plus task/session bookkeeping. No project implementation or child change is in formal scope.
- No real Git/worktree/materialization/source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.

## 2. Prior approved design retained

The v0.3 design was approved because it closed the mutable-leaf target race by making the actual Git add target the retained leaf capability: `clean_fd -> FD6 -> /proc/self/fd/6`, with exact `close_fds=True`, `pass_fds=(6,)`, no parent+name/global fallback, retained FD7/FD9 owner mapping, post-Git triple identity proof, and owner-limited cleanup.

v0.4 narrows the add-target spelling to `/proc/self/fd/6/.` after a temporary local-Git probe showed that this preserves canonical worktree registration and later native administrative operations. That add-target spelling remains leaf-capability-derived and does not reintroduce `clean_name` lookup. This part is **acceptable**.

## 3. Blocking finding

### HIGH-1 — cleanup reintroduces mutable global `<clean>` as a destructive Git target

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.4.md:31` (section 2, step 4)

v0.4 states that normal cleanup, after proving A is still the owner, uses:

```text
git worktree remove --force <clean>
```

and relies on retained-FD checks before and after the remove.

This weakens the already-approved v0.3 cleanup contract. `<clean>` is a mutable global namespace path. The pre-remove identity check does not linearize the later Git pathname resolution:

1. launcher proves the retained parent entry still names owner A;
2. after that proof but before `git worktree remove --force <clean>` resolves its operand, the `clean_name` entry can be renamed/replaced with foreign B;
3. the destructive Git cleanup may now consume the global path naming B, or otherwise act through administrative metadata whose registered path currently resolves to B;
4. the post-remove retained-FD check can detect the drift only **after** possible foreign mutation/removal.

That is the same detection-after-mutation authority failure class previously rejected for `worktree add`. It also contradicts v0.4's own statement that foreign B is never read/written/deleted.

The temporary probe establishing that `worktree remove --force <clean>` succeeds when the namespace remains stable is useful compatibility evidence, but it does not prove race-safe cleanup authority.

## 4. Exact acceptance

The replacement design must preserve leaf-capability authority at the destructive cleanup boundary as well as at add.

- A cleanup Git consumer must not use mutable global `<clean>` as its destructive authority unless an additional mechanism proves the namespace cannot change across target resolution and mutation.
- Prefer re-deriving an inherited cleanup target FD from retained `clean_fd`/FD9 and using the exact procfd-derived leaf target spelling that temporary native-Git fixtures prove safe for `worktree remove`; freeze `close_fds`, exact `pass_fds`, CLOEXEC, FD collision/lifetime, pre/post identity barriers, and no global fallback.
- If Git cannot safely remove through a retained leaf capability, the launcher must fail closed / return `ROLLBACK_INCOMPLETE` and preserve the administrative/worktree residue rather than fall back to a mutable global destructive target.
- Add a direct temporary native-Git cleanup-race witness: after the last pre-remove owner check but before Git resolves the remove target, replace same-parent A with foreign B. The result must prove B is not read/written/deleted. Either cleanup removes only retained A through the leaf capability or cleanup fails before touching B.
- Keep the already-accepted `/proc/self/fd/6/.` add seam, same-parent add race witness, global-parent replacement witness, metadata validation, legacy v0.8 negative route, and root-only temporary CPU/static scope.

## 5. Non-blocking observations

- The corrected root anchoring is clear and unambiguous.
- `/proc/self/fd/6/.` is a sound docs-level refinement of the add target because it stays within the held leaf capability and explicitly forbids parent/name/global fallbacks.
- The reported local probe is appropriate as fixture evidence for exact add spelling and canonical registration, but it does not authorize real materialization.
- Child/Gitlink blockers: **0**.

## 6. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.4.md:31)`

Current blockers: **1 HIGH Design/Authority**.  
Child/runtime blockers: **0**.

## 7. Scope reminder

This verdict binds only exact formal pair `bfa10d345f2003a3a123f69dc836462fe05959d9` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`.

Only a docs-only redesign is authorized by this verdict. No real Git/worktree/materialization, source/checkpoint/manifest/data/cache access, collection/receipt/publication, child/runtime/config modification, GPU, training, evaluation, inference, or LIBERO4IN1 action is authorized.
