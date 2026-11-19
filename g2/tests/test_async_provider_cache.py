"""G2 B8 DATA_C LRU throughput and worker-cache isolation (CPU only)."""

from collections import OrderedDict

from g2.data.aligned_provider import CandidateAlignedG2Provider, _EpisodeData


def test_b8_episode_cache_does_not_reopen_every_slot():
    assert CandidateAlignedG2Provider._episode_cache_size == 4
    counts = []
    narrow = _EpisodeData(
        {index: index for index in range(8)},
        lambda index: counts.append(index) or index,
        4,
    )
    for _ in range(16):
        for ep in range(8):
            assert narrow[ep] == ep
    assert len(counts) == 128

    counts.clear()
    realistic = _EpisodeData(
        {index: index for index in range(8)},
        lambda index: counts.append(index) or index,
        16,
    )
    for _ in range(16):
        for ep in range(8):
            assert realistic[ep] == ep
    assert len(counts) == 8


def test_fork_for_worker_has_independent_bound_loader_and_lrus(monkeypatch):
    visited = []

    def load(self, row):
        visited.append((id(self), row))
        return row * 2

    monkeypatch.setattr(CandidateAlignedG2Provider, "_load_episode", load)
    main = object.__new__(CandidateAlignedG2Provider)
    main.identity = "immutable-data-authority"
    main.corpus = {"identity": main.identity}
    main._language_bindings = {("task", 1): ("sha",)}
    main.data = _EpisodeData({0: 0, 1: 1}, main._load_episode, main._episode_cache_size)
    main._views = OrderedDict({("task", 1): "live reader handle"})
    main._language = OrderedDict({("task", 1): "live language record"})
    main.view_read_count = 3

    worker_a = main.fork_for_worker()
    worker_b = main.fork_for_worker()
    assert worker_a is not worker_b and main is not worker_a
    assert worker_a.data is not worker_b.data and main.data is not worker_a.data
    assert worker_a.data.rows is worker_b.data.rows is main.data.rows
    assert worker_a.corpus is worker_b.corpus is main.corpus
    assert (
        worker_a._language_bindings
        is worker_b._language_bindings
        is main._language_bindings
    )
    assert worker_a._views == worker_b._views == OrderedDict()
    assert worker_a._language == worker_b._language == OrderedDict()
    assert main._views and main._language
    assert worker_a.view_read_count == worker_b.view_read_count == 0

    assert worker_a.data[0] == 0
    assert worker_b.data[1] == 2
    assert visited == [(id(worker_a), 0), (id(worker_b), 1)]
    assert main.data.cache == {}
    assert list(worker_a.data.cache) == [0]
    assert list(worker_b.data.cache) == [1]


def test_speculative_witnesses_preserve_cached_identity_and_detect_conflict(tmp_path):
    import pytest

    from g2.data.episode_state import file_identity
    from g2.data.joint_index import DataCError

    source = tmp_path / "state15.pt"
    source.write_bytes(b"original")
    original = file_identity(source)
    p = object.__new__(CandidateAlignedG2Provider)
    with p.capture_prefetch_witnesses() as packet:
        p._record_prefetch_witnesses({source: original})
        assert packet == {source: original}
        replacement = tmp_path / "replacement.pt"
        replacement.write_bytes(b"replaced")
        replacement.replace(source)
        with pytest.raises(DataCError, match="version changed"):
            p._record_prefetch_witnesses({source: file_identity(source)})
    assert p._prefetch_witnesses is None
