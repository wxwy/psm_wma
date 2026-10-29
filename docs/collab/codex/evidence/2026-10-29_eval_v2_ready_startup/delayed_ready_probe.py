"""External focused probe; delay real child READY and observe real Actor budgets."""

import json
import os
from pathlib import Path
import time

events = []


def pytest_runtest_setup(item):
    assert item.name == "test_stalled_actor_request_is_bounded_and_unrelated_process_survives"
    module = item.module
    source = module.ACTOR_CODE
    assert source.count("s=socket.socket(fileno=int(sys.argv[1]))") == 1
    module.ACTOR_CODE = source.replace(
        "s=socket.socket(fileno=int(sys.argv[1]))",
        "import time;time.sleep(0.4)\ns=socket.socket(fileno=int(sys.argv[1]))",
        1,
    )
    receive, request = module.Actor._receive, module.Actor.request

    def observed_receive(actor, *args, **kwargs):
        started = time.monotonic()
        result = receive(actor, *args, **kwargs)
        if result.get("kind") == "READY":
            assert actor.timeout == 5.0
            events.append({"op": "READY", "timeout_s": actor.timeout,
                "receive_elapsed_s": time.monotonic() - started, "injected_child_delay_s": 0.4})
        return result

    def observed_request(actor, op, **kwargs):
        if op != "stall":
            return request(actor, op, **kwargs)
        assert actor.timeout == 0.15
        started = time.monotonic()
        event = {"op": op, "timeout_s": actor.timeout}
        events.append(event)
        try:
            return request(actor, op, **kwargs)
        except BaseException as error:
            event["raised"] = type(error).__name__
            raise
        finally:
            event["elapsed_s"] = time.monotonic() - started

    module.Actor._receive = observed_receive
    module.Actor.request = observed_request


def pytest_sessionfinish(session, exitstatus):
    Path(os.environ["READY_PROBE_OUTPUT"]).write_text(json.dumps({
        "exit_status": int(exitstatus), "events": events,
        "real_OS_child_and_Actor": True, "original_test_assertions_unchanged": True,
    }, indent=2) + "\n")
