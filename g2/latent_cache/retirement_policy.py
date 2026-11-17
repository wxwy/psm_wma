"""Explicit new-output policy; no implicit conversion of accepted v1 data."""

from __future__ import annotations

import os
from pathlib import Path

from g2.io import read_json

from .contract import CacheError, contained
from .storage import _hex, atomic_json, build_lock

SCHEMA = "g2_source_retention_policy_v1"


def real_path(value):
    if (
        not isinstance(value, str)
        or not Path(value).is_absolute()
        or Path(value) != Path(os.path.abspath(value))
    ):
        raise CacheError("absolute canonical retention path required")
    path = Path(value)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise CacheError("retention paths may not traverse symlinks")
    return path


def overlap(a, b):
    return a == b or a in b.parents or b in a.parents


def filesystem(path):
    return next(p for p in (path, *path.parents) if p.exists()).stat().st_dev


def validate_policy(policy, spool_root):
    if policy is None:
        return None
    fields = {
        "schema",
        "format",
        "output_root",
        "work_root",
        "spool_root",
        "config_id",
        "mapping_sha256",
        "source_versions",
        "protected_roots",
        "keep_full_audit",
        "audit_archive_root",
        "audit_retention_policy",
    }
    if (
        not isinstance(policy, dict)
        or set(policy) != fields
        or policy["schema"] != SCHEMA
        or policy["format"] != "capsule_v2"
    ):
        raise CacheError("unknown explicit source retirement policy")
    _hex(policy["config_id"])
    _hex(policy["mapping_sha256"])
    if set(policy["source_versions"]) != {"root", "child", "nav"} or any(
        not isinstance(s, str)
        or len(s) != 40
        or any(c not in "0123456789abcdef" for c in s)
        for s in policy["source_versions"].values()
    ):
        raise CacheError("retirement source versions must be fixed Git commits")
    roots = {
        k: real_path(policy[k]) for k in ("output_root", "work_root", "spool_root")
    }
    if roots["spool_root"] != Path(spool_root).absolute():
        raise CacheError("retirement policy spool differs")
    if not isinstance(policy["protected_roots"], list) or not policy["protected_roots"]:
        raise CacheError("explicit protected code/input/cache roots required")
    protected = [real_path(str(Path(p).resolve())) for p in policy["protected_roots"]]
    for k, p in roots.items():
        if any(overlap(p, q) for j, q in roots.items() if j != k) or any(
            overlap(p, q) for q in protected
        ):
            raise CacheError("retention namespaces overlap protected paths")
    if type(policy["keep_full_audit"]) is not bool:
        raise CacheError("keep_full_audit must be boolean")
    archive = policy["audit_archive_root"]
    if policy["keep_full_audit"]:
        path = real_path(archive)
        if (
            not isinstance(policy["audit_retention_policy"], str)
            or not policy["audit_retention_policy"].strip()
        ):
            raise CacheError(
                "external full audit requires an explicit retention policy"
            )
        if any(overlap(path, p) for p in (*roots.values(), *protected)) or filesystem(
            path
        ) == filesystem(roots["output_root"]):
            raise CacheError(
                "full audit archive must be separate and on another filesystem"
            )
    elif archive is not None or policy["audit_retention_policy"] is not None:
        raise CacheError("disabled full audit may not hide an archive copy")
    return policy


def validate_target(policy, target, scope):
    validate_policy(policy, policy["spool_root"])
    output = real_path(policy["output_root"])
    target = real_path(str(Path(target).absolute()))
    task, episode = scope["episode_key"].split("/")
    expected = output / "tasks" / task / "episodes" / episode
    if target != expected:
        raise CacheError("retirement target differs from canonical episode scope")
    marker = read_json(contained(output, ".g2_stage_a_dataset_root.json"))
    if marker != dict(
        schema="g2_owned_production_output_v1",
        config_id=policy["config_id"],
        output=str(output),
    ):
        raise CacheError(
            "retirement requires this run owned staging output; never old data"
        )
    if read_json(contained(output, ".g2_source_retention_policy.json")) != policy:
        raise CacheError("output source retention policy changed")
    return target


def claim_policy(policy, *, existing_only=False):
    """One output namespace cannot silently switch spool/archive policies."""
    output = real_path(policy["output_root"])
    marker = read_json(contained(output, ".g2_stage_a_dataset_root.json"))
    if marker != dict(
        schema="g2_owned_production_output_v1",
        config_id=policy["config_id"],
        output=str(output),
    ):
        raise CacheError("source retirement policy requires its owned output namespace")
    path = contained(output, ".g2_source_retention_policy.json", allow_missing=True)
    if existing_only:
        if not path.exists() or read_json(path) != policy:
            raise CacheError("output source retention policy differs")
        return
    with build_lock(output.parent / (".g2-source-policy-" + output.name)):
        if path.exists():
            if read_json(path) != policy:
                raise CacheError("output source retention policy differs")
        else:
            atomic_json(path, policy)


def from_config(cfg):
    if cfg["final_source_format"] == "working_v1":
        return None
    return dict(
        schema=SCHEMA,
        format="capsule_v2",
        output_root=cfg["output_root"],
        work_root=cfg["work_root"],
        spool_root=cfg["spool_root"],
        config_id=cfg["config_id"],
        mapping_sha256=cfg["mapping_sha256"],
        source_versions=dict(
            root=cfg["root_sha"], child=cfg["child_sha"], nav=cfg["nav_sha"]
        ),
        protected_roots=[
            cfg[k]
            for k in (
                "raw_root",
                "flat_root",
                "depth_root",
                "weights",
                "nav_repo",
                "robocasa_repo",
                "robosuite_repo",
            )
        ]
        + [str(Path(__file__).resolve().parents[2])]
        + cfg.get("source_protected_roots", []),
        keep_full_audit=cfg["keep_full_audit"],
        audit_archive_root=cfg["audit_archive_root"],
        audit_retention_policy=cfg["audit_retention_policy"],
    )
