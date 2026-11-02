"""RM-ALL-R01: public Dispatcher/Actor replay after later durable Replans."""
# ruff: noqa: F811 -- pytest resolves imported fixture names in parameters.

import copy
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from cosmos_framework.evaluation.robocasa_v2.generated_video import file_sha
from cosmos_framework.evaluation.robocasa_v2.media import MediaSink
from cosmos_framework.inference import robocasa_batch_transactions as module
from cosmos_framework.inference.robocasa_batch_transactions import (
    BatchOutput,
    MediaCandidate,
)

from tools.v3.eval_v2_replan_tests.support import (
    RAW,
    client,
    predict,
    registration,
    reserved,
)
from tools.v3.eval_v2_replan_tests.support import (
    clock_kernel as clock_kernel,
)
from tools.v3.eval_v2_replan_tests.support import (
    systems as systems,
)


def post(case, operation, record):
    return case.direct.request("POST", "http://cpu/v2/" + operation, json=record)


def replay_ack(case, index):
    reservation, receipt = case.records[index]
    return {
        **{k: reservation[k] for k in ("lease", "request_key", "payload_sha256")},
        "receipt": copy.deepcopy(receipt),
    }


def snapshot(case):
    return {
        "native_calls": len(case.service.calls),
        "decodes": len(case.decodes),
        "files": {p.name: file_sha(p) for p in case.directory.glob("generated/*")},
        "spool": case.actor.info()["media_jobs"],
        "room": case.actor.media_room(),
    }


def save_next(case):
    index = len(case.records)
    result = predict(case.value)
    receipt = case.value.media(result, index, case.sink.prediction)
    assert receipt["status"] == "VIDEO_SAVED" and receipt["index"] == index
    reservation = next(
        kwargs["json"]
        for _, path, kwargs in case.direct.calls
        if path == "/v2/media/reserve" and kwargs["json"]["replan"] == index
    )
    case.records.append((copy.deepcopy(reservation), copy.deepcopy(receipt)))
    return receipt


@pytest.fixture
def completed(tmp_path, systems):
    service, actor, direct = systems()
    assignment = registration(direct)
    value = client(direct, assignment, media_drain_timeout_s=10)
    directory = tmp_path / "media"
    directory.mkdir()
    sink = MediaSink(
        directory,
        rollout=False,
        generated="all",
        grace_s=0.1,
        drain_timeout_s=10,
        identity=dict(
            task="CloseFridge", episode=0, generation=1, attempt_id="attempt-1"
        ),
    )
    decodes = []
    generate = actor.generate_many
    decode = actor.decode_media

    def distinct_frames(payloads, updates):
        output = generate(payloads, updates)
        candidates = []
        for request, candidate in zip(payloads, output.media, strict=True):
            frames = candidate.value
            offset = request["inference"]["request_index"] % len(frames)
            candidates.append(
                MediaCandidate(frames[offset:] + frames[:offset], candidate.size)
            )
        return BatchOutput(output.actions, tuple(candidates))

    def decoded(value):
        decodes.append(value)
        return decode(value)

    actor.generate_many, actor.decode_media = distinct_frames, decoded
    case = SimpleNamespace(
        service=service,
        actor=actor,
        direct=direct,
        value=value,
        sink=sink,
        directory=directory,
        decodes=decodes,
        records=[],
    )
    try:
        first, second = save_next(case), save_next(case)
        assert first["binding"]["video_sha256"] != second["binding"]["video_sha256"]
        assert first["sha256"] != second["sha256"]
        assert (
            actor.info()["media_jobs"] == 0 and len(service.calls) == len(decodes) == 2
        )
        yield case
    finally:
        value.close()
        result = sink.close()
        assert not result["encoder_alive"] and not result["feeder_alive"]
        assert not result["process_cleanup_failed"]


def test_old_reservation_after_two_ACKs_never_allocates_spool(completed):
    case = completed
    before = snapshot(case)
    result = post(case, "media/reserve", case.records[0][0])
    assert result.status_code == 200 and result.json().get("already_saved") is True, (
        result.json(),
        case.actor.info()["media_jobs"],
    )
    assert result.json()["reserved"] is True and snapshot(case) == before
    assert (
        post(case, "media/reserve", case.records[1][0]).json()["already_saved"] is True
    )
    assert snapshot(case) == before


def test_old_ACK_after_two_ACKs_is_idempotent(completed):
    case = completed
    before = snapshot(case)
    for index in (0, 1, 0):
        result = post(case, "media/ack", replay_ack(case, index))
        assert result.status_code == 200 and result.json()["acknowledged"] is True
        assert result.json()["request_key"] == case.records[index][0]["request_key"]
    assert snapshot(case) == before


@pytest.mark.parametrize(
    "field", ["request_key", "payload_sha256", "replan", "frontier"]
)
def test_changed_historical_reservation_is_rejected_before_resource_use(
    completed, field
):
    case = completed
    before = snapshot(case)
    reservation = copy.deepcopy(case.records[0][0])
    reservation[field] = "e" * 64 if field in ("request_key", "payload_sha256") else 1
    with pytest.raises(ValueError):
        post(case, "media/reserve", reservation)
    assert snapshot(case) == before


@pytest.mark.parametrize(
    "field",
    [
        "request_key",
        "payload_sha256",
        "receipt_hash",
        "receipt_index",
        "receipt_assignment",
    ],
)
def test_changed_historical_ACK_never_mutates_saved_authority(completed, field):
    case = completed
    before = snapshot(case)
    ack = replay_ack(case, 0)
    if field in ("request_key", "payload_sha256"):
        ack[field] = "e" * 64
    elif field == "receipt_hash":
        ack["receipt"]["sha256"] = "e" * 64
    elif field == "receipt_index":
        ack["receipt"]["index"] = 1
    else:
        ack["receipt"]["binding"]["transfer"]["assignment"]["task"] = "foreign"
    with pytest.raises(ValueError):
        post(case, "media/ack", ack)
    assert snapshot(case) == before


def test_many_old_replays_do_not_fill_four_jobs_or_block_new_replans(completed):
    case = completed
    for _ in range(4):
        save_next(case)
    before = snapshot(case)
    assert before["spool"] == 0 and before["room"][0] == 4
    # Five distinct old keys plus repeats: the previous last-only cache could
    # occupy all four jobs before the fifth old reservation even arrived.
    for _ in range(3):
        for index in range(6):
            result = post(case, "media/reserve", case.records[index][0])
            assert result.status_code == 200 and result.json()["already_saved"] is True
            assert (
                post(case, "media/ack", replay_ack(case, index)).json()["acknowledged"]
                is True
            )
    assert snapshot(case) == before
    assert save_next(case)["index"] == 6
    assert (
        case.actor.info()["media_jobs"] == 0
        and len(case.service.calls) == len(case.decodes) == 7
    )


def test_foreign_valid_Session_replays_rejected_without_blocking_either_Session(
    completed,
):
    case = completed
    other = registration(case.direct, 1)
    before = snapshot(case)
    reservation = {**case.records[0][0], "lease": other["lease"]}
    ack = {**replay_ack(case, 0), "lease": other["lease"]}
    for operation, record in [("media/reserve", reservation), ("media/ack", ack)]:
        with pytest.raises(ValueError):
            post(case, operation, record)
    assert snapshot(case) == before
    other_client = client(case.direct, other, mode="none")
    try:
        assert predict(other_client)["action"] == [RAW] * 16
    finally:
        other_client.close()
    assert save_next(case)["index"] == 2
    assert (
        post(case, "media/reserve", case.records[0][0]).json()["already_saved"] is True
    )
    assert case.actor.info()["media_jobs"] == 0


def test_history_bound_counts_reserved_jobs_without_evicting_older_proofs(
    completed, monkeypatch
):
    case = completed
    assert module.MAX_MEDIA_REPLAY_RECORDS == 100001  # Existing wire index0..100000.
    monkeypatch.setattr(module, "MAX_MEDIA_REPLAY_RECORDS", 3)
    assignment = {"lease": case.value.lease}
    assert reserved(case.direct, case.actor, assignment, frontier=2, replan=2)[
        0
    ].json()["reserved"]
    assert case.actor.info()["media_jobs"] == 1
    denied, _, _ = reserved(case.direct, case.actor, assignment, frontier=3, replan=3)
    assert denied.status_code == 200 and denied.json()["reserved"] is False
    assert denied.json()["media"]["status"] == "MEDIA_INCOMPLETE"
    assert case.actor.info()["media_jobs"] == 1
    assert save_next(case)["index"] == 2  # Previously reserved proof remains valid.
    history = case.actor._acked_media[case.value.lease["session_id"]]
    assert len(history) == 3 and case.actor.info()["media_jobs"] == 0
    assert (
        reserved(case.direct, case.actor, assignment, frontier=3, replan=3)[0].json()[
            "reserved"
        ]
        is False
    )
    for index in range(3):
        assert (
            post(case, "media/reserve", case.records[index][0]).json()["already_saved"]
            is True
        )
        assert (
            post(case, "media/ack", replay_ack(case, index)).json()["acknowledged"]
            is True
        )
    other = registration(case.direct, 1)
    assert reserved(case.direct, case.actor, other)[0].json()[
        "reserved"
    ]  # Per Episode.
    assert post(case, "session/end", {"lease": other["lease"]}).json()["acknowledged"]


def test_ACK_history_released_on_End_and_stale_generation_stays_rejected(completed):
    case = completed
    session = case.value.lease["session_id"]
    assert session in case.actor._acked_media
    case.value.end()
    assert session not in case.actor._acked_media
    fresh = registration(case.direct, generation=2)
    for operation, record in [
        ("media/reserve", case.records[0][0]),
        ("media/ack", replay_ack(case, 0)),
    ]:
        with pytest.raises(ValueError):
            post(case, operation, record)
    new_client = client(case.direct, fresh, mode="none")
    try:
        assert predict(new_client)["action"] == [RAW] * 16
        assert fresh["lease"]["session_id"] != session
    finally:
        new_client.close()
    assert case.actor._acked_media == {} and case.actor.info()["media_jobs"] == 0


def test_pending_End_retains_completed_replay_authority_until_quiescence(completed):
    case = completed
    other = client(case.direct, registration(case.direct, 1), mode="none")
    entered, release = threading.Event(), threading.Event()
    generate = case.actor.generate_many

    def blocked(payloads, updates):
        entered.set()
        assert release.wait(5)
        return generate(payloads, updates)

    case.actor.generate_many = blocked
    session = case.value.lease["session_id"]
    with ThreadPoolExecutor(1) as pool:
        pending = pool.submit(predict, other)
        try:
            assert entered.wait(3)
            end = post(case, "session/end", {"lease": case.value.lease})
            assert end.status_code == 202 and end.json()["acknowledged"] is False
            assert len(case.actor._acked_media[session]) == 2
            assert (
                post(case, "media/ack", replay_ack(case, 0)).json()["acknowledged"]
                is True
            )
            release.set()
            assert pending.result(3)["action"] == [RAW] * 16
            case.value.end()
            assert session not in case.actor._acked_media
        finally:
            release.set()
            pending.result(3)
            other.close()
