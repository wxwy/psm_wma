"""Real bounded consumer/ACK/cache lifecycle on CPU synthetic published Views."""

import pytest

from g2.io import digest, read_json
from g2.latent_cache.builder import plan_episode, verify_episode
from g2.latent_cache.contract import CacheError, make_recipe
from g2.latent_cache.posthoc import build_view_first_cache, coordinator
from g2.latent_cache.storage import ViewReader, build_lock, open_episode_index
from g2.latent_cache.streaming import ConsumerLimits, EventSpool
from g2.offline.view_only_source import PACKED, working_source_info
from g2.tests.test_view_vae_builder import PREPROCESS, FakeEncoder
from g2.tests.test_working_source_access import view_first_case


def products(root):
    return {
        str(p.relative_to(root)): digest(p)
        for p in root.rglob("*")
        if p.is_file() and "vae_cache" not in p.relative_to(root).parts
    }


@pytest.mark.parametrize("compressed", [True, False])
def test_posthoc_all_views_real_ack_without_modifying_published_profile(
    tmp_path, compressed
):
    root = view_first_case(tmp_path, compressed=compressed)
    before = products(root)
    encoder = FakeEncoder()
    recipe = make_recipe(encoder.descriptor(), PREPROCESS)
    with pytest.raises(CacheError, match="VAE disabled"):
        plan_episode(root, recipe)
    plan = plan_episode(root, recipe, view_first=True)
    assert plan["logical_view_count"] == 4 and plan["physical_image_count"] == 5
    spool_root = tmp_path / "posthoc_spool"
    result = build_view_first_cache(
        root,
        encoder,
        spool_root=spool_root,
        preprocessing=PREPROCESS,
        limits=ConsumerLimits(2, 16384),
    )
    assert result["complete"] and not result["retired"] and encoder.calls == 5
    assert products(root) == before
    assert not compressed or (root / PACKED).exists()
    assert (
        read_json(root / "episode_manifest.json")["products"]["view_vae"] == "disabled"
    )
    spool = EventSpool.open(spool_root)
    receipt = spool.completed_receipt(result["job"])
    assert receipt["event_status_counts"] == {"acked": 5}
    assert spool.stats()["active_records"] == 0 and spool.stats()["completed_jobs"] == 1
    assert verify_episode(root, reencoder=FakeEncoder())["max_abs_error"] == 0
    with ViewReader(open_episode_index(root)) as reader:
        assert (
            reader.read_view("sixview/floor_top_w_rbs", 2)["owner"]["owner_state_id"]
            == 1
        )
        assert not reader.read_view("sixview/plus_Y", 2)["present"]
        assert (
            reader.read_view("islands/island_0_entity_2/plus_X", 2)["owner"][
                "owner_state_id"
            ]
            == 0
        )
        assert not reader.read_view("islands/island_0_entity_2/plus_Y", 2)["present"]
    repeated = build_view_first_cache(
        root,
        encoder,
        spool_root=spool_root,
        preprocessing=PREPROCESS,
        resume=True,
        limits=ConsumerLimits(2, 16384),
    )
    assert repeated["complete"] and encoder.calls == 5
    assert products(root) == before


def test_durable_record_before_ack_is_reused_without_encode_again(tmp_path):
    root = view_first_case(tmp_path)
    before = products(root)
    encoder = FakeEncoder()

    def crash(phase):
        if phase == "numeric_before_ack":
            raise RuntimeError("TEST_ONLY_CRASH_AFTER_NUMERIC_FSYNC")

    kwargs = dict(spool_root=tmp_path / "spool", preprocessing=PREPROCESS)
    with pytest.raises(RuntimeError, match="FSYNC"):
        build_view_first_cache(root, encoder, failpoint=crash, **kwargs)
    assert encoder.calls == 1 and (root / PACKED).exists()
    assert not (root / "vae_cache/COMPLETE.json").exists()
    result = build_view_first_cache(root, encoder, resume=True, **kwargs)
    assert result["complete"] and encoder.calls == 5
    assert products(root) == before


def test_standard_stream_lifecycle_cannot_ingest_view_first(tmp_path):
    root = view_first_case(tmp_path)
    info = working_source_info(root)["source"]
    spool = EventSpool(
        tmp_path / "spool", make_recipe(FakeEncoder().descriptor(), PREPROCESS)
    )
    job = spool.register(
        root,
        episode_key="NavigateKitchen/episode_000000",
        source_fingerprint=info["source_fingerprint"],
        profile_id=info["profile_id"],
    )
    with pytest.raises(CacheError, match="VAE disabled"):
        spool.offer_source(job)


def test_posthoc_writer_lock_and_wrong_recipe_preserve_committed_data(tmp_path):
    root = view_first_case(tmp_path)
    encoder = FakeEncoder()
    kwargs = dict(spool_root=tmp_path / "spool", preprocessing=PREPROCESS)
    with build_lock(coordinator(root)):
        with pytest.raises(CacheError):
            build_view_first_cache(root, encoder, **kwargs)
    assert encoder.calls == 0
    build_view_first_cache(root, encoder, **kwargs)
    before = {str(p): digest(p) for p in root.rglob("*") if p.is_file()}
    with pytest.raises(CacheError):
        build_view_first_cache(root, FakeEncoder(identity="b"), resume=True, **kwargs)
    assert before == {str(p): digest(p) for p in root.rglob("*") if p.is_file()}
