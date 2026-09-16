#!/usr/bin/env python3
"""D6: active Local-Memory CPU/static smoke over the real libero4in1 latent cache.

Read-only, CPU-only, no checkpoint, no GPU, no trainer.  Opens the four LIBERO
suites, freezes one real ``ActiveWindowFreeze``, produces real ``SegmentBatch``es
from the exact-window latent cache, drives the real owner through
``admit -> begin -> prepare -> scan -> commit`` for every member of the frozen
window, closes it with ``finish_window``/``resolve_local_memory_slow_window``, and
asserts that the four canonical slow selector groups all reach the graph.

What this deliberately does NOT cover (deferred to D7, which needs the LLM):

* ``_run_active_local_memory_native_forward`` -- so the in-model
  "gathered tokens -> ``local_memory2llm``" wiring is only proven here given the
  tokens the scan produced, not that the model feeds them itself.
* The trainer transaction: ``active_seal``, the scaler preflight, the optimizer
  boundary, checkpointing.
* Slot rotation across many windows: D6 freezes exactly one window.  With
  ``--members`` equal to the window size it exercises every owner phase and the
  full ``finish_window``/``resolve`` close, but never a second window.
* The registry's model-consume / forward-publish leg (``consume_prepared_for_model``
  and ``publish_active_forward``), which needs a ``NativeBatchResult`` -- the LLM's
  own output, i.e. D7.

The window is walked as a stream (produce one member, walk it, release it).  A
member's payloads carry decoded video tensors, so retaining all 128 at once costs
~120 GB and gets the probe OOM-killed; production also holds one member at a time.
* Text tokenization.  ``tokenizer_config=None`` skips it, because the production
  tokenizer is loaded from ``EDGE_POLICY_CHECKPOINT``; the native collate path
  that consumes ``text_token_ids`` is a D7 concern, and nothing D6 asserts
  depends on it.

The suite-dataset kwargs below are transcribed from
``configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py``
``_suite_dataset`` (lines 135-181).  They are duplicated rather than imported
because ``_suite_dataset`` is a closure inside ``_action_policy_libero_edge_dataloader``
and importing the config module would drag in the whole experiment graph.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

import torch

# Resolve repo root and ensure project imports.
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "cosmos-framework"))

SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")

# v0.3.5-frozen local-memory hyper-parameters, mirroring the defaults at
# cosmos_framework/model/generator/mot/config_checkpoint_contract.py:88-97 and the
# production construction at omni_mot_model.py:415-431.
LOCAL_MEMORY_DIM = 32
LOCAL_HISTORY_EVIDENCE_DIM = 96
TTT_INNER_LR = 0.1
TTT_TBPTT_STEPS = 16
K_LOCAL = 1
VISUAL_SUMMARY_DIM = 96
PROJECTOR_OUT_DIM = 2048
MAX_ACTION_DIM = 64

# config_checkpoint_contract.SELECTORS, verbatim.
SLOW_SELECTORS = (
    "local_memory_runtime.evidence_encoder.",
    "local_memory_runtime.ttt_core.",
    "local_memory2llm.",
    "local_memory_modality_embed",
)


def _build_dataset(suite: str, *, libero_root: str, cache_root: str, max_episodes: int | None):
    from cosmos_framework.data.generator.action.datasets.action_sft_dataset import (
        get_action_libero_sft_dataset,
    )

    kwargs = {}
    if max_episodes is not None:
        kwargs["max_episodes"] = max_episodes
    return get_action_libero_sft_dataset(
        root=f"{libero_root}/{suite}",
        fps=20,
        chunk_length=16,
        image_size=256,  # concat_view -> 256x512
        mode="wam",
        camera_mode="concat_view",
        action_space="frame_wise_relative",
        rotation_space="6d",
        pose_coordinate_frame="native",
        action_normalization="quantile_rot",
        val_ratio=0.01,
        # D6 needs the map-style ActionSFTDataset the producer requires; the
        # production loader wraps it in the infinite ActionIterableShuffleDataset.
        iterable_shuffle=False,
        episode_shuffle_seed=42,
        resolution=None,
        max_action_dim=MAX_ACTION_DIM,
        cfg_dropout_rate=0.1,
        format_prompt_as_json=True,
        tokenizer_config=None,  # boundary: see module docstring
        local_dummy_enabled=False,
        local_dummy_tokens=1,
        local_dummy_dim=LOCAL_MEMORY_DIM,
        local_dummy_mode="normal",
        local_history_horizon=16,
        latent_cache_root=f"{cache_root}/{suite}",
        latent_cache_verify_ratio=0.0,  # pure cache mode; never fall back to the VAE
        **kwargs,
    )


def _local_memory_shim():
    """The four registered slow modules, constructed exactly as production does.

    The evidence encoder is *not* built with its class defaults: production passes
    ``evidence_dim=96`` while the default is ``256``, so a default-constructed
    encoder would silently be a different object than the route trains.
    """
    from cosmos_framework.model.generator.mot.local_evidence import (
        CANONICAL_EVIDENCE_FEATURE_CONFIG,
        ContinualTTTLocalMemoryCore,
        LocalEvidenceEncoder,
    )

    encoder = LocalEvidenceEncoder(
        evidence_dim=LOCAL_HISTORY_EVIDENCE_DIM,
        visual_dim=VISUAL_SUMMARY_DIM,
        feature_config=CANONICAL_EVIDENCE_FEATURE_CONFIG,
    )
    core = ContinualTTTLocalMemoryCore(
        evidence_dim=LOCAL_HISTORY_EVIDENCE_DIM,
        local_dim=LOCAL_MEMORY_DIM,
        inner_lr=TTT_INNER_LR,
        ttt_tbptt_steps=TTT_TBPTT_STEPS,
        k_local=K_LOCAL,
    )
    runtime = torch.nn.Module()
    runtime.evidence_encoder = encoder
    runtime.ttt_core = core
    net = torch.nn.Module()
    net.local_memory_runtime = runtime
    net.local_memory2llm = torch.nn.Linear(LOCAL_MEMORY_DIM, PROJECTOR_OUT_DIM)
    net.local_memory_modality_embed = torch.nn.Parameter(torch.zeros(PROJECTOR_OUT_DIM))
    model = torch.nn.Module()
    model.net = net
    return model


def _group_grad_state(inventory) -> dict[str, dict[str, int]]:
    """Bucket every slow parameter into its canonical selector group."""
    groups = {selector: {"params": 0, "nonzero": 0, "missing": 0} for selector in SLOW_SELECTORS}
    for name, parameter in inventory.items():
        for selector in SLOW_SELECTORS:
            if name.startswith(selector):
                entry = groups[selector]
                entry["params"] += 1
                if parameter.grad is None:
                    entry["missing"] += 1
                elif bool(parameter.grad.abs().sum() > 0):
                    entry["nonzero"] += 1
                break
        else:
            raise RuntimeError(f"slow parameter {name!r} matches no canonical selector")
    return groups


def _rss_gb() -> float:
    """Resident set size in GiB, read straight from /proc (no psutil dependency).

    The window walk is the first place this probe holds real decoded payloads, so
    the per-member cost is worth printing rather than guessing at.
    """
    statm = Path("/proc/self/statm").read_text().split()
    return int(statm[1]) * os.sysconf("SC_PAGE_SIZE") / 2**30


def _projector_loss(net, locals_) -> torch.Tensor:
    """Mirror ``build_memory_prefix_context``'s per-sample projector application.

    Production projects each consumer's ``[K_local, D_local]`` token and adds the
    modality embedding; the scan's raw ``[B, T, D]`` tensor is a different object
    and must not be fed to the projector directly.
    """
    present = [token for token in locals_ if token is not None]
    if not present:
        raise RuntimeError("member produced no Local token to project")
    modality = net.local_memory_modality_embed.float()
    return sum((net.local_memory2llm(token.float()) + modality).sum() for token in present)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--ga", type=int, default=16, help="window size = b_stream * ga")
    parser.add_argument("--b-stream", type=int, default=8)
    parser.add_argument("--members", type=int, default=1, help="how many members to produce")
    parser.add_argument("--max-episodes", type=int, default=None, help="cap per suite (smoke speed)")
    args = parser.parse_args()

    libero_root = os.environ.get("LIBERO_ROOT")
    cache_root = os.environ.get("LIBERO_LATENT_CACHE_ROOT")
    if not libero_root:
        raise RuntimeError("LIBERO_ROOT is required")
    if not cache_root:
        raise RuntimeError("LIBERO_LATENT_CACHE_ROOT is required")
    if args.b_stream < len(SUITES):
        raise ValueError(f"--b-stream must be >= {len(SUITES)}")

    window_members = args.b_stream * args.ga
    torch.manual_seed(0)
    torch.set_grad_enabled(True)

    report: dict[str, object] = {
        "libero_root": libero_root,
        "latent_cache_root": cache_root,
        "b_stream": args.b_stream,
        "ga": args.ga,
        "window_members": window_members,
        "ttt_tbptt_steps": TTT_TBPTT_STEPS,
        "suites": {},
    }

    # ---- 1. real datasets ---------------------------------------------------
    datasets = {}
    for suite in SUITES:
        dataset = _build_dataset(
            suite, libero_root=libero_root, cache_root=cache_root, max_episodes=args.max_episodes
        )
        datasets[suite] = dataset
        frame_source = dataset._dataset
        report["suites"][suite] = {
            "episodes": len(frame_source._ep_vals),
            "valid_samples": int(frame_source._valid_cum[-1]),
            "action_dim": int(frame_source.action_dim),
            "latent_cache_root": str(frame_source._latent_cache_root),
        }
        print(
            f"[1] {suite}: episodes={len(frame_source._ep_vals)} "
            f"valid_samples={int(frame_source._valid_cum[-1])} action_dim={int(frame_source.action_dim)}"
        )

    # ---- 2. real producers, router, stream catalog --------------------------
    from cosmos_framework.data.generator.action.datasets.canonical_local_memory_producer import (
        CanonicalLocalMemorySegmentProducer,
    )
    from cosmos_framework.model.generator.mot.active_local_memory_launch import (
        SuiteRoutedSegmentProducer,
        canonical_segment_adapter_from_model,
        canonical_segment_streams,
        canonical_slow_parameters_from_model,
    )

    digests = {
        "manifest_digest": os.environ.get("PSM_R09_B2_STREAM_MANIFEST_ROOT") or "libero4in1-4suite-manifest",
        "config_digest": "v035-frozen-local-ttt",
        "source_digest": cache_root,
    }
    producers = {
        suite: CanonicalLocalMemorySegmentProducer(
            datasets[suite], category=suite, ttt_tbptt_steps=TTT_TBPTT_STEPS, **digests
        )
        for suite in SUITES
    }
    router = SuiteRoutedSegmentProducer(producers, source_digest=cache_root)
    streams = canonical_segment_streams(producers, b_stream=args.b_stream)
    slots = Counter(stream.slot_id for stream in streams)
    report["stream_catalog"] = {
        "streams": len(streams),
        "per_category": dict(Counter(stream.category for stream in streams)),
        "slots_used": sorted(slots),
    }
    print(f"[2] stream catalog: {len(streams)} streams over {len(slots)} slots")
    for suite in SUITES:
        blocks = sum(producers[suite].block_count(stream) for stream in streams if stream.category == suite)
        print(f"    {suite}: streams={report['stream_catalog']['per_category'][suite]} whole_blocks={blocks}")

    # ---- 3. real owner chain ------------------------------------------------
    from cosmos_framework.model.generator.mot.active_local_memory_driver import (
        ActiveLocalMemoryWindowDriver,
    )
    from cosmos_framework.model.generator.mot.canonical_segment_runtime import (
        CanonicalSegmentRuntimeOwner,
    )
    from cosmos_framework.model.generator.mot.config_checkpoint_contract import canonical_slow_inventory
    from cosmos_framework.model.generator.mot.local_memory_segment import RankLocalSegmentScheduler
    from cosmos_framework.model.generator.mot.production_active_wiring import (
        ProductionActiveWiringRegistry,
    )
    from cosmos_framework.model.generator.mot.production_segment_wiring import CanonicalSegmentWiring

    model = _local_memory_shim()
    adapter = canonical_segment_adapter_from_model(model)
    slow = canonical_slow_parameters_from_model(model)
    # First argument is the *runtime* module: canonical_slow_inventory prefixes
    # every discovered leaf with "local_memory_runtime." itself, so passing the
    # net would double the prefix and fail the selector cover check.
    inventory = canonical_slow_inventory(
        model.net.local_memory_runtime,
        model.net.local_memory2llm,
        model.net.local_memory_modality_embed,
    )
    if {id(parameter) for parameter in slow} != {id(parameter) for parameter in inventory.values()}:
        raise RuntimeError("launch slow-parameter set disagrees with canonical_slow_inventory")

    wiring = CanonicalSegmentWiring(adapter, slow)
    scheduler = RankLocalSegmentScheduler(
        rank=0, target_distribution={suite: 1.0 / len(SUITES) for suite in SUITES}
    )
    registry = ProductionActiveWiringRegistry(CanonicalSegmentRuntimeOwner(scheduler, wiring))
    driver = ActiveLocalMemoryWindowDriver(
        registry=registry,
        producer=router,
        streams=streams,
        window_members=window_members,
    )
    report["slow_inventory"] = {
        selector: sum(1 for name in inventory if name.startswith(selector)) for selector in SLOW_SELECTORS
    }
    print(f"[3] slow inventory: {report['slow_inventory']}")

    # ---- 4. freeze one real window ------------------------------------------
    freeze = driver.freeze_window()
    plan = freeze.plan
    if plan.ga_effective != window_members:
        raise RuntimeError(f"frozen plan has ga_effective={plan.ga_effective}, expected {window_members}")
    if len(set(plan.members)) != window_members:
        raise RuntimeError("frozen plan contains duplicate members")
    distribution = Counter(identity.category for identity in freeze.identities)
    missing = [suite for suite in SUITES if distribution.get(suite, 0) <= 0]
    if missing:
        raise RuntimeError(f"frozen window never visits suites: {missing}")
    report["window"] = {
        "ga_effective": plan.ga_effective,
        "attempt": plan.attempt,
        "plan_chain_id": plan.plan_chain_id,
        "per_category": {suite: distribution.get(suite, 0) for suite in SUITES},
        "planned_n_valid": sorted(set(plan.planned_n_valid)),
    }
    print(f"[4] frozen window: ga_effective={plan.ga_effective} per_category={report['window']['per_category']}")

    # ---- 5..7. stream the window: produce -> backward -> successful_backward
    #            -> owner.commit, one member at a time ------------------------
    # Streaming, not produce-all-then-walk: a member's payloads carry decoded video
    # tensors, so retaining a whole 128-member window costs ~100 GB and gets the
    # probe OOM-killed (measured, see the rss trace below).  Production also holds
    # one member at a time, so streaming is the more faithful shape anyway.
    #
    # Member 0 is admitted through the registry, which validates that the plan's
    # exact first member is the one being prepared; later members go through
    # ``prepare_continuation``, which is what calls the owner's ``admit_next``.
    #
    # The registry's model-consume / forward-publish leg is deliberately skipped:
    # it needs a ``NativeBatchResult``, which is the LLM's own output and belongs
    # to D7.  The owner/transaction contract below is the part D6 can prove on CPU
    # -- and the walk itself is the point: whether the 128 members a frozen window
    # commits can actually be carried to the end by one transaction.
    losses: list[float] = []
    evidence_free_members: list[int] = []
    prepared = None
    for index in range(args.members):
        member = freeze.members[index]
        # Go through the driver's own production seam, NOT ``router.produce``
        # directly: ``_produce`` first calls ``_rebind_terminal`` when the member
        # rebinds a finished episode's slot.  ``scheduler.training_stream_end``
        # retires the whole slot on an episode's last block, and ``_is_admissible``
        # then rejects every successor until ``terminal_rebind`` clears it -- so
        # bypassing this seam makes the walk die ~2 windows in with
        # "no candidate is admissible for its stable stream slot".
        segment = driver._produce(freeze, index)
        actual = int(segment.consumer_valid.sum())
        planned = int(plan.planned_n_valid[index])
        if actual != planned:
            raise RuntimeError(f"member {index}: consumer_valid={actual} but plan planned {planned}")

        valid = segment.evidence_valid[0]
        if not bool(valid.any()):
            evidence_free_members.append(index)
        if index == 0:
            # The frozen geometry is only meaningful if the evidence really came off
            # the cache: an all-zero block means _load_cached_latent zero-filled.
            evidence = segment.evidence_visual_summary_prev[0][valid]
            if not bool(evidence.abs().sum() > 0):
                raise RuntimeError("member 0 evidence is all-zero: latent cache miss or zero-fill fallback")
            actions = segment.evidence_executed_action_prev[0][valid]
            if not bool(actions.abs().sum() > 0):
                raise RuntimeError("member 0 executed-action evidence is all-zero")
            report["evidence"] = {
                "valid_steps": int(valid.sum()),
                "visual_abs_sum": float(evidence.abs().sum()),
                "action_abs_sum": float(actions.abs().sum()),
                "visual_dim": int(evidence.shape[-1]),
                "action_dim": int(actions.shape[-1]),
            }
            print(f"[5] member 0: slot={member.stream.slot_id} suite={member.stream.category} "
                  f"episode={member.stream.episode_index} cursor={member.cursor} n_valid={actual}")
            print(f"[5] member 0 evidence: {report['evidence']}")

            prepared = registry.prepare_initial(freeze.identities[0], segment, plan, trainer_grad_accum_iter=0)
            transaction = prepared.transaction
            first = prepared.inputs
            if len(first.payloads) != planned:
                raise RuntimeError("gathered payload count disagrees with the frozen plan")
            report["owner"] = {
                "phase": prepared.owner.phase.name,
                "member_index": prepared.member_index,
                "payloads": len(first.payloads),
                "locals_present": sum(1 for token in first.locals if token is not None),
                "actual_n_valid": prepared.actual_n_valid,
            }
            print(f"[6] owner prepared: {report['owner']}")
        else:
            prepared = registry.prepare_continuation(
                freeze.identities[index], segment, transaction, trainer_grad_accum_iter=index
            )

        loss = _projector_loss(model.net, prepared.inputs.locals)
        loss.backward()
        losses.append(float(loss.detach()))
        # The trainer's order: the transaction records the successful backward (and
        # commits the scheduler chronology) *before* the owner commits the sidecar,
        # which is exactly what adapter.commit asserts.
        transaction.successful_backward(index, prepared.identity, prepared.actual_n_valid)
        prepared.owner.commit(transaction, prepared.forward)
        # Drop this member's graph-bearing handle before producing the next one.
        del segment, prepared
        if index % 16 == 15 or index == args.members - 1:
            print(f"[7] walked {index + 1}/{args.members} members, rss={_rss_gb():.2f} GB")
    owner = registry.owner
    committed = len(transaction.completed_members)
    if committed != args.members:
        raise RuntimeError(f"transaction committed {committed} of {args.members} members")
    report["walk"] = {
        "members": committed,
        "loss_first": losses[0],
        "loss_last": losses[-1],
        "phase_after_walk": owner.phase.name,
        "evidence_free_members": evidence_free_members,
        "rss_gb": _rss_gb(),
    }
    print(f"[7] walked {committed} members, phase={report['walk']['phase_after_walk']}, "
          f"loss {losses[0]:.4f} -> {losses[-1]:.4f}")

    # ---- 8. close the window only when the whole plan was walked ------------
    if args.members == window_members:
        completed = owner.finish_window(transaction)
        owner.resolve_local_memory_slow_window(completed, scaler_skipped=False)
        if owner.phase.name != "IDLE":
            raise RuntimeError(f"owner did not return to IDLE: {owner.phase.name}")
        report["window_closed"] = {
            "slow_optimizer_steps": transaction.slow_optimizer_steps,
            "slow_grads_cleared": transaction.slow_grads_cleared,
            "scheduler_committed": len(scheduler.committed_identities),
        }
        print(f"[8] window closed: {report['window_closed']}")
    else:
        report["window_closed"] = None
        print(f"[8] partial window ({args.members}/{window_members}); finish_window not exercised")

    # ---- 9. every slow group reached the graph, and the clear covers all ----
    groups = _group_grad_state(inventory)
    report["grads"] = {"groups": groups}
    for selector, entry in groups.items():
        print(f"[9] {selector:44s} params={entry['params']:3d} nonzero={entry['nonzero']:3d} missing={entry['missing']:3d}")
    if any(entry["params"] == 0 for entry in groups.values()):
        raise RuntimeError(f"a canonical slow group holds no parameter: {groups}")
    if any(entry["missing"] or not entry["nonzero"] for entry in groups.values()):
        raise RuntimeError(f"not every canonical slow group reached the graph: {groups}")
    wiring.clear_local_slow_grads()
    leftover = [name for name, parameter in inventory.items() if parameter.grad is not None]
    if leftover:
        raise RuntimeError(f"clear_local_slow_grads left gradients on: {leftover}")
    report["clear_local_slow_grads"] = {"cleared": len(inventory), "leftover": 0}
    print(f"[9] clear_local_slow_grads cleared all {len(inventory)} slow parameters")

    report["result"] = "PASS"
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f"[out] wrote {args.output_json}")
    print("PASS: active Local-Memory CPU/static smoke completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
