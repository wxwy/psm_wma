# ChatGPT review — Stage-1 v1.7 request-instance design v1.0

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`
- Formal root: `9c8b4adc71b92caad5ecaf6fb044f5c01a4f9d9a`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`
- Blockers: `0`; Design/Authority: `0`; Production: `0`; Evidence: `0`; child/runtime: `0`.

## Formal target / Gitlink

Fresh review is required because the formal root changed from the previously reviewed `de92df512e1a239e7c2fd2d8d6ea60c5fc9ca02c` to `9c8b4adc71b92caad5ecaf6fb044f5c01a4f9d9a` while the child remained `93a89ba61306d840a008813f62f26a34d54850f4`.

The formal root tree independently resolves `cosmos-framework` as a mode-160000 Gitlink exactly equal to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is reachable in `wxwy/cosmos-framework`.

The formal-root delta is one commit and is limited to `SESSION.md`, `TODO.md`, and the new docs-only design `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v1.0.md`. No child or project production code is changed by this formal target.

## Prior blocker closure

The v0.9 exact-pair review had one HIGH: P0 froze the replay helper source but not one complete canonical `ReplayBinding` authority. Its exact acceptance allowed the next design to embed every `ReplayBinding` field as frozen literals, provided all fields, ordered replacement tables, owner-FD values, and expected parser/outer identities were bound and alternate sources/drift were rejected pre-replay.

v1.0 takes exactly that route. It freezes:
- `formal_parent`, base path/blob/raw identity/byte length;
- owner FD flag/value;
- expected parser byte length/SHA;
- expected outer byte length/SHA;
- exactly 8 ordered `parser_replacements` rows;
- exactly 8 ordered `source_replacements` rows.

It explicitly forbids obtaining binding values from the replay test, environment, worktree, history, future request root, or any other object. `ReplayBinding` is a design literal authority, not a fourth P0 Git-object read.

## Independent consistency checks

The literal tuple matches the canonical tuple present in the already-closed replay witness at implementation root `50b0bffeb4c94b0994d7c7bf705077fb51a9e48f`. The exact v1.0 parser table hashes to `961985b47da32e589cfab7c3c064bd336f853fd319c701be3361ba6c129da707`; the source table hashes to `24d287620936fd334526b30745839527ce3720e2be3e55ea09de8309ffa71b05`, exactly matching `_CANONICAL_TABLE_DIGESTS` in the frozen replay helper.

The frozen replay helper requires canonical base SHA `8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`, formal parent `08d5828cdb4c12afa3b798ff01826c91ceb8755a`, both canonical table digests, ordered parser replacement uniqueness, owner-FD insertion, expected parser identity, and expected outer identity. The v1.0 literal binding supplies the corresponding exact values.

The derived outer remains `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8` and remains a replay-derived result rather than a Git source object. Only that verified derived outer plus the verified adapter bytes enter the previously closed projection helper.

## Authority / lifecycle boundary

v0.7-v0.9 authority not explicitly superseded remains in force: P0/P1 are non-consuming; C begins immediately before the first freshness observation and consumes the sole construction authority; any C failure is terminal and no-retry. Approval here authorizes only construction of one docs-only request instance under this frozen design, followed by independent exact-pair review.

## Verdict

`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`

No current blocker remains for this exact design pair.

## Scope reminder

This approval does **not** authorize Stage-1 materialization/execution/retry, launcher/materializer execution, source/checkpoint/manifest/data/cache I/O outside the separately approved construction allowlist, collection/receipt/publication, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.
