# V3 Remaining Optimizations — candidate r2

Date: 2026-10-10. Owner authorized concentrated completion of remaining code optimization before staged DS validation.
Status: **LOCAL UNPUBLISHED CANDIDATE / NOT INTEGRATED / NO GPU OR RESUME AUTHORIZATION**.

Base Root: `2d45bcbe075f27b860aaf0749370f01aabaa4c8a`.
Base Child/Gitlink: `95c82d12d6780fedf8becda18cbd36d550adaadf`.
No new remote commit or Formal Pair has been created. MM SESSION/TODO and historical evidence are untouched.

## Candidate source coverage

New modules cover compact cached-pixel geometry, native batch transfer, rank-shared single-flight Episode cache, actual-consumer provenance, sampled fast state/current storage inventory, observed task exposure, strict evaluation identity, per-step/per-episode failure evidence, and a same-input Local on/off native-generation helper. Root legacy LIBERO entries are blocked rather than misrepresented as migrated.

Integration is specified as exact-blob-guarded replacements for 12 existing files. The source preparation script has not been run against the full actual repository here. Source writing is not implementation acceptance; the connected GitHub interface currently exposes read actions only.

No model forward, loss, Local core math, FSDP2, optimizer/scheduler algorithm or DCP serializer patch is proposed. Geometry proxies keep the old uint8 video shape and one byte of storage; this is not a latent-only rewrite of the model API. Prompt/action/SequencePlan still use the original ActionTransformPipeline. Shared cache uses the original reader's payload and per-window validation, and does not share mutable HF wrapper state across workers.

## Validation facts

83 isolated CPU cases pass; actual CPU tensors, background threads, synthetic Git and filesystem fixtures, and synthetic MP4 writing were exercised. Shared reader validation uses a stub parent reader; paired generation uses a toy model. Twelve local source/test files compile and parse with Python3.10 grammar.

Not run: Ruff0.12.7, full repository import/conftest, real source or DCP, full-policy inference, GPU, throughput, or strict resume. The patch generator must still validate every exact anchor and the complete resulting source in the actual checkout. No performance speedup or full migration completion is asserted.

## Required controlled comparisons

Reference: compact pixels OFF, shared reader OFF, workers0. Candidates: compact/shared ON with workers0 then2/4. Keep frozen digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`, source/window order, T16/B8/GA2/K4/Hpred16, raw15/state, learning schedule and checkpoint namespace. Record pipeline options separately because equal config_digest is not implementation parity evidence.

Gate ordering: complete-code static/CPU validation; real source/tokens/segments/loss/grad parity; actual complete DCP strict resume; authorized bounded GPU and matched-input Local intervention; controlled simulator; evaluation identity and complete 18-task results. DS only executes validated/frozen source and returns evidence, never applies patches or edits production files.
