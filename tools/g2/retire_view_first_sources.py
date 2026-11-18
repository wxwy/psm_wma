"""Plan or explicitly retire independently verified View-first VAE sources.

Never loads a VAE, renderer, MuJoCo or raw RoboCasa source. Use isolated samples
until independent Gates A-D pass; this command does not authorize corpus GC.
"""

import argparse
import json
from pathlib import Path


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset-root", type=Path, required=True)
    p.add_argument("--spool-root", type=Path, required=True)
    p.add_argument("--source-policy", type=Path, required=True)
    p.add_argument("--recipe-id", required=True)
    p.add_argument("--task", action="append")
    p.add_argument("--episode", type=int, action="append")
    p.add_argument("--expected-episodes", type=int)
    p.add_argument(
        "--resume",
        action="store_true",
        help="repair prior owned retirement intents before inspecting source manifests",
    )
    action = p.add_mutually_exclusive_group(required=True)
    action.add_argument("--plan", action="store_true")
    action.add_argument("--execute", action="store_true")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        from g2.io import read_json
        from g2.latent_cache.builder import discover_episodes, verify_episode
        from g2.latent_cache.final_source import PROFILE_SCHEMA
        from g2.latent_cache.posthoc import (
            LIFECYCLE,
            coordinator,
            resume_retirement,
            retire_view_first_cache,
        )
        from g2.latent_cache.retirement_policy import (
            POSTHOC_SCHEMA,
            validate_policy,
            validate_target,
        )
        from g2.latent_cache.storage import build_lock
        from g2.latent_cache.streaming import EventSpool
        from g2.offline.stage_a import validate_profile_episode

        policy = validate_policy(read_json(args.source_policy), args.spool_root)
        if (
            policy["schema"] != POSTHOC_SCHEMA
            or Path(policy["output_root"]) != args.dataset_root.absolute()
        ):
            raise ValueError(
                "retirement requires the explicit matching View-first dataset policy"
            )
        if args.expected_episodes is not None and args.expected_episodes <= 0:
            raise ValueError("expected episode count must be positive")
        if (args.spool_root / "config.json").exists():
            spool = EventSpool.open(args.spool_root)
            if (
                spool.lifecycle != LIFECYCLE
                or spool.source_policy != policy
                or spool.recipe["recipe_id"] != args.recipe_id
            ):
                raise ValueError("existing retirement spool scope/recipe differs")
            with spool._db() as db:
                pending = [
                    dict(r)
                    for r in db.execute("SELECT target,scope FROM jobs WHERE done>=1")
                ]
            for row in pending:
                scope = json.loads(row["scope"])
                task, ep = scope["episode_key"].split("/")
                if (args.task and task not in args.task) or (
                    args.episode
                    and int(ep.removeprefix("episode_")) not in args.episode
                ):
                    continue
                if not args.execute or not args.resume:
                    print(
                        json.dumps(
                            dict(
                                status="PENDING_OWNED_TRANSACTION",
                                target=row["target"],
                                resume_required=True,
                            )
                        )
                    )
                    return 75
                with build_lock(coordinator(row["target"])):
                    if not resume_retirement(
                        row["target"],
                        args.spool_root,
                        policy,
                        expected_recipe_id=args.recipe_id,
                    ):
                        return 75
        episodes = discover_episodes(
            args.dataset_root, tasks=args.task, episodes=args.episode
        )
        if (
            args.expected_episodes is not None
            and len(episodes) != args.expected_episodes
        ):
            raise ValueError(
                "selected episode count differs; no new retirement started"
            )
        rows = []
        for root in episodes:
            manifest = validate_profile_episode(root)
            if manifest["output_profile"]["view_vae"]:
                raise ValueError("explicit View-first profile required")
            validate_target(
                policy,
                root,
                dict(
                    episode_key=f"{manifest['task_class']}/episode_{manifest['episode_id']:06d}",
                    profile_id=manifest["output_profile"]["profile_id"],
                ),
            )
            if args.plan:
                rows.append(
                    dict(
                        episode_root=str(root),
                        audit=verify_episode(root, expected_recipe_id=args.recipe_id),
                        source_retired=manifest["schema"] == PROFILE_SCHEMA,
                    )
                )
            else:
                result = retire_view_first_cache(
                    root,
                    spool_root=args.spool_root,
                    source_policy=policy,
                    expected_recipe_id=args.recipe_id,
                )
                rows.append(dict(episode_root=str(root), **result))
                if not result.get("complete"):
                    print(json.dumps(dict(status="PENDING", results=rows)))
                    return 75
        print(
            json.dumps(
                dict(
                    schema="g2_view_first_retirement_cli_v1",
                    action="plan" if args.plan else "retire",
                    episode_count=len(rows),
                    results=rows,
                    vae_loaded=False,
                    training_ready=False,
                ),
                sort_keys=True,
            )
        )
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps(dict(status="REJECTED", error=str(exc)), sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
