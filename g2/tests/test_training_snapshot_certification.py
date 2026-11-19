"""Regressions for exact temporal, text and snapshot admission in Issue #82."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from types import SimpleNamespace

import pytest

from g2.data import verified_provider as provider
from g2.data.aligned_provider import CandidateAlignedG2Provider, _EpisodeData
from g2.data.episode_state import (
    DataBError,
    atomic_write_json,
    canonical,
    digest,
    episode_path,
)
from g2.data.joint_index import (
    TOP_VIEW_IDS,
    DataCError,
    make_joint_recipe,
    read_joint_episode,
)
from g2.language.initial_context import (
    InitialLanguageError,
    InitialLanguageRecipe,
    read_versioned_initial_language,
)
from tools.g2 import certify_training_snapshot as certify


def _joint():
    frames = (0, 5, 24)
    recipe = make_joint_recipe(
        state_recipe_id="state", view_recipe_id="view", top_variant="both"
    )
    states = []
    for ordinal, frame in enumerate(frames):
        state = dict(
            logical_state_id=ordinal,
            frame=frame,
            scene_graph_file=f"s{ordinal}/sg.gz",
            spatial_metadata_file=f"s{ordinal}/spatial_metadata.json",
            selected_views=[],
            text_id="text",
        )
        state["top_views"] = {
            name: {
                "view_id": view_id,
                "top_variant": name,
                "view_scope": "floor",
                "physical_owner_frame": 0,
                "physical_owner_ordinal": 0,
                "physical_owner_state": 0,
                "spatial_metadata_relpath": state["spatial_metadata_file"],
                "projection_id": "projection",
                "geometry_version": "geometry",
                "membership_version": "members",
                "vae_recipe_id": "view",
            }
            for name, view_id in TOP_VIEW_IDS.items()
        }
        states.append(state)
    windows = [
        dict(
            decision_frame=t,
            state15_frame=t,
            action_start_frame=t,
            action_last_frame=t + 15,
            observation_last_frame=t + 16,
            spatial_state_ordinal=int(t >= 5),
            spatial_state_frame=5 if t >= 5 else 0,
            text_id="text",
        )
        for t in range(9)
    ]
    return dict(
        schema="g2_data_c_joint_episode_v2",
        episode_index=3,
        task_class="Example",
        training_ready=False,
        recipe=recipe,
        recipe_id=canonical(recipe),
        view_vae_recipe_id="view",
        source_binding_digest="source",
        source_frame_count=25,
        static_text={"text_id": "text"},
        spatial_states=states,
        windows=windows,
    )


def _read_joint(root, joint, *, complete=True):
    path = root / "joint_index.json"
    atomic_write_json(path, joint)
    sha = digest(path)
    atomic_write_json(
        root / "COMPLETE.json",
        dict(
            schema="g2_data_c_complete_v2",
            complete=complete,
            training_ready=False,
            joint_sha256=sha,
            recipe_id=joint["recipe_id"],
            source_binding_digest="source",
            task_class="Example",
            episode_index=3,
            frame_count=25,
            decision_window_count=9,
        ),
    )
    return read_joint_episode(
        root,
        task="Example",
        episode=3,
        recipe_id=joint["recipe_id"],
        source_binding_digest="source",
        expected_sha256=sha,
        window_count=9,
    )


def test_causal_data_c_accepts_latest_source_and_retains_terminal(tmp_path):
    joint = _joint()
    assert _read_joint(tmp_path, joint)[0] == joint


@pytest.mark.parametrize(
    "fault",
    (
        "future_ordinal",
        "stale_state",
        "new_action_start",
        "terminal_owner",
        "not_complete",
    ),
)
def test_data_c_rejects_rehashed_but_incorrect_joint(tmp_path, fault):
    joint = _joint()
    if fault == "future_ordinal":
        joint["windows"][0]["spatial_state_ordinal"] = 2
    elif fault == "stale_state":
        joint["windows"][5].update(spatial_state_ordinal=0, spatial_state_frame=0)
    elif fault == "new_action_start":
        joint["windows"][0]["action_start_frame"] = 1
    elif fault == "terminal_owner":
        joint["spatial_states"][-1]["top_views"]["with_robot"][
            "physical_owner_state"
        ] = 1
    with pytest.raises(DataCError, match="latest causal|owner/state|completion"):
        _read_joint(tmp_path, joint, complete=fault != "not_complete")


@pytest.fixture
def language_case(tmp_path):
    recipe = InitialLanguageRecipe()
    root = tmp_path / "language"
    recipe_root = root / "recipes" / recipe.recipe_id
    dest = episode_path(recipe_root, "Example", 3)
    atomic_write_json(
        root / "OUTPUT_IDENTITY.json",
        dict(
            schema="g2_independent_language_root_v2",
            source_binding_digest="source",
            training_ready=False,
        ),
    )
    atomic_write_json(
        recipe_root / "RECIPE.json",
        dict(
            schema="g2_initial_language_recipe_declaration_v1",
            source_binding_digest="source",
            training_ready=False,
            recipe=recipe.to_dict(),
        ),
    )
    record = dict(
        schema="g2_initial_language_record_review_v1",
        recipe=recipe.to_dict(),
        episode_index=3,
        task_class="Example",
        initial_frame=0,
        original_instruction="Pick it up.",
        augmented_instruction="Task: Pick it up. The target is at the counter.",
        training_ready=False,
        provenance={"g1_source_binding_digest": "source"},
    )

    def write():
        record["text_id"] = canonical(
            dict(
                original_instruction=record["original_instruction"],
                augmented_instruction=record["augmented_instruction"],
                recipe_id=recipe.recipe_id,
            )
        )
        data = dest / "initial_context.json"
        marker = dest / "COMPLETE.json"
        atomic_write_json(data, record)
        atomic_write_json(
            marker,
            dict(
                schema="g2_initial_language_complete_review_v1",
                complete=True,
                recipe_id=recipe.recipe_id,
                text_id=record["text_id"],
                content_sha256=digest(data),
                training_ready=False,
            ),
        )
        return {"content_sha256": digest(data), "complete_sha256": digest(marker)}

    args = dict(
        root=root,
        recipe_id=recipe.recipe_id,
        episode_index=3,
        task_class="Example",
        original_instruction=record["original_instruction"],
        source_binding_digest="source",
    )
    return record, write, args


def test_training_text_rejects_self_consistent_replacement(language_case):
    record, write, args = language_case
    original = write()
    assert read_versioned_initial_language(**args, expected_files=original) == record
    record["augmented_instruction"] = (
        "Task: Pick it up. Target moved after the first frame."
    )
    write()
    assert read_versioned_initial_language(**args) == record
    with pytest.raises(DataBError, match="SHA256 differs"):
        read_versioned_initial_language(**args, expected_files=original)


def test_frame_zero_language_rejects_later_scene_graph(language_case, tmp_path):
    record, write, args = language_case
    view_root = tmp_path / "views"
    dest = episode_path(view_root, "Example", 3)
    early, late = "s0/sg.gz", "s1/sg.gz"
    for name in (early, late, "task_entities.json", "language.json"):
        p = dest / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(name.encode())
    files = {
        name: digest(dest / name)
        for name in (early, late, "task_entities.json", "language.json")
    }
    source = dest / "episode_manifest.json"
    atomic_write_json(
        source,
        {"files": files, "states": [{"state_id": 0, "frame": 0, "scene_graph": early}]},
    )
    record["provenance"].update(
        initial_scene_graph_relative_path=late,
        initial_scene_graph_sha256=files[late],
        view_manifest_sha256=digest(source),
        task_entities_sha256=files["task_entities.json"],
        legacy_language_sha256=files["language.json"],
    )
    write()
    with pytest.raises(InitialLanguageError, match="frame-0 Scene Graph"):
        read_versioned_initial_language(**args, view_root=view_root)


def test_episode_payload_cache_loads_on_access_and_eviction():
    seen = []

    def load(row):
        seen.append(row)
        return f"payload-{row}"

    data = _EpisodeData({key: key for key in range(4)}, load, 2)
    assert len(data) == 4 and 3 in data and not seen
    assert [data[key] for key in (0, 1, 0, 2, 1)] == [
        "payload-0",
        "payload-1",
        "payload-0",
        "payload-2",
        "payload-1",
    ]
    assert seen == [0, 1, 2, 1]
    assert list(data.cache) == [2, 1]


def test_selected_view_read_checks_projection_against_manifest(tmp_path, monkeypatch):
    joint = _joint()
    state = joint["spatial_states"][0]
    state["geometry_version"] = "geometry"
    view_ep = episode_path(tmp_path, "Example", 3)
    path = view_ep / state["spatial_metadata_file"]
    metadata = dict(
        frame=0,
        state_id=0,
        geometry_version="geometry",
        views={
            "sixview/floor_top": {"projection_id": "fixed", "meters_per_pixel": 0.01}
        },
    )
    atomic_write_json(path, metadata)
    manifest = {"files": {state["spatial_metadata_file"]: digest(path)}}
    reader = object()
    p = object.__new__(CandidateAlignedG2Provider)
    p.data = {("Example", 3): (joint, None)}
    p.identity = "data"
    p.global_memory_enabled = True
    p.view_read_count = 0
    p.view_root = tmp_path
    p._views = OrderedDict({("Example", 3): (manifest, None, reader, {})})
    identity = SimpleNamespace(
        data_version="data",
        episode_id="Example/episode_000003",
        decision_frame=0,
        logical_state_frame=0,
    )

    def native_view(_index, actual_reader, actual_metadata, _state, ref):
        assert actual_reader is reader and actual_metadata == metadata
        return SimpleNamespace(
            top_variant=ref["top_variant"],
            identity=SimpleNamespace(image_owner_frame=0),
        )

    monkeypatch.setattr("g2.data.aligned_provider._native_view", native_view)
    views = p.read_selected_views(identity, top_view_variant="without_robot")
    assert [v.top_variant for v in views] == ["without_robot"]
    metadata["views"]["sixview/floor_top"]["meters_per_pixel"] = 0.02
    atomic_write_json(path, metadata)
    with pytest.raises(DataBError, match="SHA256 differs"):
        p.read_selected_views(identity, top_view_variant="without_robot")


@pytest.fixture
def snapshot(monkeypatch):
    train, val = {("Example", 0)}, {("Example", 1)}
    split = dict(
        g1_verified_receipt_sha256="g1",
        g1_split_source_sha256="split",
        seed=provider.SPLIT_SEED,
        val_ratio=provider.VAL_RATIO,
    )
    keys = sorted(train | val)
    monkeypatch.setattr(
        provider,
        "g1_partition",
        lambda *_a, **_k: (
            {"source_binding_digest": "source"},
            split,
            {key: {"window_count": 7} for key in keys},
            train,
            val,
        ),
    )
    corpus = dict(
        schema="g2_data_c_corpus_v2",
        training_ready=False,
        top_view_variant="both",
        source_binding_digest="source",
        state15_recipe_id="state",
        view_recipe_id="view",
        recipe_id=canonical(
            make_joint_recipe(
                state_recipe_id="state", view_recipe_id="view", top_variant="both"
            )
        ),
        episodes=[
            dict(
                task_class=task, episode_index=ep, window_count=7, joint_sha256="f" * 64
            )
            for task, ep in keys
        ],
    )
    corpus["data_identity"] = canonical(corpus)
    return dict(
        schema=provider.SCHEMA,
        approval=provider.APPROVAL,
        evidence_scope="verified_data_c",
        training_ready=True,
        source_binding_digest="source",
        g1_verified_receipt_sha256=split["g1_verified_receipt_sha256"],
        g1_split_source_sha256=split["g1_split_source_sha256"],
        split_seed=provider.SPLIT_SEED,
        val_ratio=provider.VAL_RATIO,
        split_identity=canonical(split),
        language_recipe_id=provider.LANGUAGE_RECIPE,
        joint_recipe_id=corpus["recipe_id"],
        snapshot=corpus,
        train_episode_keys=list(map(list, sorted(train))),
        val_episode_keys=list(map(list, sorted(val))),
        train_windows=7,
        val_windows=7,
        online_full_map_gt_parity_certified=False,
        language_review_source_unchanged=True,
        top_view_variants=["with_robot", "without_robot"],
        certification_scope=provider.CERTIFICATION_SCOPE,
        language_bindings=[
            dict(
                task_class=task,
                episode_index=ep,
                content_sha256="1" * 64,
                complete_sha256="2" * 64,
            )
            for task, ep in keys
        ],
    )


def _seal(info):
    info["data_identity"] = provider.data_identity(info)
    info["snapshot_identity"] = canonical(info)
    return info


def test_snapshot_language_affects_data_identity_and_publish_is_immutable(
    tmp_path, snapshot
):
    other = deepcopy(snapshot)
    other["language_bindings"][1]["content_sha256"] = "3" * 64
    assert provider.data_identity(snapshot) != provider.data_identity(other)
    info = _seal(snapshot)
    path = tmp_path / "formal"
    args = dict(g1_index_root=tmp_path, data_c_root=tmp_path)
    certify.publish_snapshot(path, info, **args)
    assert provider.open_verified_snapshot(path, verify_episodes=False, **args) == info
    with pytest.raises(FileExistsError):
        certify.publish_snapshot(path, _seal(other), **args)
    assert provider.open_verified_snapshot(path, verify_episodes=False, **args) == info


@pytest.mark.parametrize(
    "fault",
    ("missing_language", "duplicate_language", "train_val_inversion", "online_parity"),
)
def test_bad_snapshot_does_not_publish_partial_directory(tmp_path, snapshot, fault):
    if fault == "missing_language":
        snapshot["language_bindings"].pop()
    elif fault == "duplicate_language":
        snapshot["language_bindings"].append(snapshot["language_bindings"][0])
    elif fault == "train_val_inversion":
        snapshot["train_episode_keys"], snapshot["val_episode_keys"] = (
            snapshot["val_episode_keys"],
            snapshot["train_episode_keys"],
        )
    else:
        snapshot["online_full_map_gt_parity_certified"] = True
    args = dict(g1_index_root=tmp_path, data_c_root=tmp_path)
    path = tmp_path / "formal"
    with pytest.raises(DataCError):
        certify.publish_snapshot(path, _seal(snapshot), **args)
    assert not path.exists()
