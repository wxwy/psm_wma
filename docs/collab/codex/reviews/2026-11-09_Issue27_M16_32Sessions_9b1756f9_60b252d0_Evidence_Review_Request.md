# Issue27 streaming M16:32 Sessions — Evidence-only review request

Date:2026-11-09 CST. Author:Codex. Status:**author focused CPU PASS; fresh GPT
Evidence review requested**. The previous independent REQUEST_CHANGES is not
closed by this author report.

## Exact pair and correction

| Authority | SHA |
| --- | --- |
| New test-only Formal Root | `9b1756f9099955d6637743f8ad2fa0ee54987b7a` |
| Unchanged Child/Gitlink | `60b252d05157b2753d2caebae32b11c878504bbe` |
| Previous production Formal Root | `15dbc97bf13437905ec38247382834067e5341ae` |
| Consumed reviewer docs/Inbox head | `b5127c82d40af7061448e6a83a922a019721517f` |

`2x16` means **2 Policy Servers x16 Sims/Server =32 total**, using the existing
streaming M16 protocol. My previous total16 interpretation was wrong. The old
two/eight tests and965+207 author results remain unchanged historical evidence;
they are not relabeled as32 or counted as newly rerun. This supplement addresses
only the MEDIUM test/Evidence gap in
`docs/collab/chatgpt/reviews/2026-11-09_Issue27_15dbc97b_60b252d0_GenericTopology_Evidence_REQUEST_CHANGES.md`.

Root PR29 and Child PR8 remain the same independent Draft PRs. Only Root tests,
CPU fixture, representative runbook row and bookkeeping change. Full Root
`scripts` tree is byte-identical to15dbc97b; Child remains clean at60b252d0.
`production_identity.json` records the exact matching trees. Later evidence/docs
commits do not replace the new Formal Root. No production, Gitlink, scheduler,
Batch math, Local-TTT, source, deadline or M/B Resume behavior changed.

## Minimal test increment

- `shared_vae_routing_test.py`: replace the old Namespace/physical_slots128
  fixture with actual existing `Store`, frozen Manifest and `Runtime` layout.
  The test injects CPU model/device boundaries through existing seams and wraps
  original `_spawn`/`_proof`, retaining real Registry/process ownership and raw
  proof persistence. Actual run lease, Manifest digest, Runtime Slot IDs and
  capacity profile reach native transactions and scoped Worker registration.
  Existing one/one and one/eight cases remain in the focused run.
- `shared_vae_streaming_m16_test.py`: mandatory two render GPUs/two Workers and
  complementary same-render one Worker cases, each with32 simultaneous approved
  Sessions under a frozen18-Task streaming Manifest. Native actors receive
  `streaming32` and16 slots each; no round/task-count or legacy8 stand-in.
- `shared_vae_daemon_fixture.py`: optional public CPU clock label, defaulting to
  the old label for original FD tests. The new case agrees with the native
  transaction parser's explicit kernel fixture. This is a CPU clock double;
  production daemon/clock/CUDA attestation has no bypass or new CLI switch.
- Runbook representative row corrected to32total/M16. Original review, raw
  archives and their historical counts are preserved. **No #28 sparse update
  code/config is included.**

## Exact clean-pair author Gate

**18/18 PASS**,0failures/errors/skips, shell exit0, gate.status=PASS.
Three changed Python test/fixture files pass Ruff/format/syntax; all1375 hashed
source files unchanged during execution; Root production tree and Child
unchanged, exact pair clean before/after. Original16 regression cases plus2 new
M16 cases are counted once; development runs are not added to the final count.
No repeat of the old965 full CPU suite was required for this test-only increment.

Raw directory:
`docs/collab/codex/evidence/2026-11-09_issue27_streaming_m16_32_sessions/`.
See `summary.json`, `production_identity.json`, `author-01/gate.json`, original
`focused.xml`/logs/source hashes, `author-01/scenarios/` and `artifact_hashes.json`.

| Actual CPU layout | Frozen native Sessions | Worker processes | Native generation per Policy | ACK/End per case |
| --- | --- | --- | --- | --- |
| 2 Servers x16 Sims,2 render GPUs | 32;16 per Policy | 2;16 per Worker | B8+B8 | 32 Policy ACK,32 Worker ACK,32 scoped End,32 native End |
| Same layout,shared render GPU | 32;16 per Policy | 1;32 Sessions,2 Policy epochs | B8+B8 | same32 counts |

Both cases assert:

1. Real persisted Manifest matches the Store, streaming schedule/M16,32 Runtime
   slots from18Tasks, strict streaming32 native capacity and full frozen identity.
   All32 unique Session/Slot IDs and2 distinct Policy epochs are approved by their
   correct Owner; actual READY limits attest16/1 or32/2 Session/epoch capacities.
2. Original executors generate B8+B8 per Policy, with distinct per-Session actions
   mapped correctly. Native responses are ACKed and retained for real Owner chunk
   verification. A legitimate unit rotation is used in synthetic raw15 actions.
3. Real scoped Unix relay/Owner HTTP issue and completion authorize step0 boundary
   reuse and step1 Worker submission for every Session.32 signed Worker features
   are checked against the exact lease/manifest/identity/epoch/source/clock, then
   ACKed. Duplicate chunk/completion/submission/ACK/End preserve the original
   response; Worker histogram contains only Bvae1 and zero queued items after ACK.
4. Wrong Worker capability, stale assignment generation and foreign Policy lease
   are rejected before altering approved state. First End leaves31 Sessions and
   live Workers intact. All32 scoped and native End acknowledgments complete.
5. Original Registry owned groups are used, actual owned CPU RSS is measured and
   startup reservations release; unrelated process is excluded from ownership
   and survives. Worker exit codes are0, sockets/directories are removed, repeated
   supervisor close is idempotent. Public raw READY/close receipts and Session
   bindings are retained; private bootstrap/capability files are not archived.

The synthetic Owner completion controls do not prove env.step. Wan encoder,
native generation/current Policy boundary, physical GPU and kernel identity are
explicit CPU doubles. These tests prove the requested process/Session/transport
contract; they are not real GPU Action parity, performance, task SR or Episode
completion evidence. No real checkpoint/remote server files were accessed.

## Original failures retained

`development-01`:16PASS/2FAIL; `development-02`:isolated2FAIL. Added HTTP diagnostic
trace showed the CPU generator had zero/collinear6D rotation columns, correctly
rejected by the unchanged raw15->env12 canonicalization before Worker data use.
Only that test action fixture was corrected to unit rotation. Original JUnits,
logs/source fingerprints and available as-executed fixture snapshots are retained.
`development-03`:2PASS. Final exact clean-pair18PASS follows the final proof fields.
This was a fixture data error, not evidence of a production defect.

## Reproduce and next boundary

Working directory `/workspace/work/psm-wma-shared-vae-issue27`:

```bash
/workspace/.venvs/psm-wma-cpu/bin/python \
  /workspace/work/issue27-m16-evidence/run_focused.py \
  --root /workspace/work/psm-wma-shared-vae-issue27 \
  --expected-root 9b1756f9099955d6637743f8ad2fa0ee54987b7a \
  --evidence-dir /workspace/work/issue27-m16-evidence/author-01
```

For independent replay use the archived `runners/run_focused.py`, exact clean
Root/Child checkout and a NEW evidence directory. It sets CUDA visibility empty,
model libraries offline, numeric threads1, pytest autoload off and external
caches. Inputs are synthetic, no checkpoint. PASS requires zero failures/errors/
skips, both32-Session proofs, unchanged production/Child and source fingerprints.

Request: GPT review this test/Evidence-only increment against the existing MEDIUM
gap, then determine #27 closure. **#28 remains TODO until #27 qualifies**; its sole
planned knob is `local_ttt_history_k` default16, K1/2/4/8/16, boundary index0 reused,
unselected frames without history VAE/FW. No sparse implementation is mixed here.
No GPU/real RoboCasa/SR/900EP/training, old-job operations or V3 merge is authorized
or performed by this handoff.
