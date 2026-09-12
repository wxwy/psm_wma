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

- immediate prior live blob SHA: `575df97acd90a88b49530e4876b2b62370dcc31b`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Execution Authority CPU/static Implementation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `bb17774ce6da4e4d14c57993fe97f813065de319`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:166)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_execution_authority_cpu_static_implementation_bb17774_93a89ba.md`

Canonical review commit:
`4b00b34f484d6f1fd0a1da12229e42c800ff0209`

Current blockers: `1 HIGH`.

Finding:
- the approved v0.1→v0.4 execution-authority chain requires the stdlib bootstrap to verify the complete adapter/authority/collection/audit formal-tree closure before any project import;
- current `bootstrap_payload()` validates only its own `sys.orig_argv`/contract and then directly executes `sys.path.insert(0, root)` + `runpy.run_module(...)`;
- the four module path/raw/blob checks occur later in `preflight_authority_invocation()`, after importing the adapter and its transitive project dependencies;
- therefore a drifted/shadowed collection or audit module may execute before the authority check that is supposed to reject it. The reported 88/88 suite does not provide the required pre-import causal witness for this case.

Exact remediation:
1. before `sys.path.insert` / `runpy`, make the stdlib bootstrap bind and verify the exact formal root, Git executable identity, project root, and all four module `(repo_path, blob_oid, raw_sha256)` identities;
2. verify regular/non-symlink path/type, raw SHA-256 and exact formal-tree `100644 blob` identity using only stdlib plus the frozen Git executable/env/prefix;
3. any mismatch must terminate before project import, project callback, authority Git/ref mutation or evidence write;
4. add direct isolated-interpreter adversarial witnesses that change only `immutable_source_collection.py` and separately the audit module while adapter/authority/bootstrap declarations remain unchanged, and prove no project-import side effect/ref/evidence is reached;
5. retain the existing bootstrap observation, endpoint, Git isolation/common-config, Evidence ABI, CAS and CPU/static contracts.

Formal root/Gitlink is valid; child commit is reachable. The implementation delta otherwise stays within the approved two root tooling/test files plus bookkeeping.

Scope reminder: no real materialization, source/checkpoint I/O, project origin/ref/evidence mutation, collection/receipt/publication, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized.

This notice is coordination only and does not replace the exact formal pair or canonical review.