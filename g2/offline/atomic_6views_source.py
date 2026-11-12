"""Materialize a source-exact, path-rebound official RoboCasa episode MJCF.

This CPU-only stage does not generate Views, native maps or scene graphs.
Its source proof is never a Room / role / training certificate. It rejects
unknown mount prefixes rather than silently substituting assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import xml.etree.ElementTree as ET

from g2.io import ContractError


DEFAULT_PREFIXES = (
    ("/opt/conda/envs/robocasa/lib/python3.10/site-packages/robosuite",
     "/mnt/data1/data_v2_0617/robosuite_repo/robosuite"),
    ("/root/robocasa/robocasa",
     "/mnt/data1/data_v2_0617/robocasa_repo/robocasa"),
)
DEFAULT_ASSET_ROOTS = (
    "/mnt/data1/data_v2_0617/robocasa_repo",
    "/mnt/data1/data_v2_0617/robosuite_repo",
)


def _hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _source_bytes(path):
    import gzip
    p = Path(path).resolve(strict=True)
    if p.stat().st_size > 32 * 1024 * 1024:
        raise ContractError("official source XML exceeds byte budget")
    if p.name.endswith(".gz"):
        with gzip.open(p, "rb") as f:
            xml = f.read(32 * 1024 * 1024 + 1)
    else:
        xml = p.read_bytes()
    if len(xml) > 32 * 1024 * 1024 or b"<!DOCTYPE" in xml.upper():
        raise ContractError("unsupported/oversized XML source")
    return xml


def _prefixes(pairs):
    result = []
    for a, b in pairs:
        pa, pb = Path(a), Path(b)
        if not pa.is_absolute() or not pb.is_absolute() or a in ("", "/"):
            raise ContractError("asset prefix rule must be absolute")
        if not pb.is_dir():
            raise ContractError("asset mapping root is not installed: " + str(pb))
        result.append((a.rstrip("/"), str(pb.resolve())))
    for i, (a, _) in enumerate(result):
        for b, _ in result[i + 1:]:
            if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                raise ContractError("overlapping asset prefix rules")
    return result


def rebind_xml(original, rules=DEFAULT_PREFIXES):
    """Change only XML file/compiler paths, never material/geometry attributes."""
    raw = _source_bytes(original)
    pairs = _prefixes(rules)
    try:
        source = ET.fromstring(raw)
    except ET.ParseError as error:
        raise ContractError("original MJCF invalid XML") from error
    changed = 0
    references = []
    for node in source.iter():
        fields = ("file",) if node.tag != "compiler" else ("assetdir", "meshdir", "texturedir")
        for key in fields:
            value = node.get(key)
            if not value:
                continue
            mapped = value
            for old, new in pairs:
                if value == old or value.startswith(old + "/"):
                    mapped = new + value[len(old):]
                    break
            if Path(value).is_absolute() and mapped == value and not Path(value).is_file():
                raise ContractError("unmapped or missing source asset: " + value)
            if mapped != value:
                node.set(key, mapped)
                changed += 1
            if key == "file":
                references.append((value, mapped))
    if not changed or not references:
        raise ContractError("official source path rebinding produced no mapped assets")
    return ET.tostring(source, encoding="utf-8"), references, changed


def inspect_original(original, ep_meta, states, *, expected_length, expected_layout):
    import numpy as np
    meta_path, states_path = Path(ep_meta).resolve(strict=True), Path(states).resolve(strict=True)
    metadata = json.loads(meta_path.read_text())
    if metadata.get("layout_id") != expected_layout or metadata.get("style_id") != expected_layout:
        raise ContractError("official layout and style identity mismatch")
    with np.load(states_path, allow_pickle=False) as archive:
        if "states" not in archive:
            raise ContractError("official archive missing FULLPHYSICS states")
        arr = archive["states"]
        if arr.ndim != 2 or arr.shape[0] != expected_length or arr.dtype.kind != "f":
            raise ContractError("raw episode state length/type mismatch")
        width = int(arr.shape[1])
    return {"model.xml.gz": _hash(original), "ep_meta.json": _hash(meta_path),
            "states.npz": _hash(states_path)}, width


def prepare_model(original, ep_meta, states, output, *, length, layout,
                  rules=DEFAULT_PREFIXES, asset_roots=DEFAULT_ASSET_ROOTS):
    """CPU-only per-episode source preparation; a new output directory required."""
    from g2.sim.source_geometry import load_model, model_source_hash
    import mujoco
    original = Path(original).resolve(strict=True)
    ep_meta = Path(ep_meta).resolve(strict=True)
    states = Path(states).resolve(strict=True)
    target = Path(output).absolute()
    if target.exists() or target.is_symlink():
        raise ContractError("source preparation output already exists")
    for protected in (original.parent, *[Path(p).resolve() for p in asset_roots]):
        if target == protected or target in protected.parents or protected in target.parents:
            raise ContractError("source output must not overlap an asset root")
    fingerprints, state_width = inspect_original(
        original, ep_meta, states, expected_length=length, expected_layout=layout)
    payload, references, changes = rebind_xml(original, rules=rules)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="._source_prepare_", dir=target.parent))
    success = False
    try:
        source_xml = tmp / "scene_rebased.xml"
        source_xml.write_bytes(payload)
        model, sources = load_model(source_xml, asset_roots)
        need = mujoco.mj_stateSize(model, mujoco.mjtState.mjSTATE_FULLPHYSICS)
        if state_width != need:
            raise ContractError("compiled model FULLPHYSICS width differs from raw source")
        result = {
            "schema": "g2_atomic_official_model_rebound_v1",
            "source_model_xml": str(original),
            "rebased_model_xml": str(target / "scene_rebased.xml"),
            "source_files": fingerprints, "source_frame_count": length,
            "layout_id": layout, "mujoco_version": mujoco.__version__,
            "compiled_ngeom": int(model.ngeom), "compiled_nbody": int(model.nbody),
            "compiled_fullphysics_dim": int(need),
            "source_model_closure_sha256": model_source_hash(sources),
            "asset_count": len(sources), "path_rebindings": changes,
            "source_rebinding_only": True,
            "room_certified": False, "role_certified": False,
            "training_ready": False,
        }
        with (tmp / "source_receipt.json").open("x", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        os.rename(tmp, target)
        success = True
        return result
    finally:
        if not success:
            shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True)
    parser.add_argument("--ep-meta", required=True)
    parser.add_argument("--states", required=True)
    parser.add_argument("--layout", type=int, required=True)
    parser.add_argument("--length", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    summary = prepare_model(args.original, args.ep_meta, args.states, args.output,
                            length=args.length, layout=args.layout)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
