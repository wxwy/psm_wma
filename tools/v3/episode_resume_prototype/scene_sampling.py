"""Non-production scene-seed plan. Never imports or launches a simulator.

New logical episodes use independently seeded, freshly constructed environments.
This is not restoration of the legacy environment's sequential RNG stream.
"""

from __future__ import annotations

import copy
import hashlib
import json

SAMPLER_VERSION = "psm_robocasa_independent_episode_seed_v1"


def _integer(value, field):
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a nonnegative integer")
    return value


def derive_episode_seed(*, requested_seed, task, logical_episode_index):
    """Stable uint32 environment seed; nonce, execution order and GPU are absent."""
    _integer(requested_seed, "requested_seed")
    _integer(logical_episode_index, "logical_episode_index")
    if (
        not isinstance(task, str)
        or not task.strip()
        or task != task.strip()
        or task in {".", ".."}
        or any(value in task for value in ("/", "\\", "\0"))
    ):
        raise ValueError("task must be one unambiguous underlying task name")
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


def plan_scene_sampling(*, task, requested_seed, new_logical_indices, attempt_nonce, legacy_sources=()):
    """Return a JSON plan only. Legacy sources are opaque, immutable references.

    ``source_episode=0`` is the future one-episode physical attempt's local index;
    it never rewrites the original attempt-local Episode/C01 identity.
    ``attempt_nonce`` records the new attempt but does not alter a slot's seed.
    """
    if not isinstance(attempt_nonce, str) or not attempt_nonce.strip() or len(attempt_nonce) > 256:
        raise ValueError("attempt_nonce must be a nonempty bounded provenance string")
    indices = list(new_logical_indices)
    for index in indices:
        _integer(index, "logical_episode_index")
    if len(indices) != len(set(indices)):
        raise ValueError("duplicate new logical Episode indices")
    # Validate seed/task even when no new episodes are needed. Do not change old
    # UNKNOWN/None seeds to the newly requested seed or a guessed derived value.
    derive_episode_seed(requested_seed=requested_seed, task=task, logical_episode_index=0)
    preserved = copy.deepcopy(list(legacy_sources))
    if not all(isinstance(source, dict) for source in preserved):
        raise ValueError("legacy_sources must contain explicit source records")
    json.dumps(preserved, ensure_ascii=False, allow_nan=False)
    episodes = []
    for index in sorted(indices):
        episodes.append(
            {
                **derive_episode_seed(requested_seed=requested_seed, task=task, logical_episode_index=index),
                "attempt_nonce": attempt_nonce,
                "source_episode": 0,
                "reset_plan": {
                    "environment_lifecycle": "fresh_environment_per_new_episode",
                    "constructor_seed_argument": "effective_seed",
                    "public_reset_calls": 1,
                    "source_episode": 0,
                    "constructor_rng_draws": "UNOBSERVED",
                    "local_memory": "fresh_episode_session_begin_end",
                    "historical_rng_state_restored": False,
                },
            }
        )
    warnings = [
        "DERIVED_ENVIRONMENT_SEED_IS_NOT_THE_REQUESTED_BASE_SEED",
        "NOT_HISTORICAL_RNG_STREAM_CONTINUATION",
        "DISTINCT_PHYSICAL_SCENES_NOT_GUARANTEED",
    ]
    seen = {}
    for episode in episodes:
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
        "schema": "psm_episode_resume_scene_plan_prototype_v1",
        "prototype_only": True,
        "sampler_version": SAMPLER_VERSION,
        "task": task,
        "requested_seed": requested_seed,
        "legacy_sources": preserved,
        "new_episodes": episodes,
        "warnings": list(dict.fromkeys(warnings)),
        "benchmark_qualification": "Independent-scene convenience plan; not a continuous legacy/base-seed benchmark",
    }
