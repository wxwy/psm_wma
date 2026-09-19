# PSM-WMA

**Persistent Spatial-Intelligence-Augmented World-Model Agent**

PSM-WMA 是面向移动操作的持续状态 / 记忆 / 世界模型研究项目。当前已经完成的工程主线是 **Temporal Local Memory + TTT fast state + Cosmos3-Edge action policy**：机器人只使用过去观测与已执行动作更新局部记忆，并把 Local Memory prefix 接入 Cosmos 原生 action-policy forward。

当前仓库包含大量历史 Gate、审计、refreeze 与实验产物；它们保留用于可追溯性。第一次进入项目时，**先看本 README 与 `docs/current/`，不要从 `docs/build/` 或 `docs/collab/` 开始读。**

## Current status

- Engineering delivery: **PASS**
- Long-run readiness: **READY_FOR_LONG_RUN**
- 5000-step authorization: **true**
- 5000-step training: **not started**
- Canonical implementation root: `2a9df880713da179aee141dd97c6b20a2b1d8c2e`
- Canonical Cosmos child: `22acb13c1fdb4f146e51e3c26f1759c73e6d0d7e`

机器可读状态见 [`PROJECT_STATUS.md`](PROJECT_STATUS.md) 与 [`artifacts/CANONICAL.json`](artifacts/CANONICAL.json)。
## Current architecture

```text
past RGB / executed action
          │
          ▼
   evidence encoder
          │
          ▼
 TTT fast-weight update   (slot-local, fp32)
          │
          ▼
 Local Memory prefix
          │
          ▼
 Cosmos3-Edge Transformer / MoT
          │
          ▼
 native Flow-Matching action loss
```

Canonical A2 training geometry:

- `B_stream = 8` stable episode streams
- `T = 16` consecutive consumer positions per stream
- one native microbatch = `8 × 16 = 128` consumers
- `GA = 16` native microbatches per optimizer update
- `2048` consumers / optimizer update
- TTT is serial along `T`, parallel across stream rows
- runtime fast state is committed only after successful outer backward
## Start here

1. Architecture: [`docs/current/architecture.md`](docs/current/architecture.md)
2. Local Memory semantics: [`docs/current/local_memory.md`](docs/current/local_memory.md)
3. Training / resume: [`docs/current/training.md`](docs/current/training.md)
4. Evaluation: [`docs/current/evaluation.md`](docs/current/evaluation.md)
5. Experiment matrix: [`docs/current/experiments.md`](docs/current/experiments.md)
6. Full documentation index: [`docs/INDEX.md`](docs/INDEX.md)

Public project entrypoints:

```bash
scripts/train_local_memory_ttt.sh  # canonical Local Memory + TTT A2; auto-resume by default
scripts/train.sh                   # compatibility alias to the canonical trainer
scripts/resume.sh                  # strict-resume alias; fails if no checkpoint exists
scripts/eval.sh                    # LIBERO closed-loop evaluation for one checkpoint
scripts/verify.sh                  # engineering + long-run readiness verification
```

These wrappers delegate to the existing Cosmos / G0 implementation; `tools/g0/` remains the internal engineering toolbox.

## Key validated evidence

- CPU regression: `244 passed / 0 failed`
- A2 real-GPU control, exact resume, native grouped-vs-scalar parity and online action path: PASS
- Full-catalog 20-step A2 run: `176.059 s/step`, peak CUDA allocated `45.045 GiB`
- Metadata-only production A2 planning: `5000/5000` optimizer windows, 0 chronology/group-shape/queue-replay errors
- Base 5000-step wall-time projection: about `10.19 days`, excluding eval/checkpoint overhead
## Repository layout

```text
README.md / PROJECT_STATUS.md   project entry and current truth
docs/current/                   concise current architecture / operation docs
docs/build/                     versioned design and Gate history
docs/collab/                    review / agent collaboration history
artifacts/CANONICAL.json        authoritative artifact pointers
artifacts/g0/                   raw machine-readable evidence
scripts/                        human-facing train/resume/eval/verify facade
tools/g0/                       internal probes, gates and diagnostics
cosmos-framework/               Cosmos3 code + PSM-WMA implementation
MEMORY/DECISIONS.md             durable engineering decisions
SESSION.md / TODO.md            internal execution ledger
```

## Scope boundary

The current `READY_FOR_LONG_RUN` statement is an **engineering readiness** result. It does not claim that the 5000-step run has completed, that Local Memory improves LIBERO success rate, or that the full PSM-WMA World Model stage has been completed.

The current research sequence remains: **Local / Recent Memory → Persistent State → Action-conditioned World Model → Full closed loop**.