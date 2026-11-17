"""Author synthetic size/field/PT parity example; no real Wan/capacity claim."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from g2.io import digest, read_json
from g2.latent_cache import final_source as final
from g2.latent_cache.builder import verify_episode
from g2.latent_cache.storage import atomic_json
from g2.offline.source_capacity import episode_bytes
from g2.tests.test_source_capsule import capsule_case, complete_working


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--summary", type=Path, required=True)
    args = p.parse_args()
    with tempfile.TemporaryDirectory(prefix="g2-issue63-protocol-") as temporary:
        kwargs, root, encoder, spool, job = capsule_case(
            Path(temporary), large_audit=True
        )
        complete_working(kwargs, root, encoder, spool, job)
        original = read_json(root / final.FULL)
        original_sha = digest(root / final.FULL)
        before = episode_bytes(root, include_files=True)
        products = {p: digest(root / p) for p in original["files"]}
        payloads = {
            str(p.relative_to(root)): digest(p)
            for p in (root / "vae_cache").rglob("*.pt")
        }
        assert spool.adopt_completed(job)
        after = episode_bytes(root, include_files=True)
        assert products == {p: digest(root / p) for p in products}
        assert payloads == {p: digest(root / p) for p in payloads}
        audit = verify_episode(root, reencoder=encoder)
        capsule = read_json(root / final.CAPSULE)
        b = {r["path"]: r["bytes"] for r in before["files"]}
        a = {r["path"]: r["bytes"] for r in after["files"]}
        rows = [
            dict(
                path=p,
                before_bytes=b.get(p, 0),
                after_bytes=a.get(p, 0),
                delta_bytes=a.get(p, 0) - b.get(p, 0),
            )
            for p in sorted(set(a) | set(b))
        ]
        result = dict(
            schema="g2_issue63_synthetic_protocol_v1",
            scope="AUTHOR_CPU_FAKE_ENCODER_SYNTHETIC_AUDIT_NOT_REAL_F27_WAN_OR_9126_CAPACITY",
            before=before,
            after=after,
            per_file_bytes=rows,
            working_source_sha256=original_sha,
            final_capsule_bytes=(root / final.CAPSULE).stat().st_size,
            original_source_bytes=before["bytes_by_category"]["working_source"],
            unchanged_product_files=len(products),
            unchanged_payload_sha256=payloads,
            all_product_and_pt_bytes_equal=True,
            states=len(capsule["views"][next(iter(capsule["views"]))]["state_records"]),
            logical_views=len(capsule["views"]),
            owner_records=sum(len(v["owners"]) for v in capsule["views"].values()),
            projections=len(capsule["projections"]),
            source_schemas=dict(
                working="g2_sealed_spatial_source_v1", final=final.SOURCE_SCHEMA
            ),
            numerical_audit=audit,
            training_ready=False,
            not_run=[
                "real169owner reencode",
                "real419pixel comparison",
                "18task private capacity",
                "32worker resources",
                "full9126",
                "training",
            ],
        )
        atomic_json(args.summary, result)


if __name__ == "__main__":
    main()
