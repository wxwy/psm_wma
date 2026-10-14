# GPT Design r1 — V3 Packed128 Gate B1 real FSDP8 Transient Numerical Comparator

**Date:** 2026-10-14
**Author:** GPT (design/independent Gate authority; Owner final approval)
**Status:** \`B0_CPU_ACCEPTANCE_CLOSED / B1_DESIGN_PROPOSED / NUMERIC_THRESHOLDS_OWNER_SIGNOFF_PENDING / B1_GPU_NOT_AUTHORIZED / B1_RUNTIME_HARNESS_NOT_IMPLEMENTED / GATE_M_HOLD / FORMAL30K_HOLD\`.
**Authority:** Owner D1=A (Gate B/M split), D2=A (B0 CPU only), D3=A (both P0/P1 mandatory), D4=A (real GPU Terminal Partial P0/P1 mandatory). B0 closure \`docs/collab/chatgpt/reviews/2026-10-14_V3_Packed128_GateB0_CPU_final_closure_ec9d162b.md\`.
**Relation:** This is an incremental **B1 design**, not a re-review of unchanged implementation pairs or a runnable GPU instruction. Supersedes no frozen Round2 requirements in \`docs/collab/chatgpt/designs/2026-10-13_GPT_V3_Packed128_GateB_Round2_comparator_and_iter1300_migration_design.md\`.

## 0. Pinned identities and scope

| Leg | Exact Root implementation | Child/Gitlink | Meaning |
|---|---|---|---|
| Source Index8 | \`b159f45906f7261d028aecc226ab7f2bb9807eb9\` | \`937066ffd90f2bf783ad4fbb4909e9c0b8922982\` | Original formal writer, iter1300 authority |
| Target Packed128 | \`c4731bca1a590663db88bd6cd74dbcf9fd513a85\` | \`c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686\` | Gate A CPU accepted; GPU B1 unverified |
| B0 isolated diagnostic | \`ec9d162b926c4f197f5cfb692499b4dbda888686\` | separately isolated root | B0 CPU closed; **no functional GPU path** |
| FSP excluded | \`d45712a37318357ba2f57bde3d0f1f448aabbbd9\` | \`8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1\` | Not a B1 comparator leg |

Original \`iter_000001300\` DCP and all four components (model, optim, scheduler, trainer), eight rank-local dataloader sidecars and \`latest_checkpoint.txt\` remain **read-only**. Failed iter1400 excluded. Transient target state adaptation is **not Gate M persistent migration**; writing a new DCP to pass B1 is prohibited. No \`Trainer.train()\` / normal \`--phase resume\` from a manufactured namespace; these entrances may save, consult an unrelated latest pointer or reject old sidecar digest.

**B0 CPU result is accepted:** DS_PRO reported 30 pytest PASS/Ruff PASS/real source and target \`--verify-payloads --hash-all-shards\` exit0, matching whole \`payload_witness\` fingerprint \`f4dd11b5903401d0f36d563b1955a6859a502bd4291cc79f31fbbcb1233ffcdd\`, 8 ranks × two windows, terminal present, Index8 16+16 collective rhythm, immutable source DCP. The raw two ~2.2MB JSON blobs are archived **on DS host**, not independently uploaded to GitHub as of this design; DS reported SHA256 \`7df3b71413d0626ad1341f57c8031de5ce6cac0d994356c301b46a324ab0e46f\` / \`25fe68ed02d4a96b86e95f28a80766dcc7d1f51aa58ec0c84acaebc1bf3a76f1\`. Preserve local archive; do not reopen B0 solely to fetch them.

## 1. B1 required matrix (all four MUST pass; never only P0)

| Test profile | Full 8×16 member | Genuine Terminal Partial |
|---|---|---|
| P0 FIXED | required real FSDP8 | required real FSDP8 |
| P1 MATCHED_STOCHASTIC | required real FSDP8 | required real FSDP8 |

Under each setup: exact Source+Target 8-rank process topology; B8 T16 GA2 K4 raw15/state/left_wrist, each rank full n_g=128, n_window=256, while true terminal n_g can be <128 and n_window<256. Index8 uses index-major 16 Native forward/backward **per GA member**, Packed128 uses slot-major **one Native forward/backward per GA member**, hence **2 forward + 2 backward per rank / optimizer window** on Packed. One successful optimizer + scheduler update per GA2 window. The two successful, sequential optimizer steps after completed iter1300 are logically **1301 and 1302**; internal native training_step iteration argument must be verified rather than guessed. Repeat both legs under identical P0/P1 witness inputs; independently verify run-to-run stability. If actual iter1300 successor windows contain mixed full/terminal cases, an independent isolated rank-safe **full-only witness fixture** can establish Full parity; terminal must still be tested with real partial Consumers, not padded and not falsely described as official iter1301 rollout.

**If any Source rank's 16-step active-index collective rhythm differs from others, stop before the distributed train step.** B0's observed two successor windows are rhythm-safe, but every additional fixture must pass the same preflight; do not reduce full geometry, invent Consumers, avoid hard samples or force masks.

## 2. Why the existing CPU B0 harness is not B1

B0 \`tools/gates/v3_packed128_gateb_compare.py\` only verifies CPU payload/plan/schema and explicitly refuses \`--mode paired-run\` with exit2 \`GPU_B1_NOT_IMPLEMENTED_OR_AUTHORIZED\`. Its \`deterministic_witness_cpu(...P1,sigma...)\` correctly raises Blocked, as production distribution-matched sigma is not implemented. Never flip this guard to run GPU.

**New executable is only a proposed implementation target:** e.g. \`tools/gates/v3_packed128_gateb_fsdp8_transient.py\` on a new isolated diagnostic branch. It must be actually implemented and independently reviewed under its own new **exact** Root SHA before any request to authorize GPU. No development edits to frozen Source/Target child, training launcher, production model or checkpoint. Diagnostic hook/mapping code should be separate. CPU-only negative/API/mock tests may be run under an independently approved preparation scope; no real GPU execution or native full DCP load without a later Owner gate.

## 3. Real trainer API and one-step event contract (source checked)

Pinned child code paths:
- \`examples/psm_wma_robocasa_corrected_phase5.py\`: builds frozen Hydra config/corrected recipe, constructs model+planner+producer and \`GroupedLocalMemoryTrainer\`, then invokes \`trainer.train\` (normal save capable, **not permitted** for B1).
- \`cosmos_framework/trainer/local_memory_grouped.py:203–348\`: \`GroupedLocalMemoryTrainer.training_step\` is the authentic per-member entry; model receives \`model_ddp.training_step(batch, iteration, _local_memory_prefixes=prefixes)\`; backward uses \`grad_scaler.scale(weighted).backward\`; after GA1: \`grad_scaler.unscale_\` if enabled, finite grads, \`callbacks.on_before_optimizer_step\`, \`model.on_before_optimizer_step\`, \`window.finish(_optimizer_step_success)\`, after-commit callback, \`on_before_zero_grad\`, \`_zero_grad\`. This is the time/gradient contract; no surrogate loss/optimizer may replace it.
- Source \`cosmos_framework/model/generator/mot/local_memory_grouped_window.py\`: each T index gathers B active consumers and weights loss by \`len(batch.payloads)/plan.n_window\` (16 native calls per GA when max length16).
- Target same file: scans identical slot rows, \`pack_native_member\` gathers **all valid slot-major consumers**, weights once per GA by \`len(packed.payloads)/plan.n_window\`. S0 must have None Local prefix, other valid Consumers get current-scanned Local prefix without detach.
- \`cosmos_framework/trainer/local_memory_grouped_resume.py:93–201\`: actual \`restore_grouped_local_state\` enforces exact top-level 10 keys, rank profile, Frontier/scheduler consistency, nested \`SegmentProvenance.config_digest\`, four fp32 Fast State tensors and Local runtime ABI; **B0 structural probes did not substitute for real GPU restore**.
- \`cosmos_framework/checkpoint/dcp.py:818–1000\`: \`DistributedCheckpointer.load\` uses strict DCP model \`ModelWrapper\`, optimizer, scheduler, trainer RNG+GradScaler and dataloader callback. Its internal \`allow_partial_load=not strict_resume\` and model missing/unexpected key checks must be verified. The comparator must reproduce successful full four-component loading from original DCP, with equal optimizer selected parameter inventory and moments, and rank-local RNG/iteration. The dataloader sidecar target *memory-only* digest adaptation must be placed at the correct callback/load boundary, not handled by turning strict_resume off.
- The receipt/source gate indicates \`config_digest\` differs for Source/Target **by the layout authority**, not model parameters. Current original source digest \`70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37\`; honest Target digest \`1ab2bbe4df9954467bb0acf0d371dce40dff8bd04cfa3c81ca0ec6fe76a94b4a\`.

**Implementation must supply an auditable Source→actual function call map and callback timeline**, including exactly when gradients are read: **after full GA2 backward, after any unscale/production clipping hooks, immediately before optimizer.step, with identical timepoints**. To compare unmodified preclip gradients, capture a separate earlier snapshot before clipping. Never assert hooks are no-ops from default config alone: inspect fully resolved runtime callbacks.

## 4. RNG witness P0/P1 — explicit blocker until true site coverage

Source code checked:
- \`cosmos_framework/model/generator/diffusion/rectified_flow.py:13–160\` \`TrainTimeSampler\` distribution is configurable (uniform/logitnormal/waver/ltx2), with optional shift; deterministic mode uses an iteration/rank seeded Generator.
- \`cosmos_framework/model/generator/omni_mot_model.py:2138–2260\`: vision sigma may be [B,1] or [B,T_max] with diffusion forcing, shift may depend on effective tokens/resolution. \`:2261–2306\` action sigma can be separate if \`independent_action_schedule\` and must be indexed into action-bearing sample subset.
- \`omni_mot_model.py:2339–2608\`: \`_add_noise_to_input\` samples epsilon for enabled vision/action and potentially LiDAR/radar/sound, using native-batch iteration/rank generator when deterministic. This will **not** naturally match per Consumer across Source index-major and Target slot-major.
- Actual RoboCasa Transform CFG dropout uses Python \`random.random()\`, dataset configuration defaults include \`cfg_dropout_rate=0.1\`. The B0 CPU per-Consumer scoped CFG witness must be carried forward, with exact token bytes/masks.
- \`omni_mot_model.py:1750–2040\`: loss has vision/action weighting, optional auxiliary MoE load balancing and \`sample_level_loss_averaging\`, so numerical parity must verify *fully resolved* config and actual reduction semantics.

P0 sigma = exactly 0.5, epsilon = frozen per-consumer deterministic witness (constant zero or keyed normal, chosen and recorded **before** GPU data); CFG state/caption/payload identities match. P1 must sample **the real resolved production distribution** by key, applying actual vision/action shifts and per-item/per-frame geometry. Same canonical ConsumerKey + stochastic-site/index/subindex must give identical sigma/epsilon/CFG inputs in both legs; record sample count, tensor shape/dtype/value sha256, and an exhaustive site-miss/extra-draw counter. No global \`torch.rand*\` monkeypatch as a shortcut.

Allowed injection is transient, scoped to **precisely identified model-instance methods/stochastic call sites**, with try/finally restoration and no serialization/publication. Sample-level reordering must use Consumer identity rather than native batch index. A known unmet stochastic site => BLOCKED; P1 not automatically proven by CPU B0.

## 5. Proposed pre-registered numerical metrics — NEED OWNER FREEZE before GPU

The exact original Round2 §6 metrics and preliminary thresholds are **reproduced as candidate**, not silently treated as Owner-approved by D3/D4. Compare in float64 diagnostics but judge according to *actual storage dtype* and tensor role; every FQN/family must pass independently, never only global gradient norm or group average.

For A=Source, B=Target, d=B−A, n=numel:
- \`relL2 = ||d||2 / max(||A||2, ||B||2, epsilon_dtype*sqrt(n))\`
- \`elemPASS = all_i(abs(d_i) <= atol_dtype + rtol_dtype*abs(A_i))\`; \`maxAbs=max_i |d_i|\`.
- Normal tensors (both ||.||2>eps*sqrt(n)): require \`elemPASS AND relL2<=limit AND cosine>=minCos\`. Both near-zero: cosine=N/A, require \`maxAbs<=atol AND RMS(d)<=eps\`. Exactly one near-zero => FAIL; optimizer-required gradient \`None\` on either side, shape/dtype/FQN mismatch, NaN/Inf => FAIL.

| Tensor class | FP32/FP64 diagnostic candidate | BF16 candidate |
|---|---|---|
| Loss scalar, every active component after correct weighting | \`atol=1e-6, rtol=1e-5\` | \`atol=2e-2, rtol=2e-2\` |
| Per-element grad and fp32 Fast State | \`atol=1e-6, rtol=1e-4\` | \`atol=2e-2, rtol=2e-2\` |
| FQN grad/fast \`relL2\` | \`<=2e-3\` | \`<=3e-2\` |
| FQN grad/fast cosine | \`>=0.9999\` | \`>=0.999\` |
| Grad/fast norm floor \`epsilon_dtype\` | \`1e-7\` | \`2e-5\` |

**Not yet numerically frozen**: distinct scale of optimizer \`ΔParameter\`, moment1/moment2, and GradScaler/Scheduler state, plus selected-FQN exact inventory. Do NOT take the numeric table above as automatically sufficient for these; a gradient bound can be too lax for micro-updates and second moments. A complete **pre-GPU** decision must explicitly freeze: (1) which tensors are compared at which step, (2) a dtype-aware absolute/relative/near-zero delta policy that cannot pass simply because initial parameter norm dwarfs updates, (3) FP32 optimizer moment near-zero handling, (4) scheduler/LR/step counters and discrete state exactness, and (5) same-witness run2run stability thresholds. Owner must ratify the numerical acceptance spec before any GPU traces are generated. No posthoc tuning based on measured discrepancy; old V2 ~2.4% relative-L2 is NOT this V3 Gate criterion.

**Preliminary conservative policy direction (NOT accepted thresholds)**: compare each optimizer-selected FQN's **DeltaParameter** rather than full parameter, use the above normal/near-zero rules with epsilon scaled to actual Delta magnitude, compare FP32 Adam moments with their own near-zero-aware metric, and require scheduler integer steps/LR and Fast-State identity/frontier exactly where discrete. Submit a complete concrete rule with a CPU negative-fixture counterexample (e.g. a wrong tiny update must fail) before seeking numerical freeze.

## 6. FSDP8 evidence set; B1 not satisfied by simple test log

Must output per leg/profile/full-vs-terminal/run/step/rank, before any substantive comparison:
1. Exact triple SHA and imported module \`__file__\`; model/optimizer/GradScaler fully resolved config/dtype and selected FQN inventory. DCP 4 component metadata/fingerprints; actual strict load and no missing/unexpected FQN; rank-local dataloader/fast state real restore. No output/checkpoint job namespace writes.
2. Every GA native call count, effective Consumer identities, valid masks, Local prefix hashes (S0 None), sigma/noise/CFG values and site coverage; true \`n_g/N\` including partial; actual weighted component losses and aux, not merely total scalar.
3. Preclip, postclip/preoptimizer **all optimizer-selected FQN gradients**, including generation/action/local, null/nonfinite/nearzero; local shard DTensor metadata and selected reconstructed/full tensor cross-check. Require comparisons at identical callbacks/boundaries.
4. \`TTT inner_loss\`, all four fast-state FP32 tensors, Local prefix and higher-order local slow-gradient evidence, candidate vs committed frontier/sidecar/scheduler, only one actual optimizer/scheduler update per completed GA2.
5. Post-optimizer \`ΔParameter\`, Adam moments, LR, step counts and GradScaler; two consecutive steps with no checkpoint saving, no drift of Consumer/RNG witness state.
6. FSDP rank collective count/rhythm, CUDA errors/OOM/NCCL failures, max memory, wall timing; source before/after SHA256 and no modification to source/latest/formal Namespace.
7. Source vs Target per FQN machine-readable metrics (\`relL2,cos,maxAbs,near_zero,elemPASS\`), per family worst FQN, exact selected-inventory coverage; two runs per leg with identical witness check. Preserve raw tensor probes sufficient for audit, subject to practical size limits.

**No direct standard training runner:** B1 harness must drive reviewed authentic lower-level train-step/callback semantics and override any save path with a provably nonwriting barrier. If early load calls implicit out-of-namespace writes, fail closed.

## 7. Independent implementation+audit phases, none auto-authorize GPU

| Milestone | Owner/implementer deliverable | Required reviewer acceptance |
|---|---|---|
| B1-S0 design + threshold proposal | This source-checked design; proposed complete numerical tables and negative unit cases | Owner signs thresholds; GPT approves actual implementation plan |
| B1-S1 isolated implementation | Standalone audited harness, scoped stochastic hooks, official strict 4-component loader + in-memory Sidecar adapter, two-step/no-save driver, machine-readable metric collector | CPU static/API mocks/negative tests, import/SHA/purity checks, strict source-to-call time map |
| B1-S2 independent code review | **New implementation SHA** and CPU evidence, detailed GPT review under \`docs/collab/chatgpt/reviews/\` plus Inbox ledger | APPROVE_GPU_READINESS **only if** all safety/numeric/equivalence preconditions satisfied; not B1 PASS |
| B1-S3 Owner GPU authorization | Explicitly limited 8×H100 ephemeral proof (four required combinations; exact iteration, namespaces, time/VRAM limits, run count) | Owner authorization; DS_PRO executes validation-only (no production code changes) |
| B1-S4 evidence verdict | All 4 combinations, full FQN metrics, two-step update parity, source immutability, no missing RNG sites | GPT independent final \`B1_PASS\` or \`REQUEST_CHANGES/BLOCKED\` on exact pair |
| Gate M | Only after B1 PASS and *new* Owner consent | Separate migration code+review/strict resume; **never** part of B1 |

**Immediate action authorized by existing Owner D1–D4 is B1 non-GPU planning only, not a B1 GPU run.** Don't ask DS_PRO to execute tests until a complete, exact-SHA new B1 harness and CPU-safe testing plan exist. DS_PRO has already stopped B0 work; no new B0 validation required.

## 8. Known gaps / explicit blocking list

- B1 GPU comparator executable does **not yet exist**; the B0 \`paired-run\` denial remains mandatory. Do not claim runtime hook, DCP load, or gradient metric implementation has been reviewed just because the production source APIs above were inspected.
- P1 actual run-time resolved sampling distribution/shift, all enabled stochastic sites, real FSDP optimizer allowlist and GradScaler need runtime authority, not copied from generic defaults.
- Precise optimizer \`ΔP\` and moments acceptance thresholds are not approved by Owner; B1 **cannot** start GPU until the policy is completed/frozen.
- Two large raw B0 evidence JSONs are **on DS host local archive**, not verified as present on GitHub. Preserve them; their lack of remote byte access does not reopen closed B0.
- Numerical \`sample_level_loss_averaging\` or aux activation unresolved at actual model config => BLOCKED, never assert mathematical equivalence from nominal source defaults.
- No runtime implementation audit has been performed: implementation SHA is absent by design. Request a fresh GPT review **when code exists**, not a fabricated APPROVE of a nonexistent executable.

**Next Owner-facing decision:** Ratify the original Round2 §6 gradient/loss/Fast-State threshold table as the **baseline proposal**, subject to a separately completed concrete DeltaParameter/optimizer moment policy, and authorize isolated B1-S1 **implementation and CPU-only test** (not GPU). Alternatively return stricter requested numeric values. Only then commission the complete B1 comparator and independent code audit.
