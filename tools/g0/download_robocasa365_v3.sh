#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:?usage: $0 <output-root> [all|pretrain|target|repo-slug ...]}"
shift || true
mkdir -p "$ROOT"

all_repos=(
  "robocasa365-pretrain-atomic"
  "robocasa365-pretrain-mg"
  "robocasa365-pretrain-composite"
  "robocasa365-target-atomic"
  "robocasa365-target-composite-seen"
  "robocasa365-target-composite-unseen"
)
pretrain_repos=(
  "robocasa365-pretrain-atomic"
  "robocasa365-pretrain-mg"
  "robocasa365-pretrain-composite"
)
target_repos=(
  "robocasa365-target-atomic"
  "robocasa365-target-composite-seen"
  "robocasa365-target-composite-unseen"
)

selector="${1:-all}"
case "$selector" in
  all)
    repos=("${all_repos[@]}")
    ;;
  pretrain)
    repos=("${pretrain_repos[@]}")
    ;;
  target)
    repos=("${target_repos[@]}")
    ;;
  *)
    repos=("$@")
    ;;
esac

for name in "${repos[@]}"; do
  case "$name" in
    robocasa365-pretrain-atomic|robocasa365-pretrain-mg|robocasa365-pretrain-composite|robocasa365-target-atomic|robocasa365-target-composite-seen|robocasa365-target-composite-unseen)
      ;;
    *)
      echo "[error] unsupported RoboCasa365 v3 repo slug: $name" >&2
      exit 2
      ;;
  esac
  dst="$ROOT/$name"
  echo "[download] ember-lab-berkeley/$name -> $dst"
  hf download "ember-lab-berkeley/$name" \
    --repo-type dataset \
    --local-dir "$dst"
done

echo "[done] requested RoboCasa365 LeRobot v3 mirrors downloaded under $ROOT"
