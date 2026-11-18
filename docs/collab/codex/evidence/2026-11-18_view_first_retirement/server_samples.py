"""Explicit two-sample server Gate helpers; no rendering, encoding or corpus GC.

Run only from a fixed repository checkout. Private inputs/derived per-file
inventories remain on the server. Wan and retirement CLIs are separate actions.
"""

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from g2.io import digest, read_json, write_json
from g2.latent_cache.builder import verify_episode
from g2.latent_cache.contract import fingerprint
from g2.latent_cache.final_source import PROFILE_SCHEMA
from g2.latent_cache.retirement_policy import POSTHOC_SCHEMA
from g2.offline.output_profile import OutputProfile
from g2.offline.source_capacity import episode_bytes
from g2.offline.stage_a import validate_profile_episode
from g2.offline.view_only_source import (
    CLAIM,
    PACKED,
    claim_view_only_root,
    working_source_info,
)

SAMPLES = (
    "tasks/CloseBlenderLid/episodes/episode_000000",
    "tasks/CloseFridge/episodes/episode_000502",
)
CHILD = "d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2"
NAV = "70eb7b447e65d793b0ebe18b258291ce46f057c1"


def inventory(root):
    result = {}
    for p in sorted(root.rglob("*")):
        if p.is_symlink():
            raise ValueError("sample contains a symlink")
        if p.is_file():
            result[str(p.relative_to(root))] = digest(p)
    return result


def original_unchanged(gate, original):
    before = read_json(gate / "original_before.json")
    assert before == {s: inventory(original / s) for s in SAMPLES}


def prepare(args):
    gate, original = args.gate.absolute(), args.original.absolute()
    gate.mkdir(exist_ok=False)
    data = gate / "dataset"
    source = [working_source_info(original / s) for s in SAMPLES]
    manifests = [validate_profile_episode(original / s) for s in SAMPLES]
    assert len({m["output_profile"]["profile_id"] for m in manifests}) == 1
    assert all(not m["output_profile"]["view_vae"] for m in manifests)
    selection = fingerprint(
        {s: i["source"]["source_id"] for s, i in zip(SAMPLES, source)}
    )
    claim_view_only_root(
        data, OutputProfile.from_dict(manifests[0]["output_profile"]), selection
    )
    write_json(
        gate / "original_before.json", {s: inventory(original / s) for s in SAMPLES}
    )
    rows = []
    for s, info in zip(SAMPLES, source):
        target = data / s
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(original / s, target)  # No hard-linked mutable indices.
        assert inventory(target) == inventory(original / s)
        m = validate_profile_episode(target)
        copied = working_source_info(target)
        assert copied["raw_sha256"] == info["raw_sha256"]
        rows.append(
            dict(
                episode=s,
                source_id=info["source"]["source_id"],
                raw_sha256=info["raw_sha256"],
                raw_bytes=info["raw_bytes"],
                gzip_bytes=(target / PACKED).stat().st_size,
                gzip_sha256=digest(target / PACKED),
                decoded_to_gzip_ratio=info["raw_bytes"]
                / (target / PACKED).stat().st_size,
                states=len(m["states"]),
                views=len(info["source"]["views"]),
                owners=sum(len(v["owners"]) for v in info["source"]["views"].values()),
                capacity=episode_bytes(target, include_files=True),
            )
        )
    policy = dict(
        schema=POSTHOC_SCHEMA,
        format="capsule_v2",
        output_root=str(data),
        work_root=str(gate / "unused_work"),
        spool_root=str(gate / "retirement_spool"),
        config_id=fingerprint(
            dict(root=args.formal_root, selection=selection, gate=str(gate))
        ),
        mapping_sha256=digest(args.mapping),
        source_versions=dict(root=args.formal_root, child=CHILD, nav=NAV),
        protected_roots=[
            str(p.resolve()) for p in (original, args.mapping, args.code, args.weights)
        ],
        keep_full_audit=False,
        audit_archive_root=None,
        audit_retention_policy=None,
        view_first_claim_sha256=digest(data / CLAIM),
    )
    write_json(gate / "source_policy.json", policy)
    original_unchanged(gate, original)
    write_json(
        gate / "gate_a.json",
        dict(
            status="PASS",
            scope="TWO_EXISTING_REAL_VIEW_FIRST_COPIES",
            root=args.formal_root,
            child=CHILD,
            rows=rows,
            original_unchanged=True,
            rendered=False,
            training_ready=False,
        ),
    )


def before_retire(args):
    gate = args.gate.absolute()
    rows, hashes = [], {}
    for s in SAMPLES:
        target = gate / "dataset" / s
        audit = verify_episode(target)
        m = validate_profile_episode(target)
        assert not m["output_profile"]["view_vae"] and m["schema"] != PROFILE_SCHEMA
        hashes[s] = dict(
            products=m["files"],
            payloads={
                str(p.relative_to(target)): digest(p)
                for p in (target / "vae_cache").rglob("*.pt")
            },
        )
        rows.append(
            dict(
                episode=s,
                audit=audit,
                capacity=episode_bytes(target, include_files=True),
            )
        )
    original_unchanged(gate, args.original.absolute())
    write_json(
        gate / "before_retire.json",
        dict(rows=rows, hashes=hashes, original_unchanged=True),
    )


def finish(args):
    gate = args.gate.absolute()
    previous = read_json(gate / "before_retire.json")
    rows = []
    for s in SAMPLES:
        target = gate / "dataset" / s
        m = validate_profile_episode(target)
        assert m["schema"] == PROFILE_SCHEMA and not m["output_profile"]["view_vae"]
        assert m["posthoc_vae_receipt"]["verified"]
        for rel, sha in {
            **previous["hashes"][s]["products"],
            **previous["hashes"][s]["payloads"],
        }.items():
            assert digest(target / rel) == sha
        for rel in (
            "spatial_source.json",
            PACKED,
            "SPATIAL_SOURCE_GZIP.json",
            "SPATIAL_SOURCE_READY.json",
            ".source_retirement",
        ):
            assert not (target / rel).exists()
        rows.append(
            dict(
                episode=s,
                audit=verify_episode(target),
                final_index_bytes=(target / "spatial_source_index.json").stat().st_size,
                capacity=episode_bytes(target, include_files=True),
            )
        )
    original_unchanged(gate, args.original.absolute())
    write_json(
        gate / "gate_c.json",
        dict(
            status="PASS",
            scope="AUTHOR_REAL_TWO_SAMPLES_NOT_INDEPENDENT_GPT_APPROVAL",
            rows=rows,
            all_products_and_payloads_byte_identical=True,
            original_unchanged=True,
            training_ready=False,
            corpus_retirement=False,
        ),
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "before-retire", "finish"))
    p.add_argument("--gate", required=True, type=Path)
    p.add_argument("--original", required=True, type=Path)
    p.add_argument("--code", required=True, type=Path)
    p.add_argument("--formal-root", required=True)
    p.add_argument("--mapping", required=True, type=Path)
    p.add_argument("--weights", required=True, type=Path)
    args = p.parse_args()
    assert (
        subprocess.check_output(
            ["git", "-C", str(args.code), "rev-parse", "HEAD"], text=True
        ).strip()
        == args.formal_root
    )
    assert (
        subprocess.check_output(
            ["git", "-C", str(args.code / "cosmos-framework"), "rev-parse", "HEAD"],
            text=True,
        ).strip()
        == CHILD
    )
    {"prepare": prepare, "before-retire": before_retire, "finish": finish}[args.action](
        args
    )
    print(
        json.dumps(
            dict(
                action=args.action,
                status="PASS",
                evidence=str(args.gate),
                training_ready=False,
            )
        )
    )


if __name__ == "__main__":
    main()
