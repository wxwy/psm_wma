"""Server-only, exact-source frozen real-request gate; no Sim or timing claims.

Native serialization preserves tensor devices, strides and aliases. Fresh
payload/prepared data and all four RNG states are restored before every path.
The velocity observer runs outside compiled decoders and must leave final
outputs identical to the preceding ordinary generation. Raw files stay private.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import traceback


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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(root):
    result = {}
    for repo in (root, root / "cosmos-framework"):
        for name in git(repo, "ls-files").splitlines():
            if name.startswith(("docs/", "artifacts/")) or not name.endswith(
                (".py", ".yaml", ".yml", ".toml", ".sh")
            ):
                continue
            path = repo / name
            if path.is_file():
                result[str(path.relative_to(root))] = sha(path)
    return result


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def tensors(value, prefix="root"):
    import torch

    result = {}
    if isinstance(value, torch.Tensor):
        result[prefix] = value.to_local() if hasattr(value, "to_local") else value
    elif dataclasses.is_dataclass(value):
        for field in dataclasses.fields(value):
            result.update(
                tensors(getattr(value, field.name), prefix + "." + field.name)
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            result.update(tensors(item, prefix + "." + str(key)))
    elif isinstance(value, (tuple, list)):
        for index, item in enumerate(value):
            result.update(tensors(item, prefix + "." + str(index)))
    return result


def tensor_hashes(value):
    import torch

    result = {}
    for key, tensor in tensors(value).items():
        cpu = tensor.detach().cpu().contiguous()
        result[key] = dict(
            shape=list(tensor.shape),
            dtype=str(tensor.dtype),
            stride=list(tensor.stride()),
            device=str(tensor.device),
            sha256=hashlib.sha256(
                cpu.reshape(-1).view(torch.uint8).numpy().tobytes()
            ).hexdigest(),
        )
    return result


def compare(left, right):
    import torch

    a, b = tensors(left), tensors(right)
    if set(a) != set(b) or not a:
        raise ValueError("nonempty identical tensor tree required")
    rows = {}
    for key in a:
        x, y = a[key].detach().cpu(), b[key].detach().cpu()
        if x.shape != y.shape or x.dtype != y.dtype:
            raise ValueError("tensor shape/dtype mismatch: " + key)
        rows[key] = dict(
            equal=torch.equal(x, y),
            max_abs=float((x.float() - y.float()).abs().max()) if x.numel() else 0.0,
            shape=list(x.shape),
            dtype=str(x.dtype),
        )
    return dict(all_equal=all(row["equal"] for row in rows.values()), tensors=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "out", "frozen", "independent", "checkpoint", "config-file"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--expected-root", required=True)
    parser.add_argument("--expected-child", required=True)
    parser.add_argument("--gpu-index", type=int, choices=range(4, 8), required=True)
    args = parser.parse_args()
    os.umask(0o077)
    root = args.root.resolve()
    args.out.mkdir(parents=True, exist_ok=False, mode=0o700)
    state = dict(status="RUNNING", independent_approval="NOT_CLAIMED", cases=[])
    initial = identity(root)
    before = fingerprint(root)
    write(args.out / "source_before.json", dict(identity=initial, files=before))
    try:
        assert initial == dict(
            root=args.expected_root,
            child=args.expected_child,
            gitlink=args.expected_child,
            root_status="",
            child_status="",
        ), "exact clean Root/Child/Gitlink required"
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == str(args.gpu_index)
        assert os.environ.get("HF_HUB_OFFLINE") == "1"
        assert os.environ.get("TRANSFORMERS_OFFLINE") == "1"
        assert os.environ.get("LD_LIBRARY_PATH") == ""
        gpu = (
            subprocess.check_output(
                [
                    "nvidia-smi",
                    "--id=" + str(args.gpu_index),
                    "--query-gpu=index,uuid,name,memory.total,memory.used,pci.bus_id",
                    "--format=csv,noheader,nounits",
                ],
                text=True,
            )
            .strip()
            .split(",")
        )
        state["gpu_before"] = [field.strip() for field in gpu]
        occupants = subprocess.check_output(
            [
                "nvidia-smi",
                "--id=" + str(args.gpu_index),
                "--query-compute-apps=pid",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        ).strip()
        if (
            occupants
            or float(gpu[4]) > 1024
            or float(gpu[3]) - float(gpu[4]) < 60 * 1024
        ):
            state["status"] = "BLOCKED_RESOURCE"
            raise RuntimeError(
                "selected GPU occupied or less than 60 GiB free; preserve other processes"
            )
        metadata = args.checkpoint / "model" / ".metadata"
        if not metadata.is_file():
            metadata = args.checkpoint / ".metadata"
        protected = [args.config_file, metadata]
        for k, step in [(1, 32), (16, 64)]:
            capture = args.frozen / f"k{k}" / "capture"
            protected.extend(
                capture / f"{label}_{step:04d}.pt"
                for label in ("request", "prepared", "outputs")
            )
            protected.extend(
                args.independent / f"k{k}" / f"{label}_K{k}_step{step:04d}.pt"
                for label in ("original", "stage1_kv", "stage2_kvpack")
            )
        protected_hashes = {str(path): sha(path) for path in protected}
        write(args.out / "private_input_hashes.json", protected_hashes)
        sys.path[:0] = [
            str(root),
            str(root / "cosmos-framework"),
            str(root / "scripts"),
        ]
        import numpy as np
        import torch
        import cosmos_framework.model.generator.mot.inference_text_kv_memory as cache_module
        from cosmos_framework.inference.common.args import CheckpointOverrides
        from cosmos_framework.inference.robocasa_transaction_mode import (
            validate_model_mode,
        )
        from cosmos_framework.scripts.action_policy_server_robocasa import (
            ActionModelService,
            ActionServerArgs,
        )

        assert (
            Path(cache_module.__file__)
            .resolve()
            .is_relative_to(root / "cosmos-framework")
        )
        assert torch.cuda.is_available() and torch.cuda.device_count() == 1
        uuid = (
            str(torch.cuda.get_device_properties(0).uuid).removeprefix("GPU-").lower()
        )
        assert uuid == gpu[1].strip().removeprefix("GPU-").lower()
        torch.manual_seed(4603)
        service = ActionModelService(
            ActionServerArgs(
                checkpoint=CheckpointOverrides(
                    checkpoint_path=str(args.checkpoint),
                    config_file=str(args.config_file),
                    use_ema_weights=False,
                ),
                output_dir=args.out / "model_load",
                guardrails=False,
                local_memory_mode="required",
                transaction_profile="legacy",
                history_source="server_vae",
                seed=4603,
                guidance=1.0,
                num_steps=30,
                raw_action_dim=15,
                action_chunk_size=16,
            )
        )
        model = service.model
        validate_model_mode(
            model,
            service.experiment_config,
            service.setup_args.checkpoint_path,
            "required",
            use_ema_weights=False,
        )
        assert torch._dynamo.config.recompile_limit == 8
        assert model.config.joint_attn_implementation == "two_way"
        assert service.raw_action_dim == 15 and service.cfg.action_chunk_size == 16
        layers = model.net.language_model.model.layers
        native_dispatch = [layer.self_attn.dispatch_attention_fn for layer in layers]
        assert len(layers) == 28 and all(
            hasattr(layer, "_orig_mod") for layer in layers
        )
        state["model"] = dict(
            torch=torch.__version__,
            cuda=torch.version.cuda,
            validate_model_mode="PASS",
            recompile_limit=8,
            layer_types=[type(layer).__name__ for layer in layers],
            local_memory_mode="required",
        )
        native_prepare, native_velocity = (
            model._prepare_inference_data,
            model._get_velocity,
        )

        def generate(k, step, label, kv, pack, observe):
            capture = args.frozen / f"k{k}" / "capture"
            # Do not map the whole tree to CUDA or CPU: original mixed-device
            # metadata, CUDA tensors, layout and aliases are part of the input.
            request = torch.load(capture / f"request_{step:04d}.pt", weights_only=False)
            prepared = torch.load(
                capture / f"prepared_{step:04d}.pt", weights_only=False
            )["prepared"]
            assert request["source_step"] == step
            assert request["requests"][0]["local_memory"]["local_ttt_history_k"] == k
            assert (
                request["kwargs"]["num_steps"] == 30
                and request["kwargs"]["guidance"] == 1.0
            )
            assert request["requires_state"] == service.requires_state
            memory = (
                request["previous_fast_record"],
                request["candidate_fast_record"],
                request["kwargs"]["_local_memory_prefixes"],
            )
            fixed = tensor_hashes(memory)
            velocities = []

            def prepare(*_pos, **_kw):
                return prepared

            def velocity(*pos, **kw):
                value = native_velocity(*pos, **kw)
                velocities.append([tensor.detach().cpu().clone() for tensor in value])
                return value

            model._prepare_inference_data = prepare
            model._get_velocity = velocity if observe else native_velocity
            try:
                torch.set_rng_state(request["torch_cpu_rng"])
                torch.cuda.set_rng_state(request["torch_cuda_rng"])
                np.random.set_state(request["numpy_rng"])
                random.setstate(request["python_rng"])
                options = dict(
                    request["kwargs"],
                    use_prefix_text_kv_cache=kv,
                    use_prefix_pack_templates=pack,
                )
                with torch.inference_mode():
                    samples = model.generate_samples_from_batch(
                        *request["args"], **options
                    )
                    raw = service._denormalize_action(
                        samples["action"][0].float().squeeze(0)
                    )
                    if service.requires_state:
                        raw = raw[1:]
                output = dict(samples=samples, raw15_action=raw)
                assert all(torch.isfinite(t).all() for t in tensors(output).values())
                assert tensor_hashes(memory) == fixed, "FastState/Prefix input mutated"
                assert all(
                    layer.self_attn.dispatch_attention_fn is fn
                    for layer, fn in zip(layers, native_dispatch, strict=True)
                )
                if observe:
                    assert len(velocities) == 30
                path = args.out / f"k{k}" / (label + ("_velocity" if observe else ""))
                path.mkdir(parents=True, exist_ok=False)
                torch.save(output, path / "outputs.pt")
                if observe:
                    torch.save(velocities, path / "velocities.pt")
                write(path / "output_hashes.json", tensor_hashes(output))
                write(path / "fixed_memory_hashes.json", fixed)
                return output, velocities
            finally:
                model._prepare_inference_data, model._get_velocity = (
                    native_prepare,
                    native_velocity,
                )

        for k, step in [(1, 32), (16, 64)]:
            case = dict(k=k, source_step=step, ordinary={}, observed={}, velocity={})
            state["cases"].append(case)
            outputs, modes = (
                {},
                [
                    ("original", False, False),
                    ("stage1", True, False),
                    ("stage2", True, True),
                ],
            )
            for label, kv, pack in modes:
                output, _ = generate(k, step, label, kv, pack, False)
                outputs[label] = output
                original = torch.load(
                    args.independent / f"k{k}" / f"original_K{k}_step{step:04d}.pt",
                    map_location="cpu",
                    weights_only=False,
                )
                case["ordinary"][label] = compare(original, output)
                write(
                    args.out / f"k{k}" / f"{label}_ordinary_comparison.json",
                    case["ordinary"][label],
                )
                assert case["ordinary"][label]["all_equal"], (
                    f"K{k}/{label} differs from independent original"
                )
            velocity_outputs = {}
            for label, kv, pack in modes:
                output, velocities = generate(k, step, label, kv, pack, True)
                case["observed"][label] = compare(outputs[label], output)
                assert case["observed"][label]["all_equal"], (
                    "velocity observer perturbed generation"
                )
                velocity_outputs[label] = velocities
            for label in ("stage1", "stage2"):
                case["velocity"][label] = [
                    compare(a, b)
                    for a, b in zip(
                        velocity_outputs["original"],
                        velocity_outputs[label],
                        strict=True,
                    )
                ]
                assert all(row["all_equal"] for row in case["velocity"][label]), (
                    f"K{k}/{label} denoising velocity differs"
                )
            case["stage1_vs_stage2"] = compare(outputs["stage1"], outputs["stage2"])
            assert case["stage1_vs_stage2"]["all_equal"]
            print(
                json.dumps(dict(k=k, status="EXACT_PARITY_PASS", denoise_steps=30)),
                flush=True,
            )
        assert torch._dynamo.config.recompile_limit == 8
        assert protected_hashes == {str(path): sha(path) for path in protected}
        state.update(
            status="PASS",
            protected_inputs_unchanged=True,
            strict_tolerance=0,
            performance_claim="NONE",
        )
    except BaseException as error:
        if state["status"] != "BLOCKED_RESOURCE":
            state["status"] = "FAIL"
        state["error"] = repr(error)
        with (args.out / "traceback.txt").open("x") as stream:
            traceback.print_exc(file=stream)
    finally:
        after_identity, after = identity(root), fingerprint(root)
        write(
            args.out / "source_after.json", dict(identity=after_identity, files=after)
        )
        state["source_unchanged"] = initial == after_identity and before == after
        if not state["source_unchanged"]:
            state["status"] = "FAIL"
        write(args.out / "gate.json", state)
        print(
            json.dumps(
                dict(
                    status=state["status"],
                    source_unchanged=state["source_unchanged"],
                    error=state.get("error"),
                )
            ),
            flush=True,
        )
    return 0 if state["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
