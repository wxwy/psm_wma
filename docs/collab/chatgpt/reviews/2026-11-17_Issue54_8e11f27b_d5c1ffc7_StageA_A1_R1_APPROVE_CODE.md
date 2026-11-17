# Issue #54 / Draft PR #55 — GPT independent F1/F2 narrow re-review

Date: 2026-11-17. **Technical verdict: APPROVE_CODE**, scoped to the A1 corrective code, CPU regression and real-source contracts described below. **F1, F2a and F2b are closed for this fixed implementation.** This is not a new-profile native F27/pixel acceptance, an A2 delivery, a production-configuration freeze, permission to merge, or training readiness.

## 1. Fixed versions and execution boundaries

- Formal Root: `8e11f27bb8e6e8d29c353a56acd0e15da1ddb2a8`.
- Cosmos Child/Gitlink: `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`, unchanged.
- Previous implementation: `27ccadb051a71adf348ee14206d7ac59e9195d36`; previous review-only parent: `8a23a91226d717c0fddb4807bf65b4822e26d9b7`.
- PR head observed before this review publication: `15713ec7a41bf343d226d4191b27ef76f8f8d5b4`, a documentation handoff child of the formal implementation.
- PR #55 remains stacked on unmerged #53 at `d36caf0fc35f3a84b739dc8df58ab992eb9f6917`.
- V3 observed from current fetch and advertised ref: `fe1089fb925d86697bebd9bef18608d9c9eae87b`. Server production root remains `875ad79189a4aaa903849b6a5a4cea0eaf62e523`; nav local G2 `70eb7b447e65d793b0ebe18b258291ce46f057c1`. These checkouts were not switched or edited.

An independent detached Root/Child checkout was created on the authorized data server. Existing interpreter only:

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
Python 3.13.11 / Torch 2.10.0+cu128 / PyArrow 21.0.0
pytest 9.0.2 / NumPy 2.2.5 / Pillow 12.2.0 / Pandas 2.2.3
MuJoCo 3.3.1 / Ruff 0.12.7
```

No environment creation, dependency installation or overlay. Tests used `CUDA_VISIBLE_DEVICES=''`, fixed-source PYTHONPATH and `PYTHONDONTWRITEBYTECODE=1`. No GPU, Wan model, weights, new F27 replay, full production or training. Original data and earlier evidence were not changed; no server commit/push. Repository publication is reports/aggregate evidence only through the GitHub connector.

## 2. Independent execution results

| Group | Passed | Failures / errors / skips | Pytest elapsed |
|---|---:|---|---:|
| Approved #53 regression | 283 | 0 / 0 / 0 | 9.68 s |
| Stage A, including actual temporary Parquet tests | 103 | 0 / 0 / 0 | 1.75 s |
| Producer / marker / viewer related regression | 45 | 0 / 0 / 0 | 1.58 s |
| **Regression total** | **431** | **0 / 0 / 0** | Separate runs above |
| Original unchanged reviewer probe file, separate from regression total | **3** | **0 / 0 / 0** | 0.25 s |

The author's ten PyArrow skips and three original MuJoCo/Pandas skips were **all actually executed and passed** in this environment. No installation was needed. Do not add the three original reviewer probes to the regression count as if they were new production-suite identities; report 431 regressions + 3 unchanged probes separately.

Original 378 testcase identities were compared against the prior independent JUnit: 283/283 #53, 50/50 original Stage A, and 45/45 related identities are retained. Stage A now has 53 additional identities (43 locally executed by the author plus 10 actual-Parquet cases).

All **204/204** source fingerprints match the author manifest and remained identical before/after review. The Root and Child checkout are clean. Byte-level Git comparisons confirm the approved #53 core, two cache CLIs and Child/Gitlink are unchanged. The only production changes in this corrective commit are:

```text
g2/offline/language_context.py
g2/offline/task_entities.py
g2/offline/stage_a.py
```

Function/class AST equality also confirms `resolve_caption_rows`, `enhance_caption`, `split_text_record`, `TextBank`, `source_entity_index` and `bind_task_entities` algorithms are unchanged. Changes to the role-table constants and the new normalization function are intentional; the profile validator adds the stale-role-version guard.

Selected Ruff checks and **16-file format** pass. JS syntax, clean/marked variants smoke, actual viewer loadEpisode on a synthetic package, synthetic package creation and strict validation pass. These are code/synthetic checks, not real new-profile image acceptance.

## 3. F1 closed: actual authoritative caption table

The actual flat table has integer `task_index` and string `__index_level_0__`. The new `normalize_task_table` correctly maps this to internal ID/text without changing the source dataset or instruction. It also preserves canonical `task_index + task` and the inverse integer-index/task layout. Duplicate/illegal IDs, missing identity, invalid text and conflicting aliases are rejected. Numeric row-index metadata does not replace explicit task IDs.

The **entire original three-probe file** was executed unchanged, with native PyArrow imports (no AST stripping, monkeypatch or fake Arrow). Its SHA256 remains:

`860424fa81b6447cb361d7272ff0a365dfef6ef6087b0a3f51ab97f63fd306e0`.

The exact original Parquet correctness assertion now passes. The previous real-source probe was also replayed with **only its output evidence path rebound**, leaving production calls and input selection unchanged: all four prescribed real initial-frame calls pass, rather than the prior four failures.

The review then expanded to the full raw-frame caption streams of five real episodes:

| Task / episode | Raw frames checked |
|---|---:|
| CloseBlenderLid / 000000 | 361 |
| CloseFridge / 000502 | 429 |
| NavigateKitchen / 002104 | 110 |
| PickPlaceCounterToStove / 004540 | 260 |
| PickPlaceDrawerToCounter / 005077 | 459 |
| **Total** | **1,619** |

For every requested frame, the unchanged production loader returned the matching episode/frame/task ID; original text UTF-8 bytes match the independently read authoritative task table and `ep_meta.lang`. The production authority-file hash checks remain active. This closes the real-layout incompatibility; no unverified `ep_meta` fallback was used.

## 4. F2 closed: independent lid and source plate

### CloseBlenderLid

Real episode 000000 now includes both exact source instances:

```text
target           -> fixture:blender_main_group
manipulated_lid  -> fixture:blender_main_group_auxiliary_main_group
```

The separately represented lid is not treated as a fabricated part of the body. The original unchanged independent-lid assertion passes. Missing or multiple candidate lids remain unresolved rather than selecting the first one.

### PickPlaceCounterToStove

Real episode 004540 now retains four distinct roles:

```text
target                 -> object:obj
source_container       -> object:obj_container
destination_object     -> object:container
destination_reference  -> fixture:stove_right_group
```

The original source-plate assertion passes. Exact object_cfg/source/SG evidence is still required; no unlisted container is invented and actual distractors are excluded.

The rule version is now `robocasa_atomic_initialization_roles_v2_candidate`. The added validator guard and its corruption/resigning regression reject an otherwise self-consistent old v1 task set on resume, preventing reuse of the prior incomplete results. Existing assets are not overwritten or migrated in place.

### Real semantic checks, not only BOUND counts

A separate reviewer-defined expected-role specification was applied to one existing episode from **each of 18 Atomic classes**. It does not read the product's FIXTURE_RULES/OBJECT_RULES to derive expectations. Each expected role is resolved from the corresponding initialization metadata, and compared against exact returned source instances, all parts and all SG IDs. All 18 sampled task cases pass. Checks include exclusion of NavigateKitchen's initialization-only source, the non-exclusive related counter for DrawerToCounter, and the original stove knob identity without inventing a knob-to-SG part binding.

For the five episodes above, first/middle/last spatial states were additionally resolved: **15 current SG/text checks pass**. The actual unchanged candidate text builder receives the repaired task sets, preserves the complete instruction, includes all required source-role facts with zero omitted facts in these samples, and produces identical text/hash on repetition. This demonstrates propagation of the lid/plate into candidate text. Additional-view union propagation is covered by explicit synthetic member tests; this review does **not** claim a measured real extra-view count without regenerating native projection/membership output.

These are representative checks, **not certification of every variant in all 9,126 episodes**. In particular, ambiguous metadata or a genuinely absent mandatory source role still fails explicitly. Language fields/budget and production parameters remain candidates.

## 5. Diagnostic files generated this turn

Canonical server review root:

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue54_a1_r1_review_8e11f27b_20261117/
  source/                         fixed clean Root/Child
  evidence/
    pr53.log / pr53.xml
    stage_a.log / stage_a.xml
    related.log / related.xml
    original_probes.log / original_probes.xml
    environment.json
    source_before.json / source_after.json
    real_probe_rebind.json
    real_source_contract_probes.py / .log / .json
    expanded_real_source_review.py / .log / .json / .html
    protocol_sample/               explicitly synthetic new-profile example
    result_audit.json
    artifact_sha256.json
```

Real source data, images, complete JUnit and private detailed source observations remain on the authorized server. The repository receives this report, replay commands and an explicitly derived aggregate JSON, not a byte-identical copy of the private real-source outputs.

Candidate-language diagnostic preview, verified HTTP 200:

`http://127.0.0.1:18765/g2_stage_a_f1f2_8e11f27b_20261117/index.html`

This is a local preview of current-source text, not a final production package or template approval.

Server evidence fingerprints:

| File | SHA256 |
|---|---|
| result_audit.json | `ed9fbf72b72c4f85c6093bdd892536922cae9d8bfa8de3da707abe2841affca4` |
| source_before.json | `2f6b2fcc4ac9b20d2fdc0cc9b63ed33feff0c814c186e851f5cab0620cdec86f` |
| original_probes.log | `77d92cd56cd64a1a5b65adac4e344cc7fd9699faace17014c0a319c92f46082d` |
| real_source_contract_probes.json | `b4c905214af4fa2597f7a6963dab7a569a62e5316d5d81855d5dc9773e297a3b` |
| expanded_real_source_review.json | `089110af7be470752a44ecbb3f8b1c1cfb9e1d96c069ccc56043e876f57e5f1c` |
| expanded_real_source_review.py | `ed70cb22eb22a1196c051465af9a8f2cfe80fb66394706e6517ccc470cb92b89` |

## 6. Next action and boundaries

No further F1/F2 correction is requested at this SHA. Preserve the reports and completed corrective source.

- GPT's next real producer gate is the four prescribed isolated Stage A samples: clean and `_w_rbs` images, projection/scale/arrow consistency, current member versus image-owner metadata, selected-view indices, generated task/text files and strict profile verification. This is **pending**, not counted in the present approval.
- Codex can continue the already-authorized **separate A2 increment** from the reviewed source: actual consumer, bounded queue/backpressure, durable ACK/recovery, shared-core sealed-source post-hoc adapter, per-view final writing/verification, owner reconciliation and safe cleanup. Preserve #53 core and regression, keep A2 commits separately reviewable. Do not represent an enqueued event or SOURCE_READY as full completion.
- A2 VAE profiles still stop at SOURCE_READY/75 until that implementation is delivered and accepted. No new-protocol streaming/post-hoc VAE parity or performance claim is made here.
- Keep Draft PR #55 and #53 unmerged; no V3/Child/nav updates. Template, image size, dtype, batch and resource settings are not frozen by this approval. No full corpus generation, state15, joint alignment or model training yet.

**Final: F1/F2 CODE/CPU + representative real-source contracts PASS. A1 new-profile native/pixel acceptance and A2 remain distinct pending gates.**
