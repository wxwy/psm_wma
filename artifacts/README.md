# Artifacts

`artifacts/g0/` contains raw machine-readable evidence from many iterations of the project. Historical directories are intentionally retained and are not all equally authoritative.

Use `CANONICAL.json` to locate the current accepted evidence. Canonical summaries and training/testing process records belong in Git. Checkpoint trees, model weights and `config.pkl` binary snapshots stay local and are ignored.

## Current canonical evidence

- engineering delivery verifier
- real-GPU A2 control
- exact resume
- full-catalog 20-step budget
- 5000-window capacity / epoch-reuse planning
- long-run readiness verifier

Do not infer authority from a directory's modification time or name alone. The canonical implementation pair and accepted artifact paths are frozen in `CANONICAL.json`.

## Evidence vs results

Engineering artifacts establish implementation properties such as shape, chronology, loss/gradient parity, resume behavior, memory budget and long-run serviceability.

Closed-loop task success rate is a research result and must be tied to a concrete checkpoint and evaluation configuration. Engineering PASS does not imply an SR improvement.