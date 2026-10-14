from __future__ import annotations

import random
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from v3_gateb1_producer_cfg import ProducerBlocked, scoped_native_producer_cfg


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
