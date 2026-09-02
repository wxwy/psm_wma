# R09-B2 P4-v4 preflight ChatGPT review history

## Scope

Root repository:
- `wxwy/psm_wma`
- branch: `V2`

Submodule:
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

This document consolidates ChatGPT review decisions previously discussed for Codex handoff.

## Review chain

### P4-v4 design v0.3

Verdict:
- `REQUEST_CHANGES`

Main findings:
- candidate payload schema and final P5 evidence schema needed byte-preserving contract.
- six-file dual-backend publication needed atomic semantics.

### P4-v4 design v0.4

Verdict:
- `APPROVE_TO_IMPLEMENT_P4_V4_PREFLIGHT_STATIC_TOOLS`

Approved scope:
- root static tooling.
- CPU-only regression tests.

Not approved:
- real preflight.
- staging creation.
- record/refreeze.
- evidence publication.
- GPU/training.

### Static implementation 010dfc7

Verdict:
- `REQUEST_CHANGES`

Findings:
- fake/minimal payload admission was possible.
- pair invariants and poison semantics were insufficient.

### Remediation 179f0f5

Verdict:
- `REQUEST_CHANGES`

Fixed:
- reused P5 final grammar.
- added pair validation.
- added poison checks.

Remaining:
- regression tests still bypassed key admission paths.

### Test hardening a77a6ca / da6158d

Verdict:
- `REQUEST_CHANGES`

Reason:
- drift fixtures improved.
- full pair fixture added.
- remaining identity mock coverage issue.

### Identity mock removal 5e4d56a

Verdict:
- `APPROVE_TO_CLOSE_P4_V4_PREFLIGHT_STATIC_TOOLS`

Reason:
- removed `_path_identity` mock from full admission test.
- admission path now uses real identity binding.

Approved scope remains static-only.

## Final authority note

The authoritative Codex-visible review artifact is this file under:

`docs/collab/chatgpt/reviews/`

CODEX_INBOX should only be used as transport/ledger. It does not replace the review artifact.
