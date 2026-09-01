#!/usr/bin/env python3
"""R09-B2 P5 exporter helpers; real export requires a separate approval."""

from __future__ import annotations

import argparse
import attrs
import dataclasses
import enum
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from collections.abc import Mapping
from typing import Any


SCHEMA = "r09_b2_p5_full_config_diff_v2"
FROZEN_OVERRIDES = ("trainer.max_iter=100", "trainer.save_zero_checkpoint=true")


class CanonicalizationError(ValueError):
    """A resolved config value cannot be represented faithfully and deterministically."""


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_json(value: object) -> str:
    import hashlib
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _callable(value: object) -> dict[str, str]:
    module, qualname = getattr(value, "__module__", None), getattr(value, "__qualname__", None)
    if not isinstance(module, str) or not isinstance(qualname, str) or "<locals>" in qualname:
        raise CanonicalizationError(f"callable has no stable FQN: {type(value)!r}")
    return {"__psm_type__": "callable", "fqn": f"{module}.{qualname}"}


def canonicalize(value: Any, seen: set[int] | None = None) -> Any:
    """Convert the complete resolved tree without repr(), omission, or address leakage."""
    seen = set() if seen is None else seen
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError("non-finite float")
        return value
    if isinstance(value, Path):
        return {"__psm_type__": "path", "value": value.as_posix()}
    if isinstance(value, enum.Enum):
        cls = type(value)
        return {"__psm_type__": "enum", "fqn": f"{cls.__module__}.{cls.__qualname__}", "name": value.name}
    if callable(value):
        return _callable(value)
    identity = id(value)
    if identity in seen:
        raise CanonicalizationError("cycle in resolved config")
    if isinstance(value, Mapping):
        seen.add(identity)
        try:
            if not all(isinstance(key, str) for key in value):
                raise CanonicalizationError("non-string mapping key")
            return {key: canonicalize(value[key], seen) for key in sorted(value)}
        finally:
            seen.remove(identity)
    if isinstance(value, (list, tuple)):
        seen.add(identity)
        try:
            return [canonicalize(item, seen) for item in value]
        finally:
            seen.remove(identity)
    if attrs.has(type(value)):
        return canonicalize(attrs.asdict(value, recurse=True), seen)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return canonicalize(dataclasses.asdict(value), seen)
    if "${" in str(value):
        raise CanonicalizationError("unresolved interpolation")
    raise CanonicalizationError(f"unsupported resolved-config value: {type(value)!r}")


def parse_d005_command(record: Mapping[str, Any]) -> tuple[str, list[str]]:
    """Derive, never recreate, the production TOML and exact trailing overrides."""
    command = record.get("command")
    if not isinstance(command, Mapping) or command.get("executable") is not False:
        raise ValueError("P5 requires a non-executable P4 D005 command")
    argv = command.get("argv")
    if not isinstance(argv, list) or not all(isinstance(token, str) for token in argv):
        raise ValueError("D005 argv must be a string token array")
    toml_tokens = [token for token in argv if token.startswith("--sft-toml=")]
    if len(toml_tokens) != 1:
        raise ValueError("D005 argv must contain exactly one --sft-toml=<path>")
    index = argv.index(toml_tokens[0])
    overrides = argv[index + 1 :]
    if tuple(overrides) != FROZEN_OVERRIDES:
        raise ValueError("D005 trailing overrides must be the frozen ordered 100-update pair")
    if any("=" not in item for item in overrides):
        raise ValueError("D005 trailing token is not a Hydra override")
    return toml_tokens[0].split("=", 1)[1], overrides


def sanitized_environment(contract: Mapping[str, Any], parent: Mapping[str, str]) -> dict[str, str]:
    """Build the child environment from D005; never overlay an arbitrary parent."""
    required = {"set", "unset", "inherit_allowlist"}
    if not required.issubset(contract) or not isinstance(contract["set"], Mapping):
        raise ValueError("malformed D005 environment contract")
    allow = contract["inherit_allowlist"]
    unset = contract["unset"]
    if not isinstance(allow, list) or not isinstance(unset, list) or not all(isinstance(x, str) for x in allow + unset):
        raise ValueError("malformed D005 allowlist/unset list")
    if set(allow) & set(unset):
        raise ValueError("D005 environment allowlist conflicts with unset")
    result = {key: parent[key] for key in allow if key in parent}
    result.update({str(key): str(value) for key, value in contract["set"].items()})
    if set(result) & set(unset):
        raise ValueError("D005 set conflicts with unset")
    return result


def build_child_request(record: Mapping[str, Any], *, root: Path, backend: str) -> dict[str, Any]:
    """Bind one child request to its verified D005; the child never accepts loose inputs."""
    if record.get("backend") != backend:
        raise ValueError("D005 backend does not match requested export")
    toml, overrides = parse_d005_command(record)
    command, environment = record["command"], record["environment"]
    cwd = Path(command["cwd"]).resolve()
    interpreter = Path(command["interpreter"]["realpath"]).resolve()
    if cwd != (root / "cosmos-framework").resolve() or not interpreter.is_absolute():
        raise ValueError("D005 cwd/interpreter is not canonical for this root")
    return {"backend": backend, "root": str(root.resolve()), "toml": toml, "overrides": overrides,
            "cwd": str(cwd), "interpreter": {"realpath": str(interpreter), "sha256": command["interpreter"]["sha256"]},
            "environment": {"contract": environment, "effective": sanitized_environment(environment, os.environ)},
            "d005_sha256": record["d005_sha256"], "source": record["source"], "budget": record["budget"], "inputs": record["inputs"], "outputs": record["outputs"]}


def build_pair_requests(recurrent: Mapping[str, Any], ttt: Mapping[str, Any], *, root: Path) -> dict[str, dict[str, Any]]:
    """Parent-only D005 gate; later approved execution consumes only these requests."""
    from tools.g0.verify_r09_b2_p4_d005 import verify_pair

    result = verify_pair(dict(recurrent), dict(ttt), root.resolve())
    if result["status"] != "PASS":
        raise ValueError("P5 refuses to compose a P4 pair that fails its frozen verifier")
    return {"recurrent": build_child_request(recurrent, root=root, backend="recurrent"),
            "ttt_fast_weight": build_child_request(ttt, root=root, backend="ttt_fast_weight")}


def _child(request: Path, output: Path) -> None:
    """Approved later only: compose one backend without launch/validate/instantiate."""
    payload = json.loads(request.read_text())
    if Path.cwd().resolve() != Path(payload["cwd"]).resolve() or Path(sys.executable).resolve() != Path(payload["interpreter"]["realpath"]).resolve():
        raise RuntimeError("P5 child cwd/interpreter differs from D005-bound request")
    if dict(os.environ) != payload["environment"]["effective"]:
        raise RuntimeError("P5 child environment differs from D005-bound request")
    if any(name.startswith("cosmos_framework.configs.base.experiment") for name in sys.modules):
        raise RuntimeError("experiment was imported before P5 child compose")
    try:
        from hydra.core.global_hydra import GlobalHydra
        if GlobalHydra.instance().is_initialized():
            raise RuntimeError("Hydra was initialized before P5 child compose")
    except ModuleNotFoundError:
        pass
    from cosmos_framework.configs.toml_config.sft_config import load_experiment_from_toml
    config = load_experiment_from_toml(payload["toml"], extra_overrides=payload["overrides"])
    import torch
    if torch.cuda.is_initialized():
        raise RuntimeError("P5 static compose initialized CUDA")
    output.write_bytes(canonical_bytes(canonicalize(config.to_dict())))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child-request", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--child-output", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child_request is None or args.child_output is None:
        raise SystemExit("real P5 parent export is intentionally withheld pending a separate execution approval")
    _child(args.child_request, args.child_output)


if __name__ == "__main__":
    main()
