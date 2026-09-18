"""Single pretrain-readiness verdict for the active Local-Memory route.

Read-only acceptance command (ChatGPT MEDIUM-3).  It does not train, produce
tensors, or mutate anything: it re-reads the machine-readable evidence already
committed for each gate and emits one ``PASS``/``FAIL``/``BLOCKED`` JSON so a
builder does not have to reconstruct "what counts as training-ready" from prose.

Gates checked:
  1. Gate 1 slot rotation        probe_full_window_postfix.json
  2. Gate 3 planning capacity    probe_epoch_reuse_planning.json
  3. Gate 3 production driver    probe_epoch_reuse_production_driver.json
  4. GPU cross-boundary resume   epreuse_gpu_resume_witness.json
  5. production queue_seed       (from #3) is catalog-derived, not a fixed constant
  6. formal identity             root/submodule HEAD SHAs

Usage:
    python tools/g0/verify_active_local_memory_pretrain_gate.py \
        [--output-json artifacts/g0/active_static_probe/pretrain_acceptance.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE_DIR = ROOT / "artifacts" / "g0" / "active_static_probe"
GPU_WITNESS = ROOT / "artifacts" / "g0" / "epreuse_gpu_resume_witness.json"


def _load(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"missing evidence: {path}")
    return json.loads(path.read_text())


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--expected-root", default=None, help="fail if current root HEAD differs")
    parser.add_argument("--expected-child", default=None, help="fail if current submodule HEAD differs")
    args = parser.parse_args()

    checks: list[dict] = []

    def check(name: str, ok: bool, detail) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    # 1. Gate 1 slot rotation: all 8 slots served, no starvation.
    try:
        g1 = _load(PROBE_DIR / "probe_full_window_postfix.json")
        per_slot = (g1.get("window") or {}).get("per_slot_blocks") or {}
        check(
            "gate1_slot_rotation",
            g1.get("result") == "PASS" and len(per_slot) == 8 and all(int(v) > 0 for v in per_slot.values()),
            {"result": g1.get("result"), "per_slot": per_slot},
        )
    except Exception as exc:  # noqa: BLE001
        check("gate1_slot_rotation", False, {"error": repr(exc)})

    # 2. Gate 3 planning capacity: > 5040 windows **and** full block coverage.
    try:
        g3 = _load(PROBE_DIR / "probe_epoch_reuse_planning.json")
        full_coverage = bool((g3.get("criterion5_block_coverage") or {}).get("full_coverage"))
        check(
            "gate3_planning_capacity",
            g3.get("result") == "PASS"
            and bool(g3.get("capacity_target_met"))
            and int(g3.get("windows_total", 0)) >= 5040
            and full_coverage,
            {
                "result": g3.get("result"),
                "windows_total": g3.get("windows_total"),
                "capacity_target_met": g3.get("capacity_target_met"),
                "full_coverage": full_coverage,
            },
        )
    except Exception as exc:  # noqa: BLE001
        check("gate3_planning_capacity", False, {"error": repr(exc)})

    # 3. Gate 3 production driver: crosses the 112-window boundary, replay-consistent.
    try:
        g3p = _load(PROBE_DIR / "probe_epoch_reuse_production_driver.json")
        check(
            "gate3_production_driver",
            g3p.get("result") == "PASS"
            and bool(g3p.get("boundary_crossed_113"))
            and not g3p.get("criterion10_replay_mismatches"),
            {
                "result": g3p.get("result"),
                "boundary_crossed_113": g3p.get("boundary_crossed_113"),
                "replay_mismatches": g3p.get("criterion10_replay_mismatches"),
            },
        )
    except Exception as exc:  # noqa: BLE001
        check("gate3_production_driver", False, {"error": repr(exc)})

    # 4. GPU cross-boundary resume witness.
    try:
        gpu = _load(GPU_WITNESS)
        check(
            "gpu_resume_cross_boundary",
            gpu.get("result") == "PASS" and not gpu.get("iter3_fields_mismatch"),
            {
                "result": gpu.get("result"),
                "fields_matched": gpu.get("iter3_fields_match"),
                "mismatch": gpu.get("iter3_fields_mismatch"),
            },
        )
    except Exception as exc:  # noqa: BLE001
        check("gpu_resume_cross_boundary", False, {"error": repr(exc)})

    # 5. production queue_seed equals the catalog-derived value of the recorded digests.
    try:
        preimage = f"{g3p['manifest_digest']}|{g3p['config_digest']}|{g3p['source_digest']}"
        derived = int(hashlib.sha256(preimage.encode("utf-8")).hexdigest()[:16], 16)
        check(
            "production_queue_seed",
            int(g3p["queue_seed"]) == derived,
            {"queue_seed": g3p["queue_seed"], "catalog_derived": derived},
        )
    except Exception as exc:  # noqa: BLE001
        check("production_queue_seed", False, {"error": repr(exc)})

    # 6. formal identity: the checkout must match the pair the evidence was produced for.
    try:
        root, child = _git("rev-parse", "HEAD"), _git("-C", "cosmos-framework", "rev-parse", "HEAD")

        def matches(current: str, expected: str | None) -> bool:
            return expected is None or current == expected or current.startswith(expected) or expected.startswith(current)

        check(
            "formal_identity",
            matches(root, args.expected_root) and matches(child, args.expected_child),
            {
                "root": root,
                "submodule": child,
                "expected_root": args.expected_root,
                "expected_child": args.expected_child,
            },
        )
    except Exception as exc:  # noqa: BLE001
        check("formal_identity", False, {"error": repr(exc)})

    failed = [c["check"] for c in checks if not c["ok"]]
    result = "PASS" if not failed else "FAIL"
    report = {"result": result, "failed": failed, "checks": checks}
    print(json.dumps(report, indent=2, default=str))
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, default=str) + "\n")
        print(f"[out] wrote {args.output_json}")
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
