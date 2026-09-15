# ChatGPT independent review — Stage-1 v1.7 ContractV05 pre-C CPU/static

Formal pair:
- root: `8bc6e93547a5a3f7db541f3843a6d36a32d23181`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`

Gate:
`G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_pre_c_rehearsal.py:379)`

Blockers: `1 HIGH`
- Design/Authority: `0`
- Implementation/authority binding: `1 HIGH`
- Evidence/Scope: `0`
- child/runtime: `0`

## Positive closure

- Formal root resolves and its `cosmos-framework` Gitlink is exactly the declared child.
- The prior source-I/O blocker is closed: the replay-helper fixture is now frozen in-memory gzip/base64 bytes; the explicit `Path(...).read_bytes()` source read is gone.
- P0 exact root/path/blob/raw identity, P1 eight ordered identities, literal ReplayBinding, exact v0.5 paths, six-key environment, canonical JSON/Markdown/patch witnesses, typed query/absence records, retirement-before-freshness and terminal no-retry remain preserved.
- `ContractV05` is now the public rehearsal input type (with `RehearsalInputV1` only an alias to the same type), and the C01-C15 matrix is present.

## HIGH 1 — C08/C15 still allow foreign-but-self-consistent fixed authority-ref absence records

The consolidated contract claims C08 and C15 PASS, but `_validate_closure()` only requires:

- `local_authority_absence.predicate == "authority_absent"`;
- `remote_authority_absence.predicate == "authority_absent"`;
- both `target` strings are merely non-empty;
- `AuthorityAbsenceV1.identity_ok()` only proves `byte_length == len(raw)` and `sha256 == sha256(raw)`.

Therefore a foreign record such as a different non-empty `target` plus arbitrary foreign `raw` with matching length/SHA remains admissible during `rehearse_v05()`. The current fixture itself uses generic `refs/local-authority` / `refs/remote-authority` targets rather than proving equality to the inherited fixed authority-ref literal(s).

This violates the active convergence directive's explicit rule that identity checks must compare against independently frozen truth, not merely self-consistency, and that every identity-bearing field replaceable by a foreign-but-self-consistent value requires a negative pre-consumer test. It also contradicts matrix rows C08 and C15 being marked PASS.

### Required remediation — one class-wide pass

1. Bind the local and remote fixed authority-ref targets to their exact frozen inherited literals in the machine-readable contract/validator; `non-empty` is insufficient.
2. Preserve live observation data as live rehearsal truth, but require fixed fields (ref/path/argv/predicate/allowlist) to equal exact authority literals and require C freshness to equal the sealed rehearsal observation.
3. Add explicit foreign-but-self-consistent negative cases for both local and remote authority absence records: mutate target and raw together with recomputed length/SHA and prove failure before consumer invocation.
4. Sweep C01-C15 for the same pattern: every authority-fixed identity must compare to an independently frozen literal; live observations may be self-hashed only after their fixed observation target/query is exact and then must be sealed for C freshness.
5. Update the requirement matrix so every row actually includes the directive-required exact frozen expected literal/value/identity, not only a prose description/reference, and point each row to its positive and foreign-self-consistent negative witness.

No CPU/static closure is granted for this exact pair. v0.5 request construction/C/materialization/source-evidence, all real I/O, child mutation, GPU and training remain forbidden.
