"""Scene execution plans. Never imports or launches a simulator.

Fresh tasks retain the literal task seed and one environment's consecutive resets.
Only true resume gaps use independent seeds when the historical RNG is unavailable.
"""

from __future__ import annotations

import copy
import hashlib
import json

from . import bounded_episode_index, bounded_records

SAMPLER_VERSION = "psm_robocasa_independent_episode_seed_v1"
FRESH_SAMPLER_VERSION = "legacy_task_stream"


def _integer(value, field):
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a nonnegative integer")
    return value


def _task(task):
    if (
        not isinstance(task, str)
        or not task.strip()
        or task != task.strip()
        or task in {".", ".."}
        or any(value in task for value in ("/", "\\", "\0"))
    ):
        raise ValueError("task must be one unambiguous underlying task name")


def derive_episode_seed(*, requested_seed, task, logical_episode_index):
    """Stable gap seed; nonce, execution order and GPU are absent."""
    _integer(requested_seed, "requested_seed")
    bounded_episode_index(logical_episode_index)
    _task(task)
    material = {
        "sampler_version": SAMPLER_VERSION,
        "requested_seed": requested_seed,
        "task": task,
        "logical_episode_index": logical_episode_index,
    }
    encoded = json.dumps(material, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    digest = hashlib.sha256(encoded).hexdigest()
    return {
        "requested_seed": requested_seed,
        "seed_family": {"requested_seed": requested_seed, "sampler_version": SAMPLER_VERSION},
        "effective_seed": int(digest[:8], 16),
        "seed_material_sha256": digest,
        "task": task,
        "logical_episode_index": logical_episode_index,
    }


def plan_scene_sampling(*, task, requested_seed, new_logical_indices, attempt_nonce, sampling_mode, legacy_sources=()):
    """Return a JSON plan only. Legacy sources are opaque, immutable references.

    Caller supplies already-verified completed historical sources. Fresh mode
    never derives a seed: one batch owns the literal seed and N public resets.
    Gap mode maps each logical slot to a separate physical Episode0 attempt.
    Neither path rewrites the original attempt-local Episode/C01 identity.
    ``attempt_nonce`` records the new attempt but does not alter a slot's seed.
    """
    if not isinstance(attempt_nonce, str) or not attempt_nonce.strip() or len(attempt_nonce) > 256:
        raise ValueError("attempt_nonce must be a nonempty bounded provenance string")
    indices = bounded_records(new_logical_indices, "new logical indices")
    for index in indices:
        bounded_episode_index(index)
    if len(indices) != len(set(indices)):
        raise ValueError("duplicate new logical Episode indices")
    # Validate seed/task even when no new episodes are needed. Do not change old
    # UNKNOWN/None seeds to the newly requested seed or a guessed derived value.
    _integer(requested_seed, "requested_seed")
    _task(task)
    preserved = copy.deepcopy(bounded_records(legacy_sources, "legacy sources"))
    if not all(isinstance(source, dict) for source in preserved):
        raise ValueError("legacy_sources must contain explicit source records")
    json.dumps(preserved, ensure_ascii=False, allow_nan=False)
    if sampling_mode not in {"fresh_task_stream", "resume_gap_independent"}:
        raise ValueError("sampling_mode must explicitly select fresh_task_stream or resume_gap_independent")
    fresh = sampling_mode == "fresh_task_stream"
    if fresh and (preserved or sorted(indices) != list(range(len(indices)))):
        raise ValueError("fresh task requires no completed historical sources and consecutive logical slots from zero")
    if not fresh and not preserved:
        raise ValueError("resume gap requires verified completed historical sources; use fresh mode for a new task")
    episodes, batches = [], []
    sampler = FRESH_SAMPLER_VERSION if fresh else SAMPLER_VERSION
    for physical, index in enumerate(sorted(indices)):
        identity = (
            {
                "requested_seed": requested_seed,
                "seed_family": {"requested_seed": requested_seed, "sampler_version": sampler},
                "effective_seed": requested_seed,
                "seed_material_sha256": None,
                "task": task,
                "logical_episode_index": index,
            }
            if fresh
            else derive_episode_seed(requested_seed=requested_seed, task=task, logical_episode_index=index)
        )
        source_episode = physical if fresh else 0
        batch_index = 0 if fresh else physical
        episode = {
            **identity,
            "attempt_nonce": attempt_nonce,
            "sampling_mode": sampling_mode,
            "source_episode": source_episode,
            "execution_batch": batch_index,
            "reset_plan": {
                "environment_lifecycle": "shared_task_environment_continuous_resets"
                if fresh
                else "fresh_environment_per_new_episode",
                "constructor_seed_argument": "effective_seed",
                "public_reset_calls": 1,
                "public_reset_ordinal": source_episode,
                "source_episode": source_episode,
                "constructor_rng_draws": "UNOBSERVED",
                "local_memory": "fresh_episode_session_begin_end",
                "historical_rng_state_restored": False,
            },
        }
        episodes.append(episode)
        if not fresh or not batches:
            batches.append(
                {
                    "batch_index": batch_index,
                    "sampling_mode": sampling_mode,
                    "effective_seed": episode["effective_seed"],
                    "environment_constructions": 1,
                    "public_reset_calls": 0,
                    "episodes": [],
                }
            )
        batches[batch_index]["episodes"].append({"logical_episode_index": index, "source_episode": source_episode})
        batches[batch_index]["public_reset_calls"] += 1
    warnings = (
        []
        if fresh
        else [
            "DERIVED_ENVIRONMENT_SEED_IS_NOT_THE_REQUESTED_BASE_SEED",
            "NOT_HISTORICAL_RNG_STREAM_CONTINUATION",
            "DISTINCT_PHYSICAL_SCENES_NOT_GUARANTEED",
        ]
    )
    seen = {}
    for episode in () if fresh else episodes:
        previous = seen.setdefault(episode["effective_seed"], episode["logical_episode_index"])
        if previous != episode["logical_episode_index"]:
            warnings.append("UINT32_DERIVED_SEED_COLLISION")
    known_legacy_seeds = {
        source["effective_seed"]
        for source in preserved
        if type(source.get("effective_seed")) is int and source["effective_seed"] >= 0
    }
    if known_legacy_seeds & set(seen):
        warnings.append("DERIVED_SEED_MATCHES_A_KNOWN_LEGACY_ENVIRONMENT_SEED")
    return {
        "schema": "psm_episode_resume_scene_plan_v1",
        "production_wired": True,
        "sampler_version": sampler,
        "sampling_mode": sampling_mode,
        "task": task,
        "requested_seed": requested_seed,
        "legacy_sources": preserved,
        "new_episodes": episodes,
        "execution_batches": batches,
        "warnings": list(dict.fromkeys(warnings)),
        "benchmark_qualification": "UNCHANGED_TASK_LITERAL_SEED_SEQUENTIAL_RESET_PROTOCOL"
        if fresh
        else "Independent-scene convenience plan; not a continuous legacy/base-seed benchmark",
    }
