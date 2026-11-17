"""Caption-authoritative candidate language; no actions or inferred relations."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from g2.io import ContractError, digest
from g2.latent_cache.contract import fingerprint

CONTEXT_FIELDS = (
    "facts_sha256",
    "included_facts_sha256",
    "fact_count",
    "omitted_fact_count",
    "original_exceeds_budget",
)


@dataclass(frozen=True)
class LanguageRecipe:
    version: str = "g2_current_spatial_facts_candidate_v1"
    include_aabb: bool = False
    decimal_places: int = 3
    max_characters: int = 4096

    def __post_init__(self):
        if (
            not isinstance(self.version, str)
            or not self.version
            or type(self.include_aabb) is not bool
            or type(self.decimal_places) is not int
            or not 0 <= self.decimal_places <= 8
            or type(self.max_characters) is not int
            or self.max_characters < 1
        ):
            raise ContractError("invalid candidate language recipe")

    def to_dict(self):
        body = dict(
            **asdict(self),
            budget_unit="UNICODE_CHARACTERS_NOT_TOKENS",
            units="m",
            production_template_frozen=False,
        )
        return dict(body, recipe_id=fingerprint(body))


def resolve_caption_rows(frame_rows, task_rows, *, frames, episode_id, ep_meta_lang):
    tasks = {}
    for row in task_rows:
        key, text = row.get("task_index"), row.get("task")
        if (
            type(key) is not int
            or not isinstance(text, str)
            or not text
            or key in tasks
        ):
            raise ContractError("invalid or duplicate authoritative task table")
        tasks[key] = text
    captions = {}
    for row in frame_rows:
        if row.get("episode_index") != episode_id:
            raise ContractError("caption frame belongs to another episode")
        frame, index = row.get("frame_index"), row.get("task_index")
        if (
            type(frame) is not int
            or frame < 0
            or type(index) is not int
            or index not in tasks
        ):
            raise ContractError("raw frame task_index is missing from tasks table")
        if frame in captions:
            raise ContractError("duplicate raw frame caption identity")
        text = tasks[index]
        if not isinstance(ep_meta_lang, str) or text != ep_meta_lang:
            raise ContractError("authoritative caption and ep_meta.lang disagree")
        captions[frame] = dict(
            original_text=text,
            task_index=index,
            frame_index=frame,
            episode_index=episode_id,
            authority="FLAT_FRAME_TASK_INDEX_TO_META_TASKS_PARQUET",
        )
    if set(frames) - set(captions):
        raise ContractError(
            "current raw frame has no authoritative caption; no fallback"
        )
    return {frame: captions[frame] for frame in frames}


def load_flat_captions(flat_root, *, episode_id, frames, ep_meta_lang):
    """Use the existing server PyArrow installation only; no environment setup."""
    import pyarrow.dataset as ds
    import pyarrow.parquet as pq

    root = Path(flat_root).resolve(strict=True)
    tasks_path = root / "meta/tasks.parquet"
    table = pq.read_table(tasks_path)
    task_rows = table.to_pylist()
    if (
        "task_index" not in table.column_names
        and "__index_level_0__" in table.column_names
    ):
        task_rows = [
            dict(task_index=r["__index_level_0__"], task=r["task"]) for r in task_rows
        ]
    dataset = ds.dataset(root / "data", format="parquet")
    filt = ds.field("episode_index") == episode_id
    # Parquet fragments are often shared by many episodes; a dataset-level
    # filter alone need not prune files. Use row-group statistics before
    # hashing, instead of rehashing the entire corpus for every episode.
    fragments = sorted(
        Path(f.path)
        for f in dataset.get_fragments(filter=filt)
        if f.split_by_row_group(filter=filt)
    )
    paths = [p if p.is_absolute() else root / p for p in fragments]
    before = {str(p): digest(p) for p in [tasks_path, *paths]}
    if not paths:
        raise ContractError("episode has no caption source fragments")
    rows = (
        ds.dataset([str(p) for p in paths], format="parquet")
        .to_table(filter=filt, columns=["episode_index", "frame_index", "task_index"])
        .to_pylist()
    )
    captions = resolve_caption_rows(
        rows, task_rows, frames=frames, episode_id=episode_id, ep_meta_lang=ep_meta_lang
    )
    if before != {str(p): digest(p) for p in [tasks_path, *paths]}:
        raise ContractError("caption authority changed while reading")
    return captions, dict(
        authority="FLAT_FRAME_TASK_INDEX_TO_META_TASKS_PARQUET",
        source_files_sha256=before,
    )


def enhance_caption(original, graph, task_set, recipe):
    if (
        not isinstance(original, str)
        or not original
        or not isinstance(recipe, LanguageRecipe)
    ):
        raise ContractError("original instruction and candidate recipe are required")
    if task_set["binding_status"] != "BOUND":
        raise ContractError("unresolved roles cannot be rendered as trusted facts")
    by_id = {e["id"]: e for e in graph["entities"]}
    facts = []
    for role in sorted(
        task_set["roles"], key=lambda r: (r["role"], r["source_instance_id"])
    ):
        for eid in sorted(role["entity_ids"]):
            if eid not in by_id:
                raise ContractError("task entity missing from current SG")
            entity = by_id[eid]
            row = dict(
                role=role["role"],
                entity_id=eid,
                source_instance_id=entity["source_instance_id"],
                source_part_id=entity["source_part_id"],
                name=entity.get("label"),
                room_uid=entity.get("room_uid"),
                island_id=entity.get("island_id"),
            )
            if recipe.include_aabb:
                low, high = entity["bbox_min"], entity["bbox_max"]
                if (
                    len(low) != 3
                    or len(high) != 3
                    or any(not math.isfinite(x) for x in low + high)
                    or any(b < a for a, b in zip(low, high))
                ):
                    raise ContractError("invalid current AABB facts")

                def fmt(value):
                    value = round(value, recipe.decimal_places)
                    return f"{0.0 if value == 0 else value:.{recipe.decimal_places}f}"

                row.update(
                    aabb_center_m=[fmt((a + b) / 2) for a, b in zip(low, high)],
                    aabb_size_m=[fmt(b - a) for a, b in zip(low, high)],
                    geometry_frame=graph["world_frame"],
                    geometry_is="ROUNDED_WORLD_AABB_NOT_CENTROID_OR_CONTACT",
                )
            facts.append(row)
    prefix = "\nCurrent spatial facts (candidate; no inferred contact/state): "
    # Budget never truncates original instruction or a half-written entity fact.
    accepted = []
    for fact in facts:
        candidate = (
            original
            + prefix
            + json.dumps(
                accepted + [fact],
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        if len(candidate) > recipe.max_characters:
            break
        accepted.append(fact)
    enhanced = (
        original
        + prefix
        + json.dumps(
            accepted, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )
        if accepted
        else original
    )
    result = dict(
        original_text=original,
        enhanced_text=enhanced,
        recipe=recipe.to_dict(),
        facts_sha256=fingerprint(facts),
        included_facts_sha256=fingerprint(accepted),
        fact_count=len(accepted),
        omitted_fact_count=len(facts) - len(accepted),
        original_exceeds_budget=len(original) > recipe.max_characters,
        original_preserved=True,
        original_sha256=fingerprint(original),
    )
    # Identical rendered text/recipe has one library entry even if omitted
    # current facts changed. Their audit hashes belong to the state index.
    result["text_id"] = fingerprint(
        dict(
            original_text=original,
            enhanced_text=enhanced,
            recipe_id=result["recipe"]["recipe_id"],
        )
    )
    return result


def split_text_record(value):
    return (
        {k: v for k, v in value.items() if k not in CONTEXT_FIELDS},
        {k: value[k] for k in CONTEXT_FIELDS},
    )


class TextBank:
    def __init__(self):
        self.texts = {}
        self.states = []

    def add(self, state_id, frame, caption, graph, task_set, recipe):
        if self.states and (
            state_id <= self.states[-1]["state_id"] or frame <= self.states[-1]["frame"]
        ):
            raise ContractError("language states must be causal and increasing")
        text = enhance_caption(caption["original_text"], graph, task_set, recipe)
        record, context = split_text_record(text)
        self.texts.setdefault(text["text_id"], record)
        row = dict(
            state_id=state_id,
            frame=frame,
            text_id=text["text_id"],
            caption_source=caption,
            fact_context=context,
        )
        self.states.append(row)
        return row
