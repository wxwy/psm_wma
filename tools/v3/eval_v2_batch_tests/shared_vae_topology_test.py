"""Issue27 configuration is generic; example topologies are not a whitelist."""

import copy
import random

import pytest

from cosmos_framework.evaluation.robocasa_v2.contract import (
    STREAMING_SCHEDULE,
    build_manifest,
    validate_manifest,
)
from robocasa_eval_v2 import shared_vae
from robocasa_eval_v2.config import execution
from robocasa_eval_v2.resources import physical_slots, render_slots
from tools.v3.eval_v2_batch_tests.shared_vae_test import profile_config
from tools.v3.eval_v2_production_tests.contract_test import manifest


def topology(
    tmp_path, servers=1, sims=1, policy_batch=1, *, streaming=False, same_render=False
):
    cfg = profile_config(tmp_path)
    cfg.update(
        single_latency_arm=None,
        gpu_ids=list(range(10, 10 + servers)),
        render_gpu_ids=[20 if same_render else 20 + i for i in range(servers)],
        sims_per_gpu=sims,
        max_infer_batch_size=policy_batch,
        batch_wait_ms=0,
    )
    if streaming:
        cfg["scheduling_protocol"] = STREAMING_SCHEDULE
        cfg["streaming_resources"] = {
            k: v
            for k, v in cfg["sim_shared_vae"]["resources"].items()
            if not k.startswith("vae_")
        }
    return cfg


@pytest.mark.parametrize(
    "servers,sims,batch",
    [
        (1, 1, 1),
        (1, 8, 8),
        (2, 8, 8),
        (1, 2, 2),
        (1, 4, 3),
        (2, 2, 4),
        (3, 3, 5),
        (4, 2, 8),
    ],
)
def test_shared_topology_is_config_driven_without_single_measurement_arm(
    tmp_path, servers, sims, batch
):
    cfg = topology(tmp_path, servers, sims, batch)
    shared_vae.validate_profile(cfg)
    assert cfg["single_latency_arm"] is None and shared_vae.enabled(cfg)
    assert len(physical_slots(cfg, 128)) == servers * sims
    assert len(set(render_slots(cfg, 128).values())) == servers
    old = manifest(episodes=1)
    m = build_manifest(
        tasks=old["tasks"],
        episodes=1,
        seed=old["seed"],
        horizons=old["horizons"],
        experiment=old["experiment"],
        execution=execution(cfg),
        local_memory="required",
    )
    assert validate_manifest(m) == m
    assert "single_latency" not in m["execution"]
    assert m["execution"]["shared_vae"]["worker"]["bmax"] == 1


def test_random_and_streaming_capacity_boundaries_are_not_topology_enumerations(
    tmp_path,
):
    rng = random.Random(27)
    for streaming, maximum in [(False, 8), (True, 32)]:
        for servers, sims, batch in [
            (1, 1, 1),
            (4, maximum, 8),
            *[
                (rng.randint(1, 4), rng.randint(1, maximum), rng.randint(1, 8))
                for _ in range(12)
            ],
        ]:
            cfg = topology(
                tmp_path, servers, sims, batch, streaming=streaming, same_render=True
            )
            shared_vae.validate_profile(cfg)
            assert len(physical_slots(cfg, 128)) == servers * sims
            assert set(render_slots(cfg, 128).values()) == {20}


@pytest.mark.parametrize(
    "change", ["off", "vae4", "vae8", "policy9", "fractional_timeout", "phase_a"]
)
def test_generic_profile_preserves_required_mode_and_existing_capacity_guards(
    tmp_path, change
):
    cfg = topology(tmp_path, 2, 8, 8)
    if change == "off":
        cfg["local_memory_mode"] = "off"
    elif change in ("vae4", "vae8"):
        cfg["sim_shared_vae"]["bmax"] = int(change[-1])
    elif change == "policy9":
        cfg["max_infer_batch_size"] = 9
    elif change == "fractional_timeout":
        cfg["terminate_grace_s"] = 10.5
    else:
        cfg["execution_profile"] = "phase_a"
    with pytest.raises(ValueError):
        shared_vae.validate_profile(cfg)


@pytest.mark.parametrize("arm", ["A", "B", "C"])
def test_single_measurement_profile_identity_remains_exact(tmp_path, arm):
    cfg = profile_config(tmp_path, arm)
    old = copy.deepcopy(execution(cfg))
    shared_vae.validate_profile(cfg)
    assert execution(cfg) == old and "shared_vae" not in execution(cfg)
