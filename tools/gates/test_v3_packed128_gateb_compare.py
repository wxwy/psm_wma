"""CPU-only B0 fixtures. Does NOT claim FSDP8/GPU numerical equivalence."""

from __future__ import annotations

import copy
import json
import random
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v3_packed128_gateb_compare as gate  # noqa: E402
from v3_gateb_numerics import compare_selected_gradient  # noqa: E402


@dataclass(frozen=True)
class SegmentIdentity:
    slot_id: int
    episode_id: str
    source_digest: str
    segment_id: int


@dataclass(frozen=True)
class SegmentProvenance:
    manifest_digest: str
    config_digest: str
    source_digest: str
    segment_id: int


@dataclass(frozen=True)
class ExactWindowSlotFrontier:
    uid: str | None = None


@dataclass(frozen=True)
class ExactWindowCatalogFrontier:
    epoch: int
    slots: tuple[ExactWindowSlotFrontier, ...]


def _source_state(rank: int = 0) -> dict:
    slot = rank * 8
    identity = SegmentIdentity(slot, "task/episode_0", "src-ep", 8)
    fast = tuple(torch.ones(1, 2, dtype=torch.float32) for _ in range(4))
    return {
        "format": gate.SIDECAR_FORMAT,
        "iteration": 1300,
        "cache_manifest_sha256": "manifest123",
        "cache_corpus_digest": "corpus123",
        "source_binding_digest": "binding123",
        "config_digest": gate.SOURCE_DIGEST,
        "profile": (rank, 8, 0, 8, 2, 96, 15, 256, 64, 256, 32, 4, 16, 0.1, 64, 16, 17),
        "frontier": ExactWindowCatalogFrontier(1, tuple(ExactWindowSlotFrontier() for _ in range(8))),
        "scheduler": {slot + i: SegmentIdentity(slot + i, "task/episode_0", "src-ep", 8) for i in range(8)},
        "sidecar": {slot: (identity,
                           SegmentProvenance("manifest123", gate.SOURCE_DIGEST, "src-ep", 8), fast)},
    }


def _key(slot: int = 3, t: int = 12) -> gate.ConsumerKey:
    return gate.ConsumerKey("source-fp", 0, 1300, 0, slot, "episode_a", "source-ep", 1, 9, 8, t)


def test_stable_seed_independent_of_key_order():
    key = _key().scoped("epsilon", "vision", 0)
    assert gate.stable_seed(key, domain="vision") == gate.stable_seed(dict(reversed(list(key.items()))), domain="vision")
    assert gate.stable_seed(key, domain="action") != gate.stable_seed(key, domain="vision")
    assert gate.stable_seed(_key(slot=4).scoped("epsilon", "vision"), domain="vision") != gate.stable_seed(key, domain="vision")


def test_scoped_python_cfg_reproducible_and_does_not_consume_global():
    random.seed(88)
    previous = random.getstate()
    with gate.scoped_python_cfg_rng(_key()):
        first = random.random()
    assert random.getstate() == previous
    with gate.scoped_python_cfg_rng(_key()):
        assert random.random() == first
    assert random.getstate() == previous


def test_scoped_python_cfg_restores_on_exception():
    before = random.getstate()
    with pytest.raises(RuntimeError, match="trial"):
        with gate.scoped_python_cfg_rng(_key()):
            random.random()
            raise RuntimeError("trial")
    assert random.getstate() == before


def test_cpu_witness_p0_and_p1_epsilon():
    key = _key()
    p0 = gate.deterministic_witness_cpu(key, profile="P0", site="sigma", modality="vision", shape=(1,))
    assert torch.equal(p0, torch.tensor([0.5]))
    x = gate.deterministic_witness_cpu(key, profile="P1", site="epsilon", modality="vision", shape=(3, 4))
    y = gate.deterministic_witness_cpu(key, profile="P1", site="epsilon", modality="vision", shape=(3, 4))
    assert torch.equal(x, y)
    assert not torch.equal(x, gate.deterministic_witness_cpu(_key(slot=4), profile="P1", site="epsilon", modality="vision", shape=(3, 4)))
    with pytest.raises(gate.Blocked, match="production shift/sampler"):
        gate.deterministic_witness_cpu(key, profile="P1", site="sigma", modality="vision", shape=(1,))


def test_sidecar_schema_and_in_memory_clone_preserve_source():
    state = _source_state()
    evidence = gate.validate_sidecar(state, rank=0, source_digest=gate.SOURCE_DIGEST)
    assert evidence["profile"][0] == 0 and evidence["active_records"] == 1
    state_copy = copy.deepcopy(state)
    newer = gate.in_memory_target_sidecar(state, source_digest=gate.SOURCE_DIGEST,
                                          target_digest="new-packed-digest", rank=0)
    assert newer["config_digest"] == "new-packed-digest"
    assert newer["sidecar"][0][1].config_digest == "new-packed-digest"
    assert state["config_digest"] == gate.SOURCE_DIGEST
    assert state["sidecar"][0][1].config_digest == state_copy["sidecar"][0][1].config_digest
    assert newer["sidecar"][0][2][0].data_ptr() != state["sidecar"][0][2][0].data_ptr()
    assert set(newer) == gate.SIDECAR_KEYS


@pytest.mark.parametrize("field", ["unknown", "config_digest", "profile", "scheduler", "sidecar"])
def test_sidecar_negative_schema(field):
    state = _source_state()
    if field == "unknown":
        state["migration_source"] = "forbidden"
    elif field == "config_digest":
        state[field] = "incorrect"
    elif field == "profile":
        state[field] = state[field][1:]
    elif field == "scheduler":
        state[field] = {0: state[field][0]}
        del state[field][0]
    else:
        identity, prov, fast = state["sidecar"][0]
        state["sidecar"][0] = (identity, replace(prov, config_digest="old-nested"), fast)
    with pytest.raises(gate.Blocked):
        gate.validate_sidecar(state, rank=0, source_digest=gate.SOURCE_DIGEST)


def test_nonfinite_fast_fails():
    state = _source_state()
    identity, prov, fast = state["sidecar"][0]
    state["sidecar"][0] = (identity, prov, (torch.tensor([float("nan")]), *fast[1:]))
    with pytest.raises(gate.Blocked, match="finite"):
        gate.validate_sidecar(state, rank=0, source_digest=gate.SOURCE_DIGEST)


def test_no_equal_digest_translation():
    with pytest.raises(gate.Blocked, match="distinct digest"):
        gate.in_memory_target_sidecar(_source_state(), source_digest=gate.SOURCE_DIGEST,
                                      target_digest=gate.SOURCE_DIGEST, rank=0)


def test_file_fingerprints_and_immutable_guard(tmp_path):
    src = tmp_path / "iter_000001300"
    for comp in gate.COMPONENTS:
        (src / comp).mkdir(parents=True)
        (src / comp / ".metadata").write_bytes(b"metadata")
        for i in range(8):
            (src / comp / f"__{i}_0.distcp").write_bytes(f"{comp}:{i}".encode())
    (src / "dataloader").mkdir()
    for rank in range(8):
        (src / "dataloader" / f"rank_{rank}.pkl").write_bytes(b"fixture")
    before = gate.snapshot_checkpoint(src, hash_shards=True)
    assert before["dcp_shards"] == 32
    assert gate.snapshot_checkpoint(src, hash_shards=True) == before
    (src / "dataloader/rank_7.pkl").write_bytes(b"changed")
    with pytest.raises(gate.Blocked, match="changed"):
        gate.unchanged_checkpoint(before, gate.snapshot_checkpoint(src, hash_shards=True))


def test_output_must_be_new_isolated_tmp_dir(tmp_path):
    with pytest.raises(gate.Blocked):
        gate._restricted_output_dir(tmp_path / "output", tmp_path, tmp_path, tmp_path)
    with pytest.raises(gate.Blocked):
        gate._restricted_output_dir(Path("/tmp"), tmp_path, tmp_path, tmp_path)


def test_paired_gpu_is_not_executable():
    assert gate.main(["--mode", "paired-run"]) == 2


def test_numerics_normal_and_near_zero():
    vec = torch.linspace(-1.0, 1.0, 100, dtype=torch.float32)
    assert compare_selected_gradient(vec, vec).passed
    a = compare_selected_gradient(torch.zeros(3), torch.zeros(3))
    assert a.passed and a.cosine is None and a.near_zero
    assert not compare_selected_gradient(torch.zeros(3), torch.ones(3)).passed
    with pytest.raises(ValueError, match="nonfinite"):
        compare_selected_gradient(torch.ones(3), torch.tensor([1., float("inf"), 1.]))
    with pytest.raises(ValueError, match="missing"):
        compare_selected_gradient(torch.ones(3), None)
    with pytest.raises(ValueError, match="shape/dtype"):
        compare_selected_gradient(torch.ones(3), torch.ones(4))


def test_numeric_errors_not_hidden_by_tensor_average():
    a = torch.ones(300, dtype=torch.float32)
    b = a.clone()
    b[-1] = 2
    assert not compare_selected_gradient(a, b).passed

@dataclass(frozen=True)
class FakeConsumerIdentity:
    slot_id: int
    episode_id: str
    source_digest: str
    segment_id: int
    cursor: int


@dataclass(frozen=True)
class FakeRequest:
    identity: FakeConsumerIdentity
    binding_epoch: int
    valid_count: int


@dataclass(frozen=True)
class FakePlan:
    members: tuple
    member_counts: tuple
    candidate_frontier: int

    @property
    def n_window(self):
        return sum(self.member_counts)


class FakePlanner:
    def __init__(self, rank: int, partial: bool = False, all_short: bool = False):
        self.rank, self.partial, self.all_short = rank, partial, all_short

    def validate_frontier(self, frontier):
        assert frontier in (0, 1)

    def plan_window(self, frontier):
        members = []
        counts = []
        for ga in range(2):
            requests = []
            for slot in range(8):
                count = 16
                if self.all_short and self.rank == 7:
                    count = 4
                elif self.partial and self.rank == 0 and ga == 1 and slot == 7:
                    count = 5
                requests.append(FakeRequest(FakeConsumerIdentity(self.rank * 8 + slot,
                                      f"episode_{self.rank}_{slot}_{frontier}", "episode-source", 9 + frontier, frontier),
                                      1, count))
            members.append(tuple(requests))
            counts.append(sum(req.valid_count for req in requests))
        return FakePlan(tuple(members), tuple(counts), frontier + 1)


def test_8rank_two_windows_full_member_plan():
    planners = [FakePlanner(r) for r in range(8)]
    states = [{"frontier": 0} for _ in range(8)]
    out = gate._frozen_manifest_from_plans(planners, states, checkpoint_fp="old1300")
    assert len(out["rows"]) == 16
    assert not out["terminal_partial_present"]
    assert all(row["member_counts"] == [128, 128] and row["n_window"] == 256 for row in out["rows"])
    assert out["rows"][0]["consumers"][0]["slot_id"] == 0
    assert out["rows"][15]["consumers"][0]["slot_id"] == 56


def test_terminal_partial_retained_with_no_padding():
    out = gate._frozen_manifest_from_plans([FakePlanner(r, partial=True) for r in range(8)],
                                            [{"frontier": 0} for _ in range(8)], checkpoint_fp="old1300")
    assert out["terminal_partial_present"]
    assert out["rows"][0]["n_window"] == 245
    assert out["rows"][0]["member_counts"] == [128, 117]
    assert out["rows"][0]["consumer_count"] == 245
    assert out["rows"][0]["index8_active_indices"][0] == list(range(16))
    assert out["rows"][0]["consumers"][-1]["absolute_step"] == 4
    # With 7 full rows and one partial (5 frames), second member has 117.
    assert out["rows"][1]["member_counts"] == [128, 117]
    assert out["rows"][1]["n_window"] == 245


def test_fsdp_rhythm_guard_on_rank_shortfall():
    with pytest.raises(gate.Blocked, match="FSDP collective rhythm unsafe"):
        gate._frozen_manifest_from_plans([FakePlanner(r, all_short=True) for r in range(8)],
                                         [{"frontier": 0} for _ in range(8)], checkpoint_fp="old1300")


def test_cpu_report_parity_and_tampered_consumer_detection(tmp_path):
    rows = gate._frozen_manifest_from_plans([FakePlanner(r) for r in range(8)],
                                            [{"frontier": 0} for _ in range(8)], checkpoint_fp="old1300")
    a = {"schema": gate.REPORT_SCHEMA, "leg": "index8", "pair": {"root": gate.SOURCE_ROOT},
         "checkpoint": {"checkpoint_fingerprint": "same-dcp"},
         "source_digest": gate.SOURCE_DIGEST, "resolved_digest": gate.SOURCE_DIGEST, "plan": rows}
    b = copy.deepcopy(a)
    b["leg"] = "packed128"
    b["pair"]["root"] = gate.PACKED_ROOT
    b["resolved_digest"] = "new-packed-digest"
    p, q = tmp_path / "source.json", tmp_path / "target.json"
    p.write_text(json.dumps(a))
    q.write_text(json.dumps(b))
    assert gate.compare_cpu_reports(p, q)["status"] == "CPU_PLAN_PARITY_ONLY"
    b["plan"]["rows"][0]["consumers"][0]["episode_uid"] = "tampered"
    q.write_text(json.dumps(b))
    with pytest.raises(gate.Blocked, match="consumer window plan"):
        gate.compare_cpu_reports(p, q)


def test_tqdm_monitor_disabled_before_progress_bar_and_restored():
    from tqdm.std import tqdm
    before = tqdm.monitor_interval
    try:
        with gate.scoped_disable_tqdm_monitor():
            assert tqdm.monitor_interval == 0
            with tqdm(total=1, disable=True):
                with gate.scoped_python_cfg_rng(_key()):
                    assert 0.0 <= random.random() < 1.0
        assert tqdm.monitor_interval == before
    finally:
        tqdm.monitor_interval = before


def test_preexisting_unrecognized_background_thread_rejected():
    import threading
    started = threading.Event()
    stop = threading.Event()

    def background():
        started.set()
        stop.wait(5)

    thread = threading.Thread(target=background, daemon=True)
    thread.start()
    assert started.wait(2)
    try:
        with pytest.raises(gate.Blocked, match="preflight requires one Python main thread"):
            with gate.scoped_disable_tqdm_monitor():
                pass
        with pytest.raises(gate.Blocked, match="CFG global RNG scope"):
            with gate.scoped_python_cfg_rng(_key()):
                pass
    finally:
        stop.set()
        thread.join(2)
    assert not thread.is_alive()


def test_tqdm_interval_restored_on_failure():
    from tqdm.std import tqdm
    before = tqdm.monitor_interval
    with pytest.raises(ValueError, match="intentional"):
        with gate.scoped_disable_tqdm_monitor():
            raise ValueError("intentional")
    assert tqdm.monitor_interval == before


def test_tqdm_thread_map_does_not_leave_tmonitor_during_cfg_scope():
    import threading
    from tqdm.contrib.concurrent import thread_map

    with gate.scoped_disable_tqdm_monitor():
        assert thread_map(lambda number: number * 2, range(4), max_workers=2, disable=True) == [0, 2, 4, 6]
        assert threading.active_count() == 1
        with gate.scoped_python_cfg_rng(_key()):
            assert 0 <= random.random() <= 1


def test_native_payload_hash_supports_frozen_action_record_and_mutable_sequence_plan():
    @dataclass(frozen=True)
    class ActionProcessingRecord:
        raw_action_dim: int
        action_normalizer: object | None = None
        action_valid_mask: object | None = None
        action_codec: object | None = None

    @dataclass
    class SequencePlan:
        has_text: bool = True
        text_view_ids: list[int] | None = None
        has_vision: bool = True
        condition_frame_indexes_vision: list[int] | None = None

    def payload():
        return {"action_processing_record": ActionProcessingRecord(15),
                "sequence_plan": SequencePlan(condition_frame_indexes_vision=[0]),
                "action_raw": torch.arange(15, dtype=torch.float32).reshape(1, 15),
                "cached_latent_required": True}

    fingerprint = gate._stable_payload_hash(payload())
    assert fingerprint == gate._stable_payload_hash(payload())
    assert len(fingerprint) == 64
    updated = payload()
    updated["action_processing_record"] = ActionProcessingRecord(14)
    assert gate._stable_payload_hash(updated) != fingerprint
    updated = payload()
    updated["sequence_plan"].condition_frame_indexes_vision.append(1)
    assert gate._stable_payload_hash(updated) != fingerprint
    updated = payload()
    updated["action_raw"][0, -1] = 999.0
    assert gate._stable_payload_hash(updated) != fingerprint


def test_native_payload_hash_distinguishes_dataclass_type_and_dict_order():
    @dataclass
    class PlanA:
        flag: bool

    @dataclass
    class PlanB:
        flag: bool

    assert gate._stable_payload_hash(PlanA(True)) != gate._stable_payload_hash(PlanB(True))
    assert gate._stable_payload_hash({"z": 3, "a": PlanA(True)}) == (
        gate._stable_payload_hash({"a": PlanA(True), "z": 3})
    )


def test_native_payload_hash_nested_unknown_leaf_and_class_fail_closed():
    @dataclass(frozen=True)
    class ActionProcessingRecord:
        raw_action_dim: int
        action_codec: object

    with pytest.raises(gate.Blocked, match="unhandled Native payload leaf type"):
        gate._stable_payload_hash({"record": ActionProcessingRecord(15, object())})
    with pytest.raises(gate.Blocked, match="unhandled Native payload leaf type"):
        gate._stable_payload_hash(object())
    with pytest.raises(gate.Blocked, match="unhandled Native payload leaf type"):
        gate._stable_payload_hash(ActionProcessingRecord)


def test_native_payload_hash_detects_dataclass_and_list_cycles():
    @dataclass
    class SequencePlan:
        nested: object = None

    record = SequencePlan()
    record.nested = record
    with pytest.raises(gate.Blocked, match="cyclic Native payload"):
        gate._stable_payload_hash(record)
    nested = []
    nested.append(nested)
    with pytest.raises(gate.Blocked, match="cyclic Native payload"):
        gate._stable_payload_hash(nested)


def test_native_payload_hash_rejects_nonfinite_dataclass_scalar():
    @dataclass(frozen=True)
    class SequencePlan:
        noisy: float

    with pytest.raises(ValueError, match="Out of range float values"):
        gate._stable_payload_hash(SequencePlan(float("nan")))
