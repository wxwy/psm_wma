"""Independent scoped peer probes; only CPU FakeEncoder/temporary fixtures."""

import multiprocessing as mp

import pytest

from g2.io import digest, read_json, write_json
from g2.latent_cache.contract import CacheError, fingerprint
from g2.latent_cache.posthoc import retire_view_first_cache
from g2.latent_cache.storage import open_episode_index
from g2.latent_cache.streaming import EventSpool
from g2.offline.view_only_source import PACKED, RECEIPT
from g2.tests.test_view_first_retirement import encode_case, retirement_case


@pytest.mark.parametrize("kind", ["receipt", "tensor"])
def test_corruption_after_real_cache_handoff_cannot_retire_gzip(tmp_path, kind):
    root, policy = retirement_case(tmp_path)
    encode_case(tmp_path, root)
    original = (root / PACKED).read_bytes()
    if kind == "receipt":
        doc = read_json(root / RECEIPT)
        doc["source_id"] = "0" * 64
        doc["receipt_id"] = fingerprint({k: v for k, v in doc.items() if k != "receipt_id"})
        write_json(root / RECEIPT, doc)
    else:
        path = next((root / "vae_cache").rglob("*.pt"))
        path.write_bytes(b"TEST_ONLY_CORRUPTED_NUMERICAL_PAYLOAD")
    with pytest.raises((OSError, ValueError, RuntimeError, EOFError)):
        retire_view_first_cache(root, spool_root=policy["spool_root"], source_policy=policy)
    assert (root / PACKED).read_bytes() == original
    assert not (root / "spatial_source_index.json").exists()
    assert not (root / "spatial_source.json").exists()


def test_retired_gzip_claim_stays_bound_when_receipt_completion_are_rehashed(tmp_path):
    root, policy = retirement_case(tmp_path)
    encode_case(tmp_path, root)
    assert retire_view_first_cache(root, spool_root=policy["spool_root"], source_policy=policy)["complete"]
    receipt = read_json(root / "SOURCE_RETIREMENT.json")
    assert set(receipt["retired_files"]) == {PACKED, RECEIPT, "SPATIAL_SOURCE_READY.json"}
    receipt["retired_files"][PACKED] = "0" * 64
    write_json(root / "SOURCE_RETIREMENT.json", receipt)
    complete = read_json(root / "COMPLETE.json")
    complete["source_retirement_sha256"] = digest(root / "SOURCE_RETIREMENT.json")
    write_json(root / "COMPLETE.json", complete)
    with pytest.raises(CacheError, match="provenance"):
        open_episode_index(root)


def retire_worker(root, policy, start, result):
    start.wait()
    try:
        r = retire_view_first_cache(root, spool_root=policy["spool_root"], source_policy=policy)
        result.put(("complete", bool(r["complete"])))
    except CacheError as exc:
        result.put(("blocked" if isinstance(exc.__cause__, BlockingIOError) else "error", str(exc)))


def test_two_processes_exclude_writers_and_resume_without_fake_events(tmp_path):
    root, policy = retirement_case(tmp_path)
    encode_case(tmp_path, root)
    payloads = {p: digest(p) for p in (root / "vae_cache").rglob("*.pt")}
    ctx = mp.get_context("fork")
    start, result = ctx.Event(), ctx.Queue()
    workers = [ctx.Process(target=retire_worker, args=(root, policy, start, result)) for _ in range(2)]
    for worker in workers:
        worker.start()
    start.set()
    for worker in workers:
        worker.join(30)
        assert worker.exitcode == 0
    outcomes = [result.get(timeout=3) for _ in workers]
    assert all(row[0] in ("complete", "blocked") for row in outcomes), outcomes
    assert any(row == ("complete", True) for row in outcomes), outcomes
    assert retire_view_first_cache(root, spool_root=policy["spool_root"], source_policy=policy)["complete"]
    assert not (root / PACKED).exists() and not (root / "spatial_source.json").exists()
    assert {p: digest(p) for p in payloads} == payloads
    open_episode_index(root)
    spool = EventSpool.open(policy["spool_root"])
    with spool._db() as db:
        assert db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM completed").fetchone()[0] == 1
