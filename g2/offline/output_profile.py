"""Explicit Stage-A output contracts; legacy completed packages stay untouched."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from g2.io import ContractError, canonical
from g2.latent_cache.contract import fingerprint

SCHEMA = "g2_spatial_profile_episode_v1"
SOURCE_SCHEMA = "g2_sealed_spatial_source_v1"
PROFILE_SCHEMA = "g2_offline_output_profile_v1"
PRODUCTS = (
    "sixview_png",
    "island_png",
    "scene_graph",
    "spatial_metadata",
    "task_entities",
    "selection",
    "language",
    "robot_pose",
    "view_vae",
)
STATUSES = {"disabled", "absent", "reference", "pending", "failed", "ready"}


@dataclass(frozen=True)
class OutputProfile:
    sixview_png: bool = True
    island_png: bool = True
    scene_graph: bool = True
    spatial_metadata: bool = True
    task_entities: bool = True
    selection: bool = True
    language: bool = True
    robot_pose: bool = True
    view_vae: bool = False
    marker_variants: bool = True
    # No training default: a caller must choose a candidate explicitly.
    selection_top_variant: str | None = None

    def __post_init__(self):
        for key, value in asdict(self).items():
            if key != "selection_top_variant" and type(value) is not bool:
                raise ContractError("profile flags must be booleans: " + key)
        if self.selection_top_variant not in (None, "clean", "w_rbs", "both"):
            raise ContractError("unknown explicit top-variant selection")
        if self.selection and (
            not self.task_entities
            or not self.spatial_metadata
            or not (self.sixview_png or self.view_vae)
            or self.selection_top_variant is None
        ):
            raise ContractError(
                "selection requires spatial/task/RGB and explicit top variant"
            )
        if self.selection_top_variant in ("w_rbs", "both") and not self.marker_variants:
            raise ContractError("requested selected marker variant is disabled")
        if self.language and not (self.task_entities and self.scene_graph):
            raise ContractError("language requires GT task entities and current SG")
        if self.task_entities and not self.scene_graph:
            raise ContractError("GT task entities require scene graph provenance")
        if self.view_vae and not self.spatial_metadata:
            raise ContractError("VAE requires sealed spatial identity and metadata")

    @property
    def render_rgb(self):
        return self.sixview_png or self.island_png or self.view_vae

    def to_dict(self):
        value = dict(
            schema=PROFILE_SCHEMA,
            **asdict(self),
            top_semantics="CLEAN_BASE_AND_OPTIONAL_W_RBS",
            production_template_frozen=False,
        )
        value["profile_id"] = fingerprint(value)
        return value

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict):
            raise ContractError("output profile must be an object")
        fields = set(cls.__dataclass_fields__)
        if set(value) <= fields:
            return cls(**value)
        if value.get("schema") != PROFILE_SCHEMA:
            raise ContractError("unknown output profile schema")
        result = cls(**{key: value[key] for key in fields})
        if canonical(result.to_dict()) != canonical(value):
            raise ContractError("profile identity or fields differ")
        return result


def completion(profile, products, *, source_sealed, vae_receipt=None):
    """A source seal is not full completion; enqueue is never a durable receipt."""
    if not isinstance(profile, OutputProfile) or set(products) != set(PRODUCTS):
        raise ContractError("complete declared product inventory is required")
    if source_sealed is not None and not (
        isinstance(source_sealed, str) and re.fullmatch(r"[0-9a-f]{64}", source_sealed)
    ):
        raise ContractError("source seal must be a SHA256 identity or None")
    missing = []
    for name in PRODUCTS:
        status = products[name]
        if status not in STATUSES:
            raise ContractError("unknown product state")
        enabled = getattr(profile, name)
        if not enabled and status != "disabled":
            raise ContractError("disabled output must not masquerade as scene absence")
        if enabled and status == "disabled":
            raise ContractError("enabled output cannot be disabled")
        if status == "absent" and name not in ("sixview_png", "island_png"):
            raise ContractError("required structured output cannot be scene-absent")
        if enabled and status not in ("ready", "absent", "reference"):
            missing.append(name)
    if profile.view_vae:
        if (
            not isinstance(vae_receipt, dict)
            or vae_receipt.get("verified") is not True
            or vae_receipt.get("source_id") != source_sealed
            or vae_receipt.get("profile_id") != profile.to_dict()["profile_id"]
        ):
            missing.append("verified_view_vae_receipt")
    complete = bool(source_sealed) and not missing
    return dict(
        profile_complete=complete,
        training_ready=False,
        source_ready=bool(source_sealed),
        pending=sorted(set(missing)),
        # Ready means these declared artifacts only, never model acceptance.
        acceptance="DECLARED_PROFILE_ONLY_NOT_TRAINING_ACCEPTANCE",
    )
