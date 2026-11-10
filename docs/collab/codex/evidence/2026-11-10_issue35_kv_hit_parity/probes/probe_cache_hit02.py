"""Server-only real-request probe. Reuse independent replay, never edit sources.

The original-label run intentionally becomes a diagnostic full-compute capture:
enable native cache FILL on every layer/step, never take GEN-only or read a cache.
Its final output MUST still equal the independent cache-OFF output or this probe
is inconclusive. The other two modes remain normal Stage1/Stage2.
"""

from __future__ import annotations

import argparse
import dataclasses
import functools
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import torch


def tensors(value, prefix="root"):
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


def tensor_info(value):
    cpu = value.detach().cpu().contiguous()
    raw = cpu.reshape(-1).view(torch.uint8).numpy().tobytes()
    return dict(
        shape=list(value.shape),
        dtype=str(value.dtype),
        stride=list(value.stride()),
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def compare(left, right):
    a, b = tensors(left), tensors(right)
    if set(a) != set(b):
        raise RuntimeError("tensor tree schema changed")
    errors = {}
    for key in a:
        x, y = a[key].detach().cpu(), b[key].detach().cpu()
        if x.shape != y.shape or x.dtype != y.dtype:
            raise RuntimeError("tensor shape or dtype changed: " + key)
        error = float((x.float() - y.float()).abs().max()) if x.numel() else 0.0
        errors[key] = dict(equal=torch.equal(x, y), max_abs=error, shape=list(x.shape))
    return dict(all_equal=all(row["equal"] for row in errors.values()), tensors=errors)


def save(path, value):
    with path.open("xb") as stream:
        os.chmod(path, 0o600)
        torch.save(value, stream)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--k", type=int, required=True)
    parser.add_argument("--step", type=int, required=True)
    args, _ = parser.parse_known_args()
    root = args.root.resolve()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(root), str(root / "cosmos-framework"), str(root / "scripts")]
    private = Path(
        "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue35_real_input_3way_replay_20261110"
    )
    spec = importlib.util.spec_from_file_location(
        "independent_replay", private / "replay_real.py"
    )
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)

    from cosmos_framework.scripts.action_policy_server_robocasa import (
        ActionModelService,
    )
    from cosmos_framework.model.generator.mot.inference_text_kv_memory import (
        InferenceTextKVMemoryState,
    )
    from cosmos_framework.data.generator.sequence_packing.runtime import get_gen_seq

    current = dict(mode=None, step=-1, velocity_calls=0)
    records = []
    native_is_gen_only = InferenceTextKVMemoryState.is_gen_only
    native_read = InferenceTextKVMemoryState.read_for_layer
    native_write = InferenceTextKVMemoryState.write_for_layer
    native_init = ActionModelService.__init__
    directory = args.out / "first_hit_probe"

    def is_gen_only(memory):
        return (
            False
            if current["mode"] == "full_compute_capture"
            else native_is_gen_only(memory)
        )

    def path(kind, layer):
        return (
            directory
            / f"{current['mode']}_s{current['step']:02d}_l{layer:02d}_{kind}.pt"
        )

    def read(memory, layer):
        value = native_read(memory, layer)
        if current["mode"] == "full_compute_capture":
            value = dataclasses.replace(
                value, frame_idx=0, und_k_cached=None, und_v_cached=None
            )
        if current["step"] in (0, 1) and value.und_k_cached is not None:
            save(path("read_und", layer), (value.und_k_cached, value.und_v_cached))
        return value

    def write(memory, layer, values):
        if current["step"] in (0, 1):
            save(path("write_und", layer), values[2:])
        return native_write(memory, layer, values)

    @functools.wraps(native_init)
    def initialized(service, *positional, **keywords):
        native_init(service, *positional, **keywords)
        directory.mkdir(exist_ok=False, mode=0o700)
        model = service.model
        layers = model.net.language_model.model.layers
        assert len(layers) == 28
        assert torch._dynamo.config.recompile_limit == 8
        metadata = dict(
            layers=len(layers),
            layer_types=[type(layer).__name__ for layer in layers],
            layer_has_orig_mod=[hasattr(layer, "_orig_mod") for layer in layers],
            config_compile_enabled=service.experiment_config.get("compile", {}).get(
                "enabled"
            ),
            recompile_limit=torch._dynamo.config.recompile_limit,
            original_label_actual_mode="full_compute_capture; forced native FILL every step, no cache reads",
        )
        (directory / "loaded.json").write_text(json.dumps(metadata, indent=2) + "\n")
        original_generate = model.generate_samples_from_batch
        original_velocity = model._get_velocity

        @functools.wraps(original_generate)
        def generate(*pos, **kw):
            kv = kw.get("use_prefix_text_kv_cache", True)
            pack = kw.get("use_prefix_pack_templates", True)
            mode = (
                "full_compute_capture" if not kv else ("stage2" if pack else "stage1")
            )
            current.update(mode=mode, step=-1, velocity_calls=0)
            if not kv:
                kw["use_prefix_text_kv_cache"] = True
                kw["use_prefix_pack_templates"] = False
            try:
                return original_generate(*pos, **kw)
            finally:
                current["mode"] = None

        @functools.wraps(original_velocity)
        def velocity(*pos, **kw):
            current["step"] = current["velocity_calls"]
            current["velocity_calls"] += 1
            return original_velocity(*pos, **kw)

        def wrapper(original, index):
            @functools.wraps(original)
            def forward(*pos, **kw):
                watched = current["step"] in (0, 1)
                row = None
                if watched:
                    row = dict(
                        mode=current["mode"],
                        step=current["step"],
                        layer=index,
                        gen_only=kw.get("gen_only", False),
                        gen_input=tensor_info(get_gen_seq(pos[0])),
                    )
                    if current["step"] == 1:
                        save(path("layer_input", index), dict(args=pos, kwargs=kw))
                output = original(*pos, **kw)
                if watched:
                    row["gen_output"] = tensor_info(get_gen_seq(output[0]))
                    records.append(row)
                return output

            return forward

        for i, layer in enumerate(layers):
            layer.forward = wrapper(layer.forward, i)
        model.generate_samples_from_batch = generate
        model._get_velocity = velocity

    InferenceTextKVMemoryState.is_gen_only = is_gen_only
    InferenceTextKVMemoryState.read_for_layer = read
    InferenceTextKVMemoryState.write_for_layer = write
    ActionModelService.__init__ = initialized
    try:
        replay.run()
    finally:
        ActionModelService.__init__ = native_init
        InferenceTextKVMemoryState.is_gen_only = native_is_gen_only
        InferenceTextKVMemoryState.read_for_layer = native_read
        InferenceTextKVMemoryState.write_for_layer = native_write

    (directory / "layer_hashes.json").write_text(json.dumps(records, indent=2) + "\n")
    native_match = {}
    for label in ("original", "stage1_kv", "stage2_kvpack"):
        name = f"{label}_K{args.k}_step{args.step:04d}.pt"
        native_match[label] = compare(
            torch.load(
                private / f"k{args.k}" / name, map_location="cpu", weights_only=False
            ),
            torch.load(args.out / name, map_location="cpu", weights_only=False),
        )
    caches = []
    for layer in range(28):

        def load(name):
            return torch.load(directory / name, map_location="cpu", weights_only=False)

        native0 = load(f"full_compute_capture_s00_l{layer:02d}_write_und.pt")
        native1 = load(f"full_compute_capture_s01_l{layer:02d}_write_und.pt")
        cached = load(f"stage1_s01_l{layer:02d}_read_und.pt")
        caches.append(
            dict(
                layer=layer,
                full_step0_vs_full_step1=compare(native0, native1),
                full_step1_vs_cached_read=compare(native1, cached),
            )
        )
    reference = {
        (r["step"], r["layer"]): r
        for r in records
        if r["mode"] == "full_compute_capture"
    }
    layer_diffs = []
    for row in records:
        if row["mode"] != "stage1":
            continue
        ref = reference[row["step"], row["layer"]]
        layer_diffs.append(
            dict(
                step=row["step"],
                layer=row["layer"],
                gen_input_equal=ref["gen_input"]["sha256"]
                == row["gen_input"]["sha256"],
                gen_output_equal=ref["gen_output"]["sha256"]
                == row["gen_output"]["sha256"],
            )
        )
    nonperturbing = all(row["all_equal"] for row in native_match.values())
    result = dict(
        status="DIAGNOSTIC_COMPLETE"
        if nonperturbing
        else "INCONCLUSIVE_PROBE_CHANGED_OUTPUT",
        k=args.k,
        step=args.step,
        final_outputs_match_independent=native_match,
        native_und_cache_comparisons=caches,
        layer_differences=layer_diffs,
        timing_not_for_performance=True,
        production_source_changed=False,
    )
    (directory / "probe_result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                status=result["status"],
                k=args.k,
                nonperturbing=nonperturbing,
                first_layer_difference=next(
                    (r for r in layer_diffs if not r["gen_output_equal"]), None
                ),
                all_native_und_static=all(
                    r["full_step0_vs_full_step1"]["all_equal"] for r in caches
                ),
                all_cache_reads_equal_native=all(
                    r["full_step1_vs_cached_read"]["all_equal"] for r in caches
                ),
            )
        )
    )
    if not nonperturbing:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
