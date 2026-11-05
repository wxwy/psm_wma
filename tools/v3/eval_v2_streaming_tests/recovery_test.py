"""Same-Task multi-Episode recovery and concurrent health-only resolution."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from cosmos_framework.evaluation.robocasa_v2.scheduler import StreamingScheduler
from cosmos_framework.evaluation.robocasa_v2.store import Store
from robocasa_eval_v2.runtime import Runtime
from tools.v3.eval_v2_production_tests.store_test import close_streams, healthy
from tools.v3.eval_v2_streaming_tests.scheduler_test import fresh, complete


def test_resume_only_resolves_same_episode_and_same_stream_health_is_idempotent(
    tmp_path,
):
    value = fresh(tmp_path, episodes=2)
    slots = {"a": uuid.uuid4().hex, "b": uuid.uuid4().hex}
    with value.locked():
        scheduler = StreamingScheduler(value, slots)
        claims = [scheduler.dispatch(w) for w in slots]
        for claim in claims:
            value.finish_invalid(claim["attempt"], "controlled original failure")
        wide = value.record_process_error(
            "CloseFridge", "coordinator_stop", "controlled Task-wide fault"
        )
        scheduler.cancel("explicit Resume after complete cleanup")
        close_streams(value, "CloseFridge")
    value = Store(value.root, value.manifest)
    with value.locked():
        scheduler = StreamingScheduler(value, slots)
        claims = [scheduler.dispatch(w) for w in slots]
        certificates = {
            error["id"]: value.certify_recovery(
                "CloseFridge", error["stream_id"], healthy
            )
            for error in value.errors("CloseFridge")
        }
        # Two independently valid Slot health proofs may race for the Task fault.
        cert2 = value.certify_recovery("CloseFridge", wide["stream_id"], healthy)
        with ThreadPoolExecutor(2) as pool:
            futures = [
                pool.submit(value.resolve_error, "CloseFridge", wide["id"], cert)
                for cert in (certificates[wide["id"]], cert2)
            ]
            assert futures[0].result(5) == futures[1].result(5)
        runtime = SimpleNamespace(store=value, certificates=certificates)
        first = complete(scheduler, claims[0])
        Runtime._resolve_faults(runtime, "CloseFridge", first)
        unresolved = [e for e in value.errors("CloseFridge") if e["resolution"] is None]
        assert len(unresolved) == 1 and unresolved[0]["attempt"]["episode"] == 1
        second = complete(scheduler, claims[1])
        Runtime._resolve_faults(runtime, "CloseFridge", second)
        assert all(e["resolution"] is not None for e in value.errors("CloseFridge"))
        close_streams(value, "CloseFridge")
        assert value.publish_views()["results_qualified"]
