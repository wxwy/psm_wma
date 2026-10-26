"""B1: exact old-code CPU saves, candidate worker0 same-job continuation.

Synthetic state files are not real DCP/CUDA/distributed acceptance. Each version
runs in its own interpreter with its own complete, pinned Child source tree.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import io
import json
import os
import pickle
import random
import subprocess
import sys
import tarfile
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
OLD_ROOT = "e6ae2084305a8c24d763d82b517984660cc73c30"
OLD_CHILD = "923d9c3fd392e6bafbdb1771a292c7b313e6b3dc"
NEW_ROOT = "76d1cc70622d3b456a3c388ad98917b7d532890b"
NEW_CHILD = "3e5bf90b4eb5fa5cbad9fa7ab62e86bf44c6b07b"
JOB = "no_ttt_packed128_droid_fresh_30k_world4_ga4"


def fingerprint(value):
    """Compare tensor bytes and complete nested state, never pickle storage IDs."""
    import numpy as np
    import torch

    if isinstance(value, torch.Tensor):
        assert value.device.type == "cpu"
        return {
            "tensor": str(value.dtype),
            "shape": list(value.shape),
            "sha256": hashlib.sha256(value.detach().contiguous().numpy().tobytes()).hexdigest(),
        }
    if isinstance(value, np.ndarray):
        return {
            "numpy": str(value.dtype),
            "shape": list(value.shape),
            "sha256": hashlib.sha256(value.tobytes()).hexdigest(),
        }
    if dataclasses.is_dataclass(value):
        return fingerprint(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): fingerprint(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [fingerprint(v) for v in value]
    assert value is None or type(value) in (int, float, str, bool), type(value)
    return value


def file_witness(directory):
    return {
        str(p.relative_to(directory)): {
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "mtime_ns": p.stat().st_mtime_ns,
            "mode": p.stat().st_mode,
        }
        for p in sorted(directory.rglob("*"))
        if p.is_file()
    }


def runtime(case, phase):
    import numpy as np
    import torch
    from examples import psm_wma_robocasa_corrected_phase5 as cli
    from examples.psm_wma_robocasa_phase5_f0_test import _args, _config, _dataset_fields, _report
    from omegaconf import OmegaConf

    cli.torch, cli.OmegaConf = torch, OmegaConf
    args = _args(case / "outputs", "--no-ttt", "--job-name", JOB, "--world-size", "4", "--ga", "4")
    args.phase = phase
    if phase == "fresh":
        args.dataset_index_root.mkdir(parents=True)
        (args.dataset_index_root / "receipt.json").write_text('{"synthetic":"B1-only"}\n')
    config = OmegaConf.create(
        {
            "phase": phase,
            "job": {"path_local": str(cli.job_namespace(args))},
            "dataloader_train": _config(args).dataloader_train,
            "model": {
                "config": {
                    "local_memory_enabled": False,
                    "max_action_dim": 64,
                    "parallelism": {"data_parallel_shard_degree": 4, "data_parallel_replicate_degree": 1},
                }
            },
            "optimizer": {
                "keys_to_select": list(cli.GENERATION_KEYS),
                "optimizer_type": "FusedAdam",
                "lr": 5e-5,
                "lr_multipliers": {k: 5.0 for k in cli.ACTION_KEYS},
                "weight_decay": 0.05,
            },
            "scheduler": {"cycle_lengths": [30000], "warm_up_steps": [500]},
            "trainer": {
                "type": "cosmos_framework.trainer.matched_no_ttt.MatchedNoTTTTrainer",
                "max_iter": 30000,
                "grad_accum_iter": 4,
                "distributed_parallelism": "fsdp",
            },
            "model_parallel": {"context_parallel_size": 1},
            "data_setting": {"seed": 123},
            "checkpoint": {"save_iter": 100, "strict_resume": True},
        }
    )
    report = _report(args)
    report.update(
        cache_manifest_sha256="manifest",
        cache_corpus_digest="corpus",
        source_binding_digest="binding",
        model_witnesses={"droid": "synthetic-only"},
        transform_rng_mode="legacy_global",
    )
    # Both versions execute their real canonical training identity and digest APIs.
    semantic = cli.training_identity(args, config, report)
    authority = SimpleNamespace(
        manifest_digest="manifest", cache_corpus_digest="corpus", source_binding_digest="binding"
    )
    digest = cli.config_digest(authority, config, b_stream=8, active_ga=4, witnesses=report["model_witnesses"])
    digest = cli._json_digest({"phase5_digest": digest, "training_identity": semantic})
    report.update(training_identity=semantic, config_digest=digest)
    contract = SimpleNamespace(
        action_horizon=16, chunk_length=16, observation_frames=17, action_dim=15, state_dim=15, **_dataset_fields()
    )
    report["effective_data_source"] = cli.describe_effective_data_source(
        config, contract, ttt_steps=16, local_memory_enabled=False
    )
    assert "no_ttt_cpu_loader" not in semantic
    return np, torch, cli, args, config, report


def make_state(case, count, rank, digest):
    import numpy as np
    import torch
    from cosmos_framework.model.generator.mot.robocasa_exact_window_local import (
        ExactWindowRankPlanner,
        ExactWindowSegmentProducer,
    )
    from cosmos_framework.model.generator.mot.robocasa_exact_window_local_test import _setup
    from cosmos_framework.trainer import matched_no_ttt as module
    from cosmos_framework.trainer.local_memory_grouped_test import _Hooks
    from cosmos_framework.trainer.matched_no_ttt_test import Model

    class NativeBatchToy(Model):
        def training_step(self, batch, iteration):
            self.seen.append(fingerprint(batch))
            value = torch.stack([a[0][1, :15].mean() for a in batch["action_raw"]]).mean()
            noise = random.random() + float(np.random.rand()) + torch.rand(())
            loss = self.net.moe_gen * value * (1 + 0.001 * noise)
            return {"flow_matching_loss_action": loss, "aux_loss_gen": loss * 0.1}, loss

    _, _, catalog, _ = _setup((count,) * 256, t=16)
    original = catalog.wrapped_sft._transform

    def transform(item, resolution):
        result = original(item, resolution)
        result.update(
            video=torch.zeros(3, 17, 2, 4, dtype=torch.uint8),
            text_token_ids=torch.tensor([1, 2, 3]),
            sequence_plan=f"{item['episode_index']}:{item['start_frame']}",
            state=torch.full((17, 15), float(item["episode_index"])),
            state_mask=torch.ones(15),
            action_mask=torch.cat((torch.ones(15), torch.zeros(49))),
            augmentation_trace=torch.tensor(
                [random.random(), float(np.random.rand()), float(torch.rand(()))], dtype=torch.float64
            ),
        )
        return result

    catalog.wrapped_sft._transform = transform
    producer = ExactWindowSegmentProducer(catalog, config_digest=digest)
    planner = ExactWindowRankPlanner(catalog, rank=rank, world_size=4, b_stream=8, active_ga=4, seed=123)
    trainer = object.__new__(module.MatchedNoTTTTrainer)
    trainer.config = SimpleNamespace(trainer=SimpleNamespace(grad_accum_iter=4, distributed_parallelism="fsdp"))
    trainer.callbacks, trainer.training_timer = _Hooks(), lambda _: nullcontext()
    trainer.bind_grouped_stream(planner, producer, config_digest=digest, num_workers=0)
    assert getattr(trainer, "_no_ttt_loader", None) is None
    # Keep the real native collator, CPU batch transfer and production trainer.
    model = NativeBatchToy()
    optimizer = torch.optim.SGD(model.parameters(), lr=1e-5, momentum=0.9)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda step: 1 / (1 + step / 500))
    scaler = torch.amp.GradScaler("cpu", enabled=False)
    events = []

    def observer(*, phase, **values):
        if phase == "native_forward":
            events.append(
                {
                    "iteration": values["iteration"],
                    "member": values["member"],
                    "positions": values["packed_positions"],
                    "consumers": [(p["episode_index"], p["start_frame"]) for p in values["payloads"]],
                    "payloads": fingerprint(values["payloads"]),
                    "loss": fingerprint(values["loss"]),
                }
            )
        elif phase == "pre_optimizer":
            events.append({"pre_optimizer_gradient": fingerprint(model.net.moe_gen.grad)})

    trainer.grouped_observer = observer
    return trainer, model, optimizer, scheduler, scaler, events


def snapshot(state):
    import numpy as np
    import torch

    trainer, model, optimizer, scheduler, scaler, _ = state
    return {
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict(),
        "scaler": scaler.state_dict(),
        "dataloader": trainer.callbacks._callbacks[0].state_dict(),
        "trainer": {
            "iteration": trainer._grouped_completed_iteration,
            "python_rng": random.getstate(),
            "numpy_rng": np.random.get_state(),
            "torch_cpu_rng": torch.get_rng_state(),
            "cuda_rng": None,
        },
    }


def advance(state, iteration):
    trainer, model, optimizer, scheduler, scaler, _ = state
    before = len(model.seen)
    losses = [
        trainer.training_step(model, optimizer, scheduler, scaler, {}, iteration, member)[1] for member in range(4)
    ]
    assert len(model.seen) == before + 4
    assert trainer._grouped_completed_iteration == iteration + 1
    assert model.net.moe_gen.grad is None
    return fingerprint(
        {
            "losses": fingerprint(losses),
            "snapshot": fingerprint(snapshot(state)),
            "events": state[-1][-5:],
            "native_batches": model.seen[-4:],
            "gradient": fingerprint(model.before_zero),
        }
    )


def fixture_run(mode, case, count, damage):
    np, torch, cli, args, config, report = runtime(case, "fresh" if mode == "save_old" else "resume")
    job = cli.job_namespace(args)
    if mode == "save_old":
        from omegaconf import OmegaConf

        class Serializer:
            @staticmethod
            def save_pkl(cfg, path):
                Path(path).write_bytes(pickle.dumps(cfg, protocol=5))

            @staticmethod
            def save_yaml(cfg, path):
                OmegaConf.save(cfg, path)

        lifecycle = cli.JobLifecycle(args, report)
        try:
            lifecycle.write_config(config, Serializer)
        finally:
            lifecycle.close()
        saved = job / "synthetic_cpu_state_iter2"
        saved.mkdir()
    else:
        if damage in ("config", "seed"):
            if damage == "config":
                config.optimizer.lr *= 2
            else:
                config.data_setting.seed += 1
            semantic = cli.training_identity(args, config, report)
            with pytest.raises(ValueError, match="semantic identity"):
                cli.check_job_namespace(args, semantic)
            return {"damage": damage, "rejected_before_native": True, "authority": "production check_job_namespace"}
        cli.check_job_namespace(args, report["training_identity"])
        saved = job / "synthetic_cpu_state_iter2"

    records = []
    for rank in range(4):
        random.seed(123 + rank)
        np.random.seed(123 + rank)
        torch.manual_seed(123 + rank)
        state = make_state(case, count, rank, report["config_digest"])
        if mode == "save_old":
            advance(state, 0)
            advance(state, 1)
            payload = pickle.dumps(snapshot(state), protocol=5)
            (saved / f"rank{rank}.pkl").write_bytes(payload)
            expected = [advance(state, 2), advance(state, 3)]
            (case / f"reference_rank{rank}.json").write_text(json.dumps(expected, sort_keys=True))
            records.append(
                {
                    "rank": rank,
                    "saved_iteration": 2,
                    "reference_iterations": [3, 4],
                    "member_counts": [len(e["consumers"]) for e in expected[0]["events"] if "consumers" in e],
                }
            )
            continue
        loaded = pickle.loads((saved / f"rank{rank}.pkl").read_bytes())
        assert loaded["dataloader"]["format"] == "psm_v3_matched_no_ttt_frontier_v1"
        assert "loader_profile" not in loaded["dataloader"]
        assert loaded["trainer"]["iteration"] == loaded["dataloader"]["iteration"] == 2
        if damage == "rank":
            loaded["dataloader"]["profile"] = ((rank + 1) % 4, *loaded["dataloader"]["profile"][1:])
        elif damage == "frontier":
            frontier = loaded["dataloader"]["frontier"]
            loaded["dataloader"]["frontier"] = dataclasses.replace(
                frontier, slots=(dataclasses.replace(frontier.slots[0], next_segment_id=777), *frontier.slots[1:])
            )
        elif damage == "digest":
            loaded["dataloader"]["config_digest"] = "0" * 64
        elif damage == "iteration":
            loaded["dataloader"]["iteration"] = 3
        trainer, model, optimizer, scheduler, scaler, _ = state
        model.load_state_dict(loaded["model"])
        optimizer.load_state_dict(loaded["optimizer"])
        scheduler.load_state_dict(loaded["scheduler"])
        scaler.load_state_dict(loaded["scaler"])
        trainer.callbacks._callbacks[0].load_state_dict(loaded["dataloader"])
        trainer._resume_required = True
        # Deliberately perturb process RNG before authoritative restoration.
        random.seed(999)
        np.random.seed(999)
        torch.manual_seed(999)
        random.setstate(loaded["trainer"]["python_rng"])
        np.random.set_state(loaded["trainer"]["numpy_rng"])
        torch.set_rng_state(loaded["trainer"]["torch_cpu_rng"])
        if damage != "none":
            with pytest.raises(ValueError, match="No-TTT"):
                advance(state, 2)
            assert model.seen == [] and state[-1] == [] and trainer._no_ttt_failed
            assert trainer._grouped_window.live.frontier == trainer._grouped_planner.initial_frontier()
            records.append({"rank": rank, "damage": damage, "rejected_before_native": True})
            continue
        expected = json.loads((case / f"reference_rank{rank}.json").read_text())
        actual = [advance(state, 2), advance(state, 3)]
        assert actual == expected, f"old uninterrupted vs new workers0 Resume diverged rank{rank}"
        records.append(
            {
                "rank": rank,
                "restored_iteration": 2,
                "matched_iterations": [3, 4],
                "exact_next_payload_loss_gradient_state_rng": True,
                "final_frontier": fingerprint(trainer._grouped_window.live.frontier),
            }
        )
    if mode == "save_old":
        for path in job.rglob("*"):
            if path.is_file():
                path.chmod(0o444)
        (case / "immutable_job_files.json").write_text(json.dumps(file_witness(job), sort_keys=True, indent=2))
    return {
        "records": records,
        "config_digest": report["config_digest"],
        "semantic": report["training_identity"],
        "job": str(job),
        "workers": 0,
    }


def child_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", choices=("save_old", "resume_new"), required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--damage", default="none")
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    import torch
    from cosmos_framework.trainer import matched_no_ttt
    from examples import psm_wma_robocasa_corrected_phase5

    sources = {}
    for module in (matched_no_ttt, psm_wma_robocasa_corrected_phase5):
        path = Path(module.__file__).resolve()
        assert path.is_relative_to(args.source.resolve()), path
        sources[str(path.relative_to(args.source))] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert not torch.cuda.is_initialized()
    with torch.enable_grad():
        result = fixture_run(args.fixture, args.case, args.count, args.damage)
    assert not torch.cuda.is_initialized()
    print(
        "B1_RESULT " + json.dumps({"pid": os.getpid(), "sources": sources, "result": result}, sort_keys=True),
        flush=True,
    )


def extract(repo, sha, destination):
    destination.mkdir(parents=True, exist_ok=True)
    archive = subprocess.check_output(["git", "archive", sha], cwd=repo)
    omitted_links = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        members = []
        for member in tar.getmembers():
            if member.issym() or member.islnk():
                # Never follow historical links into a real dataset or asset.
                if member.name.endswith(".py") or member.name.startswith(("cosmos_framework/", "examples/")):
                    raise ValueError(f"baseline Python source link requires explicit handling: {member.name}")
                omitted_links.append({"path": member.name, "target": member.linkname})
            else:
                members.append(member)
        tar.extractall(destination, members=members, filter="data")
    return omitted_links


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    directory = (
        Path(os.environ["NOTTT_B1_EVIDENCE_ROOT"])
        if "NOTTT_B1_EVIDENCE_ROOT" in os.environ
        else tmp_path_factory.mktemp("no_ttt_b1")
    )
    directory.mkdir(parents=True, exist_ok=True)
    old = directory / "old_exact_tree"
    omitted_root = extract(ROOT, OLD_ROOT, old)
    omitted_child = extract(ROOT / "cosmos-framework", OLD_CHILD, old / "cosmos-framework")
    (directory / "old_tree_sources.json").write_text(
        json.dumps(
            {
                "root_commit": OLD_ROOT,
                "child_commit": OLD_CHILD,
                "omitted_inactive_root_asset_links": omitted_root,
                "omitted_inactive_child_links": omitted_child,
                "root_tree": subprocess.check_output(
                    ["git", "rev-parse", OLD_ROOT + "^{tree}"], cwd=ROOT, text=True
                ).strip(),
                "child_tree": subprocess.check_output(
                    ["git", "rev-parse", OLD_CHILD + "^{tree}"], cwd=ROOT / "cosmos-framework", text=True
                ).strip(),
            },
            indent=2,
        )
    )
    for name, count in (("full", 64), ("terminal", 17)):
        case = directory / name
        case.mkdir()
        run_case(old / "cosmos-framework", case, count, "save_old")
    return directory, old


def run_case(source, case, count, mode, damage="none"):
    env = dict(
        os.environ,
        PYTHONPATH=str(source),
        CUDA_VISIBLE_DEVICES="",
        COSMOS_DEVICE="cpu",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        OMP_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        PYTHONDONTWRITEBYTECODE="1",
    )
    for key in ("RANK", "WORLD_SIZE", "LOCAL_RANK", "LOCAL_WORLD_SIZE", "MASTER_ADDR", "MASTER_PORT"):
        env.pop(key, None)
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--fixture",
        mode,
        "--case",
        str(case),
        "--count",
        str(count),
        "--damage",
        damage,
        "--source",
        str(source),
    ]
    label = f"{mode}_{damage}"
    (case / f"{label}_command.json").write_text(
        json.dumps(
            {
                "cwd": str(source),
                "argv": command,
                "PYTHONPATH": str(source),
                "CUDA_VISIBLE_DEVICES": "",
                "HF_HUB_OFFLINE": "1",
            },
            indent=2,
        )
    )
    result = subprocess.run(
        command, env=env, cwd=source, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180
    )
    (case / f"{label}.log").write_text(result.stdout)
    assert result.returncode == 0, result.stdout[-16000:]
    lines = [line for line in result.stdout.splitlines() if line.startswith("B1_RESULT ")]
    assert len(lines) == 1
    record = json.loads(lines[0][len("B1_RESULT ") :])
    (case / f"{label}_result.json").write_text(json.dumps(record, indent=2, sort_keys=True))
    expected_sha = OLD_CHILD if mode == "save_old" else NEW_CHILD
    for path, digest in record["sources"].items():
        original = subprocess.check_output(["git", "show", expected_sha + ":" + path], cwd=ROOT / "cosmos-framework")
        assert hashlib.sha256(original).hexdigest() == digest
    return record


@pytest.mark.parametrize("scenario,count", [("full", 64), ("terminal", 17)])
def test_exact_old_worker0_checkpoint_new_code_same_job_payload_and_full_state(prepared, scenario, count):
    directory, _ = prepared
    case = directory / scenario
    original = json.loads((case / "immutable_job_files.json").read_text())
    old = json.loads((case / "save_old_none_result.json").read_text())
    result = run_case(ROOT / "cosmos-framework", case, count, "resume_new")
    assert result["pid"] != old["pid"] and result["sources"] != old["sources"]
    assert old["result"]["semantic"] == result["result"]["semantic"]
    assert old["result"]["config_digest"] == result["result"]["config_digest"]
    assert old["result"]["job"] == result["result"]["job"]
    assert [r["rank"] for r in result["result"]["records"]] == [0, 1, 2, 3]
    counts = [row["member_counts"] for row in old["result"]["records"]]
    assert counts == ([[128] * 4] * 4 if count == 64 else [[128, 8, 128, 8]] * 4)
    assert file_witness(Path(result["result"]["job"])) == original


@pytest.mark.parametrize("damage", ["config", "seed", "rank", "frontier", "digest", "iteration"])
def test_changed_identity_or_frontier_rejected_before_native_without_old_file_writes(prepared, damage):
    directory, _ = prepared
    case = directory / "terminal"
    original = json.loads((case / "immutable_job_files.json").read_text())
    old = json.loads((case / "save_old_none_result.json").read_text())
    result = run_case(ROOT / "cosmos-framework", case, 17, "resume_new", damage)
    rows = result["result"].get("records", [result["result"]])
    assert all(row["rejected_before_native"] for row in rows)
    assert file_witness(Path(old["result"]["job"])) == original


if __name__ == "__main__":
    child_main()
