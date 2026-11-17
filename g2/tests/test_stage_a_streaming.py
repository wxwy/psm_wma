"""A2 CPU failure-mode checks; FakeEncoder is not a real VAE acceptance."""

from __future__ import annotations

import dataclasses
import multiprocessing
import threading
import time
from pathlib import Path

import pytest

from g2.io import read_json
from g2.latent_cache.builder import discover_episodes, plan_episode, verify_episode
from g2.latent_cache.contract import CacheError, make_recipe
from g2.latent_cache.production import build_profile, cleanup_inputs, target_lock
from g2.latent_cache.sealed_source import scan_source
from g2.latent_cache.storage import ViewReader, build_lock, open_episode_index
from g2.latent_cache.streaming import (
    ConsumerLimits,
    EventConsumer,
    EventSpool,
    publish_final_pixels,
)
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a, validate_profile_episode
from g2.tests.test_stage_a_package import stage_case
from g2.tests.test_view_vae_builder import PREPROCESS, FakeEncoder


def setup_case(root, *, png=True, limits=None, max_result_bytes=4 * 1024**3):
    profile = OutputProfile(
        selection_top_variant="clean", view_vae=True, sixview_png=png, island_png=png
    )
    kwargs, _ = stage_case(root, profile)
    target = root / "published"
    encoder = FakeEncoder()
    spool = EventSpool(
        root / "spool",
        make_recipe(encoder.descriptor(), PREPROCESS),
        limits=limits or ConsumerLimits(),
        max_result_bytes=max_result_bytes,
    )
    job = spool.register(
        target,
        episode_key="NavigateKitchen/episode_000000",
        source_fingerprint=kwargs["source_fingerprint"],
        profile_id=profile.to_dict()["profile_id"],
    )
    return kwargs, target, encoder, spool, job


def publish_raw(kwargs, spool, job, consumer=None, reverse=False):
    states = sorted(kwargs["rendered"].glob("state_*"), reverse=reverse)
    for stage in states:
        report = read_json(stage / "direct_color_views.json")
        publish_final_pixels(
            stage,
            report,
            lambda event: spool.enqueue(job, event, timeout_s=0),
            episode_key="NavigateKitchen/episode_000000",
            source_fingerprint=kwargs["source_fingerprint"],
            profile_id=kwargs["profile"].to_dict()["profile_id"],
        )
        if consumer:
            while consumer.step():
                pass


@pytest.mark.parametrize("png", [True, False])
def test_posthoc_ready_source_no_cycle_and_safe_release(tmp_path, png):
    kwargs, target, encoder, spool, job = setup_case(tmp_path, png=png)
    package_stage_a(destination=target, **kwargs)
    assert not (target / "COMPLETE.json").exists()
    plan = plan_episode(target, spool.recipe)
    assert plan["physical_image_count"] == 5 and plan["logical_view_count"] == 4
    assert plan["source"]["readiness_marker"] == "SPATIAL_SOURCE_READY.json"
    before = (target / "spatial_source.json").read_bytes()
    build_profile(target, encoder, preprocessing=PREPROCESS, cleanup=True)
    assert encoder.calls == 5
    assert validate_profile_episode(target)["profile_complete"]
    assert before == (target / "spatial_source.json").read_bytes()
    assert verify_episode(target)["records_checked"] == 5
    assert len(list((target / "vae_cache").rglob("*.pt"))) == 4
    assert list((target / "_spatial_inputs").rglob("*.png")) == []
    assert build_profile(target, encoder, preprocessing=PREPROCESS, resume=True)[
        "already_complete"
    ]
    assert encoder.calls == 5
    index = open_episode_index(target)
    with ViewReader(index, max_views=1) as reader:
        assert reader.read_view("sixview/floor_top", 2)["record_index"] == 0
    assert cleanup_inputs(target)["released_inputs"] == (0 if png else 5)
    assert discover_episodes(target) == [target]


@pytest.mark.parametrize("png", [True, False])
@pytest.mark.parametrize("reverse", [False, True])
def test_streaming_final_pixels_compact_owner_parity(tmp_path, png, reverse):
    kwargs, target, encoder, spool, job = setup_case(tmp_path, png=png)
    consumer = EventConsumer(spool, encoder)
    publish_raw(kwargs, spool, job, consumer, reverse)
    assert encoder.calls == 5  # FULL4 + ARROW1, REUSE_ALL0; clean never redrawn.
    package_stage_a(
        destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
    )
    assert not (target / "COMPLETE.json").exists()
    spool.seal(job)
    assert consumer.step()
    assert spool.job_status(job) == "complete"
    assert encoder.calls == 5
    assert spool.stats()["pending_inputs"] == 0
    assert list((spool.root / "records").glob("*.pt")) == []
    index = open_episode_index(target)
    assert index.manifest["views"]["sixview/floor_top"]["state_records"] == [0, 0, 0]
    assert index.manifest["views"]["sixview/floor_top_w_rbs"]["state_records"] == [
        0,
        1,
        1,
    ]
    # Re-encode the identical final input bytes using the same B=1 core on CPU.
    assert (
        verify_episode(target, reencoder=FakeEncoder())["max_abs_error"] == 0
        if png
        else True
    )
    assert validate_profile_episode(target)["vae_receipt"]["records"] == 5


class PowerLoss(BaseException):
    pass


def test_crash_after_fsync_before_ack_recovers_without_encode(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    package_stage_a(
        destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
    )

    def crash(phase):
        if phase == "numeric_before_ack":
            raise PowerLoss()

    with pytest.raises(PowerLoss):
        EventConsumer(spool, encoder, failpoint=crash).step()
    assert encoder.calls == 1 and spool.stats()["pending_inputs"] == 5
    restarted = EventConsumer(EventSpool.open(spool.root), encoder)
    assert restarted.step()
    assert encoder.calls == 1 and spool.stats()["pending_inputs"] == 4
    spool.seal(job)
    while restarted.step():
        pass
    assert encoder.calls == 5 and validate_profile_episode(target)["profile_complete"]


def test_failed_encoder_explicit_retry_preserves_rgb_sg(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    package_stage_a(
        destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
    )
    original = {p: p.read_bytes() for p in target.rglob("*") if p.is_file()}
    encoder.fail_at = 1
    with pytest.raises(RuntimeError, match="interruption"):
        EventConsumer(spool, encoder).step()
    assert not (target / "COMPLETE.json").exists()
    assert all(p.read_bytes() == data for p, data in original.items())
    with pytest.raises(CacheError, match="failed"):
        spool.job_status(job)
    spool.retry(job)
    encoder.fail_at = None
    spool.seal(job)
    while EventConsumer(spool, encoder).step():
        pass
    assert validate_profile_episode(target)["profile_complete"]


def test_bounded_queue_backpressure_and_consumer_release(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(
        tmp_path, limits=ConsumerLimits(max_events=1)
    )
    observed = []
    package_stage_a(destination=target, event_sink=observed.append, **kwargs)
    spool.enqueue(job, observed[0], timeout_s=0)
    with pytest.raises(CacheError, match="backpressure"):
        spool.enqueue(job, observed[1], timeout_s=0)

    def drain():
        time.sleep(0.05)
        EventConsumer(spool, encoder).step()

    thread = threading.Thread(target=drain)
    thread.start()
    spool.enqueue(job, observed[1], timeout_s=2)
    thread.join(2)
    assert not thread.is_alive()
    assert spool.stats()["pending_inputs"] == 1
    assert spool.stats()["statuses"] == {"acked": 1, "pending": 1}


@pytest.mark.parametrize(
    "field,value",
    [
        ("variant", "w_rbs"),
        ("canonical_view_id", "sixview/plus_X"),
        ("rgb_sha256", "0" * 64),
        ("size_wh", (1, 1)),
        ("final_pixel_phase", "EARLY_PIXELS"),
    ],
)
def test_event_tampering_refused(tmp_path, field, value):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    events = []
    package_stage_a(destination=target, event_sink=events.append, **kwargs)
    event = next(e for e in events if e.view_id == "sixview/floor_top")
    with pytest.raises(CacheError):
        spool.enqueue(job, dataclasses.replace(event, **{field: value}), timeout_s=0)


def test_source_scope_recipe_change_and_single_image_budget_rejected(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    events = []
    package_stage_a(destination=target, event_sink=events.append, **kwargs)
    with pytest.raises(CacheError, match="recipe or limits"):
        EventSpool(
            spool.root, make_recipe(FakeEncoder(identity="b").descriptor(), PREPROCESS)
        )
    with pytest.raises(CacheError, match="another source"):
        spool.register(
            target,
            episode_key="NavigateKitchen/episode_000000",
            source_fingerprint="b" * 64,
            profile_id=kwargs["profile"].to_dict()["profile_id"],
        )
    tiny = EventSpool(
        tmp_path / "tiny", spool.recipe, limits=ConsumerLimits(max_spool_bytes=1)
    )
    tiny_job = tiny.register(
        tmp_path / "other",
        episode_key=events[0].episode_key,
        source_fingerprint=events[0].source_fingerprint,
        profile_id=events[0].profile_id,
    )
    with pytest.raises(CacheError, match="one final image"):
        tiny.enqueue(tiny_job, events[0], timeout_s=0)
    assert tiny.stats()["pending_inputs"] == 0


def test_numeric_budget_failure_retains_input_and_no_false_ack(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path, max_result_bytes=1)
    package_stage_a(
        destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
    )
    with pytest.raises(CacheError, match="budget"):
        EventConsumer(spool, encoder).step()
    assert spool.stats()["pending_inputs"] == 5
    assert spool.stats()["statuses"]["failed"] == 1
    assert not (target / "COMPLETE.json").exists()


def test_pending_owner_missing_event_and_ack_corruption_block_completion(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    package_stage_a(destination=target, **kwargs)
    with pytest.raises(CacheError, match="lacks matching"):
        spool.seal(job)
    spool.enqueue_source(job)
    consumer = EventConsumer(spool, encoder)
    for _ in range(5):
        assert consumer.step()
    chunk = next((spool.root / "records").glob("*.pt"))
    chunk.write_bytes(b"corrupt")
    with pytest.raises(CacheError):
        consumer.step()
    assert not (target / "COMPLETE.json").exists()
    assert list(target.rglob("*.png"))


def test_same_target_and_consumer_writer_mutex(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    package_stage_a(destination=target, **kwargs)
    with build_lock(target_lock(target)):
        with pytest.raises(CacheError, match="another builder"):
            build_profile(target, encoder, preprocessing=PREPROCESS)
    with build_lock(spool.root / "consumer"):
        with pytest.raises(CacheError, match="another builder"):
            EventConsumer(spool, encoder).step()
    assert encoder.calls == 0


def test_final_marker_crash_can_resume_without_reencoding(tmp_path, monkeypatch):
    import g2.latent_cache.production as production

    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    package_stage_a(destination=target, **kwargs)
    original = production.atomic_json

    def fail(path, *args, **kw):
        if Path(path) == target / "COMPLETE.json":
            raise PowerLoss()
        return original(path, *args, **kw)

    with monkeypatch.context() as context:
        context.setattr(production, "atomic_json", fail)
        with pytest.raises(PowerLoss):
            build_profile(target, encoder, preprocessing=PREPROCESS)
    assert encoder.calls == 5 and not (target / "COMPLETE.json").exists()
    build_profile(target, encoder, preprocessing=PREPROCESS, resume=True)
    assert encoder.calls == 5 and validate_profile_episode(target)["profile_complete"]


def test_cleanup_is_idempotent_after_partial_unlink_and_refuses_damage(
    tmp_path, monkeypatch
):
    kwargs, target, encoder, spool, job = setup_case(tmp_path, png=False)
    package_stage_a(destination=target, **kwargs)
    build_profile(target, encoder, preprocessing=PREPROCESS)
    original = Path.unlink
    count = [0]

    def fail(path, *args, **kw):
        if "_spatial_inputs" in path.parts:
            count[0] += 1
            if count[0] == 2:
                raise PowerLoss()
        return original(path, *args, **kw)

    with monkeypatch.context() as context:
        context.setattr(Path, "unlink", fail)
        with pytest.raises(PowerLoss):
            cleanup_inputs(target)
    assert len(list((target / "_spatial_inputs").rglob("*.png"))) == 4
    assert cleanup_inputs(target)["released_inputs"] == 5
    assert scan_source(target)["views"]["sixview/floor_top"]["records"][0]["png_sha256"]
    (target / "vae_cache/sixview/floor_top.pt").write_bytes(b"damaged")
    with pytest.raises(CacheError):
        validate_profile_episode(target)


def _independent_consume(spool_root, queue):
    encoder = FakeEncoder()
    spool = EventSpool.open(spool_root)
    queue.put(EventConsumer(spool, encoder).step())


def test_independent_process_consumes_persisted_bytes(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    events = []
    package_stage_a(destination=target, event_sink=events.append, **kwargs)
    spool.enqueue(job, events[0])
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    process = ctx.Process(target=_independent_consume, args=(str(spool.root), queue))
    process.start()
    process.join(20)
    assert process.exitcode == 0 and queue.get(timeout=2) is True
    assert spool.stats()["statuses"] == {"acked": 1}
    assert encoder.calls == 0
    queue.close()


def test_shared_numeric_identity_ignores_language_publication_and_source_scope(
    tmp_path,
):
    from g2.latent_cache.contract import fingerprint

    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    events = []
    package_stage_a(destination=target, event_sink=events.append, **kwargs)
    original = events[0]
    second_profile = "b" * 64
    other_job = spool.register(
        tmp_path / "other",
        episode_key=original.episode_key,
        source_fingerprint=original.source_fingerprint,
        profile_id=second_profile,
    )
    identity = dict(
        episode_key=original.episode_key,
        view_id=original.view_id,
        rgb_sha256=original.rgb_sha256,
        source_fingerprint=original.source_fingerprint,
        profile_id=second_profile,
    )
    other = dataclasses.replace(
        original, profile_id=second_profile, event_id=fingerprint(identity)
    )
    spool.enqueue(job, original)
    spool.enqueue(other_job, other)
    consumer = EventConsumer(spool, encoder)
    assert consumer.step() and consumer.step()
    assert encoder.calls == 1
    assert len(list((spool.root / "records").glob("*.pt"))) == 1
    assert spool.stats()["statuses"] == {"acked": 2}


def test_partial_record_orphan_with_wrong_recipe_is_not_reused(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    events = []
    package_stage_a(destination=target, event_sink=events.append, **kwargs)
    spool.enqueue(job, events[0])

    def crash(phase):
        raise PowerLoss()

    with pytest.raises(PowerLoss):
        EventConsumer(spool, encoder, failpoint=crash).step()
    chunk = next((spool.root / "records").glob("*.pt"))
    chunk.write_bytes(b"bad partial result")
    with pytest.raises(CacheError):
        EventConsumer(spool, encoder).step()
    assert spool.stats()["pending_inputs"] == 1 and encoder.calls == 1


def test_current_numeric_ack_is_not_final_completion_and_cannot_clean_early(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    package_stage_a(
        destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
    )
    while EventConsumer(spool, encoder).step():
        pass
    assert encoder.calls == 5 and not (target / "COMPLETE.json").exists()
    with pytest.raises(CacheError, match="before final"):
        spool.reap(job)
    with pytest.raises(ValueError):
        cleanup_inputs(target)
    spool.seal(job)
    assert EventConsumer(spool, encoder).step()
    assert (target / "COMPLETE.json").is_file()


def test_spool_record_and_job_budgets_are_finite(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    events = []
    package_stage_a(destination=target, event_sink=events.append, **kwargs)
    tiny = EventSpool(tmp_path / "small", spool.recipe, max_records=1)
    job = tiny.register(
        tmp_path / "target2",
        episode_key=events[0].episode_key,
        source_fingerprint=events[0].source_fingerprint,
        profile_id=events[0].profile_id,
    )
    tiny.enqueue(job, events[0])
    with pytest.raises(CacheError, match="ledger budget"):
        tiny.enqueue(job, events[1])
    with pytest.raises(CacheError, match="ledger budget"):
        tiny.register(
            tmp_path / "target3",
            episode_key=events[0].episode_key,
            source_fingerprint=events[0].source_fingerprint,
            profile_id=events[0].profile_id,
        )


def test_queue_zero_timeout_does_not_drop_existing_events(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(
        tmp_path, limits=ConsumerLimits(max_events=1)
    )
    events = []
    package_stage_a(destination=target, event_sink=events.append, **kwargs)
    assert spool.enqueue(job, events[0], timeout_s=0) == "pending"
    assert spool.enqueue(job, events[0], timeout_s=0) == "pending"
    with pytest.raises(CacheError):
        spool.enqueue(job, events[1], timeout_s=0)
    assert spool.stats()["pending_inputs"] == 1
    assert EventConsumer(spool, encoder).step()
    assert spool.enqueue(job, events[0], timeout_s=0) == "acked"
    assert encoder.calls == 1


def test_reader_remains_independent_and_loads_only_requested_new_variant(
    tmp_path, monkeypatch
):
    import g2.latent_cache.storage as storage

    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    package_stage_a(destination=target, **kwargs)
    build_profile(target, encoder, preprocessing=PREPROCESS)
    opened = []
    original = storage._load

    def load(path, *args, **kw):
        opened.append(Path(path).relative_to(target / "vae_cache").as_posix())
        return original(path, *args, **kw)

    monkeypatch.setattr(storage, "_load", load)
    index = open_episode_index(target)
    assert not opened
    with ViewReader(index, max_views=2) as reader:
        reader.read_view("sixview/floor_top_w_rbs", 2)
        reader.read_view("islands/island_0_entity_2/plus_X", 0)
    assert opened == [
        "sixview/floor_top_w_rbs.pt",
        "islands/island_0_entity_2/plus_X.pt",
    ]


@pytest.mark.parametrize("png", [True, False])
def test_failed_delivery_retains_whole_source_then_refills_bounded_queue(tmp_path, png):
    kwargs, target, encoder, spool, job = setup_case(
        tmp_path, png=png, limits=ConsumerLimits(max_events=1)
    )
    diagnostic = tmp_path / "VAE_DELIVERY_PENDING.json"
    package_stage_a(
        destination=target,
        event_sink=lambda event: spool.deliver(job, event, diagnostic, timeout_s=0),
        **kwargs,
    )
    assert spool.stats()["pending_inputs"] == 1
    assert read_json(diagnostic)["inputs_retained"] is True
    before = (target / "spatial_source.json").read_bytes()
    spool.offer_source(job)
    consumer = EventConsumer(spool, encoder)
    steps = 0
    while consumer.step():
        steps += 1
        assert spool.stats()["pending_inputs"] <= 1
        assert steps < 20
    assert encoder.calls == 5 and spool.job_status(job) == "complete"
    assert validate_profile_episode(target)["profile_complete"]
    assert (target / "spatial_source.json").read_bytes() == before


def test_encode_failure_does_not_abort_spatial_publication_and_retry_refills(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    events = []
    package_stage_a(destination=tmp_path / "probe", event_sink=events.append, **kwargs)
    spool.enqueue(job, events[0])
    encoder.fail_at = 1
    with pytest.raises(RuntimeError):
        EventConsumer(spool, encoder).step()
    diagnostic = tmp_path / "VAE_DELIVERY_PENDING.json"
    result = package_stage_a(
        destination=target,
        event_sink=lambda event: spool.deliver(job, event, diagnostic, timeout_s=0),
        **kwargs,
    )
    assert (
        not result["profile_complete"]
        and (target / "SPATIAL_SOURCE_READY.json").is_file()
    )
    spool.offer_source(job)  # Source readiness is durable even while job is failed.
    assert not (target / "COMPLETE.json").exists()
    spool.retry(job)
    encoder.fail_at = None
    while EventConsumer(spool, encoder).step():
        pass
    assert encoder.calls == 6 and validate_profile_episode(target)["profile_complete"]


def test_postpublication_marker_loss_has_no_repair_witness(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    package_stage_a(destination=target, **kwargs)
    build_profile(target, encoder, preprocessing=PREPROCESS)
    assert not (target / "VAE_PROFILE_PUBLISH_PENDING.json").exists()
    (target / "COMPLETE.json").unlink()
    with pytest.raises(ValueError, match="incomplete"):
        validate_profile_episode(target, require_complete=False)


def test_profile_ack_crash_does_not_repeat_math(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path, png=False)
    package_stage_a(
        destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
    )
    spool.seal(job)
    consumer = EventConsumer(spool, encoder)
    for _ in range(5):
        consumer.step()

    def crash(phase):
        if phase == "profile_before_ack":
            raise PowerLoss()

    with pytest.raises(PowerLoss):
        EventConsumer(spool, encoder, failpoint=crash).step()
    assert validate_profile_episode(target)["profile_complete"] and encoder.calls == 5
    assert EventConsumer(spool, encoder).step()
    assert spool.job_status(job) == "complete" and encoder.calls == 5


def test_ready_episode_finalizes_while_another_producer_queue_remains_active(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    events = []
    package_stage_a(destination=target, event_sink=events.append, **kwargs)
    for event in events:
        spool.enqueue(job, event)
    consumer = EventConsumer(spool, encoder)
    for _ in range(5):
        consumer.step()
    spool.seal(job)
    other = spool.register(
        tmp_path / "another_episode",
        episode_key=events[0].episode_key,
        source_fingerprint=events[0].source_fingerprint,
        profile_id=events[0].profile_id,
    )
    spool.enqueue(other, events[0])
    assert consumer.step()  # Finalize/reap first job before draining other job.
    assert validate_profile_episode(target)["profile_complete"]
    assert spool.stats()["pending_inputs"] == 1 and encoder.calls == 5
    assert (
        len(list((spool.root / "records").glob("*.pt"))) == 1
    )  # Shared pending use protects this chunk.
    assert consumer.step() and encoder.calls == 5
    assert spool.stats()["pending_inputs"] == 0


def test_orphan_chunk_preprocessing_mismatch_cannot_ack(tmp_path):
    import torch

    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    events = []
    package_stage_a(destination=target, event_sink=events.append, **kwargs)
    spool.enqueue(job, events[0])

    def crash(phase):
        raise PowerLoss()

    with pytest.raises(PowerLoss):
        EventConsumer(spool, encoder, failpoint=crash).step()
    chunk = next((spool.root / "records").glob("*.pt"))
    data = torch.load(chunk, weights_only=True)
    data["metadata"]["preprocessing"][0]["canvas_hw"] = [16, 16]
    torch.save(data, chunk)
    with pytest.raises(CacheError, match="preprocessing"):
        EventConsumer(spool, encoder).step()
    assert spool.stats()["pending_inputs"] == 1 and encoder.calls == 1


def test_released_source_cannot_be_replaced_with_dangling_symlink(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path, png=False)
    package_stage_a(destination=target, **kwargs)
    build_profile(target, encoder, preprocessing=PREPROCESS, cleanup=True)
    source = read_json(target / "spatial_source.json")
    relative = source["views"]["sixview/floor_top"]["owners"][0]["path"]
    (target / relative).symlink_to(tmp_path / "outside_missing")
    with pytest.raises(CacheError, match="symbolic"):
        validate_profile_episode(target)


def test_new_profile_disabled_vae_rejected_before_plan_or_cache_writes(tmp_path):
    profile = OutputProfile(selection_top_variant="clean", view_vae=False)
    kwargs, _ = stage_case(tmp_path, profile)
    target = tmp_path / "published"
    package_stage_a(destination=target, **kwargs)
    with pytest.raises(CacheError, match="disabled"):
        plan_episode(target, make_recipe(FakeEncoder().descriptor(), PREPROCESS))
    assert not (target / "vae_cache").exists()


def test_producer_attach_does_not_compete_for_schema_initialization_lock(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path)
    with build_lock(spool.root / "init"):
        attached = EventSpool.open(spool.root)
        assert attached.recipe == spool.recipe
        assert attached.stats()["pending_inputs"] == 0


class _LargerCPUEncoder(FakeEncoder):
    def encode(self, rgb, preprocessing):
        import torch

        _, prep = super().encode(rgb, preprocessing)
        return torch.zeros((3, 64, 64), dtype=torch.float32), prep


def _hard_exit_numeric_writer(spool_root, phase):
    import os

    import g2.latent_cache.storage as storage

    original = storage.os.link
    spool = EventSpool.open(spool_root)

    def interrupt(src, dst, *args, **kwargs):
        if (
            Path(src).name.startswith(".view-")
            and Path(dst).parent == spool.root / "records"
        ):
            if phase == "after_link":
                original(src, dst, *args, **kwargs)
            os._exit(77)  # Deliberately skips finally, unlike a Python exception.
        return original(src, dst, *args, **kwargs)

    storage.os.link = interrupt
    EventConsumer(spool, _LargerCPUEncoder()).step()


@pytest.mark.parametrize("phase,crashes", [("before_link", 2), ("after_link", 1)])
def test_hard_exit_orphans_recovered_under_result_budget(tmp_path, phase, crashes):
    kwargs, target, encoder, spool, job = setup_case(tmp_path, max_result_bytes=120000)
    events = []
    package_stage_a(destination=target, event_sink=events.append, **kwargs)
    spool.enqueue(job, events[0])
    ctx = multiprocessing.get_context("fork")
    for _ in range(crashes):
        child = ctx.Process(
            target=_hard_exit_numeric_writer, args=(str(spool.root), phase)
        )
        child.start()
        child.join(15)
        assert child.exitcode == 77
        assert len(list((spool.root / "records").glob(".view-*.tmp"))) == 1
        assert spool.stats()["pending_inputs"] == 1
    # Recovery must preserve unrelated owned bytes and completed .pt names.
    sentinel = spool.root / "records" / "operator-note.txt"
    sentinel.write_bytes(b"do not delete")
    resumed = _LargerCPUEncoder()
    assert EventConsumer(spool, resumed).step()
    assert resumed.calls == (1 if phase == "before_link" else 0)
    assert not list((spool.root / "records").glob(".view-*.tmp"))
    assert sentinel.read_bytes() == b"do not delete"
    total = sum(p.stat().st_size for p in (spool.root / "records").iterdir())
    assert total <= spool.max_result_bytes
    assert spool.stats()["statuses"] == {"acked": 1}
    assert not (target / "COMPLETE.json").exists()


def test_posthoc_complete_release_hands_off_pending_stream_without_reencode(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(
        tmp_path, png=False, limits=ConsumerLimits(max_events=1)
    )
    package_stage_a(
        destination=target,
        event_sink=lambda e: spool.deliver(
            job, e, tmp_path / "delivery.json", timeout_s=0
        ),
        **kwargs,
    )
    spool.offer_source(job)
    posthoc = FakeEncoder()
    build_profile(target, posthoc, preprocessing=PREPROCESS, cleanup=True)
    assert not list((target / "_spatial_inputs").rglob("*.png"))
    assert EventConsumer(spool, encoder).step()
    assert encoder.calls == 0 and posthoc.calls == 5
    assert spool.job_status(job) == "complete" and spool.stats()["pending_inputs"] == 0
    assert spool.stats()["failed_jobs"] == spool.stats()["unfinished_jobs"] == 0
    # Issue58 archives completed rows; the identical handoff proof now lives
    # in the durable tombstone, while the active event ledger must be empty.
    import json

    archived = spool.completed_receipt(job)
    proof = json.loads(archived["job"]["completion_receipt"])
    assert proof["verified_cache"]["recipe_id"] == spool.recipe["recipe_id"]
    assert archived["event_status_counts"] == {"completed_by_cache": 1}
    with spool._db() as db:
        assert (
            db.execute("SELECT COUNT(*) FROM events WHERE job=?", (job,)).fetchone()[0]
            == 0
        )
        assert (
            db.execute("SELECT COUNT(*) FROM jobs WHERE id=?", (job,)).fetchone()[0]
            == 0
        )
    assert not EventConsumer(spool, encoder).step()
    assert validate_profile_episode(target)["profile_complete"]


def test_posthoc_different_recipe_cannot_retire_stream_inputs(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(
        tmp_path, png=False, limits=ConsumerLimits(max_events=1)
    )
    package_stage_a(
        destination=target,
        event_sink=lambda e: spool.deliver(
            job, e, tmp_path / "delivery.json", timeout_s=0
        ),
        **kwargs,
    )
    spool.offer_source(job)
    build_profile(
        target, FakeEncoder(identity="b"), preprocessing=PREPROCESS, cleanup=True
    )
    with pytest.raises(CacheError, match="recipe differs"):
        EventConsumer(spool, encoder).step()
    assert spool.stats()["pending_inputs"] == 1 and spool.stats()["failed_jobs"] == 1
    assert encoder.calls == 0
