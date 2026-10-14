# DS_PRO Gate B0 final CPU receipt — Owner-relayed execution evidence

**Date:** 2026-10-14
**Evidence origin:** DS_PRO final report pasted verbatim into Owner's ChatGPT conversation (2026-10-14). DS_PRO performed execution; GPT checked the related GitHub source but did **not** itself run the executor machine commands or fetch the two /tmp JSON blobs.
**Scope:** V3 Packed128 B0 independent CPU-only diagnostic, no GPU or migration.

## Formal identities

- Diagnostic root / isolated branch: \`wxwy/psm_wma:v3-gateb-comparator-b0\` @ \`ec9d162b926c4f197f5cfb692499b4dbda888686\` (DS detached worktree reports exact clean HEAD).
- Source Index8 production: root \`b159f45906f7261d028aecc226ab7f2bb9807eb9\` / child \`937066ffd90f2bf783ad4fbb4909e9c0b8922982\`.
- Target Packed128 production: root \`c4731bca1a590663db88bd6cd74dbcf9fd513a85\` / child \`c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686\`.
- Current V3 production Gitlink \`8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1\` unrelated to comparator and unchanged.
- DS env: Python 3.13.11 / Torch 2.10.0+cu128 / pytest 9.0.2 / Ruff 0.12.7 / tqdm 4.67.3; \`HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH=''\`.

## DS_PRO's reported outputs, source explicitly qualified

| Contract | DS_PRO reported evidence | Result |
|---|---|---|
| Three diagnostic files compile | \`python -m py_compile\` exit0 | PASS |
| Regression tests, incl Native dataclass handling | 30 passed in 1.54s, exit0 | PASS |
| Ruff | \`All checks passed!\`, exit0 | PASS |
| Unauthorized B1 paired-run | exit2 with \`GPU_B1_NOT_IMPLEMENTED_OR_AUTHORIZED\` | expected negative PASS |
| Index8 \`--verify-payloads --hash-all-shards\` | exit0, JSON emitted, \`payload_witness\` nonempty | PASS |
| Packed128 equivalent | exit0, JSON emitted, \`payload_witness\` nonempty | PASS |
| \`compare-cpu-reports\` | exit0, \`matched_16_rank_windows=true\`; actual witness fields compared by helper implementation | PASS |
| Actual Native transformed Input / CFG | \`payload_witness\` exactly equal, each has 16 rank×window records and 32 64-hex GA hashes | PASS |
| Witness fingerprint | \`f4dd11b5903401d0f36d563b1955a6859a502bd4291cc79f31fbbcb1233ffcdd\` on both legs | PASS |
| Consumer plan hash | \`d5c9b17e…\` on both legs; plan.rows equality true, terminal_partial true | PASS |
| Collective rhythm | both windows × eight ranks, Index8 16+16 Native calls per GA pair | PASS |
| Source Checkpoint | \`iter_000001300\`, four DCP components, 32 shards, eight dataloader sidecars, 44 files; before/after hash-all-shards unchanged | PASS |
| Checkpoint fingerprint | \`2e409afe…\` on both legs; \`--hash-all-shards\` enabled | PASS |
| Source old vs Packed config digests | Index8 \`70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37\`; Packed \`1ab2bbe4df9954467bb0acf0d371dce40dff8bd04cfa3c81ca0ec6fe76a94b4a\` | distinct as expected |

Prior DS Lane A/C evidence reused: 8-rank 17-field sidecar profile; exact 10-key schema, nested provenance digests, fast-state 4 fp32 tensors; 9126 episodes / 18 tasks; two real iter1300 successor windows and terminal segments; older 484-path pre/post source audit zero content changes. Earlier F401/TMonitor blockers were closed on e3e6df04, the dataclass hash blocker is remediated on ec9d162b and both real CPU runs are reported exit0.

## Artifact identifiers on DS execution machine (not available through this GPT runtime)

- \`/tmp/ds_pro_v3_gateb_b0_ec9d_index8_result/gateb0_index8.json\`
- \`/tmp/ds_pro_v3_gateb_b0_ec9d_packed_result/gateb0_packed128.json\`
- Diagnostics/structure probes \`/tmp/probe_plan_fp.py\`, \`/tmp/probe_payload_structure.py\` (prior round)

GPT attempted direct Remote Desktop access to the first /tmp JSON but the connected device was offline. Therefore **the complete raw JSON bodies and their full 32 hashes were not independently fetched or recomputed by GPT**; their equality is DS_PRO's reported execution outcome. The exact comparator source was independently inspected: when both \`payload_witness\` fields are nonnull, it requires dict equality; the helper's console label \`CPU_PLAN_PARITY_ONLY\` remains legacy and is not sufficient evidence by itself. DS explicitly separately verified both witnesses nonnull and their full dict equality.

## Fingerprint consistency observation

The older \`6a4d9c6a…\` plan fingerprint was obtained with \`hash_shards=False\` (source fingerprint \`faf63ff2…\`). Current \`d5c9b17e…\` follows \`--hash-all-shards\` (source fingerprint \`2e409afe…\`). The canonical ConsumerKey includes that fingerprint, so the changed plan hash reflects a changed **hash input specification**, not reported dataset/Checkpoint drift. Same mode/identity on both current legs was enforced.

## Not established by this B0 evidence

- real 4B Cosmos3-Edge 8-rank FSDP2 DCP model/optimizer/scheduler/trainer load and strict local restore
- P0/P1 model-call-site sigma/noise witness injection and production distribution-matched stochastic sampling
- real CUDA forward/backward, complete optimizer-selected FQN gradients, TTT higher-order gradients, optimizer/moment parameter-delta parity
- Gate M DCP migration or real iter1301 Formal30k resume
- performance conclusions, Nsight stall causality, or GPU authorization

**Evidence classification:** \`DS_PRO_EXECUTOR_REPORTED / GPT_SOURCE_CONFIRMED / RAW_JSON_NOT_DIRECTLY_MOUNTED\`. Preserve the two /tmp JSON files (or upload them to an evidence archive) for later forensic recheck; this receipt is not a byte-for-byte reproduction of those artifacts.
