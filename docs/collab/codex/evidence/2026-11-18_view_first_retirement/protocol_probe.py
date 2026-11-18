"""Synthetic timing/physical-byte protocol; NEVER real F27/Wan capacity proof."""

import argparse
import json
import tempfile
import time
from pathlib import Path

from g2.io import digest, read_json
from g2.latent_cache.posthoc import build_view_first_cache, retire_view_first_cache
from g2.offline.source_capacity import episode_bytes
from g2.offline.view_only_source import PACKED, working_source_info
from g2.tests.test_view_first_retirement import retirement_case
from g2.tests.test_view_vae_builder import PREPROCESS, FakeEncoder


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    with tempfile.TemporaryDirectory(prefix="g2-posthoc-protocol-") as tmp:
        root, policy = retirement_case(Path(tmp))
        info = working_source_info(root)
        packed_bytes = (root / PACKED).stat().st_size
        before = episode_bytes(root, include_files=True)
        products = read_json(root / "episode_manifest.json")["files"]
        encoder = FakeEncoder()
        start = time.monotonic()
        built = build_view_first_cache(
            root, encoder, spool_root=Path(tmp) / "encode", preprocessing=PREPROCESS
        )
        encode_s = time.monotonic() - start
        after_vae = episode_bytes(root, include_files=True)
        payloads = {
            str(p.relative_to(root)): digest(p)
            for p in (root / "vae_cache").rglob("*.pt")
        }
        start = time.monotonic()
        retired = retire_view_first_cache(
            root, spool_root=policy["spool_root"], source_policy=policy
        )
        retire_s = time.monotonic() - start
        after = episode_bytes(root, include_files=True)
        assert payloads == {p: digest(root / p) for p in payloads}
        assert all(digest(root / p) == sha for p, sha in products.items())
        value = dict(
            schema="g2_view_first_posthoc_synthetic_protocol_v1",
            scope="AUTHOR_CPU_FAKE_ENCODER_NOT_REAL_WAN_F27_OR_CAPACITY_APPROVAL",
            before_view_first=before,
            after_vae=after_vae,
            after_retirement=after,
            source_id=info["source"]["source_id"],
            raw_source_sha256=info["raw_sha256"],
            decoded_source_bytes=info["raw_bytes"],
            physical_gzip_bytes=packed_bytes,
            decoded_to_gzip_ratio=info["raw_bytes"] / packed_bytes,
            final_index_bytes=(root / "spatial_source_index.json").stat().st_size,
            fake_encode_seconds=encode_s,
            retirement_cpu_seconds=retire_s,
            fake_encoded_records=encoder.calls,
            build_complete=built["complete"],
            retirement_complete=retired["complete"],
            all_products_and_pt_preserved=True,
            pt_sha256=payloads,
            training_ready=False,
            caveat="Small synthetic audit can gzip below index size; no real storage/speed benefit inferred.",
            not_run=[
                "real Wan/GPU",
                "native F27",
                "real Gate A-D",
                "9126 production or cleanup",
                "training",
            ],
        )
    args.output.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
