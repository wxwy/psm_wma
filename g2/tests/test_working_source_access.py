"""Explicit full/gzip working-source dispatch and bounded exact-byte evidence."""

import gzip
import hashlib

import pytest

from g2.io import digest, read_json, write_json
from g2.latent_cache.contract import CacheError, fingerprint
from g2.latent_cache.final_source import load_source, working_source_sha
from g2.offline import view_only_source as working
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a
from g2.tests.test_stage_a_package import stage_case


def view_first_case(tmp_path, *, compressed=True):
    kwargs, _ = stage_case(
        tmp_path, OutputProfile(selection_top_variant="clean", view_vae=False)
    )
    target = tmp_path / "published"
    package_stage_a(destination=target, compress_source=compressed, **kwargs)
    return target


def test_legacy_default_retains_exact_raw_json_and_same_tuple_api(tmp_path):
    target = view_first_case(tmp_path, compressed=False)
    assert (target / working.FULL).is_file() and not (target / working.PACKED).exists()
    raw = (target / working.FULL).read_bytes()
    info = working.working_source_info(target, include_raw=True)
    assert info["raw"] == raw and info["raw_sha256"] == hashlib.sha256(raw).hexdigest()
    assert working.load_working_source(target) == (
        load_source(target),
        working_source_sha(target),
    )


def test_gzip_exact_original_bytes_and_transport_hashes_no_json_copy(tmp_path):
    target = view_first_case(tmp_path)
    info = working.working_source_info(target, include_raw=True)
    raw = gzip.decompress((target / working.PACKED).read_bytes())
    receipt = read_json(target / working.RECEIPT)
    assert info["raw"] == raw and info["raw_sha256"] == receipt["raw_sha256"]
    assert working_source_sha(target) == receipt["raw_sha256"]
    assert load_source(target) == info["source"]
    binding = working.view_first_binding(target, info)
    assert binding["manifest_sha256"] == digest(target / working.PACKED)
    assert binding["raw_source_sha256"] == hashlib.sha256(raw).hexdigest()
    assert set(binding["working_storage"]["files"]) == {
        working.PACKED,
        working.RECEIPT,
        "SPATIAL_SOURCE_READY.json",
    }
    assert not (target / working.FULL).exists()


@pytest.mark.parametrize(
    "mode",
    [
        "raw_limit",
        "packed_limit",
        "declared_short",
        "wrong_source",
        "missing_receipt",
        "symlink",
    ],
)
def test_invalid_compressed_sources_fail_without_materializing_json(
    tmp_path, monkeypatch, mode
):
    target = view_first_case(tmp_path)
    receipt = read_json(target / working.RECEIPT)
    if mode == "raw_limit":
        monkeypatch.setattr(working, "MAX_RAW_BYTES", 32)
    elif mode == "packed_limit":
        monkeypatch.setattr(working, "MAX_PACKED_BYTES", 32)
    elif mode in ("declared_short", "wrong_source"):
        receipt["raw_bytes" if mode == "declared_short" else "source_id"] = (
            1 if mode == "declared_short" else "0" * 64
        )
        receipt["receipt_id"] = fingerprint(
            {k: v for k, v in receipt.items() if k != "receipt_id"}
        )
        write_json(target / working.RECEIPT, receipt)
    elif mode == "missing_receipt":
        (target / working.RECEIPT).unlink()
    else:
        path = target / working.PACKED
        outside = tmp_path / "outside.gz"
        path.rename(outside)
        path.symlink_to(outside)
    with pytest.raises((ValueError, OSError)):
        working.working_source_info(target)
    assert not (target / working.FULL).exists()


def test_final_capsule_cannot_masquerade_as_full_working_source(tmp_path):
    target = view_first_case(tmp_path)
    manifest = read_json(target / "episode_manifest.json")
    manifest["schema"] = "g2_spatial_profile_episode_v2"
    write_json(target / "episode_manifest.json", manifest)
    with pytest.raises(CacheError, match="working profile"):
        working.load_working_source(target)
