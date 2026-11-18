"""Issue68 immutable-source/full inherited CPU regression receipt."""

import ast
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(os.environ["BATCH_GATE_OUT"])
BASE = "03bb897618c9c6b6d23ecfa36e802747b4b44e79"


def sources():
    return {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for root in ("g2", "tools/g2", "scripts/g2")
        for p in sorted(Path(root).rglob("*"))
        if p.is_file()
        and p.suffix in (".py", ".json", ".sh", ".html", ".js", ".css")
        and "__pycache__" not in p.parts
    }


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    if sys.argv[1] == "before":
        save("source_before.json", sources())
        return
    after = sources()
    save("source_after.json", after)
    assert after == json.loads((OUT / "source_before.json").read_text())
    cases = list(ET.parse(OUT / "pytest.xml").iter("testcase"))
    identities = {(c.attrib["classname"], c.attrib["name"]) for c in cases}
    previous = list(
        ET.parse(
            "docs/collab/codex/evidence/2026-11-18_view_first_retirement/final_retry/pytest.xml"
        ).iter("testcase")
    )
    expected = {(c.attrib["classname"], c.attrib["name"]) for c in previous}
    assert len(expected) == 612 and not expected - identities
    files = (
        subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", BASE, "--", "g2/tests"]
        )
        .decode()
        .splitlines()
    )
    for p in files:
        if p.endswith(".py"):
            assert Path(p).read_bytes() == subprocess.check_output(
                ["git", "show", BASE + ":" + p]
            ), p
    for p in (
        "g2/latent_cache/encoding.py",
        "g2/offline/atomic_6views_run.py",
        "g2/offline/episode.py",
        "g2/latent_cache/final_source.py",
        "g2/latent_cache/source_retirement.py",
        "g2/latent_cache/posthoc.py",
    ):
        assert Path(p).read_bytes() == subprocess.check_output(
            ["git", "show", BASE + ":" + p]
        ), p

    def encode_tree(text):
        return ast.dump(
            next(
                n
                for n in ast.parse(text).body
                if isinstance(n, ast.FunctionDef) and n.name == "encode_record"
            ),
            include_attributes=False,
        )

    assert encode_tree(Path("g2/latent_cache/builder.py").read_text()) == encode_tree(
        subprocess.check_output(
            ["git", "show", BASE + ":g2/latent_cache/builder.py"]
        ).decode()
    )
    failed = sum(bool(c.findall("failure")) for c in cases)
    errors = sum(bool(c.findall("error")) for c in cases)
    skip = sum(bool(c.findall("skipped")) for c in cases)
    assert failed == errors == 0
    assert not any(
        c.find("skipped") is not None
        and (c.attrib["classname"], c.attrib["name"]) not in expected
        for c in cases
    )
    value = dict(
        schema="g2_issue68_author_cpu_v1",
        tests=len(cases),
        passed=len(cases) - skip - failed - errors,
        failed=failed,
        errors=errors,
        skipped=skip,
        old612_identities_preserved=True,
        old_test_sources_preserved=True,
        new_tests=len(identities - expected),
        sources_stable=True,
        source_count=len(after),
        legacy_encode_record_ast_unchanged=True,
        legacy_b1_loader_unchanged=True,
        real_gpu_gate=False,
        training_ready=False,
    )
    save("gate.json", value)
    print(json.dumps(value, sort_keys=True))


if __name__ == "__main__":
    main()
