# ChatGPT review — Stage-1 v0.5 unified pre-C rehearsal implementation design v3.0

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-IMPLEMENTATION-DESIGN`
- Formal root: `6677343ff7bcc931d2c141ada46ced11de2fc318`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_pre_c_rehearsal_consumer_implementation_design_v3.0.md:24)`
- Blockers: `1 HIGH`; Design/Authority: `1 HIGH`; Production: `0`; Evidence/identity: `0`; child/runtime: `0`.

## Formal target / scope

The formal root resolves and its tree binds `cosmos-framework` as mode `160000` exactly equal to the declared child `93a89ba61306d840a008813f62f26a34d54850f4`. The target is docs/status-only for this Gate: the v3.0 design plus `SESSION.md`/`TODO.md`; no child/runtime implementation change is in scope.

## Positive findings

V3.0 usefully consolidates the previously fragmented static work into one sealed pre-C plan: capability identity, v0.5 output tuple, canonical JSON/Markdown/patch representation, same-object `patch_text`, dry-run add-only verification, post-write verifier, exact-once opaque consumer invocation, byte-exact readback and terminal no-retry behavior. It also keeps v0.3/v0.4 forbidden and does not authorize construction, consumer invocation, materialization or runtime execution.

## HIGH 1 — live freshness observations are moved before C but still declared non-consuming

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_pre_c_rehearsal_consumer_implementation_design_v3.0.md:24` (`rehearse_v05()` item 3), together with the stated non-consuming lifecycle.

V3.0 requires the supposedly non-consuming `rehearse_v05()` to read and freeze the exact v0.5 output absences, six-key environment, `.git`/config, local `V2`, the two remote V2/authority-ref queries, designated absence paths and their raw results. Those are the same live freshness/provenance observations that the inherited Stage-1 lifecycle places inside C.

The controlling V17 authority explicitly freezes: P0/P1 are non-consuming; **C must begin immediately before the first freshness observation and permanently consumes the one-shot authority**; and the `.git`/local-V2/remote-query/fixed-ref/designated-absence facts must be observed in the same zero-mutation C round. V21 changed the future tuple to v0.5 and preserved the capability/no-retry rules; it did not supersede this consumption boundary.

Therefore V3.0 cannot make the same live observations non-consuming merely by renaming them a rehearsal. If `rehearse_v05()` performs those real observations, authority is already consumed before `consume_once_v05()`. If instead they are injected old observations, they are not the required fresh same-round C evidence. The later C-time “freshness snapshot against sealed plan” does not erase the fact that the earlier live observations already crossed the frozen consumption boundary.

### Acceptance

Choose one explicit authority-consistent model and freeze it before implementation:

1. **Preserve the inherited lifecycle:** pre-C rehearsal may validate only static/injected capability metadata, serializer/canonicalization logic, query/path allowlists, dry-run patch semantics and post-write verifier behavior. It must not perform live `.git`, local-V2, remote-query, fixed-ref or designated-path freshness observations. C must begin before the first live freshness read; the required same-round observations then occur exactly once under C before the single opaque write. Any final request bytes that depend on those live values must be completed from that C snapshot, not from a prior live rehearsal.

or

2. If the project truly requires all live freshness observations and final request bytes to be sealed pre-C, introduce a separate explicit authority/lifecycle refreeze that supersedes the existing “C begins before first freshness observation” rule and defines why those live pre-C observations are non-consuming. The current V3.0 text does not do that.

No production/child/runtime blocker exists in this docs-only target.

## Verdict / boundary

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_pre_c_rehearsal_consumer_implementation_design_v3.0.md:24)`

No CPU/static implementation authority is granted for this exact pair.

Still NOT authorized: v0.5 construction; P0/P1/C; real consumer invocation; materialization; source/checkpoint/manifest/data/cache I/O; collection/receipt/record/publication; child/runtime/config mutation; GPU/CUDA/torchrun; training; evaluation; inference; LIBERO4IN1.
