# ChatGPT → Codex Inbox

This file is the **single append-only handoff entrypoint** for messages that ChatGPT wants Codex/other project agents to see.

## Usage

- Before starting or continuing implementation/review work, read the **latest entry at the bottom of this file**.
- Do not rewrite or delete previous entries.
- Substantive reviews may have a detailed file under:
  `docs/collab/chatgpt/reviews/`
- The Inbox entry remains the authoritative short handoff: verdict, blockers, required next action, and link to detailed review.
- If a newer entry supersedes an older one, it must say so explicitly.
- Codex does not need to edit this file to acknowledge; record execution status in the normal `SESSION.md` / `TODO.md` workflow.

---

## 2026-08-28 — R08 Gate-0 diagnostic review @ a3d11a8

**Verdict: REQUEST_CHANGES**

**Do not run Gate-0 GPU yet.**

Target:
- root: `a3d11a8ccae47e93df61655b0b2f5d959cd87f9a`
- submodule: `10bc41085de448d60d2f71b342c03a4cfcca9ee1`

Required fixes before GPU:
1. HIGH: wrap Wan VAE encoding in `torch.inference_mode()` / no-grad and detach CPU sidecars; current code can retain autograd graphs across 64×2 VAE forwards.
2. MEDIUM: enforce deterministic VAE runtime and preferably add same-input repeat control.
3. MEDIUM: make task/episode coverage real, not only episode-first selection with a task-diversity comment.
4. MEDIUM: freeze canonical PASS threshold at <=1e-6; CLI must not be able to loosen the Gate arbitrarily.

Recommended:
- persist first-frame/suffix input fingerprints and changed-pixel counts;
- optional runtime-A-z0 vs existing cache-z0 sampled parity.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Gate0_a3d11a8.md`

Next:
- CPU/static-only fixes
- new commit SHA
- re-review by ChatGPT/mm/Kimi
- GPU Gate-0 only after approval


---

## 2026-08-28 — R08 Gate-0 diagnostic re-review @ 8778b7e

**Verdict: APPROVE_TO_RUN_GATE0_GPU**

Target:
- root: `8778b7e3d0504040dd12b1eddaa9fabe32b69759`
- submodule: unchanged `10bc41085de448d60d2f71b342c03a4cfcca9ee1`

Previous blockers are closed:
1. VAE encode now uses `torch.inference_mode()`; retained z0 tensors are detached CPU tensors.
2. Deterministic runtime is enforced and recorded; same-input repeat control is present.
3. Anchor selection now has explicit task/episode stratification and machine-readable coverage.
4. Canonical threshold is frozen at `1e-6`; unrestricted `--atol` is removed.
5. Input first-frame/suffix fingerprints and changed-pixel evidence are persisted.

Important runtime interpretation:
- `PASS_STRICT_BITWISE` is a strong causal PASS candidate.
- `PASS_TOLERANCE_ATOL_1E-6` does **not** close Gate-0 by status string alone; independent review must verify there is no stable/systematic suffix-dependent nonzero signal.
- `FAIL` must follow the R08 supplement fallback route; exact-window z0 must not be used as causal historical evidence.

Next:
- Codex may run the **Gate-0 GPU diagnostic only**, after the normal D005 launch disclosure.
- Preserve JSON + raw z0 sidecar through independent runtime review.
- Do not start R08 Step 2/history/model/R09 before runtime Gate-0 review closes.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Gate0_8778b7e.md`


---

## 2026-08-28 — R08 Gate-0 scope adjustment

**Decision: downgrade Gate-0 from a research hard gate to a one-time Wan z0 causal-contract sanity check.**

Reasoning:
- Wan2.2 official design is a causal VAE and encodes the first frame as the key-frame prime before later temporal chunks.
- The current Cosmos Wan2.2 wrapper follows the same causal/key-frame-prime contract.
- In the existing closed-loop simulation path, inference does not have access to true future RGB suffixes, yet the model still predicts/controls effectively; this is strong engineering evidence that the useful current representation is not materially dependent on future frames.
- Therefore the main uncertainty is no longer “is Wan z0 causal?”, but only whether our specific Cosmos wrapper / exact-duration / chunking / bf16 / runtime path accidentally violates the official causal contract.

Execution guidance:
1. The already-reviewed `8778b7e` diagnostic may still be run once because the tooling is complete.
2. Treat it as an integration/regression sanity check, not as an exploratory algorithmic Gate.
3. If it PASSes, do **not** add more z0 causality experiments; immediately proceed to R08 history alignment.
4. If it unexpectedly FAILs, first investigate wrapper/chunking/runtime/config differences; do not conclude that Wan2.2 itself is non-causal.
5. Future documentation should prefer wording such as:
   `Wan z0 Causal Contract Sanity Check`
   instead of
   `Historical Visual Representation Causality hard Gate`.

The real R08 hard causality/leakage checks should focus on history construction:
- history visual indices strictly `< t`;
- history executed-action indices strictly `< t`;
- no current target action chunk leakage;
- no predicted/unexecuted action leakage;
- same-episode identity;
- state/action/visual timestamp alignment;
- episode-boundary correctness;
- padding/mask correctness;
- no DataLoader cross-sample contamination.

This scope adjustment does not revoke the prior approval to run the existing diagnostic once; it only changes its interpretation and prevents further over-investment in a property already guaranteed by the upstream architecture.


---

## 2026-08-28 — R08 Wan z0 sanity runtime review @ e7fb1ec

**Verdict: APPROVE_TO_CLOSE_SANITY_CHECK**

Result:
- `artifacts/g0/r08/gate0_z0_suffix_invariance.json`
- `PASS_STRICT_BITWISE`
- 128/128 A-vs-B z0 bitwise identical
- 128/128 A-repeat bitwise identical
- all `max_abs = 0`
- all tensors finite
- every A/B first-frame fingerprint identical
- every suffix fingerprint different
- minimum changed suffix pixels: 2,166,741
- minimum suffix max pixel delta: 218
- 4 suites × 4 remainder classes × 8 anchors, with 8 unique tasks/episodes per class

Provenance note:
- runtime root commit is `5ff9327`, not `8778b7e`;
- verified diagnostic script blob is identical at both commits:
  `6ab4487e5151e7082a50d9417a56c0b40a773ec0`;
- intermediate commits only changed ChatGPT review/inbox docs, so reviewed code == executed code.

Sidecar:
- local raw sidecar SHA256 recorded as
  `154f18cd8de9e0a065ef9c766649550b6e456723a3a72b708a3dfb22b9d96e5f`;
- keep it until mm2/Kimi runtime review also closes.

Interpretation:
- This closes the one-time **Wan z0 Causal Contract Sanity Check** on the ChatGPT side.
- Do not add more z0 causality experiments.
- The next real R08 hard checks are history alignment/leakage: strict `j<t`, executed-action boundary, no target/predicted-action leakage, same episode, timestamp alignment, episode boundary, mask/padding, and no DataLoader cross-sample contamination.

Next:
- wait for mm2/Kimi runtime review closure;
- then mark the old Gate-0 item DONE/closed as sanity check and proceed directly to R08 Step 2 causal history dataset/alignment.

Detailed review:
`docs/collab/chatgpt/reviews/2026-08-28_R08_Gate0_runtime_e7fb1ec.md`
