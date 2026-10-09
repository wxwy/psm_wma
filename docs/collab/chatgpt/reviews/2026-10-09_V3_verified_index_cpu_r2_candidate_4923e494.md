# PSM-WMA V3 — Verified Dataset Index CPU Round 2 Candidate Audit

Date: 2026-10-09
Owner / code reviewer: GPT/Codex
Decision: **CANDIDATE_READY_FOR_CPU_RETEST; NOT CPU GREEN; COLD/WARM REAL CORPUS NOT YET TESTED**

## Source and immutable target

- Candidate Root: `v3-persistent-dataset-index-pair-20261009`. Parent immediately before this review ledger: `c4086107df7175da68b457c30abbba16def92ecc`.
- Candidate Child: `v3-persistent-dataset-index-20261009`, exact Child/Gitlink commit: `4923e494a8bb0e1e18d7943ae00bd17f71498d88`.
- Authoritative full Root commit for this review is the HEAD commit containing this review (obtain with `git rev-parse HEAD`; never substitute the parent SHA).
- Production `V3` and `v3-local-ttt` remain unchanged.
- The Gitlink in the reviewed parent pointed to exactly `4923e494a8bb0e1e18d7943ae00bd17f71498d88`.

## Scope and evidence reviewed

- Compared complete candidate-vs-production changed-file inventory, prior failed candidate vs current fixes, and inspected the current verified index, cache/source/SFT/Local/Phase5 code paths.
- Previously tested, rejected DS_PRO pair: Root `bb89741916ff13b934c437a5213837256daa568a` / Child `f7d0897e9c801c044c52dd70f4d8a7ae4663d579`.
- Previous DS_PRO evidence: new index **10 passed**; Source/Cache/SFT **123 passed / 1 failed**; Ruff I001 failed; Ruff formatter failed three files; py_compile passed.
- The subsequent Child candidate contains the terminal-window error precedence fix, correct import ordering, Ruff-aligned implementation/test/builder formatting, and additional schema/metadata invalidation + cold/warm sample/Local/config-digest parity tests.
- Last Child commit `4923e494a8bb0e1e18d7943ae00bd17f71498d88` contains only verified-index test-format changes. The Root review update changes no Child code.
- Warm construction uses stat/content witnesses + verified bindings + mmap row map, while normal runtime read retains identity/action/state/latent validation. The warm file witness is **not** a full cryptographic verification of 451GB latent payloads.
- No independent Ruff 0.12.7 executable, PyArrow/LeRobot CPU test environment, or actual 9126-episode corpus is available to this reviewer. **No PASS is claimed for this current pair.**

## DS_PRO targeted CPU Gate (mandatory, first)

Operate in the sole existing `psm_wma_v3` directory. Never create a worktree or clean/reset/rewrite `SESSION.md`, `TODO.md`, old Evidence, code or checkpoints. DS remains a read-only source validator and evidence executor, not a code writer.

1. Fetch candidate branches; confirm exact Root HEAD from this review's commit, Child HEAD `4923e494a8bb0e1e18d7943ae00bd17f71498d88`, Root Gitlink equals Child, Child porcelain clean. Record the three full SHAs.
2. Export `HF_HUB_OFFLINE=1` **before** running pytest.
3. Run `robocasa_verified_index_test.py`, `robocasa_exact_window_source_test.py`, `robocasa_exact_window_cache_test.py`, `robocasa_exact_window_cached_sft_test.py`, `robocasa_exact_window_local_test.py` (under `cosmos_framework/model/generator/mot/`), and `examples/psm_wma_robocasa_corrected_phase5_test.py`, with pytest cache disabled.
4. Run `ruff --version` (expect **0.12.7**); `ruff check` and `ruff format --check` on eight changed index/source/cache/SFT/Phase5 implementation+test entrypoints, using project `.ruff.toml`; run `python -m py_compile` on those same files.
5. On any failure, STOP, report complete stderr and for formatter failures `ruff format --diff`. Do not edit files or declare GREEN.

## Conditional real corpus Gate (ONLY after CPU all GREEN)

- Single process, CPU only, no torchrun/GPU: build once to a fresh, external `--index-root` using the accepted source/cache. Never overwrite an existing index. Capture whole wall time, per-stage timing and digests; record receipt size, mmap size and hashes.
- Separate read-only `--verify-existing` and corrected Phase5 `--preflight --dataset-index-root` with frozen formal 30000/500/100, T16/B8/GA2/K4/world_size8, official DROID baseline. Expect `config_digest=70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`; compare source/cache/manifests, ordered episodes, sampled raw action/state/latent/global-rows and Local segment against cold witnesses.
- Demonstrate warm constructor does NOT call cold `_corpus_digest`, `_bind_episode`/identity scanner, or cached `.pt` episode loader; make timing attribution for LeRobot/HF init explicit rather than assuming optimized startup.
- Any mismatch or unresolved slow stage => BLOCKED with evidence.

**Authorization boundary:** CPU targeted test only now; after CPU all pass, ONE real cold build + read-only warm preflight are authorized. The paused 8xH100 3-step bounded GPU diagnostic and formal 30k training are **not authorized** by this review.
