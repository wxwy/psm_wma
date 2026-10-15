"""CPU fake native checkpointer integration; NO GPU/real checkpoint access."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v3_gateb1_dcp_transient as dcp  # noqa: E402


class Callback:
    checkpoint_component = "dataloader"

    def __init__(self, trainer):
        self.trainer = trainer

    def load_state_dict(self, state):
        self.trainer._pending_grouped_resume = state


class Checkpointer:
    def __init__(self, state, callback, path):
        self.state = state
        self.callback = callback
        self.config_checkpoint = SimpleNamespace(strict_resume=True)
        self.load_training_state = True
        self.path = path
        self.keys = set(dcp.REQUIRED_KEYS)
        self.warm_start = False
        self.result_iteration = 1300
        self.times = 0

    def keys_to_resume_during_load(self):
        return self.keys, SimpleNamespace(path=str(self.path), warm_start=self.warm_start)

    def load(self, model, optimizer, scheduler, grad_scaler):
        self.times += 1
        self.callback.load_state_dict(self.state)
        return self.result_iteration


@pytest.fixture
def fixture(tmp_path: Path, monkeypatch):
    checkpoint = tmp_path / "iter_000001300"
    checkpoint.mkdir()
    state = {"config_digest": dcp.SOURCE_DIGEST, "sidecar": {0: "source"}}
    trainer = SimpleNamespace(_pending_grouped_resume=None)
    callback = Callback(trainer)
    trainer.callbacks = SimpleNamespace(_callbacks=[callback])
    cp = Checkpointer(state, callback, checkpoint)
    calls = []

    def snapshot(*a, **kw):
        calls.append((a, kw))
        return {
            "checkpoint_fingerprint": "lightweight_fingerprint", "component_count": 4,
            "dcp_shards": 32,
            "files": (
                [{"path": f"model/{i}.distcp", "size": 1, "mtime_ns": 1} for i in range(32)]
                + [{"path": f"{x}/.metadata", "size": 1, "sha256": "a" * 64}
                   for x in ("model", "optim", "scheduler", "trainer")]
                + [{"path": f"dataloader/rank_{i}.pkl", "size": 1, "sha256": "b" * 64}
                   for i in range(8)]
            ),
        }

    def validate(x, *, rank, source_digest):
        assert x["config_digest"] == source_digest and rank == 0

    def translate(x, *, source_digest, target_digest, rank):
        assert x["config_digest"] == source_digest and rank == 0
        return {"config_digest": target_digest, "sidecar": x["sidecar"].copy()}

    monkeypatch.setattr(dcp, "snapshot_checkpoint", snapshot)
    monkeypatch.setattr(dcp, "validate_sidecar", validate)
    monkeypatch.setattr(dcp, "in_memory_target_sidecar", translate)
    monkeypatch.setattr(dcp, "unchanged_checkpoint", lambda a, b: a == b or (_ for _ in ()).throw(RuntimeError("changed")))
    return cp, trainer, callback, checkpoint, state, calls


def invoke(f, *, leg="index8", target_digest=None,
           b0_fp=dcp.B0_FULL_SHARD_FINGERPRINT):
    cp, trainer, callback, ckpt, _, _ = f
    return dcp.strict_transient_load(checkpointer=cp, trainer=trainer, model=object(), optimizer=object(),
                                     scheduler=object(), grad_scaler=object(), checkpoint_path=ckpt,
                                     leg=leg, rank=0, target_digest=target_digest,
                                     authoritative_b0_checkpoint_fingerprint=b0_fp)


def test_original_index8_native_load_no_translation(fixture):
    cp, trainer, cb, _, state, calls = fixture
    old = cb.load_state_dict
    result = invoke(fixture)
    assert trainer._pending_grouped_resume is state
    assert result["iteration"] == 1300 and result["dataloader_state_load_calls"] == 1
    assert result["checkpoint_write_authorized"] is False
    assert result["source_checkpoint_fingerprint"] == dcp.B0_FULL_SHARD_FINGERPRINT
    assert result["authoritative_b0_checkpoint_fingerprint"] == dcp.B0_FULL_SHARD_FINGERPRINT
    assert result["runtime_lightweight_immutability_witness"] == "lightweight_fingerprint"
    assert result["runtime_shard_contents_rehashed"] is False
    assert all(kw["hash_shards"] is False for _, kw in calls)
    assert cp.times == 1 and len(calls) == 2 and cb.load_state_dict == old


def test_packed128_transient_callback_only_changes_digest(fixture):
    cp, trainer, cb, _, state, _ = fixture
    old = cb.load_state_dict
    result = invoke(fixture, leg="packed128", target_digest="new_layout_digest")
    assert result["effective_config_digest"] == "new_layout_digest"
    assert trainer._pending_grouped_resume == {"config_digest": "new_layout_digest", "sidecar": {0: "source"}}
    assert state["config_digest"] == dcp.SOURCE_DIGEST
    assert cb.load_state_dict == old


def test_missing_target_digest_refused_before_load(fixture):
    with pytest.raises(dcp.TransientLoadBlocked, match="target config"):
        invoke(fixture, leg="packed128")
    assert fixture[0].times == 0


def test_warm_start_and_missing_component_rejected(fixture):
    fixture[0].warm_start = True
    with pytest.raises(dcp.TransientLoadBlocked, match="warm-start"):
        invoke(fixture)
    fixture[0].warm_start = False
    fixture[0].keys.remove("trainer")
    with pytest.raises(dcp.TransientLoadBlocked, match="four DCP components"):
        invoke(fixture)
    assert fixture[0].times == 0


def test_strict_resume_mandatory(fixture):
    fixture[0].config_checkpoint.strict_resume = False
    with pytest.raises(dcp.TransientLoadBlocked, match="strict"):
        invoke(fixture)


def test_callback_method_restored_after_dcp_exception(fixture):
    cp, _, cb, _, _, _ = fixture
    old = cb.load_state_dict

    def failed(*args):
        raise RuntimeError("native DCP load error")

    cp.load = failed
    with pytest.raises(RuntimeError, match="native DCP"):
        invoke(fixture)
    assert cb.load_state_dict == old


def test_iteration_mismatch_fails(fixture):
    fixture[0].result_iteration = 1
    with pytest.raises(dcp.TransientLoadBlocked, match="wrong iteration"):
        invoke(fixture)


def test_missing_callback_refused(fixture):
    fixture[1].callbacks._callbacks = []
    with pytest.raises(dcp.TransientLoadBlocked, match="exactly one"):
        invoke(fixture)


def test_source_path_mismatch_refused(fixture, tmp_path):
    fixture[0].path = tmp_path
    with pytest.raises(dcp.TransientLoadBlocked, match="source differs"):
        invoke(fixture)


def test_callback_never_called_must_fail(fixture):
    fixture[0].load = lambda *args: 1300
    with pytest.raises(dcp.TransientLoadBlocked, match="not invoked exactly once"):
        invoke(fixture)


def test_b0_full_shard_fingerprint_mismatch_fails_before_any_checkpoint_read(fixture):
    with pytest.raises(dcp.TransientLoadBlocked, match="B0 original full-shard"):
        invoke(fixture, b0_fp="0" * 64)
    assert fixture[0].times == 0 and not fixture[-1]


def test_lightweight_witness_mutation_aborts_after_native_load(fixture, monkeypatch):
    original = dcp.snapshot_checkpoint
    calls = [0]

    def altered(path, *, hash_shards):
        assert hash_shards is False
        result = original(path, hash_shards=hash_shards)
        calls[0] += 1
        if calls[0] == 2:
            result["files"][0]["mtime_ns"] += 1
        return result

    monkeypatch.setattr(dcp, "snapshot_checkpoint", altered)
    cb = fixture[2]
    callback_before = cb.load_state_dict
    with pytest.raises(RuntimeError, match="changed"):
        invoke(fixture)
    assert cb.load_state_dict == callback_before
    assert fixture[0].times == 1 and calls[0] == 2


def test_actual_B0_snapshot_does_not_read_shard_bodies(tmp_path, monkeypatch):
    import v3_packed128_gateb_compare as b0

    checkpoint = tmp_path / "iter_000001300"
    for component in b0.COMPONENTS:
        folder = checkpoint / component
        folder.mkdir(parents=True)
        (folder / ".metadata").write_bytes(b"tiny metadata")
        for i in range(8):
            (folder / f"{i}.distcp").write_bytes(b"fake shard")
    dataloader = checkpoint / "dataloader"
    dataloader.mkdir()
    for i in range(8):
        (dataloader / f"rank_{i}.pkl").write_bytes(b"fake sidecar")

    original_hash = b0.sha256_file
    recorded = []

    def checked_hash(path):
        assert path.suffix != ".distcp", "full DCP shard content hash forbidden"
        recorded.append(path)
        return original_hash(path)

    monkeypatch.setattr(b0, "sha256_file", checked_hash)
    before = dcp._lightweight_immutability_snapshot(checkpoint)
    after = dcp._lightweight_immutability_snapshot(checkpoint)
    assert before == after
    assert before["dcp_shards"] == 32
    assert len(recorded) == 24  # 4 metadata + 8 sidecars per snapshot, twice
    assert all(item.get("sha256") is None for item in before["files"]
               if item["path"].endswith(".distcp"))
    assert all("mtime_ns" in item for item in before["files"]
               if item["path"].endswith(".distcp"))
