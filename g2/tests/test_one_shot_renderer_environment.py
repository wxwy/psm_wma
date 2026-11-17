"""Independent reviewer regression: GT worker and F27 renderer must share MuJoCo compiler/runtime."""

import os
from types import SimpleNamespace

from g2.offline.full_production import Supervisor, isolated_env
from g2.tests.test_one_shot_supervisor import config_case


def test_gt_worker_inherits_renderer_dependencies_and_consumer_does_not(
    tmp_path, monkeypatch
):
    cfg, _ = config_case(tmp_path)
    assert cfg["renderer_pythonpath"]
    overlay = cfg["renderer_pythonpath"][0]
    assert overlay not in isolated_env(cfg)["PYTHONPATH"].split(os.pathsep)
    assert overlay in isolated_env(cfg, renderer=True)["PYTHONPATH"].split(os.pathsep)
    captured = {}

    def pretend_start(command, *, env, run_id, cwd, stdout=None):
        captured.update(env=env, run_id=run_id)
        return SimpleNamespace(poll=lambda: 0, wait=lambda: 0)

    import g2.offline.process_control as proc

    monkeypatch.setattr(proc, "start_owned", pretend_start)
    supervisor = Supervisor(cfg, None, [])
    result = supervisor.worker(["python", "-c", "pass"])
    assert result.returncode == 0
    assert overlay in captured["env"]["PYTHONPATH"].split(os.pathsep), (
        "GT compiler source worker must use same pinned MuJoCo deps as child F27 renderer",
        captured["env"]["PYTHONPATH"],
    )
