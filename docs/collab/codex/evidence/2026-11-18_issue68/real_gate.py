"""Author-only isolated real dual-pipeline Gate; private outputs stay on data.

Never writes to the input View dataset. Every deletion belongs to the existing
explicit retirement protocol under this new Gate, never to the 9126EP output.
"""

import argparse
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from g2.io import digest, read_json, write_json
from g2.latent_cache.batch_contract import make_batch_recipe
from g2.latent_cache.batch_encoding import WanBatchEncoder
from g2.latent_cache.batch_verify import verify_replay
from g2.latent_cache.builder import verify_episode
from g2.latent_cache.contract import fingerprint
from g2.latent_cache.final_source import load_source
from g2.latent_cache.retirement_policy import POSTHOC_SCHEMA
from g2.latent_cache.storage import _load, open_episode_index
from g2.latent_cache.streaming import EventSpool
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import validate_profile_episode
from g2.offline.view_only_source import CLAIM, claim_view_only_root

SAMPLES = (
    "tasks/CloseBlenderLid/episodes/episode_000000",
    "tasks/CloseFridge/episodes/episode_000502",
)
CHILD = "d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2"
NAV = "70eb7b447e65d793b0ebe18b258291ce46f057c1"


def inventory(root):
    return {
        str(p.relative_to(root)): digest(p)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def image_states(root):
    source = load_source(root)
    return {
        f"{s}/{vid}": None if n is None else v["owners"][n]["sha256"]
        for vid, v in source["views"].items()
        for s, n in enumerate(v["state_records"])
    }


def model(args):
    return WanBatchEncoder(
        args.weights,
        cosmos_root=args.code / "cosmos-framework",
        device="cuda:0",
        max_batch_size=32,
    )


def env(args):
    value = os.environ.copy()
    value.update(
        PYTHONPATH=str(args.code) + ":" + str(args.code / "cosmos-framework"),
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONNOUSERSITE="1",
        COSMOS_DEVICE="cuda",
        COSMOS_TRAINING="0",
        COSMOS_INTERNAL="0",
        CUDA_VISIBLE_DEVICES="4,5,6,7",
        CUBLAS_WORKSPACE_CONFIG=":4096:8",
    )
    return value


def call(
    args, name, command, *, during=None, spool=None, timeout=1200, expected_exit=0
):
    write_json(
        args.gate / (name + ".command.json"),
        dict(
            argv=command,
            expected_exit=expected_exit,
            cwd=str(args.code),
            environment={
                k: v
                for k, v in env(args).items()
                if k
                in (
                    "CUDA_VISIBLE_DEVICES",
                    "PYTHONPATH",
                    "PYTHONDONTWRITEBYTECODE",
                    "COSMOS_DEVICE",
                    "CUBLAS_WORKSPACE_CONFIG",
                )
            },
        ),
    )
    snapshots = []
    started = time.time()
    offered = False
    with (args.gate / (name + ".log")).open("w") as log:
        p = subprocess.Popen(
            command, cwd=args.code, env=env(args), stdout=log, stderr=subprocess.STDOUT
        )
        try:
            while p.poll() is None:
                current = dict(time=time.time())
                if spool and (spool / "events.sqlite").exists():
                    with sqlite3.connect(spool / "events.sqlite", timeout=5) as db:
                        ready = db.execute(
                            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='engine_workers'"
                        ).fetchone()[0]
                        if ready:
                            current["early_ack"] = db.execute(
                                "SELECT COUNT(*) FROM events e JOIN jobs j ON j.id=e.job WHERE e.status='acked' AND j.source_ready IS NULL"
                            ).fetchone()[0]
                            current["pending"] = db.execute(
                                "SELECT COUNT(*) FROM events"
                            ).fetchone()[0]
                            current["worker_count"] = db.execute(
                                "SELECT COUNT(DISTINCT gpu) FROM engine_workers WHERE state!='stopped'"
                            ).fetchone()[0]
                if during and not offered and current.get("pending", 0) > 0:
                    during()
                    offered = True
                    current["later_episode_published"] = True
                if len(snapshots) % 5 == 0:
                    current["gpu"] = subprocess.check_output(
                        [
                            "nvidia-smi",
                            "--query-gpu=index,memory.used,utilization.gpu",
                            "--format=csv,noheader,nounits",
                        ],
                        text=True,
                    ).splitlines()[4:8]
                snapshots.append(current)
                if time.time() - started > timeout:
                    p.send_signal(signal.SIGTERM)
                    p.wait(60)
                    raise RuntimeError("owned sample timed out; source retained")
                time.sleep(0.2)
            assert p.returncode == expected_exit, (name, p.returncode)
        finally:
            if p.poll() is None:
                p.send_signal(signal.SIGTERM)
                try:
                    p.wait(60)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait(10)
            write_json(
                args.gate / (name + ".resources.json"),
                dict(
                    elapsed_s=time.time() - started,
                    snapshots=snapshots,
                    late_publication=offered,
                ),
            )
    return snapshots


def audits(args, data, spool):
    rows = []
    contexts = {}
    for relative in SAMPLES:
        root = data / relative
        m = validate_profile_episode(root)
        a = verify_episode(root)
        index = open_episode_index(root)
        for vid, entry in index.manifest["views"].items():
            value, _, _ = _load(root / "vae_cache" / entry["path"])
            contexts.update(value["metadata"]["batch_executions"])
        rows.append(
            dict(
                episode=relative,
                source_id=m["source_id"],
                states=len(m["states"]),
                views=a["payloads_checked"],
                records=a["records_checked"],
                bytes=sum(p.stat().st_size for p in root.rglob("*") if p.is_file()),
                index_bytes=(root / "spatial_source_index.json").stat().st_size
                if (root / "spatial_source_index.json").exists()
                else None,
            )
        )
    stats = EventSpool.open(spool).stats()
    assert (
        stats["active_jobs"] == stats["active_records"] == stats["pending_inputs"] == 0
    )
    assert not list((spool / "records").rglob("*.pt"))
    return dict(
        rows=rows,
        actual_batch_sizes=sorted({len(c["members"]) for c in contexts.values()}),
        cross_episode_batches=sum(
            len({m["event"]["episode_key"] for m in c["members"]}) > 1
            for c in contexts.values()
        ),
        contexts=len(contexts),
        spool=stats,
    )


def native_trace(spool):
    """ACK-only recovery is not evidence that a card actually encoded."""
    calls = []
    for path in (spool / "worker_logs").glob("*.jsonl"):
        for line in path.read_text().splitlines():
            value = json.loads(line)
            if not value.get("native_called"):
                continue
            assert not value.get("test_only")
            assert (
                value["metrics"]["native_calls"] == 1
                and value["metrics"]["native_cuda_ms"] > 0
            )
            assert value["native_input_shape"][1:] == [3, 1, 256, 256]
            calls.append(value)
    gpus = sorted({v["physical_gpu"] for v in calls})
    overlap = sum(
        a["physical_gpu"] != b["physical_gpu"]
        and max(a["encode_api_started_unix"], b["encode_api_started_unix"])
        < min(a["encode_api_completed_unix"], b["encode_api_completed_unix"])
        for i, a in enumerate(calls)
        for b in calls[i + 1 :]
    )
    assert len(gpus) >= 2 and overlap > 0, (
        "two GPU native encoding/overlapping API calls not established"
    )
    return dict(
        native_gpu_ids=gpus,
        native_calls=len(calls),
        overlapping_encode_api_pairs=overlap,
        overlap_scope="ENCODE_API_INCLUDES_COLD_LOAD_PREPROCESS_NOT_CUDA_KERNEL_TRACE",
        calls=calls,
    )


def independent(args):
    args.gate.mkdir(exist_ok=False)
    data = args.gate / "dataset"
    original = {r: inventory(args.original / r) for r in SAMPLES}
    m = validate_profile_episode(args.original / SAMPLES[0])
    assert not m["output_profile"]["view_vae"]
    claim_view_only_root(
        data, OutputProfile.from_dict(m["output_profile"]), fingerprint(original)
    )
    write_json(args.gate / "original_before.json", original)

    def publish(relative):
        target = data / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.parent / (".copy-" + target.name)
        shutil.copytree(args.original / relative, temporary)
        assert inventory(temporary) == original[relative]
        temporary.rename(target)

    publish(SAMPLES[0])
    spool = args.gate / "spool"
    config = args.gate / "engine.json"
    write_json(
        config,
        dict(
            gpus=[4, 5, 6, 7],
            max_batch_size_per_gpu=32,
            batch_wait_ms=10000,
            idle_timeout_s=5,
            discovery_interval_s=0.2,
            min_free_disk_bytes=2 * 1024**3,
        ),
    )
    command = [
        sys.executable,
        "-m",
        "tools.g2.run_spatial_vae_engine",
        "--execute",
        "--mode",
        "independent",
        "--spool-root",
        str(spool),
        "--dataset-root",
        str(data),
        "--weights",
        str(args.weights),
        "--cosmos-root",
        str(args.code / "cosmos-framework"),
        "--engine-config",
        str(config),
    ]
    call(
        args,
        "initialize",
        [("--initialize" if v == "--execute" else v) for v in command],
    )
    # Real coordinator loss after durable registration and before source offer;
    # the final engine must recover it, not skip its known target forever.
    probe = "import os,sys;from pathlib import Path;from g2.io import read_json;from g2.latent_cache.streaming import EventSpool;s=EventSpool.open(sys.argv[1]);r=Path(sys.argv[2]);m=read_json(r/'episode_manifest.json');s.register(r,episode_key=f\"{m['task_class']}/episode_{m['episode_id']:06d}\",source_fingerprint=m['source_fingerprint'],profile_id=m['output_profile']['profile_id']);os._exit(77)"
    call(
        args,
        "register_crash",
        [sys.executable, "-c", probe, str(spool), str(data / SAMPLES[0])],
        expected_exit=77,
    )
    command.append("--resume")
    samples = call(
        args, "independent", command, during=lambda: publish(SAMPLES[1]), spool=spool
    )
    assert any(s.get("later_episode_published") for s in samples)
    result = read_json(spool / "engine_result.json")
    assert result["status"] == "IDLE_TIMEOUT" and len(result["batch"]["gpu"]) >= 2
    assert (
        max(
            int(b)
            for g in result["batch"]["gpu"].values()
            for b in g["batch_histogram"]
        )
        == 32
    )
    trace = native_trace(spool)
    before = audits(args, data, spool)
    assert before["cross_episode_batches"] >= 1
    policy = dict(
        schema=POSTHOC_SCHEMA,
        format="capsule_v2",
        output_root=str(data),
        work_root=str(args.gate / "unused_work"),
        spool_root=str(args.gate / "retirement_spool"),
        config_id=fingerprint(dict(root=args.formal_root, gate=str(args.gate))),
        mapping_sha256=digest(args.mapping),
        source_versions=dict(root=args.formal_root, child=CHILD, nav=NAV),
        protected_roots=[
            str(p.resolve())
            for p in (args.original, args.mapping, args.code, args.weights)
        ],
        keep_full_audit=False,
        audit_archive_root=None,
        audit_retention_policy=None,
        view_first_claim_sha256=digest(data / CLAIM),
    )
    write_json(args.gate / "policy.json", policy)
    payloads = {
        r: {
            str(p.relative_to(data / r)): digest(p)
            for p in (data / r / "vae_cache").rglob("*.pt")
        }
        for r in SAMPLES
    }
    call(
        args,
        "retirement",
        [
            sys.executable,
            "-m",
            "tools.g2.retire_view_first_sources",
            "--execute",
            "--dataset-root",
            str(data),
            "--spool-root",
            policy["spool_root"],
            "--source-policy",
            str(args.gate / "policy.json"),
            "--recipe-id",
            result["recipe_id"],
            "--expected-episodes",
            "2",
        ],
    )
    for r in SAMPLES:
        root = data / r
        assert all(digest(root / p) == sha for p, sha in payloads[r].items())
        assert all(
            digest(root / p) == sha
            for p, sha in validate_profile_episode(args.original / r)["files"].items()
        )
        assert not any(
            (root / f).exists()
            for f in (
                "spatial_source.json",
                "spatial_source.json.gz",
                "SPATIAL_SOURCE_GZIP.json",
                "SPATIAL_SOURCE_READY.json",
                ".source_retirement",
            )
        )
    # No image rerender/model reload is necessary for ordinary resume after C.
    call(args, "independent_resume", command, spool=spool)
    os.environ["CUDA_VISIBLE_DEVICES"] = "4"
    replay = verify_replay(data, model(args))
    assert original == {r: inventory(args.original / r) for r in SAMPLES}
    report = dict(
        status="PASS",
        gate="INDEPENDENT_VAE_E2E",
        fixed_root=args.formal_root,
        recipe_id=result["recipe_id"],
        discovery_after_start=True,
        manager_register_crash_resumed=True,
        engine=result,
        native_execution=trace,
        before_retirement=before,
        after_retirement=audits(args, data, spool),
        replay=replay,
        original_unchanged=True,
        training_ready=False,
    )
    write_json(args.gate / "result.json", report)
    print(json.dumps(report, sort_keys=True))


def sync(args):
    args.gate.mkdir(exist_ok=False)
    cfg = read_json(args.sync_base_config)
    for key, name in (
        ("output_root", "output"),
        ("work_root", "work"),
        ("spool_root", "spool"),
        ("run_root", "run"),
    ):
        cfg[key] = str(args.gate / name)
    cfg.update(
        root_sha=args.formal_root,
        renderer_gpus=[4],
        workers_per_gpu=2,
        max_active_jobs=2,
        allow_shared_gpu_processes=True,
        max_events=512,
        max_spool_bytes=512 * 1024**2,
        ros_port_base=27500,
        monitor_interval_s=1,
        vae_engine=dict(
            gpus=[4, 5, 6, 7],
            max_batch_size_per_gpu=32,
            batch_wait_ms=1000,
            test_crash_once="after_ack:0",
        ),
    )
    cfg["expected_recipe_id"] = make_batch_recipe(model(args).descriptor())["recipe_id"]
    config = args.gate / "config.json"
    write_json(config, cfg)
    command = [
        sys.executable,
        "-m",
        "tools.g2.run_stage_a_production",
        "run",
        "--config",
        str(config),
        "--manual-start",
    ]
    snapshots = call(args, "sync", command, spool=Path(cfg["spool_root"]))
    assert any(s.get("early_ack", 0) > 0 for s in snapshots), (
        "no durable ACK observed before source-ready"
    )
    run = read_json(Path(cfg["run_root"]) / "result.json")
    assert run["complete"] and run["phase"] == "DONE"
    engine = read_json(Path(cfg["spool_root"]) / "engine_result.json")
    assert engine["status"] == "DRAINED" and len(engine["batch"]["gpu"]) >= 2
    assert sum(engine["worker_restarts"].values()) == 1
    trace = native_trace(Path(cfg["spool_root"]))
    data = Path(cfg["output_root"])
    for r in SAMPLES:
        root = data / r
        assert not any(
            (root / f).exists()
            for f in (
                "spatial_source.json",
                "spatial_source.json.gz",
                ".source_retirement",
            )
        )
        assert image_states(root) == image_states(args.original / r), (
            "fresh F27 pixels/view availability changed"
        )
    assert not list(Path(cfg["work_root"]).glob("tasks/*/episodes/episode_*"))
    os.environ["CUDA_VISIBLE_DEVICES"] = "5"
    replay = verify_replay(data, model(args))
    report = dict(
        status="PASS",
        gate="SYNC_VIEW_VAE_E2E",
        fixed_root=args.formal_root,
        recipe_id=cfg["expected_recipe_id"],
        fresh_original_f27=True,
        all_state_pixels_and_view_sets_match_original=True,
        early_durable_ack=True,
        worker_crash_resumed_same_batch=True,
        engine=engine,
        native_execution=trace,
        audit=audits(args, data, Path(cfg["spool_root"])),
        replay=replay,
        run=run,
        training_ready=False,
    )
    write_json(args.gate / "result.json", report)
    print(json.dumps(report, sort_keys=True))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("independent", "sync"))
    for name in ("gate", "code", "original", "mapping", "weights"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--formal-root", required=True)
    p.add_argument("--sync-base-config", type=Path)
    a = p.parse_args()
    assert (
        subprocess.check_output(
            ["git", "-C", str(a.code), "rev-parse", "HEAD"], text=True
        ).strip()
        == a.formal_root
    )
    assert (
        subprocess.check_output(
            ["git", "-C", str(a.code / "cosmos-framework"), "rev-parse", "HEAD"],
            text=True,
        ).strip()
        == CHILD
    )
    {"sync": sync, "independent": independent}[a.mode](a)


if __name__ == "__main__":
    main()
