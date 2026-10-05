#!/usr/bin/env python
"""Phase6 Encode1 thresholded validation — final authority finalizer（ds Evidence 侧）。

职责边界（严格）：
- **只允许读取三个文件**：`A1_pairlock.txt`、`B0_probe.py`、`D1_threshold_validation.json`。
  不读 C0、不读 cache/source/VAE、不导入 probe、**不重跑任何 VAE/编码**、不触碰 repo。
- 全部期望值都是**本文件内的硬编码常量**，不接受任何可覆盖 authority 的 CLI 参数。
- 只写两个新文件：`E1_gate_validation.json`（判定结果）。其余产物（sha/stdout/stderr）由调用方保存。
- 结果由**进程退出码**表达：0=PASS，1=FAIL。

判定三件事：
1. pairlock 文本**包含**且**一致**（不得与硬编码期望冲突）；
2. **实际** `B0_probe.py` 的 sha256 与冻结值一致；
3. `D1_threshold_validation.json` 满足 `status=PASS / checks_failed=0 / threshold=0.0 / exact_required=true`。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# 硬编码 authority 期望（不接受任何 CLI 覆盖）
# ---------------------------------------------------------------------------
EXPECTED_SCRATCH = "8c3800565f66cfbce2929264f1c2a7854137482e"
EXPECTED_PROBE_SHA256 = "a07e7fd1cbc96d855785708e0e9c6ecc7ec89240f0fae045ed9bbd34942a3fcb"
EXPECTED_REVIEW_COMMIT = "b6c42088ae41904c0667d1066983c2829ae61c36"
EXPECTED_V3_HEAD = "3f0d5e20a29922b40054c7d348eaba77675531f2"
EXPECTED_CHILD_GITLINK = "b673ceda5a9ff058abb31224b7006f2d87771ad2"

# 已显式标注为 stale 的历史引用（允许出现在 pairlock，但只能出现在 stale 标签行上）
KNOWN_STALE_SHA = "89e62662adde2c0f1f8c0e3605e0f99007632659"

# 常量形状前置校验：任何硬编码 SHA 的长度/字符集不对（例如手打多一位）都立即致命，
# 避免把“常量笔误”误判成 Gate 失败。
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
for _n, _v, _r in (
    ("EXPECTED_SCRATCH", EXPECTED_SCRATCH, _HEX40_RE),
    ("EXPECTED_PROBE_SHA256", EXPECTED_PROBE_SHA256, _HEX64_RE),
    ("EXPECTED_REVIEW_COMMIT", EXPECTED_REVIEW_COMMIT, _HEX40_RE),
    ("EXPECTED_V3_HEAD", EXPECTED_V3_HEAD, _HEX40_RE),
    ("EXPECTED_CHILD_GITLINK", EXPECTED_CHILD_GITLINK, _HEX40_RE),
    ("KNOWN_STALE_SHA", KNOWN_STALE_SHA, _HEX40_RE),
):
    if not _r.match(_v):
        raise SystemExit(
            f"FATAL_CONSTANT_SHAPE: {_n}={_v!r} len={len(_v)} does not match {_r.pattern}")

EXPECTED_SET = {
    EXPECTED_SCRATCH,
    EXPECTED_PROBE_SHA256,
    EXPECTED_REVIEW_COMMIT,
    EXPECTED_V3_HEAD,
    EXPECTED_CHILD_GITLINK,
}

# D1 必须满足的判定契约
D1_EXPECTED_STATUS = "PASS"
D1_EXPECTED_THRESHOLD = 0.0
D1_EXPECTED_EXACT_REQUIRED = True
D1_EXPECTED_CHECKS_FAILED = 0

# pairlock 中承载 authority 锚点的键（必须出现，且取值必须与期望一致）
REQUIRED_PAIRLOCK_KEYS = {
    "phase6a_scratch_target": EXPECTED_SCRATCH,
    "threshold_freeze_review_commit": EXPECTED_REVIEW_COMMIT,
    "current_V3_bookkeeping_head": EXPECTED_V3_HEAD,
    "production_child_gitlink": EXPECTED_CHILD_GITLINK,
    "probe_sha256": EXPECTED_PROBE_SHA256,
}

# 这些前缀的键所在的整行不得出现期望集合之外的 40-hex（stale 行除外）
ANCHOR_KEY_PREFIXES = (
    "phase6a_scratch_target",
    "threshold_freeze_review_commit",
    "current_V3_bookkeeping_head",
    "production_child_gitlink",
    "probe_sha256",
    "scratch_HEAD",
    "r3_B0_probe_sha256",
    "r1_B0_probe_sha256",
    "pinned_in_review",
    "gitlink@",
    "superseded_by",
)
# 显式 stale 行：允许出现 KNOWN_STALE_SHA
STALE_KEY_PREFIXES = ("stale_prior_reference_",)

HEX40 = re.compile(r"\b[0-9a-f]{40}\b")
HEX64 = re.compile(r"\b[0-9a-f]{64}\b")
KV_LINE = re.compile(r"^\s*([A-Za-z0-9_@/.\-()]+?)\s*=\s*(.*)$")


class Finalizer:
    def __init__(self) -> None:
        self.checks: list[dict] = []
        self.failures: list[str] = []

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            self.failures.append(f"{name}: {detail}")

    # -- 1. pairlock ------------------------------------------------------
    def check_pairlock(self, text: str) -> dict:
        info: dict = {
            "required_keys_found": {},
            "key_value_conflicts": [],
            "anchor_lines_with_foreign_sha": [],
            "all_hex40_seen": [],
            "stale_lines": [],
        }
        parsed: list[tuple[str, str]] = []
        for raw in text.splitlines():
            m = KV_LINE.match(raw)
            if m:
                parsed.append((m.group(1).strip(), m.group(2).strip()))

        info["all_hex40_seen"] = sorted(set(HEX40.findall(text)))

        # 1a. 必需键存在 + 取值一致（同一键多次出现时必须全部等于期望值）
        for key, expected in REQUIRED_PAIRLOCK_KEYS.items():
            matches = [v for k, v in parsed if k == key]
            info["required_keys_found"][key] = {"count": len(matches), "values": matches}
            self.check(f"pairlock.key_present[{key}]", len(matches) >= 1,
                       f"count={len(matches)}")
            if matches:
                bad = [v for v in matches if v != expected]
                self.check(f"pairlock.key_value[{key}]", not bad,
                           f"expected={expected} offending={bad}")
                if bad:
                    info["key_value_conflicts"].append({"key": key, "expected": expected,
                                                        "found": bad})

        # 1b. 缩进的派生行（scratch_HEAD / r3_B0_probe_sha256 / pinned_in_review / gitlink@…）
        for key, expected in (
            ("scratch_HEAD", EXPECTED_SCRATCH),
            ("r3_B0_probe_sha256", EXPECTED_PROBE_SHA256),
            ("r1_B0_probe_sha256", EXPECTED_PROBE_SHA256),
            ("pinned_in_review", EXPECTED_PROBE_SHA256),
            ("gitlink@origin/V3", EXPECTED_CHILD_GITLINK),
            ("gitlink@b6c42088", EXPECTED_CHILD_GITLINK),
            ("superseded_by", EXPECTED_REVIEW_COMMIT),
        ):
            matches = [v for k, v in parsed if k == key]
            if matches:
                # 该键为可选记录项：出现即必须一致
                bad = [v for v in matches if not v.startswith(expected)]
                self.check(f"pairlock.derived[{key}]", not bad,
                           f"expected_prefix={expected} offending={bad}")

        # 1c. stale 行只能承载已知 stale SHA
        for k, v in parsed:
            if k.startswith(STALE_KEY_PREFIXES):
                info["stale_lines"].append({"key": k, "value": v})
                shas = HEX40.findall(v)
                ok = all(s == KNOWN_STALE_SHA for s in shas) and len(shas) >= 1
                self.check(f"pairlock.stale_line[{k}]", ok,
                           f"value={v!r} known_stale={KNOWN_STALE_SHA}")

        # 1d. anchor 行不得出现期望集合之外的 SHA
        for k, v in parsed:
            if k.startswith(ANCHOR_KEY_PREFIXES):
                foreign = [s for s in HEX40.findall(v) if s not in EXPECTED_SET]
                if foreign:
                    info["anchor_lines_with_foreign_sha"].append(
                        {"key": k, "value": v, "foreign": foreign})
                    self.check(f"pairlock.anchor_no_foreign_sha[{k}]", False,
                               f"foreign={foreign} value={v!r}")

        # 1e. 关键事实行必须存在（防止空/截断 pairlock 通过）
        for token in (EXPECTED_SCRATCH, EXPECTED_PROBE_SHA256, EXPECTED_REVIEW_COMMIT,
                      EXPECTED_V3_HEAD, EXPECTED_CHILD_GITLINK):
            self.check(f"pairlock.contains[{token[:12]}…]", token in text, "token 缺失")
        return info

    # -- 2. probe 实际 sha -------------------------------------------------
    def check_probe(self, probe_bytes: bytes, pairlock_text: str) -> dict:
        actual = hashlib.sha256(probe_bytes).hexdigest()
        self.check("probe.actual_sha256_matches_frozen",
                   actual == EXPECTED_PROBE_SHA256,
                   f"actual={actual} expected={EXPECTED_PROBE_SHA256}")
        # pairlock 自报值必须与实际一致（不得自相矛盾）
        reported = re.findall(r"^\s*r3_B0_probe_sha256\s*=\s*([0-9a-f]{64})",
                              pairlock_text, flags=re.M)
        self.check("probe.pairlock_reported_matches_actual",
                   bool(reported) and all(r == actual for r in reported),
                   f"reported={reported} actual={actual}")
        return {"actual_sha256": actual, "expected_sha256": EXPECTED_PROBE_SHA256,
                "pairlock_reported": reported}

    # -- 3. D1 ------------------------------------------------------------
    def check_d1(self, d1: dict) -> dict:
        got = {
            "status": d1.get("status"),
            "threshold": d1.get("threshold"),
            "exact_required": d1.get("exact_required"),
            "checks_failed": d1.get("checks_failed"),
            "checks_total": d1.get("checks_total"),
            "failures": d1.get("failures"),
            "source_observational_sha256": d1.get("source_observational_sha256"),
        }
        self.check("d1.status_is_PASS", got["status"] == D1_EXPECTED_STATUS,
                   f"status={got['status']!r}")
        self.check("d1.checks_failed_is_0",
                   isinstance(got["checks_failed"], int) and got["checks_failed"] == D1_EXPECTED_CHECKS_FAILED,
                   f"checks_failed={got['checks_failed']!r}")
        self.check("d1.threshold_is_0.0",
                   isinstance(got["threshold"], (int, float))
                   and not isinstance(got["threshold"], bool)
                   and float(got["threshold"]) == D1_EXPECTED_THRESHOLD,
                   f"threshold={got['threshold']!r}")
        self.check("d1.exact_required_is_true",
                   got["exact_required"] is D1_EXPECTED_EXACT_REQUIRED,
                   f"exact_required={got['exact_required']!r}")
        # 附加健全性（不放松主判据）
        self.check("d1.checks_total_positive",
                   isinstance(got["checks_total"], int) and got["checks_total"] > 0,
                   f"checks_total={got['checks_total']!r}")
        self.check("d1.failures_empty",
                   isinstance(got["failures"], list) and len(got["failures"]) == 0,
                   f"failures={got['failures']!r}")
        src = got["source_observational_sha256"]
        self.check("d1.source_observational_sha256_is_sha256",
                   isinstance(src, str) and bool(HEX64.fullmatch(src)),
                   f"source_observational_sha256={src!r}")
        self.check("d1.exit_code_semantics_present",
                   isinstance(d1.get("exit_code_semantics"), dict),
                   f"{type(d1.get('exit_code_semantics')).__name__}")
        return got


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Phase6 Encode1 final authority finalizer (evidence-only, read-only inputs)")
    ap.add_argument("--pairlock", required=True, type=Path)
    ap.add_argument("--probe", required=True, type=Path)
    ap.add_argument("--d1", required=True, type=Path)
    ap.add_argument("--output-json", required=True, type=Path)
    # 刻意不提供任何 authority 覆盖参数：全部期望值硬编码在本文件中。
    args = ap.parse_args()

    # 只读这三个输入
    pairlock_text = args.pairlock.read_text(encoding="utf-8")
    probe_bytes = args.probe.read_bytes()
    d1 = json.loads(args.d1.read_text(encoding="utf-8"))

    f = Finalizer()
    pairlock_info = f.check_pairlock(pairlock_text)
    probe_info = f.check_probe(probe_bytes, pairlock_text)
    d1_info = f.check_d1(d1)

    total = len(f.checks)
    failed = len(f.failures)
    status = "PASS" if failed == 0 else "FAIL"

    out = {
        "schema": "robocasa_phase6_encode1_gate_validation_v1",
        "status": status,
        "validated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z"),
        "role": "ds (execution/evidence only; no repo/cache/source write, no VAE rerun)",
        "inputs": {
            "pairlock": {"path": str(args.pairlock), "sha256": sha256_file(args.pairlock)},
            "probe": {"path": str(args.probe), "sha256": sha256_file(args.probe)},
            "d1": {"path": str(args.d1), "sha256": sha256_file(args.d1)},
        },
        "expected": {
            "scratch": EXPECTED_SCRATCH,
            "probe_sha256": EXPECTED_PROBE_SHA256,
            "review_commit": EXPECTED_REVIEW_COMMIT,
            "current_v3_head": EXPECTED_V3_HEAD,
            "child_gitlink": EXPECTED_CHILD_GITLINK,
            "d1_status": D1_EXPECTED_STATUS,
            "d1_threshold": D1_EXPECTED_THRESHOLD,
            "d1_exact_required": D1_EXPECTED_EXACT_REQUIRED,
            "d1_checks_failed": D1_EXPECTED_CHECKS_FAILED,
        },
        "observed": {
            "pairlock": pairlock_info,
            "probe": probe_info,
            "d1": d1_info,
        },
        "checks_total": total,
        "checks_failed": failed,
        "failures": f.failures,
        "checks": f.checks,
        "exit_code_semantics": {"0": "PASS", "1": "FAIL"},
    }
    args.output_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"PAIRLOCK={args.pairlock}")
    print(f"PROBE={args.probe} sha256={probe_info['actual_sha256']}")
    print(f"D1={args.d1}")
    print(f"CHECKS_TOTAL={total} CHECKS_FAILED={failed}")
    print(f"GATE_VALIDATION_STATUS={status}")
    print(f"GATE_VALIDATION_JSON={args.output_json}")
    if f.failures:
        print("FAILURES:")
        for x in f.failures:
            print(f"  - {x}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())