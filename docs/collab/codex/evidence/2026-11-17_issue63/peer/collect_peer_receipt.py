"""Read-only standard-library evidence collection for the local peer review."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
OUT = Path(__file__).resolve().parent
FORMAL = "98172110677b7631f5b7974003ffae664bdd0b85"
CHILD = "d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2"
PROBE_TEMP = Path("/tmp/g2_issue63_peer_protocol_98172110")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def read(path):
    return json.loads(path.read_text())


def main():
    source_hashes = read(OUT.parent / "revision1/source_after.json")
    source_mismatches = []
    blob_mismatches = []
    for rel, expected in source_hashes.items():
        if sha((ROOT / rel).read_bytes()) != expected:
            source_mismatches.append(rel)
        blob = subprocess.check_output(["git", "show", FORMAL + ":" + rel], cwd=ROOT)
        if sha(blob) != expected:
            blob_mismatches.append(rel)
    assert not source_mismatches and not blob_mismatches
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == FORMAL
    assert subprocess.check_output(["git", "ls-tree", FORMAL, "cosmos-framework"], cwd=ROOT, text=True).split()[2] == CHILD
    observations = []
    for directory in sorted(PROBE_TEMP.glob("test_final_receipt_cannot_disa[0-9]*")):
        if directory.is_symlink():
            continue
        tombstones = list((directory / "spool/completed").rglob("*.json"))
        assert len(tombstones) == 1
        record = read(tombstones[0])
        target = Path(record["job"]["target"])
        capsule = read(target / "spatial_source_index.json")
        receipt = read(target / "SOURCE_RETIREMENT.json")
        bound = json.loads(record["job"]["retirement"])
        with sqlite3.connect((directory / "spool/events.sqlite").as_uri() + "?mode=ro", uri=True) as db:
            jobs = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            completed = db.execute("SELECT COUNT(*) FROM completed").fetchone()[0]
        observations.append(dict(
            fixture=str(directory),
            exact_sql_bound_capsule_unchanged=bound["capsule_sha256"] == sha((target / "spatial_source_index.json").read_bytes()),
            working_proof_matches_attestation=canonical_sha(receipt["working_proof"]) == capsule["attestation"]["working_proof_sha256"],
            work_cleanup_matches_attestation=canonical_sha(receipt["work_cleanup"]) == capsule["attestation"]["work_cleanup_sha256"],
            retired_full_hash_matches_working_source=receipt["retired_files"]["spatial_source.json"] == capsule["working_source"]["manifest_sha256"],
            active_jobs=jobs,
            completed_jobs=completed,
        ))
    assert len(observations) == 3
    assert all(o["exact_sql_bound_capsule_unchanged"] and o["active_jobs"] == 0 and o["completed_jobs"] == 1 for o in observations)
    junit = {}
    for name in ("focused", "focused2", "independent"):
        suite = ET.parse(OUT / (name + ".xml")).getroot().find("testsuite")
        junit[name] = {key: int(suite.attrib[key]) for key in ("tests", "failures", "errors", "skipped")}
    files = {}
    for name in ("test_independent_protocol.py", "focused.log", "focused.xml", "focused2.log", "focused2.xml", "independent.log", "independent.xml", "collect_peer_receipt.py"):
        files[name] = sha((OUT / name).read_bytes())
    value = dict(
        formal_root=FORMAL,
        child_gitlink=CHILD,
        nav_sha="70eb7b447e65d793b0ebe18b258291ce46f057c1",
        python=sys.executable,
        source_count=len(source_hashes),
        live_sources_match_author_hashes=True,
        source_hashes_match_fixed_git_blobs=True,
        junit=junit,
        coordinated_mutation_observations=observations,
        evidence_sha256=files,
        verdict="LOCAL_REQUEST_CHANGES",
        findings=["P2-63-PEER-1"],
        gpt_server_or_capacity_approval=False,
    )
    path = OUT / "receipt.json"
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
