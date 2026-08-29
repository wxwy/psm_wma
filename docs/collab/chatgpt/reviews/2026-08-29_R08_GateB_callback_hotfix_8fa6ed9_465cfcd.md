# ChatGPT Review — R08 Gate B provenance callback hotfix @ root 8fa6ed9 / submodule 465cfcd

- Date: 2026-08-29
- Reviewer: ChatGPT
- Target root: `8fa6ed989cde75ad4e1a0fe5182d25c3b55117ef`
- Review-request root: `4288c910d196a9d8e3efb8b4caaa509fd1857bfd`
- Target submodule/Gitlink: `465cfcdccd7fd188ae1a2312f408bb9fea92b496`
- Scope: runtime callback signature hotfix only
- Verdict: **APPROVE_TO_RUN_GATE_B_CAPTURE_ONLY**

## Review

The hotfix is correct and narrowly scoped.

Framework base callback contract at:
`cosmos_framework/utils/callback.py`

is:

```python
def on_train_start(self, model: ImaginaireModel, iteration: int = 0) -> None:
    ...
```

The previous Gate-B provenance callback accepted only:

```python
on_train_start(self, model)
```

so the observed runtime failure on `iteration=0` before the first forward is explained by a real signature mismatch.

The hotfix changes only:

```python
def on_train_start(self, model, **kwargs) -> None:
    del model, kwargs
```

and updates the focused test to invoke:

```python
on_train_start(None, iteration=0)
```

This preserves:
- provenance payload fields;
- cwd-independent repo discovery;
- tracked-clean/Gitlink checks;
- checkpoint declaration;
- capture-only semantics;
- canonical manifest pinning/verifier;
- model/algorithm behavior.

No checkpoint, model, optimizer, capture comparator, or Gate-B PASS logic changed.

## Verdict

**APPROVE_TO_RUN_GATE_B_CAPTURE_ONLY**

Resume the previously approved sequence from **Normal**, then:
1. Zero
2. Shuffle

The prior approval constraints remain unchanged:
- pinned reviewed Gate-A checkpoint;
- same batch/current sample;
- same noise;
- same masks;
- same non-history inputs/config;
- only history intervention changes;
- forward/capture only;
- no backward;
- no optimizer step;
- no long training;
- no multi-GPU;
- no Gate C;
- no R09.

After all three captures, run the strict Gate-B verifier and submit the final artifact + raw sidecar hashes for runtime review before advancing.
