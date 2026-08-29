import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("verify_r08_gate_b", ROOT / "verify_r08_gate_b.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path: Path) -> argparse.Namespace:
    checkpoint = tmp_path / "iter_000000002"
    for relative, content in {"model/.metadata": b"meta", "model/__0_0.distcp": b"weights"}.items():
        path = checkpoint / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": VERIFY.MANIFEST_SCHEMA, "checkpoint_path": str(checkpoint), "files": {str(path.relative_to(checkpoint)): {"size_bytes": path.stat().st_size, "sha256": file_sha(path)} for path in checkpoint.rglob("*") if path.is_file()}}))
    VERIFY.CANONICAL_MANIFEST_PATH = manifest.resolve()
    VERIFY.CANONICAL_MANIFEST_SHA256 = file_sha(manifest)
    VERIFY.EXPECTED_ROOT_REVISIONS = {"a"}
    VERIFY.EXPECTED_SUBMODULE_REVISION = "b"
    values = {"normal": 1.0, "zero": 2.0, "shuffle": 3.0}
    fields = ("local_memory", "preds_vision", "preds_action")
    paths = {"checkpoint_manifest": manifest, "expected_iteration": 0}
    for mode, value in values.items():
        capture = {"schema_version": VERIFY.CAPTURE_SCHEMA, **{key: key for key in VERIFY.INVARIANT_KEYS}}
        capture_path = tmp_path / f"{mode}.json"
        capture_path.write_text(json.dumps(capture))
        tensor_path = tmp_path / f"{mode}.pt"
        torch.save({"schema_version": VERIFY.TENSOR_SCHEMA, **{field: [torch.tensor([value])] for field in fields}}, tensor_path)
        provenance_path = tmp_path / f"{mode}.provenance.json"
        provenance_path.write_text(json.dumps({"schema_version": VERIFY.PROVENANCE_SCHEMA, "history_mode": mode, "capture_only": True, "root_revision": "a", "submodule_revision": "b", "gitlink_revision": "b", "root_clean_tracked": True, "submodule_clean_tracked": True, "checkpoint_path": str(checkpoint)}))
        log_path = tmp_path / f"{mode}.log"
        log_path.write_text(f"Resuming ckpt {checkpoint} (warm-start, local) with keys: ['model']\nLoaded checkpoint from {checkpoint} (warm-start, local) in iteration 0\n")
        config_path = tmp_path / f"{mode}.yaml"
        config_path.write_text(f"checkpoint:\n  load_path: {checkpoint}\n  load_training_state: false\n")
        paths.update({f"{mode}_json": capture_path, f"{mode}_pt": tensor_path, f"{mode}_provenance": provenance_path, f"{mode}_log": log_path, f"{mode}_config": config_path})
    return argparse.Namespace(**paths)


def test_canonical_fixture_passes(tmp_path: Path) -> None:
    assert VERIFY.verified_result(fixture(tmp_path))["status"] == "PASS"


def test_missing_history_mask_fails(tmp_path: Path) -> None:
    args = fixture(tmp_path)
    capture = json.loads(args.zero_json.read_text())
    capture.pop("history_mask")
    args.zero_json.write_text(json.dumps(capture))
    assert VERIFY.verified_result(args)["status"] == "FAIL"


def test_wrong_capture_tensor_and_provenance_schemas_fail(tmp_path: Path) -> None:
    args = fixture(tmp_path)
    capture = json.loads(args.normal_json.read_text())
    capture["schema_version"] = "wrong"
    args.normal_json.write_text(json.dumps(capture))
    assert VERIFY.verified_result(args)["capture_schema_valid"] is False
    args = fixture(tmp_path / "tensor")
    tensors = torch.load(args.normal_pt, weights_only=True)
    tensors["schema_version"] = "wrong"
    torch.save(tensors, args.normal_pt)
    assert VERIFY.verified_result(args)["tensor_schema_valid"] is False
    args = fixture(tmp_path / "provenance")
    provenance = json.loads(args.normal_provenance.read_text())
    provenance["schema_version"] = "wrong"
    args.normal_provenance.write_text(json.dumps(provenance))
    assert VERIFY.verified_result(args)["provenance_schema_valid"] is False


def test_nonfinite_response_fails(tmp_path: Path) -> None:
    args = fixture(tmp_path)
    payload = torch.load(args.zero_pt, weights_only=True)
    payload["preds_action"] = [torch.tensor([float("inf")])]
    torch.save(payload, args.zero_pt)
    assert VERIFY.verified_result(args)["response"] is False


def test_arbitrary_manifest_fails(tmp_path: Path) -> None:
    args = fixture(tmp_path)
    args.checkpoint_manifest.write_text("{}")
    assert VERIFY.verified_result(args)["checkpoint_identity"]["checkpoint_identity_valid"] is False


def test_well_formed_noncanonical_manifest_fails(tmp_path: Path) -> None:
    args = fixture(tmp_path)
    canonical = Path(json.loads(args.checkpoint_manifest.read_text())["checkpoint_path"])
    alternative = tmp_path / "alternative"
    for relative, content in {"model/.metadata": b"other-meta", "model/__0_0.distcp": b"other-weights"}.items():
        path = alternative / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    alternative_manifest = tmp_path / "alternative-manifest.json"
    alternative_manifest.write_text(json.dumps({"schema_version": VERIFY.MANIFEST_SCHEMA, "checkpoint_path": str(alternative), "files": {str(path.relative_to(alternative)): {"size_bytes": path.stat().st_size, "sha256": file_sha(path)} for path in alternative.rglob("*") if path.is_file()}}))
    for mode in ("normal", "zero", "shuffle"):
        provenance = json.loads(getattr(args, f"{mode}_provenance").read_text())
        provenance["checkpoint_path"] = str(alternative)
        getattr(args, f"{mode}_provenance").write_text(json.dumps(provenance))
        getattr(args, f"{mode}_log").write_text(getattr(args, f"{mode}_log").read_text().replace(str(canonical), str(alternative)))
        getattr(args, f"{mode}_config").write_text(getattr(args, f"{mode}_config").read_text().replace(str(canonical), str(alternative)))
    args.checkpoint_manifest = alternative_manifest
    result = VERIFY.verified_result(args)
    assert result["checkpoint_identity"]["canonical_manifest_valid"] is False
    assert result["status"] == "FAIL"


def test_same_clean_alternate_runtime_fails(tmp_path: Path) -> None:
    args = fixture(tmp_path)
    for mode in ("normal", "zero", "shuffle"):
        provenance = json.loads(getattr(args, f"{mode}_provenance").read_text())
        provenance.update(root_revision="alternate", submodule_revision="alternate", gitlink_revision="alternate")
        getattr(args, f"{mode}_provenance").write_text(json.dumps(provenance))
    result = VERIFY.verified_result(args)
    assert result["same_runtime"] is True
    assert result["expected_runtime_valid"] is False
    assert result["status"] == "FAIL"


def test_changed_checkpoint_hash_fails(tmp_path: Path) -> None:
    args = fixture(tmp_path)
    checkpoint = Path(json.loads(args.checkpoint_manifest.read_text())["checkpoint_path"])
    (checkpoint / "model/__0_0.distcp").write_bytes(b"changed")
    assert VERIFY.verified_result(args)["checkpoint_identity"]["checkpoint_identity_valid"] is False


def test_wrong_checkpoint_path_or_load_marker_fails(tmp_path: Path) -> None:
    args = fixture(tmp_path)
    provenance = json.loads(args.shuffle_provenance.read_text())
    provenance["checkpoint_path"] = "/wrong"
    args.shuffle_provenance.write_text(json.dumps(provenance))
    assert VERIFY.verified_result(args)["manifest_checkpoint_path"] is False
    args = fixture(tmp_path / "marker")
    args.normal_log.write_text("Loaded checkpoint from elsewhere in iteration 0\n")
    assert VERIFY.verified_result(args)["actual_checkpoint_loaded"] is False
