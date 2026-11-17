"""View-first source compression and strict canonical output namespace."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from g2.io import read_json, write_json
from g2.latent_cache.contract import CacheError
from g2.offline import atomic_6views_run as producer
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a, validate_profile_episode
from g2.offline.view_only_source import (
    CLAIM,
    FULL,
    PACKED,
    RECEIPT,
    claim_view_only_root,
    load_working_source,
    verify_view_only_claim,
)
from g2.tests.test_stage_a_package import stage_case


def test_view_only_uses_lossless_compressed_source_and_all_required_products(tmp_path):
    profile = OutputProfile(selection_top_variant="clean", view_vae=False)
    kwargs, _ = stage_case(tmp_path, profile)
    target = tmp_path / "published"
    result = package_stage_a(destination=target, **kwargs)
    assert result["profile_complete"]
    assert not (target / FULL).exists()
    assert (target / PACKED).is_file() and (target / RECEIPT).is_file()
    manifest = validate_profile_episode(target)
    assert manifest["profile_complete"] and manifest["products"]["view_vae"] == "disabled"
    for name in ("task_entities.json", "language.json", "episode_manifest.json"):
        assert (target / name).is_file()
    assert list(target.glob("state_*/spatial_metadata.json"))
    assert list(target.glob("state_*/scene_graph.json.gz"))
    assert list(target.glob("state_*/*.png")) or list(target.glob("state_*/*/*.png"))
    source, sha = load_working_source(target)
    assert source["source_id"] == manifest["source_id"]
    assert sha == read_json(target / "SPATIAL_SOURCE_READY.json")["source_manifest_sha256"]
    assert "stage_static" in json.dumps(source)
    # Reopening an episode never rewrites it.
    assert validate_profile_episode(target) == manifest


def test_compressed_source_bad_bytes_or_receipt_never_validate(tmp_path):
    profile = OutputProfile(selection_top_variant="clean", view_vae=False)
    kwargs, _ = stage_case(tmp_path, profile)
    target = tmp_path / "published"
    package_stage_a(destination=target, **kwargs)
    archive = target / PACKED
    original = archive.read_bytes()
    archive.write_bytes(original + b"unexpected")
    with pytest.raises(CacheError, match="compressed source bytes"):
        validate_profile_episode(target)
    archive.write_bytes(original)
    receipt = read_json(target / RECEIPT)
    write_json(target / RECEIPT, dict(receipt, raw_sha256="0" * 64))
    with pytest.raises(CacheError, match="receipt identity"):
        validate_profile_episode(target)


def test_canonical_legacy_path_requires_new_explicit_view_only_claim(tmp_path, monkeypatch):
    root = tmp_path / "canonical"
    monkeypatch.setattr(producer.plan, "OUTPUT", root)
    profile = OutputProfile(selection_top_variant="clean", view_vae=False)
    row = dict(
        task_class="NavigateKitchen",
        episode_id=7,
        expected_relative_output="tasks/NavigateKitchen/episodes/episode_000007",
    )
    cfg = SimpleNamespace(output_root=root, vae_spool=None, output_profile=profile)
    with pytest.raises(Exception, match="claim"):
        producer._assert_profile_output_namespace(row, cfg)
    claim_view_only_root(root, profile, "a" * 64)
    assert verify_view_only_claim(root, profile)["profile_id"] == profile.to_dict()["profile_id"]
    assert producer._assert_profile_output_namespace(row, cfg) is None
    assert claim_view_only_root(root, profile, "a" * 64)
    with pytest.raises(CacheError, match="different source"):
        claim_view_only_root(root, profile, "b" * 64)
    cfg.output_profile = OutputProfile(selection_top_variant="both", view_vae=False)
    with pytest.raises(CacheError, match="exact profile"):
        producer._assert_profile_output_namespace(row, cfg)
    cfg.output_profile = profile
    (root / CLAIM).unlink()
    with pytest.raises(CacheError):
        claim_view_only_root(root, profile, "a" * 64)


def test_unclaimed_preexisting_legacy_content_never_upgraded(tmp_path):
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "episode_manifest.json").write_text("{}")
    profile = OutputProfile(selection_top_variant="clean", view_vae=False)
    with pytest.raises(CacheError, match="unowned"):
        claim_view_only_root(root, profile, "a" * 64)
    assert not (root / CLAIM).exists()
