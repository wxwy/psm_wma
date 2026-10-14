"""B1 exact iter1300 *same-job* DCP source binding, read-only and scoped.

Official Checkpointer keys_to_resume_during_load() treats an explicit load_path
without a same-job latest pointer as *warm start*, even when
load_training_state=True. Gate B1 may NOT create or alter the formal latest
pointer. Temporarily override only this Checkpointer instance's source selector
with the official _same_job_load_source(checkpoint_path) result, and refuse any
checkpoint writes. Both method overrides are restored in finally.

This module is an isolated diagnostic tool, not a Cosmos training code patch.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from types import MethodType
from typing import Any, Iterator


class SameJobBlocked(RuntimeError):
    """The original exact full-state same-job resume identity was not established."""


REQUIRED = frozenset({"model", "optim", "scheduler", "trainer", "dataloader"})


@contextmanager
def exact_readonly_same_job_source(checkpointer: Any, checkpoint_dir: Path) -> Iterator[dict[str, str]]:
    """Scope official DCP source to immutable original iter1300 without latest writes.

    Must remain active for both require_dcp_grouped_resume_component and
    strict_transient_load; never call Trainer.train() or Checkpointer.save().
    """
    if checkpoint_dir.name != "iter_000001300":
        raise SameJobBlocked("only original iter1300 is accepted")
    resolved = checkpoint_dir.resolve(strict=True)
    if not resolved.is_dir():
        raise SameJobBlocked("checkpoint path must be a directory")
    if not callable(getattr(checkpointer, "_same_job_load_source", None)):
        raise SameJobBlocked("official checkpointer lacks same-job source constructor")
    if not callable(getattr(checkpointer, "keys_to_resume_during_load", None)):
        raise SameJobBlocked("official checkpointer lacks keys_to_resume_during_load")
    if not callable(getattr(checkpointer, "save", None)):
        raise SameJobBlocked("official checkpointer save must exist for fail-closed guard")
    config = getattr(checkpointer, "config_checkpoint", None)
    if (
        config is None
        or getattr(config, "strict_resume", None) is not True
        or getattr(config, "load_training_state", None) is not True
        or getattr(checkpointer, "load_training_state", None) is not True
        or getattr(config, "load_ema_to_reg", False)
    ):
        raise SameJobBlocked("strict complete training-state resume required (no EMA copy)")
    if getattr(checkpointer, "save_to_object_store", False):
        raise SameJobBlocked("B1 snapshot source must be local, not an object-store job")

    # Original checkpoint must have all four DCP components + rank sidecars;
    # check only these small paths, never scan data/cache files.
    for item in REQUIRED:
        if not (resolved / item).is_dir():
            raise SameJobBlocked(f"original DCP missing component {item}")
    factory = checkpointer._same_job_load_source
    source = factory(str(resolved))
    if (
        getattr(source, "warm_start", None) is not False
        or getattr(source, "backend_key", "unexpected") is not None
        or Path(getattr(source, "path", "")).resolve(strict=True) != resolved
    ):
        raise SameJobBlocked("official source is not exact local same-job")

    records = {
        name: (name in vars(checkpointer), vars(checkpointer).get(name))
        for name in ("keys_to_resume_during_load", "save")
    }

    def bound_selection(_self: Any):
        return set(REQUIRED), source

    def blocked_save(_self: Any, *args: Any, **kwargs: Any):
        raise SameJobBlocked("checkpoint SAVE forbidden in Gate B1 transient runner")

    try:
        checkpointer.keys_to_resume_during_load = MethodType(bound_selection, checkpointer)
        checkpointer.save = MethodType(blocked_save, checkpointer)
        yield {"checkpoint": str(resolved), "source_kind": "same-job-transient", "checkpoint_write_allowed": "false"}
    finally:
        for name, (had_instance, original) in records.items():
            if had_instance:
                setattr(checkpointer, name, original)
            else:
                vars(checkpointer).pop(name, None)
