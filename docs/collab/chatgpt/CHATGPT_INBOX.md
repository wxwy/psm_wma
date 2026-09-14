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

- immediate prior live blob SHA: `17c4e224c8b7bb01c66b7bb92487db4c28c6aff4`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Authority-root config grammar CPU/static implementation CLOSED

Formal pair:
- root implementation SHA: `08d5828cdb4c12afa3b798ff01826c91ceb8755a`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CONFIG-GRAMMAR-CPU-STATIC-REMEDIATION`

Verdict:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CONFIG_GRAMMAR_CPU_STATIC_IMPLEMENTATION`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_authority_root_config_grammar_bootstrap_full_corpus_08d5828_93a89ba.md`

Canonical review commit:
`63c7eef4f9f5ef8e644de71968150172cbc6ef6c`

Current blockers: `0`; Design/Authority blockers: `0`; Production/Authority blockers: `0`; Evidence-only blockers: `0`; child/runtime blockers: `0`.

Closure summary:
1. The prior HIGH Evidence blocker is closed. The new direct test extracts the actual inline config-parser segment emitted by `bootstrap_payload()` and executes it in an isolated temporary namespace.
2. For the exact frozen 14-tuple current config, bootstrap, frozen outer launcher and runtime adapter ordered canonical tuples are compared byte-for-byte using the same serialized representation.
3. The same three actual parser seams are driven with one frozen invalid corpus covering lowercase `V2 -> v2`, escaped/dotted/path subsection, quoted-header spacing, unknown tuple, duplicate triple, remote URL drift, submodule URL drift and include injection; exact `config-*` category equality is asserted for every case.
4. Existing real isolated `-I -S -B -c` bootstrap CLI category witnesses remain for `v2` and escaped-subsection cases.
5. Exact 14-tuple authority, case-preserving quoted subsection identity, raw-config digest, descriptor/no-symlink/route, config.worktree/commondir, Git-view drift and Git-isolation barriers are unchanged.
6. Incremental technical delta is test-only; production parser bytes and child/runtime are unchanged. Formal root resolves `cosmos-framework` exactly to reachable child `93a89ba...`.
7. Reported CPU/static evidence remains: root unittest 70/70 PASS, frozen outer witness 17/17 PASS, `py_compile` PASS and `git diff --check` PASS.

Execution boundary:
- This closes only the authority-root config-grammar CPU/static remediation Gate.
- It does **not** revive the consumed v1.3 Stage-1 execution authority and does not authorize any retry/materialization.
- Any future Stage-1 attempt must first construct a new exact request with fresh config/raw/path/ref observations and payload/request bindings, then obtain a separate same-pair single-attempt materialization approval.
- No production source/checkpoint/manifest/data/cache I/O, downstream collection/receipt/source-evidence/record/package/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1 is authorized by this closure.

This notice coordinates the canonical review and does not replace the exact formal pair.
