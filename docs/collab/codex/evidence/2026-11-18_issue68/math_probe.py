"""Explicit real-Wan source-bound numerical probe; private artifacts stay server-side."""

import argparse
import itertools
import json
import math
import statistics
import time
from pathlib import Path

import torch

from g2.io import write_json
from g2.latent_cache.batch_contract import make_batch_recipe
from g2.latent_cache.batch_encoding import WanBatchEncoder, deterministic_numerics
from g2.latent_cache.builder import _read_rgb, discover_episodes
from g2.latent_cache.contract import fingerprint, make_recipe, preprocessing_recipe
from g2.latent_cache.encoding import WanSingleFrameEncoder
from g2.latent_cache.sealed_source import scan_source
from g2.latent_cache.storage import ViewReader, open_episode_index


def sources(data):
    streams = []
    for root in discover_episodes(data):
        plan = scan_source(root, view_first=True)
        for vid, view in sorted(plan["views"].items()):
            streams.append([(root, plan, vid, record) for record in view["records"]])
    selected = []
    for group in itertools.zip_longest(*streams):
        selected.extend(item for item in group if item is not None)
        if len(selected) >= 40:
            break
    return selected[:40]


def difference(actual, reference):
    delta = actual.double() - reference.double()
    rms = float(delta.square().mean().sqrt())
    return dict(
        max_abs=float(delta.abs().max()),
        rms=rms,
        relative_l2=float(delta.norm() / reference.double().norm().clamp_min(1e-12)),
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("baseline", "batch"))
    p.add_argument("--dataset-root", required=True, type=Path)
    p.add_argument("--weights", required=True, type=Path)
    p.add_argument("--cosmos-root", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--baseline", type=Path)
    p.add_argument("--reference-batch", type=Path)
    args = p.parse_args()
    args.output.mkdir(exist_ok=False)
    selected = sources(args.dataset_root)
    assert len(selected) == 40
    images = [_read_rgb(plan, record) for _, plan, _, record in selected]
    identities = [
        dict(
            episode=plan["episode_key"],
            view_id=vid,
            event_id=record["event_id"],
            png_sha256=record["png_sha256"],
            owner_state_id=record["owner_state_id"],
            png_path=record["png_path"],
        )
        for _, plan, vid, record in selected
    ]
    prep = preprocessing_recipe()
    input_id = fingerprint(identities)
    if args.mode == "baseline":
        encoder = WanSingleFrameEncoder(
            args.weights, cosmos_root=args.cosmos_root, device="cuda:0"
        )
        recipe = make_recipe(encoder.descriptor(), prep)
        assert (
            recipe["recipe_id"]
            == "3ee9c48399143866b2a0061f3cee01bff35842228f639380d60602d6402e2fc1"
        )
        encoder.encode(images[0], prep)
        started = time.perf_counter()
        latents = torch.stack([encoder.encode(im, prep)[0] for im in images])
        seconds = time.perf_counter() - started
        cached = []
        for root, _, vid, record in selected:
            with ViewReader(open_episode_index(root), max_views=1) as reader:
                cached.append(reader.read_view(vid, record["owner_state_id"])["latent"])
        comparison = difference(latents, torch.stack(cached))
        assert comparison["max_abs"] == 0, (
            "unchanged legacy B1 must still match its existing cached reference"
        )
        torch.save(
            dict(latents=latents, input_id=input_id, recipe=recipe),
            args.output / "reference.pt",
        )
        report = dict(
            mode="real_legacy_B1",
            input_id=input_id,
            records=40,
            recipe_id=recipe["recipe_id"],
            cached_reference=comparison,
            seconds=seconds,
            records_per_second=40 / seconds,
        )
    else:
        reference = torch.load(args.baseline, map_location="cpu", weights_only=True)
        assert reference["input_id"] == input_id
        encoder = WanBatchEncoder(
            args.weights, cosmos_root=args.cosmos_root, device="cuda:0"
        )
        recipe = make_batch_recipe(encoder.descriptor())
        encoder.encode_batch(images[:32], prep)
        hook_shapes = []
        hook = encoder.base._module.encoder.register_forward_pre_hook(
            lambda _, inputs: hook_shapes.append(list(inputs[0].shape))
        )

        def run(items):
            hook_shapes.clear()
            output = encoder.encode_batch(items, prep)
            assert hook_shapes and all(
                s[0] == len(items) and s[2] == 1 for s in hook_shapes
            ), "native encoder must retain actual B, not loop B1"
            return torch.stack([x[0] for x in output]), dict(
                encoder.last_metrics, native_encoder_shapes=list(hook_shapes)
            )

        comparisons, timing, tensors = {}, {}, {}
        for count in (1, 8, 16, 32):
            rows, trace = [], []
            for start in range(0, 32, count):
                out, metric = run(images[start : start + count])
                rows.append(out)
                trace.append(metric)
            actual = torch.cat(rows)
            tensors[str(count)] = actual
            comparisons[str(count)] = dict(
                difference(actual, reference["latents"][:32]), calls=trace
            )
            trials = []
            for _ in range(3):
                t = time.perf_counter()
                cuda_ms = 0
                for start in range(0, 32, count):
                    _, metric = run(images[start : start + count])
                    cuda_ms += metric["native_cuda_ms"]
                trials.append(
                    dict(wall_seconds=time.perf_counter() - t, native_cuda_ms=cuda_ms)
                )
            wall = statistics.median(x["wall_seconds"] for x in trials)
            timing[str(count)] = dict(
                trials=trials, median_adapter_seconds=wall, records_per_second=32 / wall
            )
        replay, _ = run(images[:32])
        same_context = difference(replay, tensors["32"])
        assert same_context["max_abs"] == 0
        reverse, _ = run(list(reversed(images[:32])))
        changed, _ = run(images[:31] + [images[39]])
        tail, tail_metric = run(images[:7])
        visual = []
        with torch.no_grad(), deterministic_numerics(torch):
            for i in (0, 3, 9, 17):
                decoded = []
                for latent in (reference["latents"][i], tensors["32"][i]):
                    frame = encoder.base._tokenizer.decode(latent[None, :, None].cuda())
                    assert (
                        tuple(frame.shape) == (1, 3, 1, 256, 256)
                        and torch.isfinite(frame).all()
                    )
                    decoded.append(
                        ((frame[0, :, 0].float().cpu() + 1) * 127.5)
                        .clamp(0, 255)
                        .round()
                    )
                delta = decoded[1] - decoded[0]
                mse = float(delta.square().mean())
                visual.append(
                    dict(
                        input_index=i,
                        max_rgb_byte_difference=float(delta.abs().max()),
                        mse=mse,
                        psnr_db=None if mse == 0 else 10 * math.log10(255**2 / mse),
                        pixel_exact=mse == 0,
                    )
                )
        encoder.base._validate_tokenizer()
        hook.remove()
        cross_gpu = None
        if args.reference_batch:
            previous = torch.load(
                args.reference_batch, map_location="cpu", weights_only=True
            )
            assert previous["input_id"] == input_id and previous["recipe"] == recipe
            cross_gpu = difference(tensors["32"], previous["latents"]["32"])
            assert cross_gpu["max_abs"] == 0, (
                "same fixed batch changed across GPU/restart; cannot silently reuse"
            )
        torch.save(
            dict(latents=tensors, input_id=input_id, recipe=recipe),
            args.output / "batches.pt",
        )
        report = dict(
            mode="real_B1_8_16_32_T1",
            input_id=input_id,
            recipe=recipe,
            comparisons=comparisons,
            warmed_timing=timing,
            same_context_replay=same_context,
            reverse_order_then_unpermute=difference(reverse.flip(0), tensors["32"]),
            changed_member_other31=difference(changed[:31], tensors["32"][:31]),
            tail7_vsB1=difference(tail, reference["latents"][:7]),
            tail7_metric=tail_metric,
            cross_gpu_restart_replay=cross_gpu,
            decoded_B32_vsB1=visual,
            numeric_vsB1="NONZERO_ALLOWED_REPORTED_NOT_BIT_EQUIVALENT",
            training_ready=False,
        )
    write_json(args.output / "inputs.json", identities)
    write_json(args.output / "result.json", report)
    print(
        json.dumps(
            dict(
                status="PASS",
                mode=report["mode"],
                output=str(args.output),
                input_id=input_id,
                recipe_id=report.get(
                    "recipe_id", report.get("recipe", {}).get("recipe_id")
                ),
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
