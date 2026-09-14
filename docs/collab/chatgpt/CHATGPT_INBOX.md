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

- immediate prior live blob SHA: `410f223f08f4e6eb2db96a3b945ddfaed65ac4af`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 v1.7 launcher freeze design v0.4 APPROVED

Formal pair:
- root design SHA: `5acb0bdadcc5ecbc22b720e5eeac6a3c95780bdc`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_launcher_freeze_design_v04_5acb0bd_93a89ba.md`

Canonical review commit:
`ef8fec1a4577167ab60de6b1b416dcda299551aa`

Current blockers: `0`; Design/Authority blockers: `0`; Production implementation blockers: `0`; Evidence-only blockers: `0`; child/runtime blockers: `0`.

Closure summary:
1. The v0.3 HIGH is closed. v0.4 appends the four missing outer-source self-check replacements with exact surrounding-literal targeting:
   - bootstrap raw length `7538 -> 9406`;
   - bootstrap raw SHA `7e1c0ecc2161984a88ea0d0eae82f9f7ced709ca919f0302f74a3a068e08c9b8 -> ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097`;
   - parser/RAW[2] length `2427 -> 2336`;
   - parser/RAW[2] SHA `72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2 -> 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`.
2. Together with v0.3's flag/adjacent-value-aware parser table and original four source replacements, the design now freezes a complete canonical replay input.
3. Direct CPU/static witness must consume the complete parser table plus all eight source replacements and prove exact final outer payload `18875` bytes / `658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`, with drift negatives for each newly added self-check literal.
4. Formal root remains docs-only for this review; Gitlink resolves exactly to reachable child `93a89ba...`; no child/runtime production bytes changed.

Authorized next action after required same-pair approvals:
- implement only `tools/psm_wma/stage1_v17_launcher_replay.py` and `tools/psm_wma/test_stage1_v17_launcher_replay.py`;
- pure stdlib / CPU-static only;
- no `main()`, Git/path/FD/network/`os.execve` I/O, project clean-root/index/ref/evidence creation, source/checkpoint/data/cache access, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This approval does **not** authorize v1.7 request construction, Stage-1 retry/materialization, or revival of v1.6's consumed authority. A future v1.7 exact request requires implementation close approval, fresh observations, and separate request review/approval.

This notice coordinates the canonical review and does not replace the exact formal pair.
