"""Observe already-materialized GEN Flash operands on isolated real layers.

Every isolated layer output is bound to the earlier unmodified whole-generation
hash. Exporting an operand is evidence only if that output remains bit-exact.
Raw FX graphs and tensors stay on the authorized server.
"""

from __future__ import annotations

import argparse
import functools
import importlib.util
import json
import operator
from pathlib import Path
import sys

import torch

from probe_cache_hit import compare, save, tensor_info


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--k", type=int, required=True)
    parser.add_argument("--step", type=int, required=True)
    args, _ = parser.parse_known_args()
    args.out.mkdir(parents=True, exist_ok=False)
    root = args.root.resolve()
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
        install_inference_memory_attention_dispatch,
        restore_inference_attention_dispatch,
    )
    from cosmos_framework.data.generator.sequence_packing.runtime import get_gen_seq
    import torch._inductor.compile_fx as compiler

    native_init = ActionModelService.__init__
    native_compile = compiler.compile_fx
    context = dict(active=None, graphs=0)
    directory = args.out / "operand_probe"
    checks = []

    def capture_compile(graph, example_inputs, *pos, **kw):
        if context["active"] is None:
            return native_compile(graph, example_inputs, *pos, **kw)
        number = context["graphs"]
        context["graphs"] += 1
        (directory / f"graph_{number:02d}_before.py").write_text(graph.code)
        flashes = [
            n
            for n in graph.graph.nodes
            if n.op == "call_function"
            and "flash_attn" in str(n.target)
            and (
                "varlen_func" in str(n.target) or "_flash_attn_forward" in str(n.target)
            )
        ]
        if not flashes:
            return native_compile(graph, example_inputs, *pos, **kw)
        selected = flashes[-1]
        assert selected.kwargs.get("causal", False) is False, (
            "last call must be GEN, not UND"
        )
        extras = []
        labels = []
        for index, label in enumerate(["q", "k", "v"]):
            n = (
                selected.args[index]
                if len(selected.args) > index
                else selected.kwargs[label]
            )
            assert isinstance(n, torch.fx.Node)
            extras.append(n)
            labels.append(label)
        outputs = [
            n
            for n in selected.users
            if n.op == "call_function"
            and n.target is operator.getitem
            and n.args[1] == 0
        ]
        if outputs:
            extras.append(outputs[0])
            labels.append("out")
        else:
            value = selected.meta.get("example_value", selected.meta.get("val"))
            assert isinstance(value, torch.Tensor), (
                "Flash output schema not a Tensor or tuple getitem0"
            )
            extras.append(selected)
            labels.append("out")
        output = next(n for n in graph.graph.nodes if n.op == "output")
        original_outputs = output.args[0]
        assert isinstance(original_outputs, (tuple, list))
        count = len(original_outputs)
        output.args = (type(original_outputs)(list(original_outputs) + extras),)
        graph.graph.lint()
        graph.recompile()
        (directory / f"graph_{number:02d}_augmented.py").write_text(graph.code)
        schema = dict(
            graph=number,
            flash_calls=len(flashes),
            selected_last_gen_call=True,
            labels=labels,
            original_outputs=count,
            targets=[str(n.target) for n in flashes],
        )
        (directory / f"graph_{number:02d}_schema.json").write_text(
            json.dumps(schema, indent=2) + "\n"
        )
        compiled = native_compile(graph, example_inputs, *pos, **kw)

        @functools.wraps(compiled)
        def observed(*a, **k):
            result = compiled(*a, **k)
            if context["active"] is not None:
                save(
                    directory / (context["active"] + "_attention.pt"),
                    dict(zip(labels, result[count:], strict=True)),
                )
                (directory / (context["active"] + "_graph.json")).write_text(
                    json.dumps(schema, indent=2) + "\n"
                )
            return result[:count]

        return observed

    @functools.wraps(native_init)
    def initialized(service, *p, **kw):
        native_init(service, *p, **kw)
        directory.mkdir(exist_ok=False, mode=0o700)
        model = service.model
        native_generate = model.generate_samples_from_batch
        done = False

        @functools.wraps(native_generate)
        def generate(*a, **k):
            nonlocal done
            result = native_generate(*a, **k)
            if done:
                return result
            done = True
            previous = install_inference_memory_attention_dispatch(model.net)
            compiler.compile_fx = capture_compile
            try:
                for history, layer in [(1, 18), (16, 16)]:
                    source = (
                        args.out.parent.parent / f"probe03/k{history}/first_hit_probe"
                    )
                    rows = json.loads((source / "layer_hashes.json").read_text())
                    for label, mode in [
                        ("full", "full_compute_capture"),
                        ("hit", "stage1"),
                    ]:
                        value = torch.load(
                            source / f"{mode}_s01_l{layer:02d}_layer_input.pt",
                            weights_only=False,
                        )
                        tag = f"K{history}_{label}"
                        context["active"] = tag
                        actual = model.net.language_model.model.layers[layer](
                            *value["args"], **value["kwargs"]
                        )
                        context["active"] = None
                        expected = next(
                            row
                            for row in rows
                            if row["mode"] == mode
                            and row["step"] == 1
                            and row["layer"] == layer
                        )
                        meta = tensor_info(get_gen_seq(actual[0]))
                        equal = meta["sha256"] == expected["gen_output"]["sha256"]
                        checks.append(
                            dict(
                                k=history,
                                layer=layer,
                                mode=mode,
                                output_matches_whole_generation=equal,
                                output=meta,
                                attention_recorded=(
                                    directory / (tag + "_attention.pt")
                                ).exists(),
                                autocast_enabled=torch.is_autocast_enabled("cuda"),
                            )
                        )
                        save(
                            directory / (tag + "_layer_output.pt"),
                            get_gen_seq(actual[0]),
                        )
            finally:
                context["active"] = None
                compiler.compile_fx = native_compile
                restore_inference_attention_dispatch(previous)
            return result

        model.generate_samples_from_batch = generate

    ActionModelService.__init__ = initialized
    try:
        replay.run()
    finally:
        ActionModelService.__init__ = native_init
        compiler.compile_fx = native_compile
    comparisons = {}
    for history in (1, 16):
        p1 = directory / f"K{history}_full_attention.pt"
        p2 = directory / f"K{history}_hit_attention.pt"
        if p1.exists() and p2.exists():
            comparisons[str(history)] = compare(
                torch.load(p1, map_location="cpu", weights_only=False),
                torch.load(p2, map_location="cpu", weights_only=False),
            )
    final_matches = {}
    for label in ("original", "stage1_kv", "stage2_kvpack"):
        name = f"{label}_K{args.k}_step{args.step:04d}.pt"
        final_matches[label] = compare(
            torch.load(
                private / f"k{args.k}" / name, map_location="cpu", weights_only=False
            ),
            torch.load(args.out / name, map_location="cpu", weights_only=False),
        )
    nonperturbing = (
        len(checks) == 4
        and all(row["output_matches_whole_generation"] for row in checks)
        and all(row["all_equal"] for row in final_matches.values())
    )
    captured = len(comparisons) == 2 and all(
        row["attention_recorded"] for row in checks
    )
    outcome = dict(
        status="OPERAND_DIAGNOSTIC_COMPLETE"
        if nonperturbing and captured
        else (
            "INCONCLUSIVE_FX_TAP_NOT_RECORDED"
            if nonperturbing
            else "INCONCLUSIVE_INSTRUMENTATION_CHANGED_LAYER"
        ),
        nonperturbing=nonperturbing,
        layer_checks=checks,
        attention_comparisons=comparisons,
        final_outputs_match_independent=final_matches,
        graph_count=context["graphs"],
        performance_claim=False,
    )
    (directory / "result.json").write_text(json.dumps(outcome, indent=2) + "\n")
    print(json.dumps(outcome))
    if not nonperturbing or not captured:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
