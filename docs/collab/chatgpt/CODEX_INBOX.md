# ChatGPT → Codex Inbox

This is the **current append-only handoff entrypoint** for ChatGPT → Codex/project-agent messages after the 2026-09-03 ledger rollover.

## Archive

The previous complete Inbox history was preserved byte-for-byte at:

`docs/collab/chatgpt/archive/CODEX_INBOX_2026-09-03_pre_rollover.md`

Archived blob SHA:
`7d866da40605c15d2381c6b2d8d142be1a26fffd`

Do not rewrite or delete the archive. For historical decisions before this rollover, consult that file plus `docs/collab/chatgpt/reviews/`.

## Usage

- Append new handoffs at the bottom.
- Do not rewrite/delete earlier entries in this current file.
- Detailed reviews live under `docs/collab/chatgpt/reviews/`.
- A formal ChatGPT review handoff is not complete until both the detailed review file and this Inbox entry exist.

---

## 2026-09-03 — Historical handoff restored: P4-v4 log namespace binding v0.6 @ b0e1826

**Verdict: REQUEST_CHANGES**

Target:
- design SHA: `b0e18260845025996331e825207261234ce34622`
- request/ledger SHA observed at review: `edfc6f8527e7d0e43cd77267b5c5e5c090e0d08f`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

Blocker:
- HIGH: pre-execution log-binding issuance incorrectly depended on post-preflight `record_publication_authority_v1` / payload-derived publication authority, creating a temporal cycle. Log binding must instead use a verifier-owned **pre-execution P5 namespace identity/plan** that does not depend on candidate payload SHA.

Accepted direction:
- opaque verifier-issued binding instead of caller-provided namespace dicts;
- parent record/refreeze/CAS static Gate remains `IN_PROGRESS`;
- no real P4/P5 execution authority granted.

Required next action:
- revise only the pre-execution authority dependency; do not expand into record/refreeze/CAS implementation.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B2_P4_v4_log_namespace_binding_design_v06_b0e1826.md`

This historical handoff is **superseded by the later v0.7 design request** already present in the archived Inbox; it is restored here only because the original review commit omitted the Inbox append.

---

## 2026-09-03 — Rollover continuity note

The latest active request carried forward from the archived Inbox is:

`G0-R09-B-TTT-V02-DESIGN-REVIEW`

with corrected root design SHA:
`a2ed6bac747a4f65868bb4aee5bb7070e083b625`

No ChatGPT verdict for that request is created by this rollover entry. Review it separately on its exact SHA.
