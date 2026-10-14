# Independent Gate B0 CPU review — dataclass Native payload hashing remediation

**Date:** 2026-10-14  
**Reviewer:** GPT, independent Evidence/Gate auditor  
**Scope:** Only isolated root diagnostic `wxwy/psm_wma:v3-gateb-comparator-b0`, **not** the frozen Index8 / Packed128 production pairs.  
**Prior diagnostic SHA (DS executed):** `e3e6df04eba7d3a5ab160b1563eee7146e1ee584`  
**New diagnostic candidate SHA:** `ec9d162b926c4f197f5cfb692499b4dbda888686`  
**Comparator source:** Index8 Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`  
**Comparator target:** Packed128 Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`  
**Verdict:** `REQUEST_CHANGES` on **old e3e6df04 B0 acceptance**; new ec9d162b is **CODE_COMMITTED / CPU_EXECUTOR_RETEST_PENDING**, not Gate approval.

## Evidence adjudication (DS_PRO 2026-10-14 final CPU report)

- Exact old diagnostic SHA `e3e6df04` Lane B: 3-file py_compile exit0; pytest 25 passed exit0; Ruff exit0; negative `--mode paired-run` exit2 with `GPU_B1_NOT_IMPLEMENTED_OR_AUTHORIZED` as intended. Earlier TMonitor import/single-thread gate blocker CLOSED; no need revisit prior e3 fixes.
- Source / Target Lane D separately passed exact pair Gitlink/import guard, source Sidecar schema/17-field profiles/digests, 8 ranks × two windows with identical `plan_fingerprint=6a4d9c6a03aedfedd679179d05c6fe59eb7317d4bebf6d6b5d39f9978b6932b5`, with real terminal partial and equal Index8 collective rhythm. Old source digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`, Packed new runtime digest `1ab2bbe4df9954467bb0acf0d371dce40dff8bd04cfa3c81ca0ec6fe76a94b4a`. These are DS-executor evidence, not firsthand GPT shell.
- **Both real CPU `--verify-payloads` legs BLOCKED exit2** at `unhandled Native payload leaf type: cosmos_framework.data.generator.action.utils.action_processing.ActionProcessingRecord`. DS read-only introspection showed additional `SequencePlan` dataclass. Output JSON absent, so `compare-cpu-reports` NOT_RUN. Neither valid Native Payload hash parity nor CFG replay confirmed on e3. No reason to repeat previously accepted static Lane A/C.

## Finding B0-DATACLASS-01 (MEDIUM — current e3 blocker)

- **Old source:** `tools/gates/v3_packed128_gateb_compare.py:339–373`, `_stable_payload_hash`, specifically old line370 fallback. Model-visible payload includes `ActionProcessingRecord` (frozen dataclass) and `SequencePlan` (mutable dataclass); walker handles tensor/list/dict/scalar but treats all dataclasses as unsupported opaque leaves.
- **Root cause:** Missing deterministic recursive dataclass serialization, not a RoboCasa source-data or Checkpoint defect.
- **Frozen contract:** B0 must hash **all** model-visible transformed Native input fields for each Consumer and compare Source vs Packed in both legs, preserving byte/semantic identity and fail-closed on unknown leaves. Same plan hash alone is insufficient; cannot silently drop unsupported fields.
- **Acceptance:** Encode concrete module-qualified class identity, dataclass field names/order and nested supported values; no repr, no skipped fields. Unknown non-dataclass values and cycles still fail closed. Check nested tensor/scalar changes alter hash. Pass real full-source CPU `--verify-payloads` in both legs, with nonempty `payload_witness` and exact `compare-cpu-reports` equality; source DCP unchanged.

## Remediation source review — NEW ec9d162b

- GitHub exact `e3e6df04..ec9d162b` has **only two diagnostic paths**, `tools/gates/v3_packed128_gateb_compare.py` and `tools/gates/test_v3_packed128_gateb_compare.py`; no production Trainer/Model, Root Gitlink, Checkpoint or launchers changed.
- New `_stable_payload_hash` uses `dataclasses.is_dataclass(item) and not isinstance(item,type)`, type-qualified class name, `dataclasses.fields` order and recursive `feed(field.name)/feed(field_value)`. Original Tensor/scalar/list/dict hashing preserved. Unknown nested non-dataclass leaves continue to throw Blocked. Cyclic collections/dataclasses now fail closed.
- Five new CPU negative/positive tests cover frozen record and mutable SequencePlan-shaped objects, field/tensor mutation, class identity, dict insertion order invariance, unknown object/class, cyclic structures, NaN field rejection. Author local representative fixture test **30 passed**, compile PASS; exact NEW remote SHA lint, tests and real data **not** run by GPT in DS environment. New code does not claim B1 GPU capability. `--mode paired-run` remains explicitly BLOCKED.
- The fix supports dataclass *structure* generically; if a nested action normalizer/codec is a non-dataclass unknown object, it remains blocked until separately reviewed. DS must report all distinct unknown leaf types/paths in one read-only probe if encountered, not drop fields.
- **Current finding disposition:** REMEDIATED_IN_SOURCE / EXECUTOR_REAL_CPU_WITNESS_PENDING. No new proven production bug.

## Narrow retest / gate boundary

On exact new `ec9d162b...`, DS_PRO runs 3-file Ruff/py_compile/pytest + negative paired-run; then **serial** Index8 and Packed128 CPU-only `--verify-payloads --hash-all-shards`, followed by `compare-cpu-reports`. Verify nonempty per-leg `payload_witness` and exact plan/payload fingerprints, source before/after SHA, clean import pair, no GPU/torchrun/Nsight. Retain all old Lane A/C and e3 B0 evidence, do not re-run old 484-path audit or edit source checkpoint. One report; GPT one final audit.

**No CPU Gate B0 closure until the new exact diagnostic SHA obtains complete executor Evidence. No GPU B1 authorization; no native FSDP8 DCP load/gradients/optimizer, Gate M migration or Formal30k restart.**
