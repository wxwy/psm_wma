"""Independent G2 episode-static enhanced language (no Stage A rerender/reencode).

Use --mode preview for human review, --mode write for an isolated recipe-versioned
episode artifact, or --mode verify to regenerate and check an existing artifact.
Input is the sealed original frame-0 SG/task roles and actual verified 20Hz
G1 instruction. Does NOT edit View/SG/VAE/legacy language.json/DATA_C.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from g2.data.episode_state import VerifiedRawEpisodes, canonical
from g2.language.initial_context import (
    InitialLanguageRecipe,
    load_initial_episode_language,
    verify_persisted_initial_language,
    write_initial_language,
)


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-root", required=True, type=Path)
    p.add_argument("--g1-verified-index", required=True, type=Path)
    p.add_argument("--g1-cache-root", required=True, type=Path)
    p.add_argument("--views-root", required=True, type=Path)
    p.add_argument("--output-root", required=True, type=Path)
    p.add_argument("--mode", choices=("preview", "write", "verify"), required=True)
    scope = p.add_mutually_exclusive_group(required=True)
    scope.add_argument("--task-class")
    scope.add_argument("--all-ready", action="store_true")
    p.add_argument("--episodes", type=int, nargs="+")
    p.add_argument("--max-episodes", type=int, default=None)
    p.add_argument("--max-characters", type=int, default=4096)
    p.add_argument("--max-candidates-per-group", type=int, default=4)
    p.add_argument("--fail-on-existing", action="store_true")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    if args.task_class and not args.episodes:
        raise ValueError("one --task-class requires explicit --episodes")
    if args.all_ready and args.episodes is not None:
        raise ValueError("--all-ready must not receive --episodes")
    if args.max_episodes is not None and args.max_episodes <= 0:
        raise ValueError("--max-episodes must be positive")
    for required in (
        args.source_root,
        args.g1_verified_index,
        args.g1_cache_root,
        args.views_root,
    ):
        if not required.is_dir():
            raise FileNotFoundError(required)
    resolved = args.output_root.resolve()
    restricted = [
        args.views_root.resolve(),
        args.source_root.resolve(),
        args.g1_cache_root.resolve(),
        args.g1_verified_index.resolve(),
    ]
    if any(resolved == r or resolved.is_relative_to(r) for r in restricted):
        raise ValueError(
            "independent language output root must not be inside producer/G1 input"
        )
    if args.mode != "preview" and args.output_root.is_symlink():
        raise ValueError("language output root cannot be a symlink")

    recipe = InitialLanguageRecipe(
        max_characters=args.max_characters,
        max_candidates_per_group=args.max_candidates_per_group,
    )
    source = VerifiedRawEpisodes(
        args.source_root, args.g1_verified_index, args.g1_cache_root
    )
    if args.mode != "preview":
        from g2.data.episode_state import atomic_write_json

        identity = args.output_root / "OUTPUT_IDENTITY.json"
        expected_root = {
            "schema": "g2_independent_language_root_v2",
            "source_binding_digest": source.source_binding,
            "evidence_scope": "full_map_frame0_gt_review_only",
            "training_ready": False,
        }
        if identity.exists():
            stored = json.loads(identity.read_text())
            if (
                stored.get("schema")
                not in {
                    "g2_independent_language_root_v1",
                    "g2_independent_language_root_v2",
                }
                or stored.get("source_binding_digest") != source.source_binding
            ):
                raise ValueError("independent language output source binding drift")
            if args.mode == "write" and stored != expected_root:
                # Migrate only the old root inventory, never alter any
                # independently sealed episode/recipe payload.
                atomic_write_json(identity, expected_root)
        elif args.mode == "write":
            atomic_write_json(identity, expected_root)
        else:
            raise ValueError("cannot verify an uninitialized language output root")
        recipe_manifest = (
            args.output_root / "recipes" / recipe.recipe_id / "RECIPE.json"
        )
        expected_recipe = {
            "schema": "g2_initial_language_recipe_declaration_v1",
            "recipe": recipe.to_dict(),
            "source_binding_digest": source.source_binding,
            "training_ready": False,
        }
        if recipe_manifest.exists():
            if json.loads(recipe_manifest.read_text()) != expected_recipe:
                raise ValueError("versioned initial language recipe changed")
        elif args.mode == "write":
            atomic_write_json(recipe_manifest, expected_recipe)
        else:
            raise ValueError("initial language version not published")
    if args.all_ready:
        candidates = sorted(
            (p.parents[2].name, int(p.parent.name.split("_")[-1]))
            for p in args.views_root.glob("tasks/*/episodes/episode_*/COMPLETE.json")
        )
    else:
        candidates = [(args.task_class, ep) for ep in sorted(set(args.episodes))]
    if args.max_episodes is not None:
        candidates = candidates[: args.max_episodes]
    if not candidates:
        raise ValueError("no explicitly selected completed episodes")
    success = 0
    errors = []
    # Don't create output folders when only previewing: preview is read-only.
    for task, ep in candidates:
        try:
            original = source.read(task, ep)
            record = load_initial_episode_language(
                view_root=args.views_root,
                raw_source=original,
                recipe=recipe,
            )
            if args.mode == "write":
                result = write_initial_language(
                    args.output_root,
                    record,
                    resume=not args.fail_on_existing,
                )
            elif args.mode == "verify":
                result = verify_persisted_initial_language(args.output_root, record)
            else:
                result = {"path": "NOT_WRITTEN", "text_id": record["text_id"]}
            success += 1
            if args.mode == "preview":
                print(
                    json.dumps(
                        {
                            "task_class": task,
                            "episode_index": ep,
                            "recipe_id": recipe.recipe_id,
                            "text_id": record["text_id"],
                            "original_instruction": record["original_instruction"],
                            "augmented_instruction": record["augmented_instruction"],
                            "ambiguity": record["scene_context"]["ambiguity"],
                            "omitted": record["scene_context"][
                                "number_of_omitted_facts"
                            ],
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
            else:
                print(
                    f"INITIAL_LANGUAGE_{args.mode.upper()}_PASS",
                    task,
                    ep,
                    result["text_id"],
                    flush=True,
                )
        except Exception as exc:
            errors.append(
                {
                    "task_class": task,
                    "episode_index": ep,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            print("INITIAL_LANGUAGE_ERROR", task, ep, errors[-1]["error"], flush=True)
    print(
        "INITIAL_LANGUAGE_SUMMARY",
        json.dumps(
            {
                "mode": args.mode,
                "selected": len(candidates),
                "success": success,
                "failed": len(errors),
                "recipe_id": recipe.recipe_id,
                "review_not_training_ready": True,
                "errors": errors[:20],
                "run_identity": canonical(
                    {
                        "recipe_id": recipe.recipe_id,
                        "source_binding_digest": source.source_binding,
                    }
                ),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
