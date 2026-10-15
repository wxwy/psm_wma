# PSM-WMA V3 — B1 P0 Threaded CFG Local-RNG CPU Gate: Native Tokenizer evidence closeout

**Date:** 2026-10-15  
**Independent reviewer:** GPT (Evidence/Gate)  
**Exact diagnostic formal implementation Root:** `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0`  
**Exact diagnostic Child/Gitlink:** `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`  
**Gate:** `B1_P0_THREADED_CFG_LOCAL_RNG_CPU_GATE`  
**Formal verdict:** **`APPROVE_TO_CLOSE` — CPU GATE ONLY**. Previous `REQUEST_CHANGES` evidence-only finding **CLOSED** by DS_PRO's focused supplemental native tokenizer evidence.  
**GPU:** `GPU_NOT_AUTHORIZED` / `GPU_UNVERIFIED`; this verdict does **not** approve GPU, P0 launch, any broader B1, Gate M, Formal30k or training.

## 1. Same-pair evidence supplementation; no repeated technical review

GitHub's isolated branch `v3-gateb1-numeric-implementation-20261014` still points to `a3239591...`; its Gitlink remains `8f3672d1...`. The previous independent code review and B1 CPU verification for the **same formal pair** are not rerun. This document performs **only** narrow remediation evidence verification for the previously open blocker, without new code modifications or reopening B0/451GB dataset checks.

- Prior `REQUEST_CHANGES` detailed review: `docs/collab/chatgpt/reviews/2026-10-15_V3_B1_CFG_local_rng_a3239591_DS_CPU_evidence_incremental_review.md`.
- Frozen acceptance request: `docs/collab/chatgpt/requests/2026-10-15_DS_PRO_V3_B1_P0_threaded_CFG_local_RNG_fix_a3239591_CPU_gate.md`.
- Frozen Owner numeric policy: `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`.
- Frozen Source Index8: `b159f45906f7261d028aecc226ab7f2bb9807eb9` / `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.
- Frozen Target Packed128: `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.
- Original B0 iter1300 DCP fingerprint: `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`.

## 2. Contract → behavior → supplemental evidence

**Previously open finding:** The first DS report's `('', [0])` synthetic tokenizer did not prove byte-identical **real native** TextTokenizerTransform caption/text-token payload across frozen Source/Target and diagnostic B1. Source/Target code used `random.random()`; diagnostic Child used `transform_draw(random.random)`. Required authentic tokenizer, both CFG branches, full tensor hashes, replay/RNG invariants.

**New DS_PRO read-only native tokenizer report, 2026-10-15** (Owner-pasted in conversation):
- Built real local DROID `Nemotron3DenseVLProcessor` from `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID`, not the synthetic tokenizer fixture. Uses real `TextTokenizerTransform.__call__`, actual native chat-template tokenization, and native JSON prompt formatter; limits CPU comparison to formatter/tokenizer steps, avoiding unrelated video/action/model/DCP.
- **44 ConsumerKeys × 2 captions = 88 cases** comparing SOURCE frozen `937066ff`, TARGET frozen `c8dabbb3`, B1 diagnostic `8f3672d1`. DS reports **88/88 equal exact caption, token IDs, full token tensor SHA256**, 0 mismatches, spanning **7 dropout keys and 37 non-dropout keys**.
- Non-dropout sample: `pick up the blue cup from the table`, key step=1301 ga=1; native JSON prompt preserved, 66 tokens, full SHA256 `6762e2e49abcc32684a29d88c195f5652c9f1646feb022b6640dea0f9dde4195` for all three legs.
- Dropout sample: key step=1301 ga=2, empty caption, 17 native tokens, full SHA256 `4fb39e1397ac104009c9c21d237bf301bc93026b183f5fb41c54d22616095b88` for all three legs.
- DS reports default `transform_draw(random.random)` and global `random.random()` same draw value `0.052363598850944326`, no-context behavior, global RNG state unchanged by B1 adapter, deterministic B1 replay with an active unrelated Python background thread; **10/10** focused checks passed with exit 0.
- GPT independently read GitHub diagnostic Child `cosmos_framework/data/generator/action/utils/transform_random.py`: `_TRANSFORM_RNG` ContextVar defaults to None, and `transform_draw(legacy_draw)` returns `legacy_draw()` when no scope. This supports equivalence to unscoped frozen SRC/TGT draw. The actual `/tmp` test scripts/logs remain DS-host artifacts and were **not** executed or accessed by GPT.
- Prior DS CPU gate test record for unchanged implementation: **23/23** py_compile, **23/23** Ruff (zero findings), **149/149** pytest and **12/12** specialized CPU checks. These are inherited as **previously reviewed evidence for the same formal pair**, not re-executed here.
- Supplemental `/tmp` provenance (DS-host, not GitHub): `/tmp/verify_a3239591_native_tokenizer.py`, `/tmp/capture_native_samples.py`, `/tmp/native_tokenizer_run.log`. DS reports no GitHub/Child modifications, GPU/torchrun/model load/real DCP, no B0 or previous 149 retest.

**Disposition of the sole outstanding evidence-only finding:** **CLOSED**. This supplemental direct native output comparison supplies the prior missing evidence; previous code-level assessment remains unchanged. The restricted CPU-only claim does not assert full end-to-end video/action transform payload, GPU training numerical parity, or actual training execution.

## 3. Residual gates and owner execution boundary

- Old code `46e9cc0e5dc97a1f7f813b2a332b095aa1062a4a` P0 8×H100 Smoke remained **BLOCKED before completed iter1301**: no GPU gradient/Adam/fast-state equivalence, Target never launched. Do not reinterpret it as numerical mismatch or as pass.
- The Owner's earlier P0 GPU receipt exclusively authorized **old** `46e9cc0e`, **not** `a3239591`. Existing SHA-identity barrier must reject old receipt.
- **New Owner authorization is still required** to run diagnostic `a3239591...` P0_FIXED repeat0, source Index8 iter1301/1302 first, review SOURCE before Target Packed128; 8×H100 co-resident safe conditions if explicitly re-approved. Launch CWD must be each frozen Child root (`cd "$LEG_ROOT/cosmos-framework"`) for CWD-relative Nemotron model JSON. Original DCP/latest read-only; isolated /tmp results; no checkpoint writes or auto retries.
- P1/repeat1/full B1 GPU numerical parity, Gate M, Formal30k remain HOLD and require their respective future gates. **No Owner GPU authorization was requested, issued, inherited, or inferred by this review.**
- Formal implementation pair is unchanged; V3 review/Inbox commits are bookkeeping and not replacement implementation SHA; no full V3 audit now.

## 4. Literal final verdict

**`B1_P0_THREADED_CFG_LOCAL_RNG_CPU_GATE` → `APPROVE_TO_CLOSE`**, bound only to diagnostic Root `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / Child `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`. Historical `REQUEST_CHANGES` was valid when issued; this new evidence-only closure supersedes it for this Gate without re-reviewing unchanged implementation. **GPU_NOT_AUTHORIZED / GPU_UNVERIFIED**.
