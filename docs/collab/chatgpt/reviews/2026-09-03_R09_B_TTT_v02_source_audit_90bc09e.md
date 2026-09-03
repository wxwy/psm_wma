# Independent Source-Audit Review — R09-B TTT v0.2.1 continual Local Memory

- Gate: `G0-R09-B-TTT-V02-STATIC-SOURCE-AUDIT`
- Requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V02_CPU_ALGORITHM_IMPLEMENTATION`
- Source-audit SHA under review: `90bc09e9117a8aabab144007aa82d2771e21fc0f`
- Ledger/request SHA observed at review start: `bc8907033423349d887dc391b8377c9895e3b756`
- Approved design authority: `9074e4eb7f399e69beb0e0409bb01b0452fe9ed1`
- Prior ChatGPT design approval: `f229b633d483b53c7615907ba790ac3c19fc6af3`
- Audit document: `docs/build/PSM-WMA_R09_B_TTT_source_audit_v0.2_2026-09-03.md`
- Frozen Cosmos Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. Remote `V2` was resolved through the connected GitHub API immediately before and during review.

At review start and immediately before persistence, remote `V2` HEAD was ledger/request SHA `bc8907033423349d887dc391b8377c9895e3b756`; its parent is exactly source-audit SHA `90bc09e9117a8aabab144007aa82d2771e21fc0f`.

The cumulative source-audit change from the prior formal design-approval ledger `a35526587559236e6211cfe7e380ecdad28aca57` to `90bc09e` is docs/status only: `SESSION.md`, `TODO.md`, and the new source-audit document. No root production code, Cosmos submodule code, or Gitlink changed. The Gitlink at the exact technical SHA remains `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

GitHub exposes no status/check-run evidence for `90bc09e`; submitted `git diff/show --check` is repository-recorded evidence rather than independently rerun CI here.

## Verdict

`REQUEST_CHANGES`

The audit is technically strong in five of the six mandatory v0.2.1 source-audit areas. I independently spot-checked the frozen Cosmos baseline and confirmed the main training/runtime findings: the trainer performs backward inside each microbatch; the current TTT backend is the detached/window-local B0/B1 prototype; `LocalHistoryRuntime` does not persist returned backend state across calls; current native flow loss performs per-item non-batch reduction before later scalar mean; and the current chronology/window pipeline cannot by itself prove a unique persistent fast-state owner or exact TBPTT boundary.

The proposed CPU-core/chronology/loss/runtime Gate split is also appropriately conservative and does not itself authorize implementation.

However one mandatory v0.2.1 deliverable is not auditable from the exact reviewed source identities: the positive production inference-context trace in Section 5 cites files that are absent from both the reviewed root tree and frozen Cosmos tree. Because v0.2.1 explicitly required the **real production inference/closed-loop call path with immutable `file:line` evidence**, this source-audit Gate is not complete yet.

## HIGH-1 — production inference-context evidence is not resolvable at the reviewed SHAs

**File:** `docs/build/PSM-WMA_R09_B_TTT_source_audit_v0.2_2026-09-03.md:150-188`

### Root cause

Section 5 states a positive current production call graph involving:

```text
closed_loop_eval.py
  -> HTTP /predict or /predict_batch
  -> ActionPolicyRunner._prep_policy_item()
  -> scripts/action_policy_server_libero.py:959 / :1061 torch.inference_mode()
  -> OmniMoTModel.generate_samples_from_batch
```

and further cites `generator_mixin.py` for the generation wrapper.

I attempted to resolve those claimed source files at the exact audited identities:

- root `wxwy/psm_wma@90bc09e9117a8aabab144007aa82d2771e21fc0f`;
- submodule `wxwy/cosmos-framework@21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

The following claimed paths/names are not present in either exact recursive tree / exact contents lookup:

- `scripts/action_policy_server_libero.py`;
- `closed_loop_eval.py`;
- `cosmos_framework/model/generator/generator_mixin.py` (or another resolved `generator_mixin.py` path supporting the cited lines).

Direct exact-path fetches for the claimed server/generator paths also fail to resolve at the frozen Gitlink/root SHA.

Therefore the Section 5 conclusions may well describe a real deployment/local script, but they are not currently tied to an immutable reviewed repository object. The audit cannot simultaneously claim “all six exact `file:line` tables” and use an unresolvable/unversioned production inference source as the authority for one of those six tables.

This matters because the approved v0.2.1 contract specifically required the source audit to trace the **real production inference/closed-loop entry** and determine where the W-only grad region can legally sit relative to `torch.inference_mode()`. That conclusion must not be promoted from an untracked/local file into frozen source authority.

### Required acceptance criteria

1. Resolve the actual production inference/closed-loop source to an immutable identity. Accept either:
   - a repo-relative path that exists at the exact reviewed root SHA or frozen Cosmos Gitlink; or
   - a separately versioned repository/file with an exact commit/blob SHA that is explicitly added to the source-audit provenance set.
2. Re-state Section 5 using exact `repo@commit:path:line` evidence from that immutable source for:
   - the HTTP/server entry;
   - lock/context-manager boundary;
   - `torch.no_grad()` / `torch.inference_mode()` nesting;
   - generation call;
   - rollout/env identity and done/reset fields actually available in the request path.
3. If those production scripts are local, deployment-only, generated, or otherwise cannot be frozen, change Section 5 from a positive current-fact conclusion to `UNRESOLVED/BLOCKED`: explicitly state that the current reviewed repos do not prove the production inference context and defer that seam to a later separately versioned inference Gate.
4. Do not run inference or modify production code to close this finding. A docs/provenance-only remediation is sufficient.
5. Preserve the current algorithm, training, loss/noise, chronology and CPU-core findings; do not reopen them unless the corrected immutable source contradicts them.
6. Keep all current authority boundaries: no Cosmos implementation, backend execution, torch runtime, GPU, training/evaluation/inference, optimizer/config refreeze, P4/P5 real operations or B2-T.

## Accepted source-audit findings

The following parts of `90bc09e` are accepted and should be retained:

1. **Current backend/runtime gap:** old `TTTLocalMemoryBackend` is not v0.2.1 implementation evidence; its detached/window-local state and surrogate inner objective require replacement.
2. **Trainer/TBPTT constraint:** current trainer backward occurs per microbatch, so a persistent graph cannot safely cross arbitrary packed microbatch boundaries; complete chronological segments must become backward atoms or an equivalent future design must prove the same semantics.
3. **CPU fast-core proposal:** four-member MLP fast-state pytree, learned Q/K/V/W0, per-sample feature-mean KVB, post-update read, whole-pytree reset/detach and exact slow/fast ownership are appropriate next-design subjects. Recommended `D_ttt`, `D_ff`, activation, dtype/precision, `inner_lr` and default TBPTT length remain proposals until the next implementation-design Gate freezes them.
4. **Native loss/noise audit:** current per-item noise path is reusable in principle when each chronological `(episode,t)` becomes an item; valid-step global numerator/denominator normalization still needs an explicit future adapter rather than reusing a naive microbatch scalar mean.
5. **Chronological ownership audit:** current independent window/pack path does not prove unique episode/transition fast-state ownership across packing, retries, epoch boundaries, workers/ranks and grad accumulation; the proposed fail-closed single-rank/segment design seam is appropriate.
6. **Gate split:** source audit -> CPU algorithm/gradient implementation design -> CPU functional contract -> chronology/loss integration design -> bounded runtime/GPU/inference gates -> optimizer/config authority rebuild is sufficiently conservative. Approval of any earlier stage must not imply later runtime authority.

## Scope

Do not issue `APPROVE_TO_DESIGN_R09_B_TTT_V02_CPU_ALGORITHM_IMPLEMENTATION` for source-audit SHA `90bc09e` yet. Close only the immutable production-inference provenance issue above and re-request review on a new technical SHA.

This review authorizes no Cosmos implementation, TTT backend execution, torch/model/data/checkpoint runtime access, GPU/CUDA/torchrun, training, evaluation, inference/inference smoke, optimizer/resolved-config refreeze, P4/P5 real operation, B2-T or formal Local Memory training.
