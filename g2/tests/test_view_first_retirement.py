"""Reuse final-v2 retirement after genuine posthoc cache completion."""

from pathlib import Path

import pytest

from g2.io import digest
from g2.latent_cache import final_source as final
from g2.latent_cache.builder import verify_episode
from g2.latent_cache.posthoc import build_view_first_cache, retire_view_first_cache
from g2.latent_cache.retirement_policy import POSTHOC_SCHEMA
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a, validate_profile_episode
from g2.offline.view_only_source import (
    CLAIM,
    FULL,
    PACKED,
    RECEIPT,
    claim_view_only_root,
    load_working_source,
)
from g2.tests.test_stage_a_package import stage_case
from g2.tests.test_view_vae_builder import PREPROCESS, FakeEncoder


def retirement_case(tmp_path, *, compressed=True):
    profile = OutputProfile(selection_top_variant="clean", view_vae=False)
    kwargs, _ = stage_case(tmp_path, profile)
    output = tmp_path / "dataset"
    claim_view_only_root(output, profile, "a" * 64)
    root = output / "tasks/NavigateKitchen/episodes/episode_000000"
    package_stage_a(destination=root, compress_source=compressed, **kwargs)
    policy = dict(
        schema=POSTHOC_SCHEMA,
        format="capsule_v2",
        output_root=str(output),
        work_root=str(tmp_path / "unused_work"),
        spool_root=str(tmp_path / "retirement_spool"),
        config_id="a" * 64,
        mapping_sha256="b" * 64,
        source_versions=dict(root="1" * 40, child="2" * 40, nav="3" * 40),
        protected_roots=[
            str(Path(__file__).resolve().parents[2]),
            str(kwargs["inputs"].parent),
            str(kwargs["rendered"]),
        ],
        keep_full_audit=False,
        audit_archive_root=None,
        audit_retention_policy=None,
        view_first_claim_sha256=digest(output / CLAIM),
    )
    return root, policy


def encode_case(tmp_path, root):
    return build_view_first_cache(
        root,
        FakeEncoder(),
        spool_root=tmp_path / "encode_spool",
        preprocessing=PREPROCESS,
    )


@pytest.mark.parametrize("compressed", [True, False])
def test_posthoc_retirement_preserves_profiles_products_and_payload_bytes(
    tmp_path, compressed
):
    root, policy = retirement_case(tmp_path, compressed=compressed)
    original = validate_profile_episode(root)
    source, raw_sha = load_working_source(root)
    encode_case(tmp_path, root)
    payloads = {
        str(p.relative_to(root)): digest(p) for p in (root / "vae_cache").rglob("*.pt")
    }
    result = retire_view_first_cache(
        root, spool_root=policy["spool_root"], source_policy=policy
    )
    assert result["complete"]
    final_manifest = validate_profile_episode(root)
    assert final_manifest["schema"] == final.PROFILE_SCHEMA
    assert final_manifest["output_profile"] == original["output_profile"]
    assert final_manifest["products"] == original["products"]
    assert (
        final_manifest["states"] == original["states"]
        and final_manifest["files"] == original["files"]
    )
    assert final_manifest["posthoc_vae_receipt"]["verified"]
    assert payloads == {p: digest(root / p) for p in payloads}
    assert all(digest(root / p) == sha for p, sha in original["files"].items())
    for name in (FULL, PACKED, RECEIPT, "SPATIAL_SOURCE_READY.json"):
        assert not (root / name).exists()
    capsule = final.load_capsule(root)
    assert (
        capsule["source_id"] == source["source_id"]
        and capsule["working_source"]["raw_source_sha256"] == raw_sha
    )
    assert verify_episode(root, reencoder=FakeEncoder())["max_abs_error"] == 0
    assert retire_view_first_cache(
        root, spool_root=policy["spool_root"], source_policy=policy
    )["already_complete"]
    encoder = FakeEncoder(fail_at=1)
    assert build_view_first_cache(
        root,
        encoder,
        spool_root=tmp_path / "not_created",
        preprocessing=PREPROCESS,
        resume=True,
    )["already_complete"]
    assert encoder.calls == 0 and not (tmp_path / "not_created").exists()
    assert not (root.parents[3] / ".g2_source_retention_policy.json").exists()


@pytest.mark.parametrize("failure", ["pending", "bad_tensor", "wrong_claim"])
def test_posthoc_retirement_refuses_incomplete_or_damaged_data(tmp_path, failure):
    root, policy = retirement_case(tmp_path)
    before = {
        p: digest(root / p)
        for p in (
            PACKED,
            RECEIPT,
            "SPATIAL_SOURCE_READY.json",
            "episode_manifest.json",
            "COMPLETE.json",
        )
    }
    if failure != "pending":
        encode_case(tmp_path, root)
    if failure == "bad_tensor":
        path = next((root / "vae_cache").rglob("*.pt"))
        path.write_bytes(b"INVALID_TEST_ONLY_NUMERIC")
    elif failure == "wrong_claim":
        policy["view_first_claim_sha256"] = "0" * 64
    with pytest.raises((ValueError, OSError, RuntimeError, EOFError)):
        retire_view_first_cache(
            root, spool_root=policy["spool_root"], source_policy=policy
        )
    assert before == {p: digest(root / p) for p in before}
    assert not (root / final.CAPSULE).exists()
