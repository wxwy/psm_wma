"""Public config/preview and real frozen Store identity, without hardware."""

import copy
import json

import pytest
import yaml

from cosmos_framework.evaluation.robocasa_v2.contract import build_manifest
from cosmos_framework.evaluation.robocasa_v2.store import Store
from robocasa_eval_v2.cli import main
from robocasa_eval_v2.config import execution, resolve
from tools.v3.eval_v2_batch_tests.shared_vae_topology_test import topology
from tools.v3.eval_v2_production_tests.contract_test import manifest
from tools.v3.eval_v2_production_tests.entry_test import config


@pytest.mark.parametrize(
    "servers,sims,batch", [(1, 1, 1), (1, 8, 8), (2, 8, 8), (3, 3, 5), (2, 32, 8)]
)
def test_public_yaml_preview_uses_same_streaming_slots_for_arbitrary_legal_topologies(
    tmp_path, capsys, servers, sims, batch
):
    path, paths = config(tmp_path)
    cfg = topology(tmp_path, servers, sims, batch, streaming=True)
    cfg.update({k: v for k, v in paths.items() if k not in ("gpu_ids", "schema")})
    cfg["episodes_per_task"] = 50
    path.write_text(yaml.safe_dump(cfg))
    args, resolved = resolve(["dry-run", "--config", str(path)])
    assert resolved["single_latency_arm"] is None
    assert execution(resolved)["shared_vae"]["worker"]["bmax"] == 1
    assert main(["dry-run", "--config", str(path)]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["physical_slot_capacity"] == servers * sims
    assert len(preview["used_gpus"]) == servers
    assert preview["models_loaded"] == preview["environments_created"] == 0
    assert not (tmp_path / "out").exists()


def make_manifest(cfg):
    old = manifest()
    return build_manifest(
        tasks=old["tasks"],
        episodes=old["episodes_per_task"],
        seed=old["seed"],
        horizons=old["horizons"],
        experiment=old["experiment"],
        execution=execution(cfg),
    )


@pytest.mark.parametrize(
    "field",
    ["sims_per_gpu", "max_infer_batch_size", "batch_wait_ms", "worker_resources"],
)
def test_shared_history_keeps_full_resume_identity_and_never_adopts_changed_m_or_b(
    tmp_path, field
):
    cfg = topology(tmp_path, 2, 4, 4)
    original = make_manifest(cfg)
    store = Store(tmp_path / "run", original)
    store.create()
    with Store(store.root, copy.deepcopy(original)).locked():
        pass
    changed = copy.deepcopy(cfg)
    if field == "worker_resources":
        changed["sim_shared_vae"]["resources"]["vae_startup_rss_bytes"] += 1
    else:
        changed[field] += 1
    candidate = make_manifest(changed)
    assert candidate["digest"] != original["digest"]
    before = {str(p): p.read_bytes() for p in store.root.rglob("*") if p.is_file()}
    with pytest.raises(ValueError, match="identity mismatch"):
        with Store(store.root, candidate).locked():
            pass
    assert before == {
        str(p): p.read_bytes() for p in store.root.rglob("*") if p.is_file()
    }
