"""B1: original source and target producer use identical keyed text CFG dropout.

Only the given producer instance is intercepted, around its *real* transform.
Requires num_workers=0 and B0's strict Python RNG scope; no global patch.
"""
from __future__ import annotations

from contextlib import contextmanager
from types import MethodType
from typing import Any, Callable, ContextManager, Iterator


class ProducerBlocked(RuntimeError):
    """Native Transform or ConsumerKey authority was not established."""


@contextmanager
def scoped_native_producer_cfg(*, trainer: Any, producer: Any,
                                consumer_key: Callable[..., Any],
                                scoped_rng: Callable[[Any], ContextManager[Any]]) -> Iterator[None]:
    """Precisely one native producer's Transform has isolated B0 CFG RNG."""
    if getattr(trainer, "_grouped_num_workers", None) != 0:
        raise ProducerBlocked("CFG Native witness requires num_workers=0 and serial transform")
    sft = getattr(getattr(producer, "catalog", None), "wrapped_sft", None)
    if sft is None or not callable(getattr(sft, "_transform", None)):
        raise ProducerBlocked("real corrected Native SFT Transform not bound")
    if not callable(getattr(producer, "produce", None)):
        raise ProducerBlocked("real ExactWindowSegmentProducer.produce missing")
    original_produce = producer.produce
    original_transform = sft._transform
    existing = "produce" in vars(producer)
    old_instance = vars(producer).get("produce")

    def wrapped_produce(_producer: Any, request: Any):
        identity = request.identity
        window = getattr(trainer, "_grouped_window", None)
        if window is None or window.plan is None:
            raise ProducerBlocked("producer called without an active grouped window")
        ga = window._member_index
        if ga not in (0, 1):
            raise ProducerBlocked("native member index not in GA2")
        iteration = getattr(trainer, "_grouped_completed_iteration", None)
        if type(iteration) is not int or iteration < 1300:
            raise ProducerBlocked("original DCP iteration not restored")

        def transformed(payload: dict[str, Any], resolution: Any):
            if not isinstance(payload, dict) or type(payload.get("start_frame")) is not int:
                raise ProducerBlocked("CFG transform payload missing absolute frame/Consumer identity")
            absolute_step = payload["start_frame"]
            if not identity.cursor * 16 <= absolute_step < identity.cursor * 16 + request.valid_count:
                raise ProducerBlocked("CFG transform frame outside frozen member Consumer range")
            key = consumer_key(request=request, iteration=iteration, ga_member=ga, absolute_step=absolute_step)
            with scoped_rng(key):
                return original_transform(payload, resolution)

        sft._transform = transformed
        try:
            return original_produce(request)
        finally:
            sft._transform = original_transform

    producer.produce = MethodType(wrapped_produce, producer)
    try:
        yield
    finally:
        sft._transform = original_transform
        if existing:
            producer.produce = old_instance
        else:
            vars(producer).pop("produce", None)


def b0_consumer_cfg_scope(trainer: Any, producer: Any, *, rank: int, checkpoint_fp: str):
    """Real native B0 canonical key+text-CFG seed; no namespace substitutions."""
    from v3_packed128_gateb_compare import ConsumerKey, scoped_python_cfg_rng

    if type(rank) is not int or not 0 <= rank < 8 or not checkpoint_fp:
        raise ProducerBlocked("rank/checkpoint fingerprint must match original B0 witness")

    def make_key(*, request: Any, iteration: int, ga_member: int, absolute_step: int):
        identity = request.identity
        return ConsumerKey(
            checkpoint_fp, rank, iteration, ga_member, identity.slot_id,
            identity.episode_id, identity.source_digest, request.binding_epoch,
            identity.segment_id, identity.cursor, absolute_step,
        )

    return scoped_native_producer_cfg(trainer=trainer, producer=producer,
                                       consumer_key=make_key, scoped_rng=scoped_python_cfg_rng)
