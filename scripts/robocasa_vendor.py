"""Read-only runtime provenance for the pinned RoboCasa evaluation environment.

Executed by the SIMULATOR interpreter, with its import environment and -B, before model or env creation.
Source identity and physics compatibility are different gates: this attests the
former and never claims to reproduce the unknown data-generation environment.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import marshal
import os
import subprocess
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "third_party/robosuite_patches/vendor.lock.json"
ASSET_SUFFIXES = {".xml", ".obj", ".stl", ".mtl", ".png", ".jpg", ".jpeg", ".webp", ".json", ".txt", ".yaml", ".yml"}


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_raw(repo: Path, *args) -> str:
    env = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        env.pop(name, None)
    env.update(GIT_NO_LAZY_FETCH="1", GIT_ALLOW_PROTOCOL="file", GIT_NO_REPLACE_OBJECTS="1")
    return subprocess.check_output(
        ["git", "--no-optional-locks", "-C", str(repo), *args], text=True, stderr=subprocess.PIPE, env=env
    )


def git(repo: Path, *args) -> str:
    return git_raw(repo, *args).strip()


def audit_source(module_origin: Path, *, package: str, expected_commit: str, assets: dict) -> dict:
    origin = module_origin.resolve(strict=True)
    repo = Path(git(origin.parent, "rev-parse", "--show-toplevel")).resolve()
    if origin != repo / package / "__init__.py":
        raise ValueError(f"{package}: import origin is not its tracked package root")
    if git(repo, "rev-parse", "HEAD") != expected_commit:
        raise ValueError(f"{package}: source commit mismatch")
    # Check index AND working tree. Ignored files are audited too: ignored .py,
    # .so or backups must not evade the clean-source requirement.
    if git(repo, "diff", "--name-only", "HEAD", "--"):
        raise ValueError(f"{package}: tracked source is dirty")
    names = set(
        filter(
            None,
            git_raw(repo, "ls-files", "--others", "-z").split("\0"),
        )
    )
    observed = {}
    expected_assets = assets.get(package, {})
    if not isinstance(expected_assets, dict):
        raise ValueError("asset manifest must map relative paths to SHA256")
    for name in sorted(names):
        path = repo / name
        relative = Path(name)
        if path.is_symlink() or not path.resolve().is_relative_to(repo):
            raise ValueError(f"{package}: untrusted source/asset symlink: {name}")
        if "__pycache__" in relative.parts and relative.suffix == ".pyc":
            # Read-only probe disables bytecode writes. Existing bytecode must
            # correspond to a tracked Python source; arbitrary sourceless code rejects.
            try:
                source = Path(importlib.util.source_from_cache(str(path)))
            except ValueError as error:
                raise ValueError("unrecognized bytecode path") from error
            if git(repo, "ls-files", "--error-unmatch", str(source.relative_to(repo))) and source.is_file():
                data = path.read_bytes()
                if data[:4] != importlib.util.MAGIC_NUMBER or len(data) > 10 * 1024 * 1024:
                    raise ValueError("foreign or oversized bytecode")
                code = marshal.loads(data[16:])
                if (
                    not isinstance(code, types.CodeType)
                    or Path(code.co_filename).resolve() != source.resolve()
                    or code
                    != compile(
                        source.read_bytes(), code.co_filename, "exec", dont_inherit=True, optimize=sys.flags.optimize
                    )
                ):
                    raise ValueError("cached bytecode differs from pinned Python source")
                continue
        if (
            not name.startswith(f"{package}/models/assets/")
            or relative.suffix.lower() not in ASSET_SUFFIXES
            or path.is_symlink()
            or not path.resolve().is_relative_to(repo)
            or not path.is_file()
        ):
            raise ValueError(f"{package}: untrusted untracked/ignored source: {name}")
        actual = sha256_file(path)
        if expected_assets.get(name) != actual:
            raise ValueError(f"{package}: asset missing from approved inventory or SHA mismatch: {name}")
        observed[name] = actual
    if set(observed) != set(expected_assets):
        raise ValueError(f"{package}: approved asset inventory differs from installed untracked assets")
    return {
        "commit": expected_commit,
        "git_tree": git(repo, "rev-parse", "HEAD^{tree}"),
        "source_root": str(repo),
        "origin": str(origin),
        "tracked_clean": True,
        "untracked_asset_sha256": observed,
        "untracked_source_clean": True,
    }


def probe_runtime(*, lock_path=DEFAULT_LOCK, asset_manifest=None, tasks=("CloseFridge", "NavigateKitchen")) -> dict:
    lock_path = Path(lock_path).resolve(strict=True)
    lock = json.loads(lock_path.read_text())
    if lock["schema"] != "psm_robocasa_vendor_lock_v1":
        raise ValueError("unknown vendor lock schema")
    patch = lock_path.parent / lock["robosuite"]["patch"]
    if sha256_file(patch) != lock["robosuite"]["patch_sha256"]:
        raise ValueError("vendor patch checksum mismatch")
    assets = json.loads(Path(asset_manifest).read_text()) if asset_manifest else {}
    if not isinstance(assets, dict) or set(assets) - {"robosuite", "robocasa"}:
        raise ValueError("unknown asset-manifest packages")
    packages = {}
    expected_versions = dict(
        lock["runtime_versions"],
        robosuite=lock["robosuite"]["package_version"],
        robocasa=lock["robocasa"]["package_version"],
    )
    for name, expected in expected_versions.items():
        version = importlib.metadata.version(name)
        spec = importlib.util.find_spec(name)
        if version != expected or spec is None or not spec.origin:
            raise ValueError(f"{name}: installed version/origin mismatch")
        item = {"distribution_version": version, "origin": str(Path(spec.origin).resolve(strict=True))}
        if name in ("robosuite", "robocasa"):
            expected_commit = lock[name]["patched_commit" if name == "robosuite" else "commit"]
            item.update(audit_source(Path(spec.origin), package=name, expected_commit=expected_commit, assets=assets))
        item["module_sha256"] = sha256_file(Path(item["origin"]))
        packages[name] = item
    # Import only AFTER source/version validation; never accept a path-only claim
    # from a configuration file or execute a known dirty vendor's __init__.
    for name, expected in expected_versions.items():
        module = importlib.import_module(name)
        if (
            str(Path(module.__file__).resolve(strict=True)) != packages[name]["origin"]
            or module.__version__ != expected
        ):
            raise ValueError(f"{name}: actual imported module differs from its metadata/spec")
    mujoco = importlib.import_module("mujoco")
    if mujoco.mj_versionString() != "3.3.1" or mujoco.mj_version() != 331:
        raise ValueError("MuJoCo native library version mismatch")
    packages["mujoco"]["native_version"] = mujoco.mj_versionString()
    packages["mujoco"]["native_version_number"] = mujoco.mj_version()
    packages["mujoco"]["native_library_sha256"] = {
        p.name: sha256_file(p) for p in sorted(Path(mujoco.__file__).parent.glob("libmujoco.so*"))
    }
    if not packages["mujoco"]["native_library_sha256"]:
        raise ValueError("cannot identify native MuJoCo shared library")
    # Tiny XML compile only; no Kitchen, MjData, reset, step, rendering or GPU.
    flags = {}
    for enabled in (False, True):
        model = mujoco.MjModel.from_xml_string(
            '<mujoco><option><flag multiccd="' + ("enable" if enabled else "disable") + '"/></option></mujoco>'
        )
        effective = bool(model.opt.enableflags & int(mujoco.mjtEnableBit.mjENBL_MULTICCD))
        if effective != enabled:
            raise ValueError("MuJoCo multiccd compile witness mismatch")
        flags[str(enabled)] = int(model.opt.enableflags)
    if "mjENBL_SLEEP" in mujoco.mjtEnableBit.__members__:
        raise ValueError("unexpected sleeping capability in pinned MuJoCo")
    registry = importlib.import_module("robocasa.utils.dataset_registry_utils")
    horizons = {task: registry.get_task_horizon(task) for task in tasks}
    if not horizons or any(type(v) is not int or v <= 0 for v in horizons.values()):
        raise ValueError("official task horizons must be positive integers")
    # Re-audit after imports so imported modules cannot silently dirty their checkout.
    for name in ("robosuite", "robocasa"):
        audit_source(
            Path(packages[name]["origin"]), package=name, expected_commit=packages[name]["commit"], assets=assets
        )
    result = {
        "schema": "psm_robocasa_runtime_v1",
        "lock_sha256": sha256_file(lock_path),
        "probe_sha256": sha256_file(Path(__file__)),
        "interpreter": {
            "executable": os.path.abspath(sys.executable),
            "prefix": sys.prefix,
            "pythonpath_env": os.environ.get("PYTHONPATH", ""),
            "base_prefix": sys.base_prefix,
            "binary_sha256": sha256_file(Path(sys.executable).resolve()),
        },
        "packages": packages,
        "protocol": {
            "official_horizons": horizons,
            "horizon_multiplier_applied": False,
            "environment_instantiated": False,
            "split_evidence_scope": "required evaluation protocol, not an observed Kitchen state",
            "horizon_authority": "pinned robocasa registry (already includes 1.0.1 update)",
            "object_split": "target",
            "layout_split": "target",
        },
        "physics_capabilities": {
            "multiccd_compile_flags": flags,
            "sleeping_islands": False,
            "sleeping_true_supported": False,
            "real_kitchen_behavior_validated": False,
        },
    }
    return dict(result, digest=hashlib.sha256(canonical(result)).hexdigest())


def collect_runtime(
    *,
    sim_python: Path,
    lock_path=DEFAULT_LOCK,
    asset_manifest=None,
    tasks=("CloseFridge", "NavigateKitchen"),
    timeout_s=120,
    simulation_env=None,
) -> dict:
    """Ask the actual selected interpreter; never take runtime identity from YAML."""
    sim_python = Path(os.path.abspath(sim_python))
    lock_path = Path(lock_path).resolve(strict=True)
    executable_hash = sha256_file(sim_python.resolve(strict=True))
    command = [
        str(sim_python),
        "-B",
        str(Path(__file__).resolve()),
        "--lock",
        str(lock_path),
        "--tasks",
        ",".join(tasks),
    ]
    if asset_manifest:
        command += ["--asset-manifest", str(Path(asset_manifest).resolve(strict=True))]
    env = os.environ.copy() if simulation_env is None else dict(simulation_env)
    env.update(CUDA_VISIBLE_DEVICES="", MUJOCO_GL="disable", PYTHONDONTWRITEBYTECODE="1")
    completed = subprocess.run(command, env=env, capture_output=True, text=True, timeout=timeout_s, check=True)
    # Vendor imports may print warnings to stdout; the final machine record has a
    # dedicated prefix, exactly once. Keep raw stdout/stderr as diagnostic evidence.
    records = [line[len("PSM_RUNTIME ") :] for line in completed.stdout.splitlines() if line.startswith("PSM_RUNTIME ")]
    if len(records) != 1:
        raise ValueError("runtime interpreter did not return exactly one attestation")
    result = json.loads(records[0])
    digest = result.pop("digest", None)
    if (
        result.get("schema") != "psm_robocasa_runtime_v1"
        or digest != hashlib.sha256(canonical(result)).hexdigest()
        or result.get("lock_sha256") != sha256_file(lock_path)
        or result.get("probe_sha256") != sha256_file(Path(__file__))
        or result.get("interpreter", {}).get("executable") != str(sim_python)
        or result["interpreter"].get("pythonpath_env", "") != env.get("PYTHONPATH", "")
        or result["interpreter"].get("binary_sha256") != executable_hash
        or sha256_file(sim_python.resolve()) != executable_hash
    ):
        raise ValueError("runtime attestation/interpreter binding mismatch")
    return {
        "evaluation_runtime": dict(result, digest=digest),
        "runtime_probe_evidence": {
            "argv": command,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "returncode": completed.returncode,
        },
    }


def dataset_provenance(metadata_file: Path) -> dict:
    metadata_file = Path(metadata_file).resolve(strict=True)
    payload = json.loads(metadata_file.read_text())
    found = {name: {} for name in ("robocasa", "robosuite", "mujoco")}
    version_fields = {}

    def walk(value, path=""):
        if isinstance(value, dict):
            for key, child in value.items():
                pointer = path + "/" + key.replace("~", "~0").replace("/", "~1")
                if "version" in key.lower():
                    version_fields[pointer] = child
                for name in found:
                    if key == name + "_version" and isinstance(child, str):
                        found[name][pointer] = child
                    elif key == name and isinstance(child, dict) and isinstance(child.get("version"), str):
                        found[name][pointer + "/version"] = child["version"]
                walk(child, pointer)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, path + "/" + str(index))

    walk(payload)
    recorded = {}
    for name, matches in found.items():
        values = set(matches.values())
        if len(values) > 1:
            raise ValueError(f"ambiguous recorded generation version: {name}")
        recorded[name] = next(iter(values)) if values else "NOT_RECORDED"
    return {
        "metadata_file": str(metadata_file),
        "metadata_sha256": sha256_file(metadata_file),
        "metadata_recorded_versions": version_fields,
        "recorded_generation_versions": recorded,
        "version_field_evidence": found,
        "generation_git_commit": "UNKNOWN",
        "capture_time_commit": "UNKNOWN",
        "equivalent_to_evaluation_runtime": "NOT_PROVEN",
        "recorded_version_is_not_capture_time_tag_proof": True,
    }


def build_verified_evaluation_identity(
    *, sim_python, lock_path=DEFAULT_LOCK, asset_manifest=None, simulation_env=None, **identity_args
) -> dict:
    """Batch C integration API; does not change the pre-B legacy Queue entry."""
    from v3_evaluation_identity import build_evaluation_identity

    tasks = list(identity_args["tasks"])
    identity_args["tasks"] = tasks
    attestation = collect_runtime(
        sim_python=sim_python,
        lock_path=lock_path,
        asset_manifest=asset_manifest,
        tasks=[name for name, _ in tasks],
        simulation_env=simulation_env,
    )
    base = build_evaluation_identity(**identity_args)
    identity = dict(
        base["identity"],
        schema="psm_v3_eval_identity_vendor_v1",
        evaluation_runtime=attestation["evaluation_runtime"],
        dataset={
            "sources": [dataset_provenance(Path(directory) / "extras/dataset_meta.json") for _, directory in tasks]
        },
    )
    # Raw import warnings/tracebacks belong in evidence, never in the immutable
    # manifest equality used by same-task resume.
    return {
        "manifest": {"identity": identity, "digest": hashlib.sha256(canonical(identity)).hexdigest()},
        "runtime_probe_evidence": attestation["runtime_probe_evidence"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--asset-manifest", type=Path)
    parser.add_argument("--tasks", default="CloseFridge,NavigateKitchen")
    args = parser.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["MUJOCO_GL"] = "disable"
    with tempfile.TemporaryDirectory(prefix="psm-vendor-probe-") as cache:
        # Compiler/import caches are ephemeral and outside source/training paths.
        os.environ["NUMBA_CACHE_DIR"] = str(Path(cache) / "numba")
        os.environ["MPLCONFIGDIR"] = str(Path(cache) / "matplotlib")
        os.environ["HF_HOME"] = str(Path(cache) / "huggingface")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        print(
            "PSM_RUNTIME "
            + json.dumps(
                probe_runtime(lock_path=args.lock, asset_manifest=args.asset_manifest, tasks=args.tasks.split(",")),
                sort_keys=True,
            )
        )
