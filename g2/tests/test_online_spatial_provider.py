"""Live F27 source, offline selection and native Reader handoff on CPU."""

from dataclasses import replace
from io import BytesIO
from types import SimpleNamespace

import pytest
import torch
from cosmos_framework.inference.g2_policy_conditions import mask_content_identity
from cosmos_framework.model.generator.mot.g2_contracts import (
    G2SampleIdentity,
    GlobalCacheSignature,
)
from PIL import Image

from g2.io import ContractError, digest, write_json
from g2.latent_cache.batch_contract import ENCODER_SCHEMA, NUMERICS, make_batch_recipe
from g2.latent_cache.contract import fingerprint
from g2.offline.spatial_metadata import state_metadata
from g2.online import view_encoder
from g2.online.spatial_provider import LiveSpatialProvider
from g2.online.spatial_source import LIVE_VIEWS, task_binding_identity
from g2.online.view_encoder import decode_rgb, read_view_recipe

SOURCE = "a" * 64
TOP = "sixview/floor_top"
MARKED = f"{TOP}_w_rbs"
ISLAND = "islands/island_0_entity_7/plus_X"
UNRELATED = "sixview/minus_X"


def _recipe():
    return make_batch_recipe(
        {
            "schema": ENCODER_SCHEMA,
            "numerics": NUMERICS,
            "max_batch_size": 32,
            "test_only": False,
            "legacy_loader": {"device": "cuda:0"},
        }
    )


class FixtureEncoder:
    """Exercise routing with image-specific latents without a Wan or CUDA call."""

    def __init__(self):
        self.decoded = []

    def encode(self, raw):
        color = int(decode_rgb(raw)[0, 0, 0])
        self.decoded.append(color)
        return torch.full((48, 16, 16), float(color))


def _publish(root, *, frame, episode="ep-1", owner=None, colors=(17, 23, 37, 49)):
    owner = frame if owner is None else owner
    path = root / LIVE_VIEWS
    path.parent.mkdir(parents=True, exist_ok=True)
    inventory = {
        TOP: ("top", None, ["entity_7", "entity_8"]),
        MARKED: ("top", None, ["entity_7", "entity_8"]),
        ISLAND: ("side", "island_0_entity_7", ["entity_7"]),
        UNRELATED: ("unrelated", None, ["entity_8"]),
    }
    images, owners, plan = [], {}, {}
    for (vid, (native, island, entities)), color in zip(
        inventory.items(), colors, strict=True
    ):
        png = f"{vid}.png"
        file = path.parent / f"frame_{owner}" / png
        if not file.exists():
            file.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (40, 24), (color, 4, 5)).save(file)
        images.append(dict(rgb_file=png, native_view=native))
        plan[native] = dict(native_entity_ids=entities, room_uid=0, island_id=island)
        owners[vid] = dict(
            path=file.relative_to(path.parent).as_posix(),
            frame=owner,
            state_id=owner // 20,
            sha256=digest(file),
            projection=dict(
                axis="floor_top",
                coordinate_frame="NATIVE_ROOM_REFERENCE",
                reference_frame=dict(
                    origin_world=[0, 0, 0], axes_world=[[1, 0, 0], [0, 1, 0], [0, 0, 1]]
                ),
                right_world=[1, 0, 0],
                up_world=[0, 1, 0],
                forward_world=[0, 0, 1],
                uv_min_room=[0, 0],
                width=40,
                height=24,
                meters_per_pixel=0.01,
                native_entity_ids=entities,
            ),
        )
    scene = dict(
        scene_id=f"scene-{episode}",
        source_sha256=SOURCE,
        frame_id=frame,
        world_frame="world",
        rooms=[{"uid": 0}],
        entities=[{"id": name, "kind": "object"} for name in ("entity_7", "entity_8")],
    )
    spatial = state_metadata(
        scene, images, plan, state_id=frame // 20, owner_rows=owners
    )
    live = dict(
        schema="g2_online_f27_views_v1",
        source_sha256=SOURCE,
        episode_id=episode,
        spatial_metadata=spatial,
    )
    write_json(path, live)
    text = dict(
        text_id="fixture-text",
        original_instruction="Open the fixture.",
        augmented_instruction="Open the fixture. In the kitchen.",
    )
    task = dict(binding_status="BOUND", entity_ids=["entity_7"])
    write_json(root / "initial_condition.json", dict(task_set=task, text=text))
    identity = G2SampleIdentity(
        episode_id=episode,
        scene_id=scene["scene_id"],
        subtask_id="atomic_000000",
        decision_frame=frame,
        logical_state_frame=frame,
        task_binding_id=task_binding_identity(episode, SOURCE, task, text["text_id"]),
        data_version="data",
        alignment_version="alignment",
        state15_recipe_id="state15",
    )
    return SimpleNamespace(
        path=path,
        live=live,
        identity=identity,
        source=dict(path=path.relative_to(root.parent).as_posix(), sha256=digest(path)),
        text=dict(
            original_instruction=text["original_instruction"],
            enhanced_instruction=text["augmented_instruction"],
            source_identity=SOURCE,
            initial_context_identity=text["text_id"],
        ),
    )


def _signature(variant="with_robot"):
    return GlobalCacheSignature(
        text=None,
        top_variant=variant,
        reader_version="reader",
        projector_version="projector",
        geometry_encoding_version="geometry",
        mask_version="mask",
        views=(),
        projections=(),
        rasters=(),
        view_types=(),
    )


def _open(provider, row, variant="with_robot"):
    return provider.snapshot(
        row.identity,
        _signature(variant),
        spatial_source=row.source,
        static_text=row.text,
    )


@pytest.mark.parametrize(
    "variant, top, color", [("with_robot", MARKED, 23), ("without_robot", TOP, 17)]
)
def test_r2_reuses_offline_members_projection_mask_and_historical_owner(
    tmp_path, variant, top, color
):
    encoder = FixtureEncoder()
    provider = LiveSpatialProvider(tmp_path, _recipe(), encoder, max_views=4)
    work = tmp_path / "g2-online-case"
    zero = _publish(work, frame=0)
    initial = _open(provider, zero, variant)
    current = _publish(work, frame=20, owner=0)
    current.identity = replace(current.identity, decision_frame=32)
    selected = _open(provider, current, variant)
    assert selected.source == "online_rollout"
    assert [v.view_id for v in selected.signature.views] == [ISLAND, top]
    assert selected.signature.view_types[0] == (
        "island",
        "plus_X",
        "0",
        "island_0_entity_7",
        None,
    )
    assert all(v.image_owner_frame == 0 for v in selected.signature.views)
    assert (
        selected.signature.views[0].geometry_version
        != initial.signature.views[0].geometry_version
    )
    assert selected.signature.projections == initial.signature.projections
    image = provider.load_view(selected, 1)
    assert image.raster.original_hw == (24, 40) and image.raster.canvas_hw == (256, 256)
    assert image.projection.physical_width_m == 0.4
    assert mask_content_identity(image.valid_mask) == selected.mask_content_ids[1]
    assert 0 < image.valid_mask.sum() < image.valid_mask.numel()
    assert image.latent.unique().tolist() == [float(color)]
    assert encoder.decoded == [color]
    with pytest.raises(ValueError, match="SHA256"):
        _open(provider, zero, variant)


def test_r2_source_from_another_episode_or_future_frame_is_refused(tmp_path):
    provider = LiveSpatialProvider(tmp_path, _recipe(), FixtureEncoder(), max_views=4)
    first = _publish(tmp_path / "g2-online-a", frame=0)
    second = _publish(
        tmp_path / "g2-online-b", frame=0, episode="ep-2", colors=(0, 5, 7, 8)
    )
    assert provider.load_view(_open(provider, second), 1).latent.unique().tolist() == [
        5.0
    ]
    with pytest.raises(ContractError, match="current Episode"):
        provider.snapshot(
            first.identity,
            _signature(),
            spatial_source=second.source,
            static_text=first.text,
        )
    with pytest.raises(ContractError, match="spatial frontier"):
        provider.snapshot(
            replace(first.identity, decision_frame=20),
            _signature(),
            spatial_source=first.source,
            static_text=first.text,
        )
    with pytest.raises(ContractError, match="current spatial publication"):
        provider.snapshot(first.identity, _signature())


@pytest.mark.parametrize("fault", ["task", "owner", "projection", "png"])
def test_r2_changed_evidence_does_not_reach_encoder(tmp_path, fault):
    provider = LiveSpatialProvider(tmp_path, _recipe(), FixtureEncoder(), max_views=4)
    row = _publish(tmp_path / "g2-online-a", frame=0)
    view = row.live["spatial_metadata"]["views"][MARKED]
    if fault == "task":
        row.text["initial_context_identity"] = "wrong"
    elif fault == "png":
        _open(provider, row)  # Cover a previously verified preprocessing cache hit.
        (row.path.parent / view["image_owner"]["path"]).write_bytes(
            b"corrupt PNG bytes"
        )
    else:
        if fault == "owner":
            view["image_owner"]["frame"] = 20
        else:
            view["image_projection"]["meters_per_pixel"] = 0.2
        metadata = row.live["spatial_metadata"]
        metadata.pop("spatial_metadata_id")
        metadata["spatial_metadata_id"] = fingerprint(metadata)
        write_json(row.path, row.live)
        row.source["sha256"] = digest(row.path)
    with pytest.raises(
        ValueError,
        match={
            "task": "task entities",
            "owner": "owner",
            "projection": "projection",
            "png": "SHA256",
        }[fault],
    ):
        _open(provider, row)
    assert not provider.encoder.decoded


def test_r2_exact_recipe_and_final_png_contract(tmp_path):
    recipe = _recipe()
    path = tmp_path / "vae.json"
    write_json(path, recipe)
    assert read_view_recipe(path, recipe["recipe_id"]) == recipe
    with pytest.raises(ContractError, match="training job"):
        read_view_recipe(path, "b" * 64)
    buffer = BytesIO()
    Image.new("RGBA", (2, 4)).save(buffer, format="PNG")
    with pytest.raises(ContractError, match="final RGB PNG"):
        decode_rgb(buffer.getvalue())


@pytest.mark.parametrize("bad_latent", [False, True])
def test_r2_view_encoder_pipe_and_owned_process_cleanup(monkeypatch, bad_latent):
    # Exercise the real parent channel and process lifecycle with a CPU peer.
    # The peer returns fixture floats and never loads Wan.
    script = """
import socket
import struct
import sys
from g2.online.view_encoder import MAX_PNG_BYTES, LATENT_BYTES, _receive, _send
with socket.socket(fileno=int(sys.argv[1])) as channel:
    _send(channel, sys.argv[2].encode())
    assert _receive(channel, MAX_PNG_BYTES) == b"fixture"
    if sys.argv[3] == "True":
        _send(channel, b"wrong length")
    else:
        _send(channel, struct.pack("=f", 2.5) * (LATENT_BYTES // 4))
    assert not channel.recv(1)
"""
    popen = view_encoder.subprocess.Popen

    def open_fixture(command, **settings):
        return popen(
            [command[0], "-c", script, command[3], command[-1], str(bad_latent)],
            **settings,
        )

    monkeypatch.setattr(view_encoder.subprocess, "Popen", open_fixture)
    encoder = view_encoder.OnlineViewEncoder(
        weights="fixture", recipe_path="fixture", recipe_id="a" * 64, timeout_s=10
    )
    process = encoder.process
    try:
        if bad_latent:
            with pytest.raises(ContractError, match="wrong latent size"):
                encoder.encode(b"fixture")
            assert encoder.process is None
        else:
            latent = encoder.encode(b"fixture")
            assert latent.shape == (48, 16, 16)
            assert latent.unique().tolist() == [2.5]
    finally:
        encoder.close()
    assert process.poll() == 0
