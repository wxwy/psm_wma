"""Legacy path reuse only when v2 source and output ownership agree."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from g2.io import ContractError, read_json, write_json
from g2.offline import atomic_6views_run as producer
from g2.tests.test_source_capsule import capsule_case


def test_legacy_view_path_accepts_only_signed_owned_v2_namespace(tmp_path, monkeypatch):
    _, target, _, spool, _ = capsule_case(tmp_path)
    root = Path(spool.source_policy["output_root"])
    monkeypatch.setattr(producer.plan, "OUTPUT", root)
    row = dict(
        task_class="NavigateKitchen",
        episode_id=0,
        expected_relative_output="tasks/NavigateKitchen/episodes/episode_000000",
    )
    cfg = SimpleNamespace(output_root=root, vae_spool=spool.root)

    # A freshly claimed empty output is safe, even when its name is legacy.
    assert not target.exists()
    producer._assert_profile_output_namespace(row, cfg)

    # A legacy/unowned output path is never silently upgraded.
    marker = root / ".g2_stage_a_dataset_root.json"
    original = read_json(marker)
    write_json(marker, dict(original, config_id="0" * 64))
    with pytest.raises(ContractError, match="not owned"):
        producer._assert_profile_output_namespace(row, cfg)
    write_json(marker, original)

    # A wrong relative episode target cannot escape the run-owned namespace.
    wrong = dict(row, expected_relative_output="tasks/Other/episodes/episode_000000")
    with pytest.raises(ContractError, match="not owned"):
        producer._assert_profile_output_namespace(wrong, cfg)

    # A worker without a signed v2 spool cannot reuse the old output path.
    cfg.vae_spool = None
    with pytest.raises(ContractError, match="owned"):
        producer._assert_profile_output_namespace(row, cfg)

    # Explicit new staging output remains supported without a new v2 exception.
    cfg.output_root = tmp_path / "independent_stage_a"
    assert producer._assert_profile_output_namespace(row, cfg) is None
