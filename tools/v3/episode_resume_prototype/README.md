# Flexible Episode Resume: design-only CPU prototype

Contract: `docs/collab/chatgpt/requests/2026-10-23_Codex_V3_RoboCasa_flexible_episode_resume_contract.md`.
Current design: `docs/collab/codex/designs/2026-10-23_V3_RoboCasa_flexible_episode_resume_design_r2.md`.
The r1 design/evidence remain historical. R2 addresses only fresh sampling,
contradictory COMPLETE claims and durable pending-slot recovery.

No production launcher imports these modules. They never schedule a policy or a
simulator, migrate a real run, or write historical results. The input examples are
synthetic files and verified-record doubles; `verified=True` is an internal test
boundary, not an assertion to trust in an external catalog. Production must
revalidate source evidence under its original identity.

Run the isolated CPU Gate, with external evidence/cache directories:

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
python -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
  tools/v3/episode_resume_prototype
```

Use the official manual evaluation launcher only after its separately reviewed
production implementation. These modules do not change today's whole-task
Resume behavior. Current evaluations and G1 worktrees must remain unchanged.
