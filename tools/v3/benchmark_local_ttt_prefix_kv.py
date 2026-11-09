#!/usr/bin/env python3
"""Issue31: same-Local-DCP, Prefix-ON B1 text-KV correctness/performance probe.

Model-only author evidence. No HTTP server, Sim, Worker, training, SR or model
mode override. Uses a deterministic synthetic composite observation and real
loaded Local-TTT parameters to construct a fixed Prefix/FastState. All raw
artifacts stay in the selected device's new output directory.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def identity(root):
    child = root / "cosmos-framework"
    return dict(
        root=git(root, "rev-parse", "HEAD"),
        child=git(child, "rev-parse", "HEAD"),
        gitlink=git(root, "rev-parse", "HEAD:cosmos-framework"),
        root_status=git(root, "status", "--porcelain"),
        child_status=git(child, "status", "--porcelain"),
    )


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def digest(tensor):
    value = tensor.detach().cpu().contiguous()
    return hashlib.sha256(value.view(dtype=__import__("torch").uint8).numpy().tobytes()).hexdigest()


def gpu_info(index):
    fields = "index,uuid,name,memory.total,memory.used,utilization.gpu,pci.bus_id"
    return subprocess.check_output(
        ["nvidia-smi", "-i", str(index), "--query-gpu=" + fields, "--format=csv,noheader,nounits"],
        text=True,
    ).strip()


def percentile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p
    lo = int(position)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def summary(rows):
    return {
        name: dict(
            mean=statistics.mean(values := [row[name] for row in rows]),
            p50=percentile(values, 0.5),
            p95=percentile(values, 0.95),
            n=len(values),
        )
        for name in (
            "native_generate_gpu_ms",
            "native_generate_wall_ms",
            "current_vae_gpu_ms",
            "peak_allocated_bytes",
            "peak_reserved_bytes",
        )
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root-worktree", type=Path, required=True)
    p.add_argument("--expected-root", required=True)
    p.add_argument("--expected-child", required=True)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--config-file", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--gpu-index", type=int, choices=range(4, 8), required=True)
    p.add_argument("--seed", type=int, default=31)
    p.add_argument("--warmup-pairs", type=int, default=3)
    p.add_argument("--pairs", type=int, default=30)
    p.add_argument("--profile-one", action="store_true")
    a = p.parse_args()
    if a.pairs < 20 or a.warmup_pairs < 2:
        p.error("at least 20 interleaved measurement pairs and 2 warmup pairs required")
    root = a.root_worktree.resolve()
    before = identity(root)
    if (
        before["root"] != a.expected_root
        or before["child"] != a.expected_child
        or before["gitlink"] != a.expected_child
        or before["root_status"]
        or before["child_status"]
    ):
        raise RuntimeError("exact clean Root/Child/Gitlink required before model loading")
    if not a.config_file.is_file() or not a.checkpoint.is_dir():
        raise RuntimeError("local checkpoint/config missing; no network fallback")
    a.output_dir.mkdir(parents=True, exist_ok=False)
    write_json(a.output_dir / "source_before.json", before)
    sys.path[:0] = [str(root), str(root / "cosmos-framework"), str(root / "scripts")]
    result = dict(
        status="RUNNING",
        identity=before,
        independent_approval="NOT_CLAIMED",
        checkpoint=str(a.checkpoint.resolve()),
        checkpoint_config_sha256=hashlib.sha256(a.config_file.read_bytes()).hexdigest(),
        input_kind="deterministic synthetic composite and executed history; real Local DCP",
        gpu_before=gpu_info(a.gpu_index),
        seed=a.seed,
        guidance=1.0,
        num_steps=30,
        local_memory_mode="required",
        history_updates_outside_generation_timing=True,
        pack_template_reuse_with_prefix=False,
        validation_scope="B1 single GPU two_way only",
    )
    handles = []
    vae_original = None
    service = None
    try:
        gpu_fields = result["gpu_before"].split(",")
        if float(gpu_fields[3]) - float(gpu_fields[4]) < 24 * 1024:
            raise RuntimeError("less than 24 GiB free on selected GPU; preserve other processes")
        metadata = a.checkpoint / "model" if (a.checkpoint / "model").is_dir() else a.checkpoint
        result["checkpoint_metadata_sha256"] = hashlib.sha256((metadata / ".metadata").read_bytes()).hexdigest()
        import numpy as np
        import torch
        from cosmos_framework.inference.common.args import CheckpointOverrides
        from cosmos_framework.inference.robocasa_transaction_mode import validate_model_mode
        from cosmos_framework.scripts.action_policy_server_robocasa import ActionModelService, ActionServerArgs
        from PIL import Image

        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise RuntimeError("exactly one visible CUDA device required")
        expected_uuid = result["gpu_before"].split(",")[1].strip().removeprefix("GPU-").lower()
        actual_uuid = str(torch.cuda.get_device_properties(0).uuid).removeprefix("GPU-").lower()
        if expected_uuid != actual_uuid:
            raise RuntimeError("visible CUDA device does not match authorized physical GPU")
        result["torch"] = torch.__version__
        result["cuda"] = torch.version.cuda
        torch.manual_seed(a.seed)
        args = ActionServerArgs(
            checkpoint=CheckpointOverrides(
                checkpoint_path=str(a.checkpoint.resolve()),
                config_file=str(a.config_file.resolve()),
                use_ema_weights=False,
            ),
            output_dir=a.output_dir / "model_load",
            guardrails=False,
            local_memory_mode="required",
            transaction_profile="legacy",
            history_source="server_vae",
            seed=a.seed,
            guidance=1.0,
            num_steps=30,
            raw_action_dim=15,
            action_chunk_size=16,
        )
        service = ActionModelService(args)
        model = service.model
        validate_model_mode(
            model, service.experiment_config, service.setup_args.checkpoint_path, "required", use_ema_weights=False
        )
        result["validate_model_mode_and_dcp_inventory"] = "PASS"
        if (
            model.config.joint_attn_implementation != "two_way"
            or model.config.video_temporal_causal
            or service.cfg.action_chunk_size != 16
            or service.raw_action_dim != 15
        ):
            raise RuntimeError("frozen B1/two_way/raw15/H16 benchmark contract differs")
        if service.experiment_config.get("compile", {}).get("enabled", False):
            raise RuntimeError("this Gate requires the frozen compile.enabled=false configuration")

        # No server observation file is read/exported. Only generated local probe input.
        rng = np.random.default_rng(a.seed)
        image = rng.integers(0, 256, size=(256, 512, 3), dtype=np.uint8)
        png = io.BytesIO()
        Image.fromarray(image).save(png, format="PNG")
        request = dict(
            image=base64.b64encode(png.getvalue()).decode(),
            image_size=256,
            prompt="Close the fridge.",
            domain_name="robocasa",
            state=[0.2, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.5],
        )
        prep = service._prep_policy_item(request)
        runtime = model.net.local_memory_runtime
        device = runtime.core.slot_queries.device
        visual = torch.randn(1, 16, 96, device=device)
        action_history = torch.randn(1, 16, 15, device=device) * 0.1
        # Use the registered model-owned entry point so FSDP materializes the
        # loaded slow weights exactly as it does in the production adapter.
        tokens, fast_state, _ = model.net.scan_local_memory(
            visual,
            action_history,
            torch.ones(1, 16, dtype=torch.bool, device=device),
            create_graph=False,
        )
        prefix = tokens[0, -1].detach().clone()
        fixed_fast_hashes = [digest(t) for t in fast_state]
        result["fixed_inputs"] = dict(
            rgb_sha256=hashlib.sha256(png.getvalue()).hexdigest(),
            prepared_video_sha256=digest(prep["video_padded"]),
            visual96_sha256=digest(visual),
            executed_actions_sha256=digest(action_history),
            prefix_sha256=digest(prefix),
            prefix_shape=list(prefix.shape),
            fast_state_sha256=fixed_fast_hashes,
        )
        layers = model.net.language_model.model.layers
        original_dispatch = [layer.self_attn.dispatch_attention_fn for layer in layers]
        audit = None

        def layer_hook(i):
            def hook(module, positional, kwargs):
                if audit is not None:
                    row = audit[i]
                    row["forwards"] += 1
                    row["gen_only"] += int(kwargs.get("gen_only", False))
                    row["prefix_context"] += int(kwargs.get("memory_prefix_context") is not None)

            return hook

        def prefix_hook(i):
            def hook(module, positional):
                if audit is not None and positional[0].shape[0] == prefix.shape[0]:
                    audit[i]["prefix_kv_projection"] += 1

            return hook

        for i, layer in enumerate(layers):
            handles.extend(
                (
                    layer.register_forward_pre_hook(layer_hook(i), with_kwargs=True),
                    layer.self_attn.k_proj_moe_gen.register_forward_pre_hook(prefix_hook(i)),
                )
            )
        vae_events = []
        vae_original = model.tokenizer_vision_gen.encode

        def timed_vae(*args, **kwargs):
            start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            start.record()
            encoded = vae_original(*args, **kwargs)
            end.record()
            vae_events.append((start, end))
            return encoded

        model.tokenizer_vision_gen.encode = timed_vae

        def run(mode, tag, current_prefix=prefix, with_audit=False):
            nonlocal audit
            audit = (
                [dict(forwards=0, gen_only=0, prefix_context=0, prefix_kv_projection=0) for _ in layers]
                if with_audit
                else None
            )
            batch = service._single_policy_batch(prep)
            vae_events.clear()
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
            start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            wall = time.perf_counter()
            start.record()
            with torch.inference_mode():
                samples = model.generate_samples_from_batch(
                    batch,
                    guidance=1.0,
                    num_steps=30,
                    seed=[a.seed],
                    has_negative_prompt=False,
                    _local_memory_prefixes=(current_prefix,),
                    use_prefix_text_kv_cache=mode == "optimized",
                )
            end.record()
            torch.cuda.synchronize()
            row = dict(
                tag=tag,
                mode=mode,
                native_generate_gpu_ms=start.elapsed_time(end),
                native_generate_wall_ms=(time.perf_counter() - wall) * 1000,
                current_vae_gpu_ms=sum(x.elapsed_time(y) for x, y in vae_events),
                peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            )
            assert all(
                layer.self_attn.dispatch_attention_fn is old
                for layer, old in zip(layers, original_dispatch, strict=True)
            )
            if audit is not None:
                row["layers"] = audit
            for key, values in samples.items():
                assert all(torch.isfinite(t).all() for t in values), key
            cpu = {key: [t.detach().float().cpu() for t in values] for key, values in samples.items()}
            row["output_sha256"] = {key: [digest(t) for t in values] for key, values in cpu.items()}
            # The real generation returns raw15 and includes the conditioning state row.
            assert cpu["action"][0].shape[-1] == 15
            return row, cpu

        def compare(left, right):
            errors = {}
            for key in left:
                assert len(left[key]) == len(right[key])
                errors[key] = []
                for x, y in zip(left[key], right[key], strict=True):
                    errors[key].append(dict(max_abs=float((x - y).abs().max()), mean_abs=float((x - y).abs().mean())))
                    torch.testing.assert_close(x, y, rtol=1e-4, atol=1e-5)
            return errors

        # Interleaved warmup, then audit correctness on already-warm kernels.
        warmup = []
        for i in range(a.warmup_pairs):
            for mode in ("baseline", "optimized") if i % 2 == 0 else ("optimized", "baseline"):
                row, _ = run(mode, f"warmup-{i}")
                warmup.append(row)
        write_json(a.output_dir / "warmup.json", warmup)
        base_audit, baseline = run("baseline", "audit-baseline", with_audit=True)
        opt_audit, optimized = run("optimized", "audit-optimized", with_audit=True)
        result["audit_output_errors"] = compare(baseline, optimized)
        for row in base_audit["layers"]:
            assert row == dict(forwards=30, gen_only=0, prefix_context=30, prefix_kv_projection=30)
        for row in opt_audit["layers"]:
            assert row == dict(forwards=30, gen_only=29, prefix_context=30, prefix_kv_projection=30)
        changed_row, changed = run("optimized", "different-prefix", prefix + 0.5, with_audit=True)
        assert not torch.equal(optimized["action"][0], changed["action"][0]), "Prefix must affect real actions"
        retry_row, retry = run("optimized", "original-request-again", with_audit=True)
        result["repeat_request_errors"] = compare(optimized, retry)
        for row in retry_row["layers"]:
            assert row["gen_only"] == 29, "each request must refill its own text cache"
        write_json(
            a.output_dir / "audit.json",
            dict(baseline=base_audit, optimized=opt_audit, changed_prefix=changed_row, repeated_original=retry_row),
        )
        records = []
        for i in range(a.pairs):
            for mode in ("baseline", "optimized") if i % 2 == 0 else ("optimized", "baseline"):
                row, actual = run(mode, f"pair-{i}")
                row["errors_from_baseline"] = compare(baseline, actual)
                records.append(row)
                with (a.output_dir / "measurements.jsonl").open("a") as stream:
                    stream.write(json.dumps(row, allow_nan=False) + "\n")
            print(json.dumps(dict(pair=i + 1, pairs=a.pairs, last_two=records[-2:])), flush=True)
        result["measurements"] = {
            mode: summary([r for r in records if r["mode"] == mode]) for mode in ("baseline", "optimized")
        }
        if a.profile_one:
            kernels = {}
            for mode in ("baseline", "optimized"):
                with torch.profiler.profile(
                    activities=[torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA]
                ) as prof:
                    run(mode, f"profile-{mode}")
                prof.export_chrome_trace(str(a.output_dir / f"profile_{mode}.json"))
                kernels[mode] = {}
                for event in prof.events():
                    if event.device_type == torch.autograd.DeviceType.CUDA:
                        kernels[mode][event.name] = kernels[mode].get(event.name, 0) + 1
            write_json(a.output_dir / "kernel_counts.json", kernels)
        assert [digest(t) for t in fast_state] == fixed_fast_hashes
        assert digest(prefix) == result["fixed_inputs"]["prefix_sha256"]
        assert hashlib.sha256((metadata / ".metadata").read_bytes()).hexdigest() == result["checkpoint_metadata_sha256"]
        after = identity(root)
        write_json(a.output_dir / "source_after.json", after)
        assert after == before
        result["source_unchanged"] = True
        result["correctness"] = "PASS"
        base = result["measurements"]["baseline"]["native_generate_gpu_ms"]["p50"]
        opt = result["measurements"]["optimized"]["native_generate_gpu_ms"]["p50"]
        result["speedup_p50"] = base / opt
        result["performance"] = "PASS" if base / opt >= 1.05 else "NOT_MET"
        result["status"] = "PASS" if result["performance"] == "PASS" else "CORRECTNESS_PASS_PERFORMANCE_NOT_MET"
    except Exception as error:
        import traceback

        with (a.output_dir / "failure_traceback.txt").open("x") as stream:
            traceback.print_exc(file=stream)
        result.update(status="FAIL", error=repr(error))
        raise
    finally:
        for handle in handles:
            handle.remove()
        if vae_original is not None:
            service.model.tokenizer_vision_gen.encode = vae_original
        result["gpu_after"] = gpu_info(a.gpu_index)
        write_json(a.output_dir / "result.json", result)
        if "torch" in sys.modules:
            torch = sys.modules["torch"]
            if torch.distributed.is_initialized():
                torch.distributed.destroy_process_group()
    print(json.dumps(result, indent=2), flush=True)
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
