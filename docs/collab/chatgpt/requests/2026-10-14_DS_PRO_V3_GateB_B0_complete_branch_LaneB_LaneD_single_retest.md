# GPT → DS_PRO — V3 Gate B0 candidate unblocked: ONE Lane B+D completion and ONE GPT audit

**Date:** 2026-10-14  
**Scope:** `CPU_ONLY / DS_PRO_VALIDATION_ONLY`. **No GPU/torchrun/Nsight, no B1 native model DCP load, no DCP writes/migration/training/inference or Formal30k worktree changes.**  
**Diagnostic candidate:** `wxwy/psm_wma` isolated branch `v3-gateb-comparator-b0` **exact HEAD `528c100fd120c3fad52739f2ec09a8cd8cab50e6`**. This SHA includes all five original candidate ZIP files (four exact paths + isolated README equivalent); GitHub per-file readback was byte-for-byte checked against ZIP SHA256 `911946134effd478071ef61180ff0eaadaee4721f4b7dc70080a6b5e348c6852`. Do **NOT** require DS host to access the original ChatGPT ZIP.

## 1. Previous DS CPU evidence accepted as scoped source audit; do not repeat unrelated work

DS first B0 report (Owner relayed 2026-10-13) established:
- Source Index8 Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`; Target Packed128 Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`, matching Gitlinks;
- Lane C: 4 metadata, 32 `.distcp` shards, 8 rank sidecars, full 17-field rank-specific profile, old digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`, 9126 episodes / 18 tasks, all profile/provenance/fast states read-only PASS;
- Real iter1300 successor two windows per-rank `GA0/GA1` member_counts and terminal partials have been measured. The **Index8 native FSDP call rhythm was exactly 16 + 16 for all8 ranks on both windows**; terminal partial is *already present in real source frontier*, rather than a hypothetical GPU fixture only;
- Entire source snapshot before/after (484 paths) had **0 content differences**; Lane A SHA/environment except missing candidate PASS;
- Prior Lane B and D **NOT_RUN solely because original ZIP absent on DS host**. The blockage is now repaired by exact remote branch content.

Do **not** re-run prior full sidecar/catalog/frontier probes as separate jobs without a newly found contradiction. New Lane D naturally computes a paired plan and its own source immutability evidence; that is not a request to duplicate the old Lane C independent audit.

## 2. New candidate fetch / exact identity — prerequisite

On DS server, fetch **without updating/checking out** pinned Formal30k:
```bash
git -C <any-isolated-root-clone-of-wxwy/psm_wma> fetch origin v3-gateb-comparator-b0
git -C <that-clone> worktree add --detach /tmp/ds_pro_v3_gateb_b0_complete_20261014 528c100fd120c3fad52739f2ec09a8cd8cab50e6
git -C /tmp/ds_pro_v3_gateb_b0_complete_20261014 rev-parse HEAD
```
Require exact `528c100fd120c3fad52739f2ec09a8cd8cab50e6`; confirm the following source files exist in the **same** diagnostic worktree:
- `tools/gates/v3_packed128_gateb_compare.py`
- `tools/gates/v3_gateb_numerics.py`
- `tools/gates/test_v3_packed128_gateb_compare.py`
- `docs/DS_PRO_V3_GATEB_B0_CPU_VALIDATION_2026-10-13.md`
- `tools/gates/GATE_B0_README.md`

Pin sha256/paths and module `__file__` and exact paired Root/Child/Gitlink. No mixing with the old partial commit `853cf9a...` or with FSP child. The complete candidate is available in GitHub now; if exact `fetch` fails, return `BLOCKED_FETCH` with raw error rather than silently substituting ZIP/old branch.

## 3. Execute remaining Lane B and Lane D in one DS batch

**Lane B (can run independently of Lane D's metadata prep):**
```bash
export HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH=''
export DIAG_ROOT=/tmp/ds_pro_v3_gateb_b0_complete_20261014
export VENV=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv
cd "$DIAG_ROOT"
"$VENV/bin/python" -m py_compile tools/gates/v3_packed128_gateb_compare.py tools/gates/v3_gateb_numerics.py tools/gates/test_v3_packed128_gateb_compare.py
"$VENV/bin/python" -m pytest -q tools/gates/test_v3_packed128_gateb_compare.py
"$VENV/bin/ruff" check tools/gates/v3_packed128_gateb_compare.py tools/gates/v3_gateb_numerics.py tools/gates/test_v3_packed128_gateb_compare.py
"$VENV/bin/python" tools/gates/v3_packed128_gateb_compare.py --mode paired-run
```
Expected for last explicit *negative* test: **exit2** with `GPU_B1_NOT_IMPLEMENTED_OR_AUTHORIZED`; other three exit0. Preserve per-command exit codes and actual stdout/stderr. The author independently reran 21/21 pytest, compile exit0 and paired-run exit2 on the exact ZIP code with CPU torch2.10; **Ruff was unavailable in author container** and must be established in DS environment.

**Lane D (after exact candidate/pair/source identity pins, run the two legs SEQUENTIALLY):**
Use the **verbatim command template** from this exact diagnostic commit:
`docs/DS_PRO_V3_GATEB_B0_CPU_VALIDATION_2026-10-13.md` §"DS step 2", replacing only documented **filesystem paths** with actual existing isolated Index8/Packed worktrees and clean brand-new `/tmp` output namespaces. Use `--mode cpu-plan-only --num-workers 0 --steps 2 --hash-all-shards --verify-payloads`. Then run `--mode compare-cpu-reports` on both real JSON reports. Do not use formal `--phase resume` or `--stop-after-iter`. No source checkpoint edit/namespace reuse.
- Verify source original iter1300 checkpoint fingerprint and source/target resolved digest as pinned.
- Require both reports have matching 8rank ×2 windows with actual per-rank/GA `member_counts`, same Consumer Identity sequences, real transformed Native input SHA and scoped Python CFG RNG replay.
- Target top-level + every active nested `SegmentProvenance.config_digest` translation is in-memory-only, source unchanged.
- Source checkpoint complete pre/post SHA256 must remain equal across Lane D; reuse old Lane C prior snapshot as baseline only if same exact immutable source path and SHA inventory. Avoid concurrent multiple 32-shard full hash sweeps; run source/target legs serially.
- If unsupported Native payload leaf/type, tokenizer timing/thread issue, wrong paths or modules or default RNG semantics are exposed, record first traceback and `BLOCKED` without modifying implementation/code/data/checkpoint. Do NOT invoke GPU as workaround.
- B0's `P1` CPU epsilon witness is only a structural test; production distribution-matched sigma/noise injection and all real gradient comparisons remain **B1 NOT IMPLEMENTED**.

## 4. One consolidated final report only

Deliver **`DS_PRO_V3_PACKED128_GATE_B0_LANE_B_D_COMPLETION_2026-10-14.md`** that integrates **old Lane A/C evidence** (with exact source report reference, no re-run) and **new Lane B/D evidence**, pinning diagnostic SHA `528c100fd120c3fad52739f2ec09a8cd8cab50e6`, two formal paired Root/Child/Gitlinks, candidate exact file hashes, commands/exit codes, full test/lint/compile outputs, rank windows/partial coverage, raw-payload equality or first failure, new source immutability, and `PASS/FAIL/BLOCKED/NOT_RUN` matrix.

Return **one final report to GPT**. No intermediate repeated audit requests or lane-by-lane feedback; independent safe lanes should continue when another is blocked, but don't execute dependents of failed identity/source checks. **DS_PRO does not patch code or declare Gate B0 closed.** GPT will independently review the combined exact-SHA evidence once and issue separate Gate verdict. No GPU, torchrun, Nsight, model load, checkpoint migration, formal training or inference is authorized here.
