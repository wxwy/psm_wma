"""Reproduce a CPU-only synthetic protocol example, never real acceptance data.

This diagnostic intentionally imports test fixtures. Production and readers do
not import this module, and it cannot replace the four real GPT-server samples.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from g2.io import read_json, write_json
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    # Explicit diagnostic import; no renderer, VAE, MuJoCo or ROS execution.
    from g2.tests.test_stage_a_package import stage_case

    profile = OutputProfile(selection_top_variant="clean")
    kwargs, _ = stage_case(args.output / "fixture", profile)
    episode = args.output / "example_episode"
    manifest = package_stage_a(destination=episode, **kwargs)
    state = manifest["states"][0]
    task = read_json(episode / "task_entities.json")["sets"][
        state["task_entity_set_id"]
    ]
    language = read_json(episode / "language.json")
    text = language["texts"][language["states"][0]["text_id"]]
    example = dict(
        example_kind="SYNTHETIC_CPU_PROTOCOL_NOT_ROBOCASA_ACCEPTANCE",
        state=state,
        GT_TaskEntitySet=task,
        candidate_text=text,
        spatial_metadata=read_json(episode / state["spatial_metadata"]),
    )
    write_json(args.output / "protocol_example.json", example)
    print(
        json.dumps(
            dict(
                status="SYNTHETIC_PROTOCOL_WRITTEN",
                output=str(args.output),
                state_count=manifest["state_count"],
                profile_complete=manifest["profile_complete"],
                training_ready=False,
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
