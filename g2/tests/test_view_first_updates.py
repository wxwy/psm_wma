"""Synthetic producer-boundary geometry/pixel update; not real F27 evidence."""

from PIL import Image

from g2.io import digest, read_json, write_json
from g2.latent_cache.builder import verify_episode
from g2.latent_cache.posthoc import build_view_first_cache
from g2.latent_cache.storage import open_episode_index
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a
from g2.tests.test_stage_a_package import stage_case
from g2.tests.test_view_vae_builder import PREPROCESS, FakeEncoder


def test_actual_published_pixel_updates_make_new_records_without_reshaping_identity(
    tmp_path,
):
    kwargs, _ = stage_case(
        tmp_path, OutputProfile(selection_top_variant="clean", view_vae=False)
    )
    inputs = read_json(kwargs["inputs"])
    inputs["states"] = inputs["states"][:2]
    row = inputs["states"][1]
    # A known object translates within its support; root gaps and IDs persist.
    for name in ("snapshot", "scene_graph"):
        path = row[name]["path"]
        snapshot = read_json(path)
        entity = next(e for e in snapshot["entities"] if e["native_id"] == 2)
        entity["bbox_min"][0] += 0.05
        entity["bbox_max"][0] += 0.05
        for vertex in entity["vertices"]:
            vertex[0] += 0.05
        write_json(path, snapshot)
        row[name]["sha256"] = digest(path)
    write_json(kwargs["inputs"], inputs)
    receipt = read_json(kwargs["rendered"] / "episode_receipt.json")
    receipt["states"] = receipt["states"][:2]
    receipt["source_inputs_sha256"] = digest(kwargs["inputs"])
    write_json(kwargs["rendered"] / "episode_receipt.json", receipt)
    kwargs["captions"] = {f: r for f, r in kwargs["captions"].items() if f in (0, 10)}
    first = kwargs["rendered"] / "state_000000_frame_000000"
    current = kwargs["rendered"] / "state_000001_frame_000010"
    report = read_json(current / "direct_color_views.json")
    for asset in report["views"]:
        path = current / asset["rgb_file"]
        original = path if path.exists() else first / asset["rgb_file"]
        with Image.open(original) as image:
            image = image.copy()
        image.putpixel((0, 0), (30, 40, 50))
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        asset["sha256"] = digest(path)
    report["scene_materialized_views"] = [a["rgb_file"] for a in report["views"]]
    report["scene_view_refs"] = {}
    report["scene_source_state"] = 1
    write_json(current / "direct_color_views.json", report)
    root = tmp_path / "published"
    package_stage_a(destination=root, compress_source=True, **kwargs)
    original_products = read_json(root / "episode_manifest.json")["files"]
    encoder = FakeEncoder()
    result = build_view_first_cache(
        root, encoder, spool_root=tmp_path / "spool", preprocessing=PREPROCESS
    )
    assert result["complete"] and encoder.calls == 8
    index = open_episode_index(root)
    assert len(index.manifest["views"]) == 4
    assert all(v["state_records"] == [0, 1] for v in index.manifest["views"].values())
    assert all(v["shape"][0] == 2 for v in index.manifest["views"].values())
    assert all(digest(root / path) == sha for path, sha in original_products.items())
    assert verify_episode(root, reencoder=FakeEncoder())["max_abs_error"] == 0
