"""Independent G2 initial-snapshot spatial-language artifact.

No renderer, VAE, Cosmos model, online adapter or Stage-A writer is imported.
This builder reads only the original caption, episode frame-0 SG and task entity
bindings; it never writes or rewrites View/SG/language.json or DATA_C payloads.
The review-v1 template is intentionally NOT a frozen training recipe.
"""

from __future__ import annotations

import gzip
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from g2.data.episode_state import (
    atomic_write_json,
    canonical,
    digest,
    episode_path,
    json_load,
    require_regular,
)


class InitialLanguageError(ValueError):
    """Fail-closed language/source evidence error."""


@dataclass(frozen=True)
class InitialLanguageRecipe:
    version: str = "g2_initial_spatial_context_review_v1"
    decimal_places: int = 3
    max_characters: int = 4096
    max_candidates_per_group: int = 2
    ambiguity_policy: str = "same_label_and_category_in_same_room"
    freeze_frame: int = 0
    production_template_frozen: bool = False

    def __post_init__(self):
        if (
            type(self.version) is not str
            or self.version != "g2_initial_spatial_context_review_v1"
            or type(self.decimal_places) is not int
            or not 0 <= self.decimal_places <= 6
            or type(self.max_characters) is not int
            or self.max_characters < 128
            or type(self.max_candidates_per_group) is not int
            or not 1 <= self.max_candidates_per_group <= 32
            or self.ambiguity_policy != "same_label_and_category_in_same_room"
            or self.freeze_frame != 0
            or self.production_template_frozen is not False
        ):
            raise InitialLanguageError("unrecognized or unsafe initial language recipe")

    @property
    def recipe_id(self):
        return canonical(asdict(self))

    def to_dict(self):
        return dict(asdict(self), recipe_id=self.recipe_id)


def _fmt(x, decimals: int):
    if not math.isfinite(x):
        raise InitialLanguageError("nonfinite world BBox")
    out = round(float(x), decimals)
    if out == 0:
        out = 0.0
    return f"{out:.{decimals}f}"


def _bbox(entity, recipe):
    lo, hi = entity.get("bbox_min"), entity.get("bbox_max")
    if (
        type(lo) not in (list, tuple)
        or type(hi) not in (list, tuple)
        or len(lo) != 3
        or len(hi) != 3
        or any(
            type(a) not in (int, float) or type(b) not in (int, float)
            for a, b in zip(lo, hi)
        )
        or any(
            not math.isfinite(a) or not math.isfinite(b) or b < a
            for a, b in zip(lo, hi)
        )
    ):
        raise InitialLanguageError(f"invalid initial bbox for {entity.get('id')}")
    return {
        "bbox_center_m": [
            _fmt((a + b) / 2, recipe.decimal_places) for a, b in zip(lo, hi)
        ],
        "bbox_size_m": [_fmt(b - a, recipe.decimal_places) for a, b in zip(lo, hi)],
        "bbox_origin": "world_axis_aligned_bbox_not_center_of_mass",
    }


def _role_sort_key(group):
    role = group["role"]
    priority = (
        0
        if role == "target" or role.startswith("manipulated_")
        else 1
        if role in ("source", "source_reference")
        else 2
        if role in ("destination", "destination_reference", "related_reference")
        else 3
    )
    return (
        priority,
        role,
        group["name"].casefold(),
        group["room_uid"],
        group["entity_ids"][0],
    )


def _entity_id_key(value: str):
    prefix, sep, suffix = value.rpartition("_")
    return (prefix, int(suffix)) if sep and suffix.isdigit() else (value, -1)


def _candidate_groupings(sg: dict, task_set: dict) -> list[dict]:
    if sg.get("world_frame") != "world" or sg.get("frame_id") != 0:
        raise InitialLanguageError(
            "only frame-0 SG in canonical world frame is supported"
        )
    if task_set.get("binding_status") != "BOUND":
        raise InitialLanguageError("unbound task entities cannot be rendered")
    entries = sg.get("entities")
    if type(entries) is not list:
        raise InitialLanguageError("missing initial SG entities")
    by_id = {}
    for entity in entries:
        key = entity.get("id")
        if not isinstance(key, str) or key in by_id:
            raise InitialLanguageError("duplicate/missing initial SG entity ID")
        by_id[key] = entity
    roles = task_set.get("roles")
    if type(roles) is not list or not roles:
        raise InitialLanguageError("no source-bound task roles")
    groups = {}
    for r in roles:
        role = r.get("role")
        assigned = r.get("entity_ids")
        if (
            not isinstance(role, str)
            or not role
            or type(assigned) is not list
            or not assigned
        ):
            raise InitialLanguageError("malformed bound task role")
        for entity_id in assigned:
            if entity_id not in by_id:
                raise InitialLanguageError("role entity absent in SG")
            bound = by_id[entity_id]
            label = bound.get("label")
            category = bound.get("source_category_id")
            room = bound.get("room_uid")
            if not isinstance(label, str) or not label:
                raise InitialLanguageError("unlabeled task entity")
            if type(room) is not int:
                raise InitialLanguageError("task entity lacks known Room")
            ident = (role, label.casefold(), str(category).casefold(), room)
            if ident not in groups:
                groups[ident] = dict(
                    role=role,
                    name=label,
                    room_uid=room,
                    category=category,
                    entity_ids=set(),
                    bound_ids=set(),
                )
            groups[ident]["bound_ids"].add(entity_id)
            # Conservative candidate expansion prevents presenting a GT-only
            # single bound fixture as uniquely selected where the same class
            # has multiple physically distinct objects in the same Room.
            for e in entries:
                if (
                    isinstance(e.get("label"), str)
                    and e["label"].casefold() == label.casefold()
                    and str(e.get("source_category_id")).casefold()
                    == str(category).casefold()
                    and e.get("room_uid") == room
                ):
                    groups[ident]["entity_ids"].add(e["id"])
    out = []
    for group in groups.values():
        group["entity_ids"] = sorted(group["entity_ids"], key=_entity_id_key)
        group["bound_ids"] = sorted(group["bound_ids"], key=_entity_id_key)
        if not group["entity_ids"]:
            raise InitialLanguageError("task candidate expansion is empty")
        out.append(group)
    # Only a unique *semantic* target can anchor geometric ordering. Do not use
    # the source GT-selected drawer/counter id to place it first: that would
    # quietly reveal which of several identical instances an oracle bound.
    anchors = []
    for group in out:
        if (
            group["role"] == "target" or group["role"].startswith("manipulated_")
        ) and len(group["entity_ids"]) == 1:
            ent = by_id[group["entity_ids"][0]]
            center = [(a + b) / 2 for a, b in zip(ent["bbox_min"], ent["bbox_max"])]
            if all(math.isfinite(c) for c in center):
                anchors.append((ent["room_uid"], center))
    if len(anchors) == 1:
        room, center = anchors[0]
        for group in out:
            if group["room_uid"] != room or len(group["entity_ids"]) <= 1:
                continue

            def score(key):
                ent = by_id[key]
                a, b = ent["bbox_min"], ent["bbox_max"]
                midpoint = [(x + y) / 2 for x, y in zip(a, b)]
                if not all(math.isfinite(x) for x in midpoint):
                    raise InitialLanguageError("nonfinite candidate center")
                return (
                    sum((x - y) ** 2 for x, y in zip(midpoint, center)),
                    _entity_id_key(key),
                )

            group["entity_ids"] = sorted(group["entity_ids"], key=score)
    return sorted(out, key=_role_sort_key), by_id


def _fact(group, entity, *, candidate_count, recipe):
    room = entity["room_uid"]
    island = entity.get("island_id")
    if island is not None and (
        (not isinstance(island, str) or not island) and type(island) is not int
    ):
        raise InitialLanguageError("invalid Island identity")
    return {
        "entity_id": entity["id"],
        "name": entity["label"],
        "role": group["role"],
        "room_uid": room,
        "island_id": island,
        "category": entity.get("source_category_id"),
        "source_instance_id": entity.get("source_instance_id"),
        "source_part_id": entity.get("source_part_id"),
        "same_label_candidates": candidate_count,
        **_bbox(entity, recipe),
    }


def _render(original: str, groups: list[dict], recipe: InitialLanguageRecipe):
    header = (
        f"Task: {original}\n"
        "Initial spatial context (world frame; metres; episode frame 0):"
    )
    displayed = []
    for group in groups:
        for fact in group["facts"][: group["display_count"]]:
            room = f"R{fact['room_uid']}" if fact["room_uid"] >= 0 else "unknown"
            island = (
                f"; island={fact['island_id']}" if fact["island_id"] is not None else ""
            )
            role = fact["role"] + (
                "_candidate" if fact["same_label_candidates"] > 1 else ""
            )
            center = ", ".join(fact["bbox_center_m"])
            size = ", ".join(fact["bbox_size_m"])
            displayed.append(
                f"- {fact['name']} [{fact['entity_id']}]: role={role}; room={room}{island}; "
                f"bbox_center=({center}); bbox_size=({size})."
            )
    notes = []
    for g in groups:
        total = g["candidate_total"]
        shown = g["display_count"]
        if total > 1:
            room_label = f"R{g['room_uid']}" if g["room_uid"] >= 0 else "unknown"
            line = (
                f"Ambiguity: role={g['role']}; label={g['name']}; room={room_label}; "
                f"{total} same-label candidate(s)"
            )
            if total > shown:
                line += (
                    f"; {shown} listed, {total - shown} omitted by candidate cap/budget"
                )
            notes.append(line + ".")
    return "\n".join([header, *displayed, *notes])


def build_initial_language(
    *,
    original_instruction: str,
    scene_graph: dict,
    task_set: dict,
    task_class: str,
    episode_index: int,
    recipe: InitialLanguageRecipe = InitialLanguageRecipe(),
) -> dict:
    """Pure deterministic builder; no environment or filesystem required."""
    if not isinstance(original_instruction, str) or not original_instruction:
        raise InitialLanguageError("original caption must be nonempty")
    if (
        not isinstance(task_class, str)
        or not task_class.isalnum()
        or type(episode_index) is not int
    ):
        raise InitialLanguageError("unsafe episode identity")
    if not isinstance(recipe, InitialLanguageRecipe):
        raise InitialLanguageError("unknown recipe type")
    if task_set.get("schema") != "g2_gt_task_entity_set_v1":
        raise InitialLanguageError("unknown task-role schema")
    groups, by_id = _candidate_groupings(scene_graph, task_set)
    if len(groups) > 24:
        raise InitialLanguageError("too many independent task entity role groups")
    for g in groups:
        g["candidate_total"] = len(g["entity_ids"])
        g["facts"] = [
            _fact(
                g, by_id[entity_id], candidate_count=g["candidate_total"], recipe=recipe
            )
            for entity_id in g["entity_ids"]
        ]
        g["display_count"] = min(len(g["facts"]), recipe.max_candidates_per_group)
    # Never silently truncate a word, original caption or a structured fact.
    # Preserve at least one representative from every task-role group, and
    # record exact number of omitted same-label candidates on overflow.
    while True:
        content = _render(original_instruction, groups, recipe)
        if len(content) <= recipe.max_characters:
            break
        removable = [g for g in groups if g["display_count"] > 1]
        if not removable:
            raise InitialLanguageError(
                "token/char budget too short for one object per role"
            )
        removable[-1]["display_count"] -= 1
    included = []
    ambiguity = []
    for g in groups:
        included.extend(g["facts"][: g["display_count"]])
        if g["candidate_total"] > 1:
            ambiguity.append(
                {
                    "role": g["role"],
                    "name": g["name"],
                    "room_uid": g["room_uid"],
                    "candidate_count": g["candidate_total"],
                    "shown_count": g["display_count"],
                    "omitted_count": g["candidate_total"] - g["display_count"],
                    # GT bound identity stays in audit-only data. It is not
                    # injected as a unique oracle target in the policy text.
                    "gt_bound_entity_ids_for_audit_only": g["bound_ids"],
                }
            )
    payload = {
        "schema": "g2_initial_language_record_review_v1",
        "task_class": task_class,
        "episode_index": episode_index,
        "initial_frame": 0,
        "original_instruction": original_instruction,
        "augmented_instruction": content,
        "scene_context": {
            "world_frame": "world",
            "units": "metres",
            "geometry": "world_axis_aligned_bbox_not_center_of_mass",
            "facts": included,
            "ambiguity": ambiguity,
            "number_of_omitted_facts": sum(
                g["candidate_total"] - g["display_count"] for g in groups
            ),
            "relations_policy": "NO_ON_INSIDE_CONTACT_OR_STATE_INFERRED",
            "source_roles": task_set.get("grounding"),
        },
        "recipe": recipe.to_dict(),
        "original_preserved": True,
        "training_ready": False,
        "text_id": canonical(
            {
                "original_instruction": original_instruction,
                "augmented_instruction": content,
                "recipe_id": recipe.recipe_id,
            }
        ),
    }
    return payload


def _safe_episode_asset(epdir: Path, rel: str) -> Path:
    if (
        not isinstance(rel, str)
        or not rel
        or Path(rel).is_absolute()
        or ".." in Path(rel).parts
    ):
        raise InitialLanguageError("unsafe source artifact reference")
    target = epdir / rel
    require_regular(target)
    return target


def load_initial_episode_language(
    *,
    view_root,
    raw_source: dict,
    recipe: InitialLanguageRecipe = InitialLanguageRecipe(),
):
    """Read only the producer's sealed state 0; bind text to original G1 caption."""
    task, ep = raw_source["task_class"], raw_source["episode_index"]
    epdir = episode_path(view_root, task, ep)
    manifest_path = _safe_episode_asset(epdir, "episode_manifest.json")
    complete_path = _safe_episode_asset(epdir, "COMPLETE.json")
    task_path = _safe_episode_asset(epdir, "task_entities.json")
    legacy_path = _safe_episode_asset(epdir, "language.json")
    manifest = json_load(manifest_path)
    complete = json_load(complete_path)
    if (
        not complete.get("complete")
        or complete.get("episode_manifest_sha256") != digest(manifest_path)
        or manifest.get("episode_id") != ep
        or manifest.get("task_class") != task
        or not manifest.get("states")
    ):
        raise InitialLanguageError(
            "View-first episode has no matching sealed completion"
        )
    state = manifest["states"][0]
    if state.get("frame") != 0 or state.get("state_id") != 0:
        raise InitialLanguageError("initial spatial snapshot is not frame 0")
    if raw_source["source_frame_count"] < 17:
        raise InitialLanguageError(
            "RoboCasa original episode too short for G1 exact window"
        )
    sg_path = _safe_episode_asset(epdir, state["scene_graph"])
    with gzip.open(sg_path, "rt") as file:
        sg = json.load(file)
    binding = json_load(task_path)
    if binding.get("schema") != "g2_episode_task_entities_v1":
        raise InitialLanguageError("unexpected task-binding envelope")
    set_id = state.get("task_entity_set_id")
    bound_set = binding.get("sets", {}).get(set_id)
    if not bound_set:
        raise InitialLanguageError("initial task entity set not found")
    legacy = json_load(legacy_path)
    if legacy.get("schema") != "g2_episode_text_bank_v1":
        raise InitialLanguageError("original caption bank unavailable")
    if len(legacy.get("texts", {})) != 1:
        raise InitialLanguageError("original caption varies within atomic episode")
    old = next(iter(legacy["texts"].values()))
    caption = old.get("original_text")
    if not old.get("original_preserved") or caption != raw_source["instruction"]:
        raise InitialLanguageError("original G1 instruction differs from View caption")
    if (
        not legacy.get("states")
        or legacy["states"][0]["frame"] != 0
        or legacy["states"][0]["caption_source"]["original_text"] != caption
        or legacy["states"][0]["caption_source"]["episode_index"] != ep
    ):
        raise InitialLanguageError("initial caption is not G1 source frame 0")
    entry = build_initial_language(
        original_instruction=caption,
        scene_graph=sg,
        task_set=bound_set,
        task_class=task,
        episode_index=ep,
        recipe=recipe,
    )
    entry["provenance"] = {
        "evidence_scope": "full_map_initial_gt_only_not_online_certified",
        "g1_source_binding_digest": raw_source["source_binding_digest"],
        "g1_original_frame_count": raw_source["source_frame_count"],
        "g1_original_range": raw_source["source_range"],
        "source_view_episode_id": manifest["source_id"],
        "initial_scene_graph_relative_path": state["scene_graph"],
        "initial_scene_graph_sha256": digest(sg_path),
        "task_entity_set_id": set_id,
        "task_entities_sha256": digest(task_path),
        "view_manifest_sha256": digest(manifest_path),
        "legacy_language_sha256": digest(legacy_path),
        "geometry_version": state.get("geometry_version"),
    }
    return entry


def _dest(root, entry: dict):
    return (
        Path(root)
        / "recipes"
        / entry["recipe"]["recipe_id"]
        / "tasks"
        / entry["task_class"]
        / "episodes"
        / f"episode_{entry['episode_index']:06d}"
    )


def verify_persisted_initial_language(root, expected: dict) -> dict:
    dest = _dest(root, expected)
    marker_path, source = dest / "COMPLETE.json", dest / "initial_context.json"
    require_regular(marker_path)
    require_regular(source)
    receipt = json_load(marker_path)
    if (
        receipt.get("schema") != "g2_initial_language_complete_review_v1"
        or receipt.get("complete") is not True
        or receipt.get("content_sha256") != digest(source)
        or receipt.get("text_id") != expected["text_id"]
        or receipt.get("recipe_id") != expected["recipe"]["recipe_id"]
    ):
        raise InitialLanguageError(
            "initial language output does not match sealed source/recipe"
        )
    try:
        stored = json_load(source)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InitialLanguageError("invalid stored initial language JSON") from exc
    if stored != expected:
        raise InitialLanguageError(
            "initial language output does not match sealed source/recipe"
        )
    return {
        "episode_index": expected["episode_index"],
        "task_class": expected["task_class"],
        "text_id": expected["text_id"],
        "recipe_id": expected["recipe"]["recipe_id"],
        "content_sha256": receipt["content_sha256"],
        "path": str(source),
        "training_ready": False,
    }


def write_initial_language(root, expected: dict, *, resume: bool = True):
    """Atomically publish standalone version; no mutation of View/SG/VAE/DATA_C."""
    dest = _dest(root, expected)
    marker_path = dest / "COMPLETE.json"
    if marker_path.exists():
        if not resume:
            raise FileExistsError(marker_path)
        return verify_persisted_initial_language(root, expected)
    if dest.exists() and any(dest.iterdir()):
        raise InitialLanguageError("partial or unowned output; refuse overwrite")
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / "initial_context.json"
    atomic_write_json(target, expected)
    atomic_write_json(
        marker_path,
        {
            "schema": "g2_initial_language_complete_review_v1",
            "complete": True,
            "recipe_id": expected["recipe"]["recipe_id"],
            "text_id": expected["text_id"],
            "content_sha256": digest(target),
            "training_ready": False,
        },
    )
    return verify_persisted_initial_language(root, expected)


def read_versioned_initial_language(
    root,
    *,
    recipe_id: str,
    task_class: str,
    episode_index: int,
    source_binding_digest: str,
    original_instruction: str,
    view_root=None,
) -> dict:
    """Read an explicitly chosen immutable language version without rebuilding it.

    DATA_C may keep its spatial/G1 index unchanged while its model-side Reader
    selects a different text recipe. This is a *candidate* sidecar: it does not
    itself certify the training split, online GT equivalence or final template.
    """
    if (
        type(recipe_id) is not str
        or len(recipe_id) != 64
        or any(ch not in "0123456789abcdef" for ch in recipe_id)
    ):
        raise InitialLanguageError("unsafe language recipe ID")
    if (
        not isinstance(task_class, str)
        or not task_class.isalnum()
        or type(episode_index) is not int
        or not 0 <= episode_index < 10_000_000
    ):
        raise InitialLanguageError("unsafe language episode key")
    root = Path(root)
    root_info = root / "OUTPUT_IDENTITY.json"
    require_regular(root_info)
    info = json_load(root_info)
    if (
        info.get("schema") != "g2_independent_language_root_v2"
        or info.get("source_binding_digest") != source_binding_digest
        or info.get("training_ready") is not False
    ):
        raise InitialLanguageError("standalone language root source binding differs")
    recipe_dir = root / "recipes" / recipe_id
    rec_path = recipe_dir / "RECIPE.json"
    require_regular(rec_path)
    rec = json_load(rec_path)
    if (
        rec.get("schema") != "g2_initial_language_recipe_declaration_v1"
        or rec.get("source_binding_digest") != source_binding_digest
        or rec.get("recipe", {}).get("recipe_id") != recipe_id
        or canonical(
            {k: v for k, v in rec.get("recipe", {}).items() if k != "recipe_id"}
        )
        != recipe_id
        or rec.get("training_ready") is not False
    ):
        raise InitialLanguageError("standalone language recipe drift")
    dest = (
        recipe_dir / "tasks" / task_class / "episodes" / f"episode_{episode_index:06d}"
    )
    data_path, marker_path = dest / "initial_context.json", dest / "COMPLETE.json"
    require_regular(data_path)
    require_regular(marker_path)
    receipt = json_load(marker_path)
    if (
        receipt.get("schema") != "g2_initial_language_complete_review_v1"
        or receipt.get("complete") is not True
        or receipt.get("recipe_id") != recipe_id
        or receipt.get("content_sha256") != digest(data_path)
        or receipt.get("training_ready") is not False
    ):
        raise InitialLanguageError("standalone language content receipt drift")
    record = json_load(data_path)
    if (
        record.get("schema") != "g2_initial_language_record_review_v1"
        or record.get("recipe", {}).get("recipe_id") != recipe_id
        or record.get("text_id") != receipt.get("text_id")
        or record.get("episode_index") != episode_index
        or record.get("task_class") != task_class
        or record.get("initial_frame") != 0
        or record.get("training_ready") is not False
        or record.get("original_instruction") != original_instruction
        or record.get("provenance", {}).get("g1_source_binding_digest")
        != source_binding_digest
    ):
        raise InitialLanguageError(
            "standalone text identity/original/causal provenance mismatch"
        )
    if record["text_id"] != canonical(
        {
            "original_instruction": record["original_instruction"],
            "augmented_instruction": record["augmented_instruction"],
            "recipe_id": recipe_id,
        }
    ):
        raise InitialLanguageError("standalone augmented text fingerprint mismatch")
    if view_root is not None:
        epdir = episode_path(view_root, task_class, episode_index)
        provenance = record["provenance"]
        manifest = _safe_episode_asset(epdir, "episode_manifest.json")
        sg = _safe_episode_asset(epdir, provenance["initial_scene_graph_relative_path"])
        task = _safe_episode_asset(epdir, "task_entities.json")
        old = _safe_episode_asset(epdir, "language.json")
        if (
            provenance["view_manifest_sha256"] != digest(manifest)
            or provenance["initial_scene_graph_sha256"] != digest(sg)
            or provenance["task_entities_sha256"] != digest(task)
            or provenance["legacy_language_sha256"] != digest(old)
        ):
            raise InitialLanguageError(
                "standalone language initial View/SG/caption source drift"
            )
    return record
