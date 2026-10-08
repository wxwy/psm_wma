# Corrected V3 — Dataset Acceptance Receipt / Round-3 Count Audit v0.1

Date: 2026-10-08  |  Scope: **tools-only, opt-in**  |  Owner-authorized GitHub implementation by GPT.

## 1. Scope / authority

- Root parent: `597ce73d3c3cd4ac4d4a2e34db2c18e6a3e3e446` (`V3`).
- Production child/Gitlink: `8c3800565f66cfbce2929264f1c2a7854137482e` (unchanged).
- Corrected V3 design v3.0 + Phase1A/1B/2/3/3.5 + Owner's 2026-10-05 Phase3.5 refreeze remain authoritative.
- This change **does not** alter `RoboCasaExactWindowCacheCatalog`, `RoboCasaExactWindowSourceReader`, `Wan2pt2VAEInterface`, the trainer, checkpoints, or any existing Gate verdict.
- Existing Phase3.5 exact threshold `0.0` remains frozen. The new receipt is not a threshold change, a parity verdict, or permission to start formal 30k training.
- The training server is operational and accessible to DS_PRO. Only GPT's remote device connection is unavailable; therefore the original Round-3 JSON and production cache files have **not** been independently inspected or modified by GPT. Tests use synthetic fixtures only.

## 2. Problems addressed

1. Round-3 report claims `4/9` non-exact for A/B and A/C, while the listed per-window facts comprise **3 non-exact and 6 exact**. This is a report inconsistency, **not** independently corrected raw evidence. `tools/v3/audit_round3_parity.py` calculates counts directly from a normalized per-window JSON record, rejects duplicate identities / missing comparisons / non-finite or contradictory metrics, and returns nonzero on any claimed-count mismatch. It does not fabricate or overwrite DS_PRO evidence.
2. Expensive full-cache structural auditing and real Wan VAE parity should not be repeated merely because a training launcher is restarted. `tools/v3/dataset_acceptance_receipt.py` makes a **draft** recording original evidence, relevant code/weight identities and a one-time content-hashed file inventory. A separate explicit review and external HMAC signing key are required to create an `ACCEPTED` receipt. Only approved receipts can be verified as reusable evidence.

## 3. Three receipt operations

### A. `draft` — evidence snapshot only

Inputs: exact-window cache root, flat LeRobot v3 source root, evidence index JSON, full cache corpus/source binding digests, VAE weight SHA256, full runtime/builder Git SHAs. The tool checks manifest counts and declared-vs-discovered episode payloads, computes SHA256 for every selected file (cache manifest + `.pt` episodes; source `meta` + `data` and optionally `videos`), captures file size/mtime, and records B3/B4/B5/P3P5 evidence file SHA256 and observed PASS/FAIL/OPEN.

Output: `schema=psm_v3_dataset_acceptance_receipt_v1`, `status=EVIDENCE_ONLY`, no signature and no approval. Drafting is a **one-time I/O-heavy** operation: hashing a 451 GB cache has a real I/O cost, but **does not load or invoke the VAE**. Recording full source videos may also take substantial time and space-bandwidth. Original source/data/manifest files are never changed.

The separate evidence-index JSON uses:

```json
{
  "schema": "psm_v3_acceptance_evidence_index_v1",
  "cache_manifest_sha256": "<64hex>",
  "cache_corpus_digest": "<64hex>",
  "source_binding_digest": "<64hex>",
  "vae_weights_sha256": "<64hex>",
  "runtime_commit": "<full 40hex child sha>",
  "gates": [
    {"name": "B3", "status": "PASS", "evidence_path": "/absolute/path/B3.json"},
    {"name": "B4", "status": "PASS", "evidence_path": "/absolute/path/B4.json"},
    {"name": "B5", "status": "PASS", "evidence_path": "/absolute/path/B5.json"},
    {"name": "P3P5", "status": "FAIL", "evidence_path": "/absolute/path/P3P5.json"}
  ]
}
```

This is a **schema example**, not a substitute for the original Round-3 evidence held on the training server. Each JSON evidence must itself contain a consistent top-level `status` or `gate.status`. B5 is builder self-reproducibility **only**, never a substitute for P3P5 current-runtime parity.

### B. `approve` — separate owner/GPT review and signing

Prerequisites: all four gates PASS under separately reviewed applicable contracts; source videos included in inventory; approval review file contains the exact literal `APPROVE_V3_DATASET_ACCEPTANCE_RECEIPT` **and** the exact cache manifest SHA256 and source binding digest; a secret key file of at least 32 unpredictable bytes outside source control. An `EVIDENCE_ONLY` draft with P3P5 FAIL/OPEN can **never** be promoted to ACCEPTED. The resulting receipt binds review SHA256 and HMAC-SHA256. The CLI never overwrites the draft.

This is an additional cryptographic attestation, **not** an assertion that the code itself can grant Owner approval. The signing key is controlled by GPT/Owner and must never be committed or given to an untrusted build job.

### C. `verify` — offline receipt reuse

Checks the receipt signature, schema/status, runtime child SHA, VAE weights SHA256, source binding digest, current manifest SHA256 and complete file-path inventory.

- `--mode full` (default): re-hashes every inventoried file; strong byte-integrity verification without VAE but still I/O heavy.
- `--mode fast --trust-immutable-storage`: compares file paths, sizes and `mtime_ns`, plus current manifest SHA; requires an **explicit declaration of trusted immutable storage**. This is efficient but cannot detect malicious rewrites that preserve file metadata. It is **not** cryptographic proof of unchanged file bytes. If dataset mutability cannot be controlled, use `full`.
- Changes to manifest, VAE hash, runtime commit, source digest, content, file set, or signature cause nonzero fail-closed. Path relocation is allowed with `full` if bytes and semantic authority match.

Preferred output location for an eventual approved receipt: `cache_root/.validation/acceptance_v1.json`. A draft should be written in a separate evidence area such as `/tmp` and reviewed before signing; this implementation does **not** write anything to the actual training server.

## 4. Actual commands (DS_PRO can execute CPU-only verification now on the available training server)

```bash
# CPU only, read-only input; nonzero is expected while the Round-3 report is inconsistent.
python tools/v3/audit_round3_parity.py \
  --input /tmp/.../gate3_part1_encode1_abc.json \
  --claimed-a-b-non-exact 4 --claimed-a-c-non-exact 4

# CPU/disk I/O only, no VAE. Requires a complete evidence-index JSON.
python tools/v3/dataset_acceptance_receipt.py draft \
  --cache-root "$CACHE_ROOT" --source-root "$SOURCE_ROOT" \
  --evidence-index "$EVIDENCE_INDEX" \
  --corpus-digest "$CORPUS_DIGEST" --source-binding-digest "$SOURCE_BINDING_DIGEST" \
  --vae-sha256 "$VAE_SHA256" --runtime-commit "$CHILD_SHA" \
  --builder-commit "$BUILDER_SHA" --include-videos \
  --output /tmp/v3_acceptance_draft.json

# Only after Owner/GPT has explicitly closed P3P5 and signed a review; NO current authorization.
python tools/v3/dataset_acceptance_receipt.py approve \
  --draft /tmp/v3_acceptance_draft.json --review-file "$APPROVED_REVIEW" \
  --key-file "$PRIVATE_SIGNING_KEY" --output "$ACCEPTED_RECEIPT"

# Future repeat validation (requires explicitly trusted immutable asset storage).
python tools/v3/dataset_acceptance_receipt.py verify \
  --receipt "$ACCEPTED_RECEIPT" --cache-root "$CACHE_ROOT" --source-root "$SOURCE_ROOT" \
  --key-file "$PRIVATE_SIGNING_KEY" --runtime-commit "$CHILD_SHA" \
  --vae-sha256 "$VAE_SHA256" --source-binding-digest "$SOURCE_BINDING_DIGEST" \
  --require-gate P3P5 --mode fast --trust-immutable-storage
```

CPU regression command from root:

```bash
python -m unittest discover -s tools/v3 -p 'test_*.py' -v
```

## 5. Exclusions / next Gate

**Not implemented**: wiring receipts into existing production trainer or skipping Phase1B's `RoboCasaExactWindowSourceReader` initial full episode/window binding scan. Skipping frozen Phase1B validation requires a separate reviewed opt-in fast source-binding snapshot, with bitwise/equivalent binding tests and a meaningful immutable-data authority. A receipt alone cannot make the existing reader faster. This tools-only change intentionally avoids changing the approved `8c380056` production child and its formal-pair readiness.

Still required: DS_PRO must provide the actual raw Round-3 JSON, reconcile 4/9 against observed identities, and complete a separately frozen P3P5 numerical-tolerance Gate before an `ACCEPTED` certificate can be issued. The existing Owner refreeze allows bounded H100 readiness independently, but formal 30k remains separately gated.

## 6. Owner placement clarification — post-encode, outside training (2026-10-08)

**Acceptance occurs exactly once as an offline, post-VAE-encoding, pre-dataset-release step.** Training must neither generate nor approve nor re-run acceptance receipts, execute VAE parity, or perform any receipt-based full-file hashing. The tools introduced here are stand-alone commands, not part of the V3 trainer or launcher. Production training continues to use the already-frozen Phase1A/1B identity and per-window validation contracts; a separate explicit refreeze would be required to remove any existing checks or optimize Phase1B binding scans. A receipt is the historical data-quality witness, not a new training prerequisite or alternative to the frozen runtime guards.

**Verification status (2026-10-08):** GPT independently executed the exact GitHub blob-identical four tool/test files in an isolated local Python 3.13 sandbox: `python -m unittest discover -s tools/v3 -p 'test_*.py' -v` = **19 tests PASS**; `python -m compileall -q tools/v3` = **PASS**. Ruff was unavailable. **This is not a test on the training server**; DS_PRO can run the same CPU-only tests independently now, without changing any production/training worktrees. GPT's remote connection is unavailable, but the training server remains accessible to DS_PRO. The actual Round-3 JSON is not in committed V3, so the report's 4/9 vs enumerated 3/9 inconsistency remains awaiting raw-evidence adjudication.
