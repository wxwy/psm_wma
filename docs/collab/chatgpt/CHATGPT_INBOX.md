# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

## Live rollover

- immediate prior live blob SHA: `7f87ea0acd7a8918b09c0cc96d55e21ee18085e0`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Causal Owner Identity Execution Design v0.1 REQUEST_CHANGES

Formal pair:
- root docs SHA: `5bf6e3d033d2ad6d9f68483c629f2d852f6a8b9d`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.1.md:23)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_causal_owner_identity_execution_design_v01_5bf6e3d_93a89ba.md`

Canonical review commit:
`ca685656178cb13a460586c504022bce4a65f7c8`

Current blockers: `2 HIGH` (`2 design/authority`, `0 child/runtime`).

Blockers:
1. The design places fixed-name CLEAN under a newly-created private authority parent, but inherited launcher/bootstrap authority still freezes CLEAN, `--cwd`, `--index`, and `--bootstrap-project-root` to `/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8`. The new private parent has no frozen canonical mapping to that path and its own causal anchor is not defined. Preserve the inherited fixed path under a trusted ROOT FD, or explicitly refreeze every changed path-bearing authority and causally anchor the private parent.
2. The retained owner authority is frozen only through native Git add/status/list/cleanup. It is not carried through backing-file handoff and final bootstrap/exec; inherited handoff still uses global `CLEAN + name` and bootstrap consumes the absolute root string. Freeze clean-FD-relative backing operations, final absolute-path→clean-FD identity admission, and owner-FD numeric/lifecycle rules so parent/clean FDs cannot collide with or leak past the exact final `{3,4,5}` ABI.

The `/proc/self/fd/<parent_fd>/CLEAN` Git mechanism is feasible in principle; the rejection is not about procfs itself. Exact acceptance and required CPU/static witnesses are in the canonical review.

Scope reminder: **no CPU/static implementation is authorized from this pair**. No real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
