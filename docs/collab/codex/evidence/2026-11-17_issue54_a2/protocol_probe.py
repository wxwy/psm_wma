"""Synthetic two-entrypoint protocol receipt, never a real Wan/GPT gate."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import torch

from g2.io import digest, read_json, write_json
from g2.latent_cache.production import build_profile
from g2.latent_cache.storage import _load, open_episode_index
from g2.latent_cache.streaming import EventConsumer, publish_final_pixels
from g2.offline.stage_a import package_stage_a, validate_profile_episode
from g2.tests.test_stage_a_streaming import setup_case
from g2.tests.test_view_vae_builder import PREPROCESS, FakeEncoder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    if args.summary.exists():
        raise ValueError("refuse to overwrite earlier protocol evidence")
    root = Path(tempfile.mkdtemp(prefix="issue54_a2_cpu_protocol_"))
    kwargs, target, encoder, spool, job = setup_case(root)
    for stage in sorted(kwargs["rendered"].glob("state_*")):
        publish_final_pixels(
            stage,
            read_json(stage / "direct_color_views.json"),
            lambda e: spool.enqueue(job, e),
            episode_key="NavigateKitchen/episode_000000",
            source_fingerprint=kwargs["source_fingerprint"],
            profile_id=kwargs["profile"].to_dict()["profile_id"],
        )
        while EventConsumer(spool, encoder).step():
            pass
    package_stage_a(
        destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
    )
    import shutil

    second = root / "posthoc"
    shutil.copytree(target, second)  # Identical sealed source, including gzip headers.
    ready = validate_profile_episode(target, require_complete=False)
    spool.seal(job)
    while EventConsumer(spool, encoder).step():
        pass
    streamed = validate_profile_episode(target)
    post_encoder = FakeEncoder()
    post_result = build_profile(second, post_encoder, preprocessing=PREPROCESS)
    a, b = open_episode_index(target), open_episode_index(second)
    for field in ("episode_key", "episode", "source", "recipe", "states"):
        assert a.manifest[field] == b.manifest[field]
    for vid, entry in a.manifest["views"].items():
        va, _, _ = _load(a.cache_root / entry["path"])
        vb, _, _ = _load(b.cache_root / entry["path"])
        assert torch.equal(va["latents"], vb["latents"])
        assert va["metadata"] == vb["metadata"]
        for field in (
            "path",
            "shape",
            "dtype",
            "state_records",
            "record_sha256",
            "metadata_sha256",
        ):
            assert entry[field] == b.manifest["views"][vid][field]
    source = read_json(target / "spatial_source.json")
    write_json(
        args.summary,
        dict(
            schema="g2_a2_synthetic_protocol_example_v1",
            scope="CPU_FAKE_ENCODER_NOT_REAL_WAN_NATIVE_OR_TRAINING_ACCEPTANCE",
            artifact_root=str(root),
            source_id=source["source_id"],
            recipe=a.manifest["recipe"],
            before_vae=dict(
                profile_complete=ready["profile_complete"], pending=ready["pending"]
            ),
            after_vae=dict(
                profile_complete=streamed["profile_complete"],
                vae_receipt=streamed["vae_receipt"],
            ),
            views={
                vid: dict(
                    state_records=v["state_records"],
                    path=v["path"],
                    shape=v["shape"],
                    numeric_file_sha256=v["sha256"],
                )
                for vid, v in a.manifest["views"].items()
            },
            producer_events={
                eid: {
                    k: d[k]
                    for k in (
                        "view_id",
                        "variant",
                        "final_pixel_phase",
                        "pixel_record_key",
                        "size_wh",
                    )
                }
                for eid, d in source["final_pixel_events"].items()
            },
            stream_encoder_calls=encoder.calls,
            posthoc_encoder_calls=post_encoder.calls,
            posthoc_result=post_result,
            identical_source_and_logical_index=True,
            serialized_payload_byte_equality_required=False,
            numeric_max_abs_error=0,
            cache_index_sha256=digest(a.cache_root / "manifest.json"),
            spool_stats=spool.stats(),
            training_ready=False,
        ),
    )


if __name__ == "__main__":
    main()
