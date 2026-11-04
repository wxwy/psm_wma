"""New-protocol OS double; reuse the established native CPU fixture unchanged."""

import json
import sys
import time
from pathlib import Path

from tools.v3.eval_v2_batch_tests import os_fixture as old


def main():
    old.kernel_fixture()
    if sys.argv[1] == "server":
        from cosmos_framework.inference import robocasa_batch_transactions as batch

        original = batch.BatchedSessionTransactions

        class StreamingBatch(original):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, capacity_profile="streaming32", **kwargs)

        batch.BatchedSessionTransactions = StreamingBatch
        old.run_server(sys.argv[2:])
        return
    from cosmos_framework.simulation.robocasa import eval_v2_worker as worker

    original = worker.serve

    def controlled(channel, cfg, *, factory):
        root = Path(cfg["task_root"]).parents[1]
        manifest = json.loads((root / "manifest.json").read_bytes())
        count = (
            len(manifest["execution"]["gpu_ids"])
            * manifest["execution"]["sims_per_gpu"]
        )

        def overlap(stage):
            directory = root / "_internal/cpu_streaming_startup" / stage
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / cfg["physical_slot_id"]
            if path.exists():
                return
            start = time.monotonic()
            path.write_text(json.dumps({"start": start}))
            limit = start + 90
            while len(list(directory.iterdir())) < count:
                if time.monotonic() >= limit:
                    raise TimeoutError("controlled concurrent startup did not overlap")
                time.sleep(0.01)
            time.sleep(0.3)
            path.write_text(json.dumps({"start": start, "end": time.monotonic()}))

        overlap("READY")

        def environment(task, spec, grant):
            overlap("make_env")
            return factory(task, spec, grant)

        original(channel, cfg, factory=environment)

    worker.serve = controlled
    old.run_sim(sys.argv[2:])


if __name__ == "__main__":
    main()
