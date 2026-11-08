"""Bounded, immutable artifact contracts shared by the isolated G2 modules."""
import hashlib
import json
from pathlib import Path


class ContractError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def parse_json(payload):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ContractError("duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid(value):
        raise ContractError("nonfinite JSON: " + value)
    return json.loads(payload, object_pairs_hook=pairs, parse_constant=invalid)


def read_json(path, limit=128 * 1024 * 1024):
    path = Path(path)
    if path.stat().st_size > limit:
        raise ContractError("JSON exceeds byte limit")
    return parse_json(path.read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    indent=2, allow_nan=False) + "\n", encoding="utf-8")


def new_output(path, sources):
    path = Path(path).resolve()
    for source in sources:
        source = Path(source).resolve()
        if source == path or source in path.parents or path in source.parents:
            raise ContractError("output overlaps source: " + str(source))
    if path.exists():
        raise ContractError("output must be new")
    return path


def sha(value, name="sha256"):
    if (not isinstance(value, str) or len(value) != 64 or
            any(c not in "0123456789abcdef" for c in value)):
        raise ContractError("invalid " + name)
    return value


def verified_file(root, record):
    path = Path(record["path"])
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ContractError("artifact path must be relative and contained")
    path = Path(root) / path
    if path.is_symlink() or Path(root).resolve() not in path.resolve().parents:
        raise ContractError("artifact escapes bundle")
    if path.stat().st_size != record["bytes"] or digest(path) != sha(record["sha256"]):
        raise ContractError("artifact hash/size mismatch: " + str(path))
    return path
