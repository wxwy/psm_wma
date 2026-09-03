# ChatGPT Independent Review — R09-B TTT v0.2 inference-provenance remediation

Date: 2026-09-03

## Verdict

**APPROVE_TO_DESIGN_R09_B_TTT_V02_CPU_ALGORITHM_IMPLEMENTATION**

This verdict applies **only** to implementation/remediation SHA:

`39ec772720603ce9cae98b7e30cb41c10437f64e`

with root submodule/Gitlink:

`cosmos-framework = 21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

Observed `V2` request/ledger HEAD at review start:

`b3b9a4e764a0aa032ace6efd86abf1d717b31213`

`b3b9a4e...` is a review-request/ledger commit whose parent is `39ec772...`; it is **not** the implementation SHA and does not inherit or substitute for this verdict.

## Freshness / identity check

The reviewer environment attempted to establish a local checkout/fetch path, but direct container GitHub DNS was unavailable. Freshness was therefore independently established through the live GitHub connector immediately before review: branch `V2` resolved to `b3b9a4e...`, parent `39ec772...`. The exact root `cosmos-framework` submodule entry at `39ec772...` resolves to `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

Review baseline for the prior blocking verdict:

`90bc09e9117a8aabab144007aa82d2771e21fc0f`

The prior ChatGPT verdict on that SHA was `REQUEST_CHANGES` with one HIGH blocker: production inference-context evidence was not tied to resolvable immutable source identities.

## Materials reviewed

- `docs/collab/chatgpt/CODEX_INBOX.md`
- `docs/build/PSM-WMA_R09_B_TTT_source_audit_v0.2_2026-09-03.md`
- prior ChatGPT review `docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v02_source_audit_90bc09e.md`
- `TODO.md`
- `SESSION.md`
- exact Cosmos tracked sources under Gitlink `21d064f2...`

No GPU, training, evaluation, inference, model/checkpoint loading, or production execution was used for this review.

## HIGH-1 closure

**CLOSED.** The remediation now binds Section 5 to three exact tracked Cosmos blobs, and each identity was independently resolved at Gitlink `21d064f2...`:

| source | audited blob SHA | independent result |
| --- | --- | --- |
| `cosmos_framework/scripts/action_policy_server_libero.py` | `9ef6845ade715dbe617f2c7e98553251929ae4b7` | MATCH |
| `cosmos_framework/simulation/libero/closed_loop_eval.py` | `b31a3fc7f9d3b10b47cf3a429a7b785cd31e6918` | MATCH |
| `cosmos_framework/model/generator/omni_mot_model.py` | `89d1d32ddd2f906ee118e2dbe6d0bd71be8dd2b1` | MATCH |

The production-context claims are also source-consistent:

1. `closed_loop_eval.py:235-295` constructs the serial/batch HTTP payload from `image`, `prompt`, `domain_name`, and `image_size` and calls `/predict` or `/predict_batch`.
2. `action_policy_server_libero.py:866-881` validates those same request fields.
3. `action_policy_server_libero.py:931-966` and `:979-1068` place model generation under `self._lock` and then `torch.inference_mode()`.
4. `omni_mot_model.py:2878-2879` directly decorates `generate_samples_from_batch()` with `@torch.no_grad()`; no `generator_mixin.py` authority is required.
5. `omni_mot_model.py:4210-4238` consumes caller-provided `data_batch["local_memory"]` and aligns it with `sequence_plan.has_local_memory`; this supports the audit's proposed seam at the server lock boundary before the existing `torch.inference_mode()` region.
6. `closed_loop_eval.py:1193-1263` rebuilds `active`/`cur` slot lists as environments finish, confirming that active-slot compaction occurs and that HTTP batch position cannot safely serve as persistent rollout identity.

Accordingly, the previous provenance defect was documentary/source-identity related rather than evidence of a contradictory production call graph, and `39ec772...` fixes it without changing Cosmos tracked code or the Gitlink.

## Accepted source-audit conclusions retained

The earlier accepted parts of `90bc09e...` remain unchanged and accepted for the purpose of advancing to the next **design-only** Gate:

- current ordinary 128-window packing plus immediate per-microbatch backward is insufficient for a configurable exact TBPTT segment;
- the proposed fast state remains a four-member functional MLP pytree with learned Q/K/V/W0, per-sample feature-mean KVB update, post-update read, whole-tree reset/detach and explicit slow/fast ownership;
- `ttt_tbptt_steps` is a single positive configurable truncation length, default `16`; truncation detaches graph while preserving state value;
- native per-item Cosmos noise may remain per valid item, but valid-step global numerator/denominator normalization needs a later integration Gate;
- inference persistent state currently lacks a stable owner because request schema does not carry rollout/env identity, executed action, control step, or reset/done authority;
- chronology/loss/runtime integration, inference state registry, GPU smoke, training authority, and production execution remain separate Gates.

## Authorization boundary

This approval authorizes **only** the next versioned CPU algorithm/gradient implementation **design** and its CPU-only contract-test design.

It does **not** authorize:

- implementation or execution of the new TTT backend in Cosmos;
- chronology/loss/runtime integration;
- production request-schema or server-state-registry implementation;
- torch/model/data/checkpoint runtime execution for this Gate;
- GPU/CUDA/torchrun;
- training, evaluation, inference, or inference smoke;
- optimizer/resolved-config refreeze;
- P4/P5 real preflight, staging, record/refreeze, export or compose;
- B2-T or formal Local Memory training.

Any implementation/remediation commit after `39ec772...` requires a fresh same-SHA review. This approval must not be reused for a later SHA.
