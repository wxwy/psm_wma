"""Read-only standard-library binding of the Issue63 narrow peer closure."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[6]
FORMAL = "a169fea07016b80b3639646cc9925ac70b6525a8"
REJECTED = "98172110677b7631f5b7974003ffae664bdd0b85"
CHILD = "d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2"
FIXTURES = Path("/tmp/g2_issue63_peer_closure_a169fea0")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    sources = read(OUT.parent / "revision2/source_after.json")
    assert sources == read(OUT.parent / "revision2/source_before.json")
    for rel, expected in sources.items():
        assert sha((ROOT / rel).read_bytes()) == expected, rel
        assert sha(subprocess.check_output(["git", "show", FORMAL + ":" + rel], cwd=ROOT)) == expected, rel
    implementation = read(OUT.parent / "revision2/implementation_scope.json")
    assert implementation["formal_root"] == FORMAL
    assert implementation["source_sha256"] == sources
    assert subprocess.check_output(["git", "ls-tree", FORMAL, "cosmos-framework"], cwd=ROOT, text=True).split()[2] == CHILD
    narrow = subprocess.check_output(["git", "diff", "--name-only", REJECTED, FORMAL, "--", "g2", "tools", "scripts", "cosmos-framework"], cwd=ROOT, text=True).splitlines()
    assert narrow == ["g2/latent_cache/final_source.py", "g2/tests/test_source_retirement_faults.py"]
    old = OUT.parent / "peer"
    expected_preserved = {
        "test_independent_protocol.py": "cbc86a7b29e529fd5ace678fe5a10a78303aaefe25d71e470c23df2959883a1f",
        "REPORT.md": "76683dfc686620e2b11aebe3933fb837418af938e53bc1e6acc54812f4589861",
        "independent.log": "eb876165d764bf4982a489cf24507322fa796fc1c9b3c0636d30bfc2c9fbd4b8",
        "receipt.json": "1c9ddc7cad0c55a3170c7cc1ddfc3f6f98e077b213b4c1b52018f44e326614ad",
    }
    for name, expected in expected_preserved.items():
        assert sha((old / name).read_bytes()) == expected, name
    old_receipt = read(old / "receipt.json")
    for name, expected in old_receipt["evidence_sha256"].items():
        assert sha((old / name).read_bytes()) == expected, name
    suite = ET.parse(OUT / "probe.xml").getroot().find("testsuite")
    junit = {k: int(suite.attrib[k]) for k in ("tests", "failures", "errors", "skipped")}
    assert junit == dict(tests=5, failures=0, errors=0, skipped=0)
    observations = []
    for directory in sorted(FIXTURES.glob("test_final_receipt_cannot_disa[0-9]*")):
        if directory.is_symlink():
            continue
        with sqlite3.connect((directory / "spool/events.sqlite").as_uri() + "?mode=ro", uri=True) as db:
            active = db.execute("SELECT retirement,target FROM jobs").fetchall()
            completed = db.execute("SELECT COUNT(*) FROM completed").fetchone()[0]
        assert len(active) == 1 and completed == 0
        bound, target = json.loads(active[0][0]), Path(active[0][1])
        assert bound["capsule_sha256"] == sha((target / "spatial_source_index.json").read_bytes())
        observations.append(dict(
            fixture=str(directory),
            original_sql_capsule_binding_preserved=True,
            active_jobs=len(active),
            completed_jobs=completed,
        ))
    assert len(observations) == 3
    value = dict(
        formal_root=FORMAL,
        child_gitlink=CHILD,
        nav_sha="70eb7b447e65d793b0ebe18b258291ce46f057c1",
        previous_rejected_root=REJECTED,
        observed_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        python=sys.executable,
        source_count=len(sources),
        all_live_sources_match_fixed_git_blobs=True,
        source_hashes_match_author_revision2=True,
        narrow_product_and_test_paths=narrow,
        preserved_previous_evidence_sha256=expected_preserved,
        junit=junit,
        rejected_mutation_observations=observations,
        closure_evidence_sha256={name: sha((OUT / name).read_bytes()) for name in ("probe.log", "probe.xml", "collect_closure_receipt.py")},
        finding="P2-63-PEER-1",
        finding_status="CLOSED",
        new_confirmed_p1_p2=[],
        verdict="LOCAL_CODE_REVIEW_PASS",
        gpt_server_or_capacity_approval=False,
        training_ready=False,
    )
    with (OUT / "receipt.json").open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
