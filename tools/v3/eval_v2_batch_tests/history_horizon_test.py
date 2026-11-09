"""Configuration/Manifest H authority and current Native shared-Worker CPU probes."""

import copy

import pytest
import yaml

from cosmos_framework.evaluation.robocasa_v2.contract import (
    ACTION_CHUNK_SIZE,
    canonical,
    validate_manifest,
)
from cosmos_framework.inference.robocasa_session_transactions_test import (
    clock_kernel as clock_kernel,
)
from robocasa_eval_v2.config import DEFAULTS, execution, resolve
from tools.v3.eval_v2_batch_tests.history_k_test import frozen
from tools.v3.eval_v2_batch_tests.shared_vae_routing_test import info, rig_for
from tools.v3.eval_v2_batch_tests.shared_vae_test import profile_config
from tools.v3.eval_v2_production_tests.entry_test import config


@pytest.mark.parametrize("choice", ["omitted", None, ACTION_CHUNK_SIZE])
def test_public_resolution_uses_Action_Chunk_not_episode_horizon_and_dense_identity(
    tmp_path, choice
):
    path, inputs = config(tmp_path)
    cfg = {**profile_config(tmp_path), **inputs}
    cfg.pop("local_ttt_history_k", None)
    if choice != "omitted":
        cfg["local_ttt_history_k"] = choice
    path.write_text(yaml.safe_dump(cfg))
    _, resolved = resolve(["fresh", "--config", str(path)])
    assert DEFAULTS["local_ttt_history_k"] is None
    assert resolved["local_ttt_history_k"] == ACTION_CHUNK_SIZE
    expected = copy.deepcopy(resolved)
    expected["local_ttt_history_k"] = None
    m = frozen(resolved)
    assert canonical(m) == canonical(frozen(expected))
    assert "local_ttt_history_k" not in execution(resolved)
    m["horizons"]["CloseFridge"] = 12
    from cosmos_framework.evaluation.robocasa_v2.contract import digest

    m["digest"] = digest({n: v for n, v in m.items() if n != "digest"})
    assert validate_manifest(m)["protocol"]["action_chunk_size"] == ACTION_CHUNK_SIZE
    assert resolved["local_ttt_history_k"] != m["horizons"]["CloseFridge"]


def test_policy_H_is_compared_to_frozen_protocol_before_worker_start(tmp_path):
    with rig_for(tmp_path, 1, 1, False, history_k=4) as rig:
        worker = rig.runtime.workers[0]
        clock = next(iter(rig.actors.values())).clock_domain
        wrong = info(clock, 4)
        wrong["action_chunk_size"] = (
            12  # K4 divides both12 and16; matching K alone is insufficient.
        )
        with pytest.raises(ValueError, match="Action Horizon"):
            rig.supervisor.ensure(worker, wrong)
        assert not rig.runtime.commands and not rig.supervisor.handles
        handle = rig.supervisor.ensure(worker, info(clock, 4))
        assert (
            handle.public["action_chunk_size"]
            == handle.proof["action_chunk_size"]
            == ACTION_CHUNK_SIZE
        )
