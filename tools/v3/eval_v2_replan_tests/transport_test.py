"""All-mode real API/HTTP -> actor -> Encoder -> receipt -> ACK ordering."""
# ruff: noqa: F811 -- pytest resolves imported fixture names in parameters.

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
import requests
from cosmos_framework.evaluation.robocasa_v2.generated_video import inspect_video
from cosmos_framework.evaluation.robocasa_v2.media import MediaSink
from cosmos_framework.inference.robocasa_batch_transactions import (
    BatchOutput,
    MediaCandidate,
)
from cosmos_framework.inference.robocasa_session_transactions import digest
from cosmos_framework.simulation.robocasa.eval_v2_transactions import PolicyTransport

from tools.v3.eval_v2_replan_tests.support import (
    RAW,
    client,
    http_server,
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


def sink_at(path, **kwargs):
    path.mkdir(exist_ok=True)
    return MediaSink(
        path,
        rollout=False,
        generated="all",
        grace_s=0.1,
        drain_timeout_s=10,
        identity=dict(
            task="CloseFridge", episode=0, generation=1, attempt_id="attempt-1"
        ),
        **kwargs,
    )


def test_ten_replans_real_HTTP_encoder_decode_receipts_ACK_and_final_End(
    tmp_path, systems
):
    service, actor, direct = systems()
    assignment = registration(direct)
    sink = sink_at(tmp_path / "media")
    acknowledgments = []

    def before(method, path, record):
        if path == "/v2/media/ack":
            receipt = record["receipt"]
            final = tmp_path / "media" / receipt["path"]
            assert final.is_file()
            saved = final.with_suffix(".receipt.json")
            assert json.loads(saved.read_bytes()) == receipt
            assert (
                inspect_video(final, frames=3, size=[32, 32])["sha256"]
                == receipt["sha256"]
            )
            acknowledgments.append(receipt["index"])

    with http_server(service, before) as (base, calls):
        settings = dict(
            server_url=base,
            predict_timeout_s=5,
            max_infer_batch_size=1,
            local_memory_mode="off",
            save_generated_video="all",
            media_drain_timeout_s=10,
        )
        value = PolicyTransport(settings, assignment, time.monotonic() + 90)
        try:
            for index in range(10):
                result = predict(value)
                assert result["action"] == [RAW] * 16
                receipt = value.media(result, index, sink.prediction)
                assert receipt["status"] == "VIDEO_SAVED"
            # End immediately after the last replan: no cancelled tail.
            value.end()
            report = value.media_diagnostics()
            assert report["completion"] == {
                "status": "COMPLETE",
                "expected": 10,
                "acknowledged": 10,
            }
            assert acknowledgments == list(range(10))
            assert len(service.calls) == 10  # never regenerate actions to fix media
            assert actor.info()["sessions"] == actor.info()["media_jobs"] == 0
            assert sum(path == "/v2/media/reserve" for _, path, _ in calls) == 10
        finally:
            value.close()
            closed = sink.close()
    assert (
        closed["generated_media"]["saved"] == list(range(10)) and closed["dropped"] == 0
    )
    assert not closed["forced_encoder_cleanup"] and not closed["process_cleanup_failed"]
    assert len(list((tmp_path / "media/generated").glob("*.mp4"))) == 10


def test_four_job_spool_full_returns_backpressure_and_other_End_releases(systems):
    _, actor, direct = systems()
    assignments = [registration(direct, i) for i in range(5)]
    for a in assignments[:4]:
        response, _, _ = reserved(direct, actor, a)
        assert response.status_code == 200 and response.json()["reserved"]
    assert actor.info()["media_spool_max_jobs"] == 4
    assert actor.info()["media_spool_max_bytes"] == 512 * 1024**2
    response, _, last = reserved(direct, actor, assignments[4])
    assert response.status_code == 429
    assert actor.info()["media_jobs"] == 4
    assert direct.request(
        "POST", "http://cpu/v2/session/end", json={"lease": assignments[0]["lease"]}
    ).json()["acknowledged"]
    assert direct.request("POST", "http://cpu/v2/media/reserve", json=last).json()[
        "reserved"
    ]
    assert actor.info()["media_jobs"] == 4


def test_client_backpressure_waits_outside_executor_and_resumes_after_End(
    systems, tmp_path
):
    _, actor, direct = systems(media_spool_max_jobs=1)
    first, second = registration(direct), registration(direct, 1)
    assert reserved(direct, actor, first)[0].json()["reserved"]
    value = client(direct, second)
    sink = sink_at(tmp_path / "media")
    with ThreadPoolExecutor(1) as executor:
        job = executor.submit(predict, value)
        try:
            time.sleep(0.1)
            assert not job.done() and not actor._busy
            assert direct.request(
                "POST", "http://cpu/v2/session/end", json={"lease": first["lease"]}
            ).json()["acknowledged"]
            result = job.result(timeout=3)
            assert value.media(result, 0, sink.prediction)["status"] == "VIDEO_SAVED"
            assert value.media_diagnostics()["completion"]["status"] == "COMPLETE"
        finally:
            value.close()
            assert not sink.close()["process_cleanup_failed"]


def test_reservation_timeout_keeps_actions_and_explicit_incomplete(systems):
    service, actor, direct = systems(media_spool_max_jobs=1)
    first, second = registration(direct), registration(direct, 1)
    reserved(direct, actor, first)
    value = client(direct, second, media_drain_timeout_s=0.06)
    try:
        for index in range(2):
            result = predict(value)
            assert (
                result["action"] == [RAW] * 16
                and result["media"]["status"] == "disabled"
            )
            value.media(
                result, index, lambda *a: pytest.fail("unreserved media delivered")
            )
        assert len(service.calls) == 2
        assert value.media_diagnostics()["completion"]["status"] == "MEDIA_INCOMPLETE"
        assert all("media" not in r for r in service.calls)
    finally:
        value.close()


@pytest.mark.parametrize("fault", ["candidate_bytes", "decode_bytes", "decoder_crash"])
def test_oversize_or_decode_failure_never_drops_silently_or_changes_actions(
    systems, fault
):
    service, actor, direct = systems(media_spool_max_bytes=2048)
    original = actor.generate_many

    def generate(payloads, updates):
        output = original(payloads, updates)
        return BatchOutput(
            output.actions,
            tuple(
                MediaCandidate("latent", 4096 if fault == "candidate_bytes" else 8)
                for _ in payloads
            ),
        )

    actor.generate_many = generate
    if fault == "decoder_crash":
        actor.decode_media = lambda _: (_ for _ in ()).throw(
            OSError("injected decoder")
        )
    else:
        actor.decode_media = lambda _: ["x" * 4096]
    value = client(direct, registration(direct))
    try:
        result = predict(value)
        assert result["action"] == [RAW] * 16
        value.media(
            result, 0, lambda *a: pytest.fail("invalid generated media delivered")
        )
        assert value.media_diagnostics()["completion"]["status"] == "MEDIA_INCOMPLETE"
        assert len(service.calls) == 1
    finally:
        value.close()
    assert actor.info()["sessions"] == actor.info()["media_jobs"] == 0


def test_slow_decode_and_fetch_still_save_before_ACK(systems, tmp_path):
    _, actor, direct = systems()
    original = actor.decode_media
    entered, release = threading.Event(), threading.Event()

    def slow_decode(v):
        entered.set()
        assert release.wait(3)
        return original(v)

    actor.decode_media = slow_decode
    assignment = registration(direct)
    value = client(direct, assignment)
    sink = sink_at(tmp_path / "media")
    result = predict(value)
    try:
        assert entered.wait(2)
        assert actor.info()["media_jobs"] == 1
        with ThreadPoolExecutor(1) as pool:
            delivery = pool.submit(value.media, result, 0, sink.prediction)
            time.sleep(0.1)
            assert not delivery.done()
            assert not any(p == "/v2/media/ack" for _, p, _ in direct.calls)
            release.set()
            assert delivery.result(10)["status"] == "VIDEO_SAVED"
    finally:
        release.set()
        value.close()
        assert not sink.close()["process_cleanup_failed"]


def test_lost_server_ACK_retries_same_receipt_without_extra_encode(systems, tmp_path):
    _, actor, direct = systems()
    value = client(direct, registration(direct))
    sink = sink_at(tmp_path / "media")
    original = direct.request
    acks = []

    def drop_first(method, url, **kwargs):
        response = original(method, url, **kwargs)
        if url.endswith("/v2/media/ack"):
            acks.append(kwargs["json"]["receipt"])
            if len(acks) == 1:
                raise requests.ConnectionError("ACK lost after server release")
        return response

    direct.request = drop_first
    try:
        result = predict(value)
        receipt = value.media(result, 0, sink.prediction)
        assert receipt["status"] == "VIDEO_SAVED" and acks == [receipt, receipt]
        assert actor.info()["media_jobs"] == 0
        reserve = next(
            k["json"] for _, path, k in direct.calls if path == "/v2/media/reserve"
        )
        replay = direct.request(
            "POST", "http://cpu/v2/media/reserve", json=reserve
        ).json()
        assert replay["already_saved"] is True and actor.info()["media_jobs"] == 0
        with pytest.raises(ValueError, match="identity reused"):
            direct.request(
                "POST",
                "http://cpu/v2/media/reserve",
                json={**reserve, "payload_sha256": "f" * 64},
            )
        assert (
            value.media(result, 0, lambda *a: pytest.fail("duplicate encode")) is None
        )
        assert len(list((tmp_path / "media/generated").glob("*.mp4"))) == 1
        # A foreign duplicate is a media diagnostic, never another action or a
        # native-loop exception. The already-saved file remains untouched.
        assert (
            value.media(
                {**result, "payload_sha256": "f" * 64},
                0,
                lambda *a: pytest.fail("foreign encode"),
            )
            is None
        )
        assert value.media_diagnostics()["completion"]["status"] == "MEDIA_INCOMPLETE"
    finally:
        value.close()
        assert not sink.close()["process_cleanup_failed"]


def test_permanent_ACK_loss_retains_file_and_reports_incomplete(systems, tmp_path):
    # This budget includes a real Encoder cold start before the ACK fault.
    _, actor, direct = systems(media_drain_timeout_s=10)
    value = client(direct, registration(direct), media_drain_timeout_s=10)
    sink = sink_at(tmp_path / "media")
    original = direct.request
    ack_attempts = []

    def lost(method, url, **kwargs):
        if url.endswith("/v2/media/ack"):
            receipt = kwargs["json"]["receipt"]
            final = tmp_path / "media" / receipt["path"]
            assert final.is_file()
            assert (
                json.loads(final.with_suffix(".receipt.json").read_bytes()) == receipt
            )
            ack_attempts.append(time.monotonic())
            time.sleep(0.02)
            raise requests.ConnectionError("permanent ACK loss")
        return original(method, url, **kwargs)

    direct.request = lost
    try:
        result = predict(value)
        assert value.media(result, 0, sink.prediction) is None
        assert ack_attempts  # Never pass merely because startup timed out before ACK.
        diagnostics = value.media_diagnostics()
        assert diagnostics["completion"]["status"] == "MEDIA_INCOMPLETE"
        assert diagnostics["predictions"]["0"]["path"] == "generated/replan_0000.mp4"
        receipt = json.loads(
            (tmp_path / "media/generated/replan_0000.receipt.json").read_bytes()
        )
        assert (
            inspect_video(
                tmp_path / "media" / receipt["path"], frames=3, size=[32, 32]
            )["sha256"]
            == receipt["sha256"]
        )
    finally:
        value.close()
        assert not sink.close()["process_cleanup_failed"]


@pytest.mark.parametrize("mode", ["none", "first"])
def test_none_and_first_never_reserve_or_wait_for_VIDEO_SAVED(systems, mode):
    service, _, direct = systems()
    value = client(direct, registration(direct), mode)
    try:
        result = predict(value)
        if mode == "none":
            assert (
                "media" not in service.calls[0]
                and result["media"]["status"] == "disabled"
            )
        else:
            assert service.calls[0]["media"] == {"replan": 0}
        assert not any(p == "/v2/media/reserve" for _, p, _ in direct.calls)
        assert "completion" not in value.media_diagnostics()
    finally:
        value.close()


def test_reservation_and_ACK_identity_cannot_be_changed_or_released_early(systems):
    _, actor, direct = systems()
    assignment = registration(direct)
    response, _, record = reserved(direct, actor, assignment)
    assert response.json()["reserved"]
    assert direct.request("POST", "http://cpu/v2/media/reserve", json=record).json()[
        "reserved"
    ]
    with pytest.raises(ValueError, match="identity reused"):
        direct.request(
            "POST",
            "http://cpu/v2/media/reserve",
            json={**record, "payload_sha256": "b" * 64},
        )
    with pytest.raises(ValueError, match="invalid media ACK"):
        direct.request(
            "POST",
            "http://cpu/v2/media/ack",
            json={
                k: v
                for k, v in record.items()
                if k in ("lease", "request_key", "payload_sha256")
            },
        )
    assert actor.info()["media_jobs"] == 1
    assert digest(record) != digest({**record, "replan": 1})


def test_ready_media_cannot_be_ACKed_without_durable_receipt(systems, tmp_path):
    _, actor, direct = systems()
    value = client(direct, registration(direct))
    sink = sink_at(tmp_path / "media")
    try:
        result = predict(value)
        deadline = time.monotonic() + 3
        while actor.info()["busy"] and time.monotonic() < deadline:
            time.sleep(0.01)
        assert not actor.info()["busy"]
        proof = dict(
            lease=value.lease,
            request_key=result["request_key"],
            payload_sha256=result["payload_sha256"],
        )
        with pytest.raises(ValueError, match="durable VIDEO_SAVED"):
            direct.request("POST", "http://cpu/v2/media/ack", json=proof)
        assert actor.info()["media_jobs"] == 1 and not list(
            (tmp_path / "media").glob("generated/*.mp4")
        )
        receipt = value.media(result, 0, sink.prediction)
        assert receipt["status"] == "VIDEO_SAVED" and actor.info()["media_jobs"] == 0
        with pytest.raises(ValueError, match="changed strict media ACK"):
            direct.request(
                "POST",
                "http://cpu/v2/media/ack",
                json={**proof, "receipt": {**receipt, "sha256": "f" * 64}},
            )
    finally:
        value.close()
        assert not sink.close()["process_cleanup_failed"]


def test_cancelled_session_cannot_deliver_or_resurrect_media(systems):
    _, actor, direct = systems()
    value = client(direct, registration(direct))
    try:
        result = predict(value)
        deadline = time.monotonic() + 3
        while True:
            reply = direct.request(
                "POST", "http://cpu/v2/session/end", json={"lease": value.lease}
            )
            if reply.json()["acknowledged"]:
                break
            assert time.monotonic() < deadline
            time.sleep(0.01)
        assert (
            value.media(result, 0, lambda *a: pytest.fail("post-End delivery")) is None
        )
        assert value.media_diagnostics()["completion"]["status"] == "MEDIA_INCOMPLETE"
        assert actor.info()["media_jobs"] == actor.info()["sessions"] == 0
    finally:
        value.close()


def test_strict_decode_is_not_starved_by_new_inference_queue(systems):
    _, actor, direct = systems()
    values = [
        client(direct, registration(direct, i), "all" if i == 0 else "none")
        for i in range(2)
    ]
    original = actor.generate_many
    entered, release = threading.Event(), threading.Event()
    order = []

    def generate(payloads, updates):
        slot = payloads[0]["inference"]["session_id"]
        first = slot == values[0].lease["session_id"]
        order.append("generation0" if first else "generation1")
        if first:
            entered.set()
            assert release.wait(4)
        return original(payloads, updates)

    actor.generate_many = generate
    decode = actor.decode_media

    def decoding(value):
        order.append("strict_decode0")
        return decode(value)

    actor.decode_media = decoding
    with ThreadPoolExecutor(2) as pool:
        a = pool.submit(predict, values[0])
        try:
            assert entered.wait(2)
            b = pool.submit(predict, values[1])
            limit = time.monotonic() + 2
            while not actor.info()["queued"]:
                assert time.monotonic() < limit
                time.sleep(0.01)
            release.set()
            assert a.result(3)["action"] == b.result(3)["action"] == [RAW] * 16
            assert order == ["generation0", "strict_decode0", "generation1"]
            # No local receipt was requested in this priority-only test, so the
            # Episode's media must explicitly remain incomplete at End.
            assert (
                values[0].media_diagnostics()["completion"]["status"]
                == "MEDIA_INCOMPLETE"
            )
        finally:
            release.set()
            for value in values:
                value.close()


def test_End_waits_for_final_VIDEO_SAVED_and_other_session_End_is_not_locked(
    systems, tmp_path
):
    _, actor, direct = systems()
    value = client(direct, registration(direct))
    other = registration(direct, 1)
    sink = sink_at(tmp_path / "media")
    entered, release = threading.Event(), threading.Event()

    def delayed_save(index, result):
        entered.set()
        assert release.wait(5)
        return sink.prediction(index, result)

    result = predict(value)
    with ThreadPoolExecutor(2) as pool:
        saved = pool.submit(value.media, result, 0, delayed_save)
        ended = pool.submit(value.end)
        try:
            assert entered.wait(2)
            time.sleep(0.1)
            assert not ended.done()
            # No model lock is owned while the client waits for its Encoder.
            end = direct.request(
                "POST", "http://cpu/v2/session/end", json={"lease": other["lease"]}
            )
            assert end.json()["acknowledged"] and actor.info()["sessions"] == 1
            release.set()
            assert saved.result(10)["status"] == "VIDEO_SAVED"
            ended.result(5)
        finally:
            release.set()
            saved.result(10)
            value.close()
            assert not sink.close()["process_cleanup_failed"]
    assert actor.info()["sessions"] == 0


@pytest.mark.parametrize(
    "fault", ["late_fetch", "foreign_fetch", "bad_encoder_receipt"]
)
def test_late_or_foreign_delivery_never_ACKs_and_keeps_actions(
    systems, tmp_path, fault
):
    service, actor, direct = systems()
    value = client(direct, registration(direct), media_drain_timeout_s=0.15)
    original = direct.request

    def request(method, url, **kwargs):
        response = original(method, url, **kwargs)
        if method == "GET" and "/v2/media/" in url and response.status_code == 200:
            if fault == "late_fetch":
                time.sleep(0.2)
            elif fault == "foreign_fetch":
                record = response.json()
                record["payload_sha256"] = "f" * 64
                from cosmos_framework.inference.robocasa_session_transactions import (
                    Reply,
                    json_bytes,
                )

                from tools.v3.eval_v2_replan_tests.support import Response

                return Response(Reply(200, json_bytes(record)))
        return response

    direct.request = request
    try:
        result = predict(value)
        assert result["action"] == [RAW] * 16
        value.media(result, 0, lambda *a: {"status": "queued"})
        assert value.media_diagnostics()["completion"]["status"] == "MEDIA_INCOMPLETE"
        assert not any(p == "/v2/media/ack" for _, p, _ in direct.calls)
        assert len(service.calls) == 1
    finally:
        value.close()
    assert actor.info()["media_jobs"] == 0
