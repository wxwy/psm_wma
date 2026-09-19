#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/cosmos-framework/.venv/bin/python"
[[ -x "$PY" ]] || { echo "ERROR: missing cosmos-framework/.venv" >&2; exit 2; }

EXPECTED_ROOT=2a9df880713da179aee141dd97c6b20a2b1d8c2e
EXPECTED_CHILD=22acb13c1fdb4f146e51e3c26f1759c73e6d0d7e
BASE="$ROOT/artifacts/g0/a2_long_run_readiness_2a9df880"
OUT="${VERIFY_OUTPUT:-/tmp/psm_wma_a2_long_run_readiness.json}"

cd "$ROOT"
exec "$PY" tools/g0/verify_a2_long_run_readiness.py \
  --delivery artifacts/g0/sync_a2_final_verification_2a9df880_v3.json \
  --combined "$BASE/a2_stable_slot_long_run_5000.json" \
  --capacity "$BASE/a2_capacity_5000.json" \
  --reuse "$BASE/a2_epoch_reuse_5000.json" \
  --receipt "$BASE/probe_5000_receipt.json" \
  --expected-root "$EXPECTED_ROOT" \
  --expected-child "$EXPECTED_CHILD" \
  --output "$OUT"