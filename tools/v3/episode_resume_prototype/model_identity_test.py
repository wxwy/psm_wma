"""Synthetic read-only identity gate; no real checkpoint, GPU or model load."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import pickle
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "episode_resume_model_identity", Path(__file__).with_name("model_identity.py")
)
identity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(identity)
ROOT = Path(__file__).resolve().parents[3]


def _json_digest(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _write_shard(path, payload=b"tiny fake tensor bytes"):
    # Legal torch-style ZIP local headers; deliberately not represented as a
    # semantically loadable model or real torch.distributed.checkpoint.Metadata.
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in (
            ("archive/data.pkl", pickle.dumps({"prototype_fixture": True}, protocol=4)),
            ("archive/version", b"3\n"),
            ("archive/byteorder", b"little"),
            ("archive/data/0", payload),
        ):
            archive.writestr(zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0)), data)


@pytest.fixture
def checkpoint(tmp_path):
    path = tmp_path / "只读模型/checkpoints/iter_000004000"
    model = path / "model"
    model.mkdir(parents=True)
    (model / ".metadata").write_bytes(pickle.dumps({"prototype_fixture": True, "ranks": [0, 1]}, protocol=4))
    _write_shard(model / "__0_0.distcp")
    _write_shard(model / "__1_0.distcp", b"second tiny fake tensor bytes")
    return path


def build(checkpoint, **changes):
    arguments = dict(checkpoint=checkpoint, num_steps=30, action_horizon=16, guidance=1.0)
    return identity.build_model_identity(**(arguments | changes))


def legacy(current, *, runtime=True):
    parameters = current["parameters"]
    body = {
        "schema": "psm_v3_eval_identity_vendor_v1" if runtime else "psm_v3_eval_identity_v1",
        "root_sha": "a" * 40,
        "child_sha": "b" * 40,
        "checkpoint": parameters["checkpoint"]["path"],
        "model_metadata_sha256": parameters["checkpoint"]["metadata_sha256"],
        "model_shard_stat_witnesses": copy.deepcopy(current["observed_checkpoint_stats"]),
        "checkpoint_identity_scope": "metadata_hash_and_shard_stats_not_full_payload_hash",
        "config_sha256": "c" * 64,
        "tasks": [{"task": "CloseFridge", "dataset_dir": "/原数据", "env_metadata_sha256": "e" * 64}],
        "protocol": {
            "num_steps": parameters["num_steps"],
            "R": parameters["action_horizon"],
            "guidance": parameters["guidance"],
            "seed": 0,
            "trials": 5,
            "gpu_ids": [0],
            "save_generated_video": "none",
        },
    }
    if runtime:
        body["evaluation_runtime"] = {"schema": "synthetic_runtime", "digest": "d" * 64}
    return {"identity": body, "digest": _json_digest(body)}


def _witness(path):
    info = path.stat()
    return path.read_bytes(), info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def test_exactly_four_parameters_full_hashes_and_no_file_writes(checkpoint):
    before = {path.name: _witness(path) for path in (checkpoint / "model").iterdir()}
    current = build(checkpoint)
    assert set(current["parameters"]) == {"checkpoint", "num_steps", "action_horizon", "guidance"}
    model = current["parameters"]["checkpoint"]
    assert model["scope"] == "full_model_sha256_v1"
    assert model["path"] == str(checkpoint.resolve())
    assert model["metadata_sha256"] == hashlib.sha256(before[".metadata"][0]).hexdigest()
    assert [row["name"] for row in model["shards"]] == ["__0_0.distcp", "__1_0.distcp"]
    for row in model["shards"]:
        assert row["sha256"] == hashlib.sha256(before[row["name"]][0]).hexdigest()
    assert identity.compare_model_identity(current, build(checkpoint)) == {
        "status": "MATCH",
        "errors": [],
        "warnings": [],
    }
    assert before == {path.name: _witness(path) for path in (checkpoint / "model").iterdir()}
    assert list(checkpoint.iterdir()) == [checkpoint / "model"]


@pytest.mark.parametrize("parameter,value", [("num_steps", 31), ("action_horizon", 8), ("guidance", 1.5)])
def test_each_scalar_parameter_mismatch_has_exact_old_new_values(checkpoint, parameter, value):
    old, new = build(checkpoint), build(checkpoint, **{parameter: value})
    report = identity.compare_model_identity(old, new)
    assert report["status"] == "MODEL_MISMATCH"
    assert len(report["errors"]) == 1
    assert report["errors"][0]["parameter"] == parameter
    assert report["errors"][0]["old"] == old["parameters"][parameter]
    assert report["errors"][0]["new"] == value


def test_different_actual_checkpoint_path_is_hard_mismatch(checkpoint, tmp_path):
    alternate = tmp_path / "another/checkpoint"
    shutil.copytree(checkpoint, alternate)
    old, new = build(checkpoint), build(alternate)
    report = identity.compare_model_identity(old, new)
    assert report["status"] == "MODEL_MISMATCH"
    assert report["errors"][0]["parameter"] == "checkpoint"
    assert report["errors"][0]["old"]["path"] == str(checkpoint.resolve())
    assert report["errors"][0]["new"]["path"] == str(alternate.resolve())


def test_same_path_equal_size_replaced_weights_are_detected_with_mtime_restored(checkpoint):
    shard = checkpoint / "model/__0_0.distcp"
    _write_shard(shard, b"AAAA")
    old = build(checkpoint)
    info = shard.stat()
    _write_shard(shard, b"BBBB")
    os.utime(shard, ns=(info.st_atime_ns, info.st_mtime_ns))
    new = build(checkpoint)
    assert shard.stat().st_size == info.st_size and shard.stat().st_mtime_ns == info.st_mtime_ns
    assert old["parameters"]["checkpoint"]["metadata_sha256"] == new["parameters"]["checkpoint"]["metadata_sha256"]
    report = identity.compare_model_identity(old, new)
    assert report["status"] == "MODEL_MISMATCH" and report["errors"][0]["parameter"] == "checkpoint"
    assert (
        old["parameters"]["checkpoint"]["shards"][0]["sha256"] != new["parameters"]["checkpoint"]["shards"][0]["sha256"]
    )


def test_same_bytes_changed_timestamp_matches_new_identity_but_never_bypasses_legacy(checkpoint):
    old = build(checkpoint)
    manifest = legacy(old)
    shard = checkpoint / "model/__0_0.distcp"
    info = shard.stat()
    os.utime(shard, ns=(info.st_atime_ns, info.st_mtime_ns + 10_000_000))
    new = build(checkpoint)
    assert old["digest"] == new["digest"]
    assert identity.compare_model_identity(old, new)["status"] == "MATCH"
    bridged = identity.legacy_ingest(manifest, new)
    assert bridged["status"] == "MODEL_MISMATCH"
    assert bridged["errors"][0]["parameter"] == "checkpoint"
    assert (
        bridged["errors"][0]["old"]["model_shard_stat_witnesses"]
        != bridged["errors"][0]["new"]["model_shard_stat_witnesses"]
    )


def test_owner_optin_manual_legacy_checkpoint_relocation_keeps_historical_manifest_immutable(
    checkpoint, tmp_path
):
    original = build(checkpoint)
    manifest = legacy(original)
    original_manifest = copy.deepcopy(manifest)
    original_files = {p.name: _witness(p) for p in (checkpoint / "model").iterdir()}
    relocated = tmp_path / "new-volume" / checkpoint.name
    shutil.copytree(checkpoint, relocated, copy_function=shutil.copy2)
    current = build(relocated)
    assert current["parameters"]["checkpoint"]["path"] != original["parameters"]["checkpoint"]["path"]
    # No relocation permission, no old-schema migration.
    assert identity.legacy_ingest(manifest, current)["status"] == "MODEL_MISMATCH"
    # Only an explicit Owner acknowledgement accepts the moved, unchanged DCP.
    decision = identity.legacy_ingest(manifest, current, allow_relocated_checkpoint=True)
    assert decision["status"] == "LEGACY_STAT_BRIDGE_MATCH" and decision["errors"] == []
    assert decision["owner_accepted_relocated_legacy_checkpoint"] is True
    assert decision["historical_payload_sha256"] is None
    notice = next(x for x in decision["warnings"] if x["code"] == "OWNER_ACCEPTED_LEGACY_CHECKPOINT_RELOCATION")
    assert notice["old_checkpoint_path"] == str(checkpoint.resolve())
    assert notice["current_checkpoint_path"] == str(relocated.resolve())
    assert notice["reuse_blocked"] is False
    assert manifest == original_manifest
    assert original_files == {p.name: _witness(p) for p in (checkpoint / "model").iterdir()}
    # A strong new-run identity still checks full path unless separately designed.
    assert identity.compare_model_identity(original, current)["status"] == "MODEL_MISMATCH"


@pytest.mark.parametrize("tamper", ["metadata", "shard_size", "shard_mtime", "checkpoint_iteration", "num_steps"])
def test_owner_optin_legacy_relocation_does_not_waive_other_identity_witnesses(
    checkpoint, tmp_path, tamper
):
    manifest = legacy(build(checkpoint))
    moved_name = "iter_000004001" if tamper == "checkpoint_iteration" else checkpoint.name
    relocated = tmp_path / "new-volume" / moved_name
    shutil.copytree(checkpoint, relocated, copy_function=shutil.copy2)
    shard = relocated / "model/__0_0.distcp"
    if tamper == "metadata":
        (relocated / "model/.metadata").write_bytes(pickle.dumps({"changed": True}, protocol=4))
    elif tamper == "shard_size":
        with zipfile.ZipFile(shard, "a") as archive:
            archive.writestr("additional_payload", b"tampered content")
    elif tamper == "shard_mtime":
        info = shard.stat()
        os.utime(shard, ns=(info.st_atime_ns, info.st_mtime_ns + 1_000_000_000))
    current = build(relocated, **({"num_steps": 31} if tamper == "num_steps" else {}))
    result = identity.legacy_ingest(manifest, current, allow_relocated_checkpoint=True)
    assert result["status"] == "MODEL_MISMATCH"
    assert result["errors"]


def test_owner_legacy_relocation_flag_rejects_non_boolean(checkpoint):
    manifest = legacy(build(checkpoint))
    with pytest.raises(identity.IdentityInputError, match="RELOCATION_FLAG_INVALID"):
        identity.legacy_ingest(manifest, build(checkpoint), allow_relocated_checkpoint="yes")


def test_changed_metadata_is_checkpoint_mismatch(checkpoint):
    old = build(checkpoint)
    (checkpoint / "model/.metadata").write_bytes(pickle.dumps({"different": "valid metadata structure"}, protocol=4))
    new = build(checkpoint)
    assert identity.compare_model_identity(old, new)["errors"][0]["parameter"] == "checkpoint"


@pytest.mark.parametrize(
    "failure",
    [
        "metadata_missing",
        "metadata_empty",
        "metadata_bad",
        "metadata_trailing",
        "shards_missing",
        "shard_empty",
        "shard_bad",
        "shard_truncated",
        "shard_symlink",
    ],
)
def test_bad_or_missing_checkpoint_inputs_fail_without_a_new_identity(checkpoint, failure):
    model = checkpoint / "model"
    metadata, shard = model / ".metadata", model / "__0_0.distcp"
    if failure == "metadata_missing":
        metadata.unlink()
    elif failure == "metadata_empty":
        metadata.write_bytes(b"")
    elif failure == "metadata_bad":
        metadata.write_bytes(b"not pickle metadata")
    elif failure == "metadata_trailing":
        metadata.write_bytes(metadata.read_bytes() + b"trailing")
    elif failure == "shards_missing":
        for path in model.glob("*.distcp"):
            path.unlink()
    elif failure == "shard_empty":
        shard.write_bytes(b"")
    elif failure == "shard_bad":
        shard.write_bytes(b"not a tensor container")
    elif failure == "shard_truncated":
        shard.write_bytes(b"PK\x03\x04")
    else:
        shard.unlink()
        shard.symlink_to(model / "__1_0.distcp")
    with pytest.raises(identity.IdentityInputError) as error:
        build(checkpoint)
    assert error.value.code in {"CHECKPOINT_INPUT_INVALID", "CHECKPOINT_HEADER_INVALID"}


def _forbidden_unpickle():
    raise AssertionError("a metadata pickle was executed")


class _Reduce:
    def __reduce__(self):
        return _forbidden_unpickle, ()


def test_metadata_pickle_opcodes_are_never_executed(checkpoint, monkeypatch):
    (checkpoint / "model/.metadata").write_bytes(pickle.dumps(_Reduce(), protocol=4))
    monkeypatch.setattr(pickle, "load", _forbidden_unpickle)
    monkeypatch.setattr(pickle, "loads", _forbidden_unpickle)
    assert build(checkpoint)["parameters"]["checkpoint"]["metadata_sha256"]


def test_changed_inventory_during_hashing_fails_closed(checkpoint, monkeypatch):
    original = identity._read_hash

    def read(path, expected, *, metadata):
        value = original(path, expected, metadata=metadata)
        if not metadata:
            path.touch()
        return value

    monkeypatch.setattr(identity, "_read_hash", read)
    with pytest.raises(identity.IdentityInputError) as error:
        build(checkpoint)
    assert error.value.code == "CHECKPOINT_CHANGED_DURING_READ"


@pytest.mark.parametrize(
    "changes",
    [
        {"num_steps": True},
        {"num_steps": 0},
        {"action_horizon": False},
        {"action_horizon": -1},
        {"guidance": True},
        {"guidance": float("nan")},
        {"guidance": float("inf")},
    ],
)
def test_invalid_scalar_input_is_not_reported_as_a_compatible_identity(checkpoint, changes):
    with pytest.raises(identity.IdentityInputError) as error:
        build(checkpoint, **changes)
    assert error.value.code == "INVALID_MODEL_PARAMETER"


def test_guidance_numeric_representation_is_canonical(checkpoint):
    assert build(checkpoint, guidance=1)["digest"] == build(checkpoint, guidance=1.0)["digest"]
    assert build(checkpoint, guidance=-0.0)["digest"] == build(checkpoint, guidance=0.0)["digest"]


def test_identity_digest_or_fifth_hard_field_cannot_be_forged(checkpoint):
    current = build(checkpoint)
    for changes in ({"digest": "a" * 64}, {"parameters": current["parameters"] | {"root_sha": "a" * 40}}):
        with pytest.raises(identity.IdentityInputError):
            identity.compare_model_identity(current, current | changes)


def test_legacy_bridge_preserves_original_identity_and_never_invents_historical_payload_hash(checkpoint):
    current = build(checkpoint)
    manifest = legacy(current)
    before = copy.deepcopy(manifest)
    provenance = {
        key: manifest["identity"][key] for key in ("root_sha", "child_sha", "config_sha256", "evaluation_runtime")
    }
    result = identity.legacy_ingest(manifest, current, current_provenance=provenance)
    assert result["status"] == "LEGACY_STAT_BRIDGE_MATCH" and result["errors"] == []
    assert result["original_manifest_digest"] == manifest["digest"]
    assert result["original_identity"] == manifest["identity"] == before["identity"]
    assert result["current_model_identity_ref"] == current["digest"]
    assert result["historical_payload_sha256"] is None
    assert result["warnings"][0]["code"] == "LEGACY_PAYLOAD_HASH_NOT_RETROSPECTIVELY_AVAILABLE"
    assert "ORIGINAL_MANIFEST" in result["episode_validation"]
    result["original_identity"]["protocol"]["seed"] = 99
    assert manifest == before


@pytest.mark.parametrize(
    "key,value,code",
    [
        ("root_sha", "e" * 40, "SOURCE_PROVENANCE_CHANGED"),
        ("child_sha", "f" * 40, "SOURCE_PROVENANCE_CHANGED"),
        ("config_sha256", "f" * 64, "CONFIG_PROVENANCE_CHANGED"),
        ("evaluation_runtime", {"changed": "physical environment"}, "RUNTIME_PROVENANCE_CHANGED"),
    ],
)
def test_source_config_or_runtime_changes_warn_without_a_fifth_hard_equality(checkpoint, key, value, code):
    current = build(checkpoint)
    manifest = legacy(current)
    provenance = {
        name: manifest["identity"][name] for name in ("root_sha", "child_sha", "config_sha256", "evaluation_runtime")
    }
    provenance[key] = value
    result = identity.legacy_ingest(manifest, current, current_provenance=provenance)
    assert result["status"] == "LEGACY_STAT_BRIDGE_MATCH" and result["errors"] == []
    warning = next(row for row in result["warnings"] if row["code"] == code)
    assert warning["reuse_blocked"] is False and "NOT_SAME_CONDITION_BENCHMARK" in warning["comparability"]


def test_tasks_seed_media_and_resource_changes_are_original_plan_provenance_only(checkpoint):
    current = build(checkpoint)
    manifest = legacy(current)
    manifest["identity"]["protocol"].update(
        seed=42, trials=8, gpu_ids=[7, 6], save_generated_video="all", timeouts={"task_wall_s": 999}, base_port=9999
    )
    manifest["identity"]["tasks"].append({"task": "NavigateKitchen", "dataset_dir": "/other"})
    manifest["digest"] = _json_digest(manifest["identity"])
    result = identity.legacy_ingest(manifest, current)
    assert result["status"] == "LEGACY_STAT_BRIDGE_MATCH"
    assert result["original_invocation_plan"]["seed"] == 42
    assert "tasks" not in result["legacy_model_parameters"]


def test_unknown_legacy_runtime_warns_and_is_not_fabricated(checkpoint):
    current = build(checkpoint)
    result = identity.legacy_ingest(
        legacy(current, runtime=False), current, current_provenance={"root_sha": "a" * 40, "child_sha": "b" * 40}
    )
    assert result["status"] == "LEGACY_STAT_BRIDGE_MATCH"
    assert result["original_provenance"]["evaluation_runtime"] is None
    assert "RUNTIME_PROVENANCE_UNKNOWN" in {row["code"] for row in result["warnings"]}


@pytest.mark.parametrize("name,value", [("num_steps", 31), ("R", 8), ("guidance", 2.0)])
def test_legacy_four_parameter_changes_still_fail_with_old_new_values(checkpoint, name, value):
    current = build(checkpoint)
    manifest = legacy(current)
    manifest["identity"]["protocol"][name] = value
    manifest["digest"] = _json_digest(manifest["identity"])
    result = identity.legacy_ingest(manifest, current)
    assert result["status"] == "MODEL_MISMATCH"
    assert len(result["errors"]) == 1
    assert result["errors"][0]["old"] == value
    assert result["errors"][0]["new"] == current["parameters"]["action_horizon" if name == "R" else name]


@pytest.mark.parametrize(
    "failure",
    ["digest", "unknown_schema", "stats_missing", "stats_duplicate", "metadata_hash_missing", "boolean_stats"],
)
def test_unverifiable_legacy_manifest_cannot_be_ingested(checkpoint, failure):
    current = build(checkpoint)
    manifest = legacy(current)
    original = manifest["identity"]
    if failure == "digest":
        manifest["digest"] = "0" * 64
    else:
        if failure == "unknown_schema":
            original["schema"] = "unknown"
        elif failure == "stats_missing":
            original.pop("model_shard_stat_witnesses")
        elif failure == "stats_duplicate":
            original["model_shard_stat_witnesses"].append(original["model_shard_stat_witnesses"][0])
        elif failure == "boolean_stats":
            original["model_shard_stat_witnesses"][0][1] = True
        else:
            original.pop("model_metadata_sha256")
        manifest["digest"] = _json_digest(original)
    with pytest.raises(identity.IdentityInputError) as error:
        identity.legacy_ingest(manifest, current)
    assert error.value.code == "LEGACY_MANIFEST_INVALID"


def test_actual_unchanged_production_legacy_manifest_can_be_read_without_claim_or_rewrite(checkpoint, tmp_path):
    spec = importlib.util.spec_from_file_location("unchanged_v3_identity", ROOT / "scripts/v3_evaluation_identity.py")
    production = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(production)
    root, child = tmp_path / "source", tmp_path / "source/cosmos-framework"

    def git(repo, *arguments):
        return subprocess.check_output(
            ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "-C", str(repo), *arguments],
            stderr=subprocess.STDOUT,
            text=True,
        ).strip()

    for repo in (root, child):
        repo.mkdir(parents=True)
        git(repo, "init", "-q")
        (repo / "fixture.txt").write_text("CPU source fixture\n")
        git(repo, "add", "fixture.txt")
        git(repo, "-c", "user.name=CPU Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
    git(root, "update-index", "--add", "--cacheinfo", f"160000,{git(child, 'rev-parse', 'HEAD')},cosmos-framework")
    git(root, "-c", "user.name=CPU Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "gitlink")
    config = tmp_path / "config.yaml"
    config.write_text("synthetic: true\n")
    dataset = tmp_path / "dataset/extras"
    dataset.mkdir(parents=True)
    (dataset / "dataset_meta.json").write_text(json.dumps({"env_args": {"env_name": "CloseFridge"}}))
    manifest = production.build_evaluation_identity(
        root=root,
        checkpoint=checkpoint,
        config_file=config,
        tasks=[("CloseFridge", dataset.parent)],
        protocol={"num_steps": 30, "R": 16, "guidance": 1.0, "seed": 0, "trials": 5},
    )
    output = tmp_path / "historical/evaluation_manifest.json"
    output.parent.mkdir()
    output.write_text(json.dumps(manifest, ensure_ascii=False))
    before = _witness(output)
    result = identity.legacy_ingest(json.loads(output.read_text()), build(checkpoint))
    assert result["status"] == "LEGACY_STAT_BRIDGE_MATCH"
    assert result["original_manifest_digest"] == manifest["digest"]
    assert _witness(output) == before
    assert sorted(path.name for path in output.parent.iterdir()) == ["evaluation_manifest.json"]
