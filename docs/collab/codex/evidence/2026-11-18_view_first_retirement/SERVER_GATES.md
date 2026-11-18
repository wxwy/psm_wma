# Fixed-source author server Gates A–D

2026-11-18 CST. **AUTHOR_SAMPLE_PASS; independent GPT approval pending.**
This report does not approve corpus retirement, merge or training.

Formal implementation Root `5c7ea400035e2727a2dae1d63dfe7d21b14b9ff2`,
Child/Gitlink `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`, nav G2
`70eb7b447e65d793b0ebe18b258291ce46f057c1`.
Draft [PR67](https://github.com/wxwy/psm_wma/pull/67) targets V3
`b6311222c364543787f913215bf584065aa1c275`; advertised V3 was freshly checked
again after the real Gates and still matched that base.

## Source and environment

Remote Desktop Commander connected to `data`. Fixed repository code was
fetched from GitHub into this **new isolated** checkout:

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/
  .g2_view_first_posthoc_gate_5c7ea400_20261118/
    source/       # detached formal Root and exact Child
    cpu/          # original-environment raw CPU logs/JUnit/hash proof
    samples/      # two on-server copies, B/C spools and real receipts
    recovery/     # one additional Fridge cache copy, real crash/parallel resume
```

Original running producer Root stayed b6311222, Child d5c1ffc7 and nav70eb7b44;
all tracked worktrees remained clean. No server commit/push or production
source/config change occurred. Only completed Blender/000000 and Fridge/000502
were copied on-server. Images, raw states/models, compressed sources, weights
and original logs were not exported. The repository holds derived metadata,
hashes and command text, not these private inputs or raw server files.

Existing project interpreter (no installs/new environment):

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
Python3.13.11; Torch2.10.0+cu128; NumPy2.2.5; Pillow12.2.0;
pytest9.0.2; Ruff0.12.7; PyArrow21.0.0; MuJoCo3.3.1; Pandas2.2.3
```

Project numerical/cache/retirement CLIs used that interpreter and explicit
fixed Root/Child PYTHONPATH, with no nav `g2` path. Read-only orchestration,
checkout and the initial sample claim/copy wrapper also used host `python3`;
they installed nothing and did not encode or perform the retirement engine.
The real recovery probe used the original PSM interpreter throughout.

The existing local interpreter separately reported599 PASS/13 optional SKIP;
the unchanged full server run reported **612/612 PASS,0 FAIL/ERROR/SKIP**.
All560 baseline IDs and all105 old test source files remain. All246 tested
product source hashes match fixed Git blobs and remained stable through the
real Gates. Original encoder/core/producer/model/Gitlink stayed unchanged.
The local read-only peer independently reported4/4 adversarial probes PASS;
these are separate from612 and are not summed as disjoint cases.

The initial local supervisor25s timeout, unchanged focused pass and full pass
remain in local raw evidence. The server full regression passed; this does
not establish the initial timeout's root cause or rewrite its failed log.

## Actual Gates and consumer closure

| Gate | Executed result |
|---|---|
| A | Both published View-first packages validate; exact gzip/raw hashes, source IDs and all copied bytes agree;81states/12views/169physical owners |
| B | Actual H100/Wan B1/T1/256×256,169records in12per-View files; independent reencode169/169 with max_abs_error=0,atol=rtol=0; originals unchanged |
| C | Existing v2 protocol publishes compact source and independent posthoc receipt; final source/cache consumers pass; all original products and PT bytes unchanged; gzip/fullJSON/oldreceipt/oldREADY/journal absent; repeat succeeds |
| D | Real Fridge cache copy, hard exit77 after gzip unlink before final COMPLETE; journal persists and COMPLETE is absent; no-resume returns75; two actual concurrent resumes return0/busy2; two public retries return0;80records/allproduct/PT hashes unchanged; zero fabricated events |

B spool has two completed tombstones and zero active jobs/events/results after
its own publication. C-only handoffs are genuine verified complete caches,
with no invented stream ACK. The real D probe exercises **one** deletion
boundary and actual two-process concurrency;23 additional hard-exit boundaries,
ENOSPC, live-reader and other failures are CPU synthetic tests. It does not
claim every injected failure was rerun with real Wan data.

After C, both episodes were sent through the build CLI again with the same
recipe/spool and `CUDA_VISIBLE_DEVICES=''`. Both returned already_complete/
retired; every final file remained byte-identical, no encoding occurred and
no full JSON was recreated. The original published source episodes were
rehashed at the end and remained byte-identical. `tmux view` remained alive.

Recipe:
`3ee9c48399143866b2a0061f3cee01bff35842228f639380d60602d6402e2fc1`.

## Measured bytes and times

File byte totals below include all episode files; allocated block bytes and
individual file hashes remain in the private receipts/derived machine summary.
Decoded raw bytes are **not** claimed as disk space reclaimed from gzip.

| Episode | View-only MiB | With cache, before C MiB | Final MiB | Saved MiB | Gzip B | Final index B |
|---|---:|---:|---:|---:|---:|---:|
| Blender000000 |19.23|23.60|22.14|1.46|1,698,701|162,976|
| Fridge000502 |24.38|28.33|26.99|1.34|1,571,936|158,160|

Raw decoded source sizes were33,871,612/30,364,617 bytes; gzip ratios were
19.940/19.317. Final source indices remain well below the existing1MiB bound.
Numeric/PT and product bytes did not change. Total net measured reduction
after B was2,940,281 file bytes across the two samples. No corpus estimate is
inferred from these two episodes.

- B end-to-end267.95s (0.631records/s), including repeated source validation,
  bounded admission/ACK, encoding and cache assembly. This is not pure Wan,
  render or sixview latency, and is not a9,126-episode throughput commitment.
- Strict independent reencode30.57s, separate process/model and physical GPU4;
  initial B used GPU6. Existing view contexts shared those GPUs. Sampled peak
  GPU6 total usage was7,569MiB, including other contexts, not VAE-only memory.
  GPU0–3 were excluded; no existing task was stopped or reconfigured.
- C plan11.39s, execute58.92s, repeat11.34s. Collector attempt metrics were
  7.42/8.08s; they exclude other CLI validation/handshake work and must not be
  relabeled as the complete retirement command's latency.
- Real D crash/recovery/concurrency/retries62.32s. Retired B-entry retry10.67s.

## Commands, protocol and remaining scope

[server_commands.json](server_commands.json) records exact issued command
strings, flags, fixed paths/environment, resource checks and failpoint. These
are historical sample commands, not a script to rerun against existing or
production directories. A new independent run must use a fresh Gate/sample
root and a correct new-root claim, keeping the formal code fixed.
[server_summary.json](server_summary.json) binds actual results and private
log/JUnit/receipt SHA256 and byte sizes. All raw evidence stays under the
server Gate root above. [The runbook](../../../../build/PSM-WMA_G2_view_first_posthoc_retirement_2026-11-18.md)
contains interfaces, recovery rules, before/after structure and corpus command
drafts. Final data needs the new posthoc-aware verifier; old data stays
supported by it. The old producer is not changed during its ongoing run.

NOT_RUN: new real F27/native regeneration (existing published Views are reused),
full9,126 VAE/retirement, corpus release, independent GPT approval, training,
production configuration change or merge. Original large sources remain in
the active production root. Full retirement is an explicit later owner action
after independent acceptance and completion of the View task; two samples do
not authorize it. `training_ready=false` remains explicit.
