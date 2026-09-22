#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:?usage: $0 <output-root>}"
mkdir -p "$ROOT"

repos=(
  "robocasa365-target-atomic"
  "robocasa365-target-composite-seen"
  "robocasa365-target-composite-unseen"
)

for name in "${repos[@]}"; do
  dst="$ROOT/$name"
  echo "[download] ember-lab-berkeley/$name -> $dst"
  hf download "ember-lab-berkeley/$name" \
    --repo-type dataset \
    --local-dir "$dst"
done

echo "[done] RoboCasa365 target LeRobot v3 mirrors downloaded under $ROOT"
