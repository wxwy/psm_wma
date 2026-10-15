"""B1: source/target producer transform with Consumer-keyed text CFG dropout.

Use a SHALLOW COPY of the genuine frozen ActionTransformPipeline and its native
TextTokenizerTransform, replacing only the CFG dropout decision with a local
random.Random(seed). No process-global random.seed/getstate/setstate or global
thread exclusion: FSDP/CUDA may launch unrelated background threads.
num_workers=0 + main-thread-only transform are still mandatory.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import copy
import random
import threading
from types import MethodType
from typing import Any, Callable, ContextManager, Iterator


class ProducerBlocked(RuntimeError):
    """Native Transform or ConsumerKey authority was not established."""


@contextmanager
def scoped_keyed_native_caption_transform(key: Any, transform: Any) -> Iterator[Callable[..., Any]]:
    """Clone the frozen native transform; replace ONLY its Python CFG draw.

    Frozen TextTokenizerTransform.__call__ performs one random.random() when
    cfg_dropout_rate > 0. The clone has dropout disabled and receives the same
    sampled caption-blanking decision *after* the native JSON prompt formatter
    and immediately before the actual tokenizer call. No ambient RNG mutation.
    """
    from v3_packed128_gateb_compare import ConsumerKey, stable_seed

    if threading.current_thread() is not threading.main_thread():
        raise ProducerBlocked("Native CFG Transform must run on the Python main thread (nw=0)")
    if not isinstance(key, ConsumerKey):
        raise ProducerBlocked("original B0 ConsumerKey is required for Native CFG")
    if (type(transform).__name__ != "ActionTransformPipeline"
            or type(transform).__module__ != "cosmos_framework.data.generator.action.utils.transforms"):
        raise ProducerBlocked("frozen native ActionTransformPipeline provenance unknown")
    tokenizer = getattr(transform, "text_tokenizer", None)
    if (tokenizer is None or type(tokenizer).__name__ != "TextTokenizerTransform"
            or type(tokenizer).__module__ != "cosmos_framework.data.generator.augmentors.text_tokenizer"):
        raise ProducerBlocked("frozen native TextTokenizerTransform provenance unknown")
    if (getattr(tokenizer, "tokenize_separately", None) is not False
            or getattr(transform, "prompt_json_formatter", None) is None
            or getattr(transform, "idle_frames_augmentor", None) is not None):
        raise ProducerBlocked("unsupported non-RoboCasa CFG randomness/prompt transform")
    caption_key = getattr(transform, "caption_key", None)
    if (caption_key != "ai_caption" or getattr(tokenizer, "input_keys", None) != [caption_key]
            or getattr(tokenizer, "cfg_dropout_rate", None) != 0.1):
        raise ProducerBlocked("RoboCasa native CFG caption/rate authority mismatch")

    native_copy = copy(tokenizer)
    transform_copy = copy(transform)
    if native_copy is tokenizer or transform_copy is transform:
        raise ProducerBlocked("native transform/tokenizer must have independent shallow copies")
    native_copy.cfg_dropout_rate = 0.0
    rng_seed = stable_seed(key.scoped("cfg_dropout", "caption"), domain="python_cfg")
    dropout = random.Random(rng_seed).random() < 0.1
    calls = 0

    def keyed_tokenizer(payload: dict[str, Any]) -> dict[str, Any]:
        nonlocal calls
        if threading.current_thread() is not threading.main_thread():
            raise ProducerBlocked("Native CFG tokenization attempted off the main thread")
        calls += 1
        if calls != 1:
            raise ProducerBlocked("native CFG tokenizer called more than once per Consumer")
        if not isinstance(payload, dict) or not isinstance(payload.get(caption_key), (dict, str)):
            raise ProducerBlocked("native CFG caption payload missing/unsupported")
        if dropout:
            payload[caption_key] = ""
        return native_copy(payload)

    transform_copy.text_tokenizer = keyed_tokenizer
    yield transform_copy
    if calls != 1:
        raise ProducerBlocked("native CFG tokenizer was not called exactly once")


@contextmanager
def scoped_native_producer_cfg(*, trainer: Any, producer: Any,
                                consumer_key: Callable[..., Any],
                                scoped_rng: Callable[[Any], ContextManager[Any]],
                                payload_fingerprint: Callable[[Any], str] | None = None) -> Iterator[list[dict[str, Any]]]:
    """Precisely one producer's original Transform, with scoped CFG override."""
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
    recorded: list[dict[str, Any]] = []

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
            with scoped_rng(key) as optional_transform:
                native_transform = original_transform if optional_transform is None else optional_transform
                if not callable(native_transform):
                    raise ProducerBlocked("scoped CFG transform override is not callable")
                transformed_sample = native_transform(payload, resolution)
            if payload_fingerprint is not None:
                digest = payload_fingerprint(transformed_sample)
                recorded.append({"consumer": key.as_dict(), "transformed_payload_sha256": digest})
            return transformed_sample

        sft._transform = transformed
        try:
            return original_produce(request)
        finally:
            sft._transform = original_transform

    producer.produce = MethodType(wrapped_produce, producer)
    try:
        yield recorded
    finally:
        sft._transform = original_transform
        if existing:
            producer.produce = old_instance
        else:
            vars(producer).pop("produce", None)


def b0_consumer_cfg_scope(trainer: Any, producer: Any, *, rank: int, checkpoint_fp: str):
    """Real native B0 canonical key+text-CFG seed; no namespace substitutions."""
    from v3_packed128_gateb_compare import ConsumerKey, _stable_payload_hash

    if type(rank) is not int or not 0 <= rank < 8 or not checkpoint_fp:
        raise ProducerBlocked("rank/checkpoint fingerprint must match original B0 witness")

    def make_key(*, request: Any, iteration: int, ga_member: int, absolute_step: int):
        identity = request.identity
        return ConsumerKey(
            checkpoint_fp, rank, iteration, ga_member, identity.slot_id,
            identity.episode_id, identity.source_digest, request.binding_epoch,
            identity.segment_id, identity.cursor, absolute_step,
        )

    native_pipeline = producer.catalog.wrapped_sft._transform
    return scoped_native_producer_cfg(
        trainer=trainer, producer=producer, consumer_key=make_key,
        scoped_rng=lambda key: scoped_keyed_native_caption_transform(key, native_pipeline),
        payload_fingerprint=_stable_payload_hash,
    )
