# ChatGPT review — Stage-1 v1.7 request-instance design v0.7

Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`

Formal pair:
- root: `6361fdbcfded999e43a4efb86861f75734cef100`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`

Final verdict:
`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`

Blockers: `0`.
- Design/Authority: `0`
- Production implementation: `0`
- Evidence/Scope: `0`
- child/runtime: `0`

## Review disposition

v0.7 closes the two HIGH Design/Authority blockers from v0.6.

1. **Unique construction-authority consumption point is now unambiguous.** The design freezes the sequence `P0 non-consuming immutable input acquisition -> P1 non-consuming pure replay/projection -> C consuming construction attempt`. C begins, and the sole construction authority is permanently consumed, immediately before the first same-round `.git`, ref, remote, path-absence, or environment observation. Every C observation/identity/write/verification/exception failure is terminal and no-retry.
2. **Phase-P input acquisition is now explicitly authorized without ambient inference.** P0 is the only non-consuming read-only acquisition authority and is limited to exact Git-object-database reads of frozen launcher/base/outer/adapter/formal-tree/Gitlink objects and their blob/raw identities. Ambient worktree, output-path, source/checkpoint/manifest/data/cache, network and mutation reads remain prohibited. Verified outer/adapter bytes are the only allowed P1 inputs.
3. **Replay binding is mechanically constrained.** The closed `stage1_v17_launcher_replay` helper is pure and, on the canonical base SHA, enforces the canonical formal parent plus parser/source replacement-table digests before accepting the replay. v0.7 additionally binds the replay binding, base object/raw identity, replay output raw/length/SHA and parser identity into the P0 result.
4. **P1 remains pure and non-consuming.** It calls only the closed projection root `079167743685247d6aae62a671436e834411a3cb` on P0-verified injected bytes and returns the complete `ProjectedRequestClosure`; it cannot read Git/path/network/environment or write outputs.
5. **C preserves the previously approved construction closure.** The frozen v0.5 allowlist remains: local `.git`/config/local V2; exactly two timeout-protected `git ls-remote` queries with command/rc/stdout/stderr identities; fixed authority-ref and designated-path absence; six environment values; owner-FD/cwd/index/evidence targets. The P0/P1 closure and all C observations must be recorded in canonical JSON, with detached Markdown sidecar whole-JSON binding.
6. **No materialization authority is granted.** Successful C may write and mechanically verify exactly one docs-only request Markdown/JSON pair, then hard-stop for an independent exact-pair review. It does not authorize launcher/materializer execution, Stage-1 materialization/retry, payload/source/checkpoint/manifest/data/cache access, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

## Formal-scope checks

- Formal commit immediate parent is `66818c7edb267045f057e58bf76e1aa3239c666b`.
- Incremental scope is docs-only v0.7 plus `SESSION.md` / `TODO.md`; no runtime/project-code change.
- Formal root Gitlink resolves exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- The phrase “future formal root/its frozen parent Git object database” is interpreted under the explicit exact-object/OID constraints: P0 obtains already-existing immutable objects by frozen identities and does not require a not-yet-created future request commit to exist.

## Authorized consequence

After same-pair three-party approval, exactly one new construction authority exists under v0.7. It may execute P0/P1 non-consumingly and then one consuming C attempt to construct one fresh docs-only exact request pair. That future pair must receive an independent exact-pair three-party request review before any Stage-1 materialization authority can exist.
