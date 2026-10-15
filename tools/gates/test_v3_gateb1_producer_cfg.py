from __future__ import annotations

import json
import random
import threading
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from v3_gateb1_producer_cfg import (
    ProducerBlocked, b0_consumer_cfg_scope, scoped_keyed_native_caption_transform,
    scoped_native_producer_cfg,
)
from v3_packed128_gateb_compare import ConsumerKey, stable_seed


class SFT:
    def _transform(self, payload, resolution):
        return (payload["start_frame"], random.random(), resolution)


class Producer:
    def __init__(self):
        self.catalog = SimpleNamespace(wrapped_sft=SFT())
    def produce(self, request):
        return [self.catalog.wrapped_sft._transform({"start_frame": t}, "480")
                for t in range(request.identity.cursor*16, request.identity.cursor*16 + request.valid_count)]


def fixture(*, worker=0, start=0, length=3):
    trainer = SimpleNamespace(_grouped_num_workers=worker, _grouped_completed_iteration=1300,
                              _grouped_window=SimpleNamespace(plan=object(), _member_index=0))
    producer = Producer()
    request = SimpleNamespace(identity=SimpleNamespace(cursor=start, slot_id=0), valid_count=length)
    seen = []
    def key(**kwargs):
        seen.append(kwargs)
        return kwargs["absolute_step"]
    @contextmanager
    def rng(k):
        prev = random.getstate()
        random.seed(k)
        try:
            yield
        finally:
            random.setstate(prev)
    return trainer, producer, request, key, rng, seen


def test_native_producer_CFG_is_consumer_keyed_and_rng_global_state_restored():
    t, p, r, key, rng, seen = fixture()
    before = random.getstate()
    original = p.produce.__func__
    with scoped_native_producer_cfg(trainer=t, producer=p, consumer_key=key, scoped_rng=rng):
        out = p.produce(r)
        assert [a[0] for a in out] == [0, 1, 2]
        assert [a[1] for a in out] == [random.Random(i).random() for i in range(3)]
    assert random.getstate() == before
    assert len(seen) == 3
    assert all(x["iteration"] == 1300 and x["ga_member"] == 0 for x in seen)
    assert p.produce.__func__ is original and "produce" not in vars(p)


def test_different_GA_and_iteration_propagate_without_global_mutation():
    t,p,r,key,rng,seen = fixture(start=3,length=2)
    t._grouped_window._member_index = 1
    t._grouped_completed_iteration = 1301
    with scoped_native_producer_cfg(trainer=t,producer=p,consumer_key=key,scoped_rng=rng):
        assert len(p.produce(r)) == 2
    assert [x["absolute_step"] for x in seen] == [48,49]
    assert all(x["ga_member"] == 1 and x["iteration"] == 1301 for x in seen)


def test_parallel_producer_must_block():
    t,p,r,key,rng,seen = fixture(worker=1)
    with pytest.raises(ProducerBlocked, match="num_workers=0"):
        with scoped_native_producer_cfg(trainer=t,producer=p,consumer_key=key,scoped_rng=rng):
            p.produce(r)


def test_missing_native_transform_blocks_before_producer_patch():
    t,p,r,key,rng,seen = fixture()
    p.catalog.wrapped_sft._transform = None
    with pytest.raises(ProducerBlocked, match="Transform"):
        with scoped_native_producer_cfg(trainer=t,producer=p,consumer_key=key,scoped_rng=rng):
            pass


def test_bad_absolute_step_and_exception_restore_all_methods():
    t,p,r,key,rng,seen = fixture()
    original = p.produce.__func__
    # The transform is wrapped only for the duration of an actual produce() call.
    def bad_produce(_request):
        return p.catalog.wrapped_sft._transform({"start_frame": 999}, "480")
    p.produce = bad_produce
    with scoped_native_producer_cfg(trainer=t,producer=p,consumer_key=key,scoped_rng=rng):
        with pytest.raises(ProducerBlocked, match="outside"):
            p.produce(r)
    assert p.produce is bad_produce
    del p.produce
    assert p.produce.__func__ is original
    with pytest.raises(ValueError, match="forced"):
        with scoped_native_producer_cfg(trainer=t,producer=p,consumer_key=key,scoped_rng=rng):
            raise ValueError("forced")
    assert p.produce.__func__ is original


def test_actual_transform_payload_sha_is_captured_with_original_consumer_key():
    from dataclasses import dataclass
    import hashlib

    @dataclass(frozen=True)
    class Key:
        absolute_step: int

        def as_dict(self):
            return {"absolute_step": self.absolute_step}

    t, p, r, _old_key, rng, _ = fixture()
    def record(**kwargs):
        return Key(kwargs["absolute_step"])
    def fingerprint(sample):
        return hashlib.sha256(repr(sample).encode()).hexdigest()
    with scoped_native_producer_cfg(trainer=t, producer=p, consumer_key=record,
                                    scoped_rng=lambda key: rng(key.absolute_step),
                                    payload_fingerprint=fingerprint) as captured:
        output = p.produce(r)
        assert [w["consumer"]["absolute_step"] for w in captured] == [0, 1, 2]
        assert [w["transformed_payload_sha256"] for w in captured] == [fingerprint(x) for x in output]
    assert "produce" not in vars(p)


# Real frozen RoboCasa ActionTransformPipeline/TextTokenizerTransform ABI fixtures.
# The native tokenizer performs one random.random() CFG decision on the caption.
# B1 must keep native prompt+tokenizer while avoiding ALL process-global RNG mutation.


class TextTokenizerTransform:
    __module__ = "cosmos_framework.data.generator.augmentors.text_tokenizer"

    def __init__(self):
        self.input_keys = ["ai_caption"]
        self.cfg_dropout_rate = 0.1
        self.tokenize_separately = False

    def __call__(self, payload):
        caption = payload["ai_caption"]
        if isinstance(caption, dict):
            caption = json.dumps(caption)
            payload["ai_caption"] = caption
        if self.cfg_dropout_rate > 0 and random.random() < self.cfg_dropout_rate:
            caption = ""
            payload["ai_caption"] = caption
        payload["text_token_ids"] = (caption,)
        return payload


class ActionTransformPipeline:
    __module__ = "cosmos_framework.data.generator.action.utils.transforms"

    def __init__(self):
        self.caption_key = "ai_caption"
        self.text_tokenizer = TextTokenizerTransform()
        self.prompt_json_formatter = object()
        self.idle_frames_augmentor = None

    def __call__(self, payload, resolution):
        payload = dict(payload)
        payload["ai_caption"] = {"task": payload["start_frame"], "resolution": resolution}
        return self.text_tokenizer(payload)


def _consumer_key(step=0):
    return ConsumerKey(
        "2" * 64, 0, 1300, 0, 0, "episode_a", "source_digest", 1, 5, 0, step,
    )


def test_native_cloned_transform_matches_original_single_CFG_draw_without_global_rng():
    native = ActionTransformPipeline()
    original_tokenizer = native.text_tokenizer
    previous_rng = random.getstate()
    for step in range(64):
        key = _consumer_key(step)
        seed = stable_seed(key.scoped("cfg_dropout", "caption"), domain="python_cfg")
        expected_caption = json.dumps({"task": step, "resolution": "256"})
        if random.Random(seed).random() < 0.1:
            expected_caption = ""
        with scoped_keyed_native_caption_transform(key, native) as cloned:
            assert cloned is not native
            assert cloned.text_tokenizer is not native.text_tokenizer
            result = cloned({"start_frame": step}, "256")
        assert result["ai_caption"] == expected_caption
        assert result["text_token_ids"] == (expected_caption,)
        assert native.text_tokenizer is original_tokenizer
        assert original_tokenizer.cfg_dropout_rate == 0.1
    assert random.getstate() == previous_rng


def test_real_B1_CFG_witnesses_same_with_framework_background_thread_alive():
    started = threading.Event()
    release = threading.Event()

    def framework_background():
        started.set()
        release.wait(10)

    background = threading.Thread(target=framework_background, daemon=True)
    background.start()
    assert started.wait(2)
    pipeline = ActionTransformPipeline()
    original = pipeline.text_tokenizer
    identity = SimpleNamespace(
        cursor=0, slot_id=0, episode_id="episode_a",
        source_digest="source_digest", segment_id=5,
    )
    request = SimpleNamespace(identity=identity, valid_count=4, binding_epoch=1)
    trainer = SimpleNamespace(
        _grouped_num_workers=0, _grouped_completed_iteration=1300,
        _grouped_window=SimpleNamespace(plan=object(), _member_index=0),
    )

    class FakeProducer:
        def __init__(self, native_pipeline):
            self.catalog = SimpleNamespace(
                wrapped_sft=SimpleNamespace(_transform=native_pipeline),
            )

        def produce(self, segment):
            return [
                self.catalog.wrapped_sft._transform({"start_frame": t}, "256")
                for t in range(segment.valid_count)
            ]

    producer = FakeProducer(pipeline)
    previous_rng = random.getstate()
    evidence = []
    try:
        for _ in range(2):
            with b0_consumer_cfg_scope(trainer, producer, rank=0, checkpoint_fp="2" * 64) as witnesses:
                outputs = producer.produce(request)
                evidence.append((tuple(witnesses), tuple(item["ai_caption"] for item in outputs)))
                assert len(witnesses) == 4
            assert pipeline.text_tokenizer is original
            assert producer.catalog.wrapped_sft._transform is pipeline
        assert evidence[0] == evidence[1]
        assert random.getstate() == previous_rng
        assert background.is_alive()
    finally:
        release.set()
        background.join(3)
    assert not background.is_alive()


def test_keyed_native_scope_fail_closed_on_unsupported_random_sites_and_provenance():
    native = ActionTransformPipeline()
    key = _consumer_key()
    native.text_tokenizer.tokenize_separately = True
    with pytest.raises(ProducerBlocked, match="unsupported"):
        with scoped_keyed_native_caption_transform(key, native):
            pass
    native.text_tokenizer.tokenize_separately = False
    native.idle_frames_augmentor = object()
    with pytest.raises(ProducerBlocked, match="unsupported"):
        with scoped_keyed_native_caption_transform(key, native):
            pass
    native.idle_frames_augmentor = None
    native.text_tokenizer.cfg_dropout_rate = 0.2
    with pytest.raises(ProducerBlocked, match="rate"):
        with scoped_keyed_native_caption_transform(key, native):
            pass
    native.text_tokenizer.cfg_dropout_rate = 0.1
    with pytest.raises(ProducerBlocked, match="provenance"):
        with scoped_keyed_native_caption_transform(key, object()):
            pass
    with pytest.raises(ProducerBlocked, match="ConsumerKey"):
        with scoped_keyed_native_caption_transform(object(), native):
            pass


def test_native_keyed_caption_rejects_zero_or_duplicate_tokenizer_calls():
    native = ActionTransformPipeline()
    with pytest.raises(ProducerBlocked, match="not called exactly once"):
        with scoped_keyed_native_caption_transform(_consumer_key(), native):
            pass

    with pytest.raises(ProducerBlocked, match="more than once"):
        with scoped_keyed_native_caption_transform(_consumer_key(), native) as clone:
            clone({"start_frame": 0}, "256")
            clone({"start_frame": 0}, "256")
    assert native.text_tokenizer.cfg_dropout_rate == 0.1


def test_native_keyed_caption_fails_closed_from_non_main_thread():
    native = ActionTransformPipeline()
    observed = []

    def background():
        try:
            with scoped_keyed_native_caption_transform(_consumer_key(), native):
                pass
        except ProducerBlocked as exc:
            observed.append(str(exc))

    thread = threading.Thread(target=background)
    thread.start()
    thread.join(4)
    assert not thread.is_alive()
    assert len(observed) == 1 and "main thread" in observed[0]
