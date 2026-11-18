"""Create validated, paired R1/R2 recipes from an immutable G2 data snapshot.

The G1 real checkpoint/config, G1 text tokenizer, and G1 original partition
are mandatory sources. Training budgets MUST be supplied explicitly; no
implicit 'formal' step counts or speculative hyperparameter schedules.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from cosmos_framework.data.generator.action.utils.static_task_text import (
    StaticTaskTextRecipe,
)
from cosmos_framework.model.generator.mot.g2_contracts import GlobalMemoryConfig
from cosmos_framework.trainer.g2_training import (
    G2TrainingPlan,
    GroupSchedule,
    validate_comparison_plans,
)
from examples.psm_wma_robocasa_g2_recipe import G2RunRecipe
from g2.data.episode_state import atomic_write_json, digest, require_regular
from g2.data.verified_provider import open_verified_snapshot


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    for name in (
        "snapshot-root",
        "g1-verified-index-root",
        "data-c-root",
        "state15-root",
        "view-root",
        "initial-language-root",
        "g1-config",
        "g1-checkpoint",
        "edge-tokenizer-dir",
        "output-dir",
    ):
        p.add_argument("--" + name, type=Path, required=True)
    for name in (
        "stage-a-steps",
        "stage-b-steps",
        "target-effective-consumers",
        "b-stream",
        "grad-accum-steps",
        "world-size",
        "save-iter",
    ):
        p.add_argument("--" + name, type=int, required=True)
    p.add_argument("--initial-language-recipe-id", required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    if args.output_dir.exists():
        raise FileExistsError("G2 paired recipe output directory must be new")
    for name in (
        "stage_a_steps",
        "stage_b_steps",
        "target_effective_consumers",
        "b_stream",
        "grad_accum_steps",
        "world_size",
        "save_iter",
    ):
        if type(getattr(args, name)) is not int or getattr(args, name) <= 0:
            raise ValueError(name + " must be a positive integer")
    if args.save_iter > args.stage_a_steps + args.stage_b_steps:
        raise ValueError("save interval exceeds requested training length")
    receipt = open_verified_snapshot(
        args.snapshot_root,
        g1_index_root=args.g1_verified_index_root,
        data_c_root=args.data_c_root,
    )
    if receipt["language_recipe_id"] != args.initial_language_recipe_id:
        raise ValueError("training language identity differs from certification")
    required = (
        args.g1_config,
        args.g1_checkpoint / "model/.metadata",
        args.edge_tokenizer_dir / "text_tokenizer/tokenizer.json",
    )
    for path in required:
        require_regular(path)
    g1_config_sha = digest(args.g1_config)
    g1_dcp_sha = digest(args.g1_checkpoint / "model/.metadata")
    text_tokenizer_sha = digest(
        args.edge_tokenizer_dir / "text_tokenizer/tokenizer.json"
    )
    text = StaticTaskTextRecipe(
        planned_video_frames=17,
        fps=20.0,
        height=256,
        width=512,
        tokenizer_identity=text_tokenizer_sha,
        cfg_dropout_rate=0.1,
    )
    # Group clocks, not wall-clock global steps. Warmup and decay are disabled
    # by the user's first-run decision, with no mid-stage schedule resets.
    total = args.stage_a_steps + args.stage_b_steps
    constant = GroupSchedule(
        warmup_steps=0,
        decay="constant",
        min_factor=1.0,
        horizon_steps=total,
    )
    provider_kwargs = dict(
        snapshot_root=str(args.snapshot_root),
        g1_verified_index_root=str(args.g1_verified_index_root),
        data_c_root=str(args.data_c_root),
        state15_root=str(args.state15_root),
        view_root=str(args.view_root),
        initial_language_root=str(args.initial_language_root),
        initial_language_recipe_id=args.initial_language_recipe_id,
    )
    recipes = {}
    for name in ("R1", "R2"):
        enabled = name == "R2"
        training = G2TrainingPlan(
            profile=name,
            init_checkpoint_identity=g1_dcp_sha,
            data_identity=receipt["data_identity"],
            split_identity=receipt["split_identity"],
            text_recipe_identity=text.identity,
            state15_recipe_identity=receipt["snapshot"]["state15_recipe_id"],
            stage_a_steps=args.stage_a_steps,
            stage_b_steps=args.stage_b_steps,
            target_effective_consumers=args.target_effective_consumers,
            b_stream=args.b_stream,
            grad_accum_steps=args.grad_accum_steps,
            world_size=args.world_size,
            global_schedule=constant if enabled else None,
            gen_schedule=constant,
            action_schedule=constant,
        )
        recipe = G2RunRecipe(
            training=training,
            text=text,
            global_memory=GlobalMemoryConfig(
                enabled=enabled, top_view_variant="with_robot"
            ),
            alignment_version=receipt["snapshot"]["alignment_version"],
            view_recipe_id=receipt["snapshot"]["view_recipe_id"] if enabled else None,
            provider_factory="g2.data.verified_provider:open_verified_provider",
            provider_kwargs=provider_kwargs,
            g1_config_path=str(args.g1_config),
            g1_config_sha256=g1_config_sha,
            save_iter=args.save_iter,
        )
        recipe.g1_snapshot()
        recipe.check_init_checkpoint(args.g1_checkpoint)
        recipes[name] = recipe
    pair = validate_comparison_plans(recipes["R1"].training, recipes["R2"].training)
    args.output_dir.mkdir(parents=True)
    for name, recipe in recipes.items():
        atomic_write_json(
            args.output_dir / (name.lower() + "_g2_recipe.json"), asdict(recipe)
        )
    atomic_write_json(
        args.output_dir / "PAIR_RECEIPT.json",
        {
            "schema": "g2_paired_training_recipes_v1",
            "r1_identity": recipes["R1"].identity,
            "r2_identity": recipes["R2"].identity,
            "source_snapshot_identity": receipt["snapshot_identity"],
            "g1_model_metadata_sha256": g1_dcp_sha,
            "g1_config_sha256": g1_config_sha,
            "language_recipe_id": receipt["language_recipe_id"],
            "text_recipe_identity": text.identity,
            "constant_group_lr": True,
            "warmup_steps": 0,
            "decay": "constant",
            "requested_budget": {
                "stage_a_steps": args.stage_a_steps,
                "stage_b_steps": args.stage_b_steps,
                "target_effective_consumers": args.target_effective_consumers,
                "b_stream": args.b_stream,
                "grad_accum_steps": args.grad_accum_steps,
                "world_size": args.world_size,
            },
            "pair": pair,
            "evidence_scope": "formal_source_bound_run_recipes_not_started",
        },
    )
    print(
        "G2_R1_R2_RECIPES_CREATED",
        json.dumps(
            {
                "r1": str(args.output_dir / "r1_g2_recipe.json"),
                "r2": str(args.output_dir / "r2_g2_recipe.json"),
                "same_data_identity": receipt["data_identity"],
                "same_original_g1_split": receipt["split_identity"],
                "text_recipe_identity": text.identity,
                "constant_lr": True,
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
