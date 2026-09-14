# ChatGPT independent review — Stage-1 v1.7 launcher freeze design v0.2

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`
- Formal root: `699e8567669187faadf1c46b36bff02eabb0206e`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_launcher_freeze_design_v0.2.md:58)`

## Scope / pair verification

- The formal root resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- This round is docs-only design remediation. No launcher module/test implementation, request construction, Stage-1 retry/materialization, source/checkpoint/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized.
- v1.6 one-shot execution authority is explicitly recorded as consumed after the pre-exec outer-payload SHA fail-close; no direct retry authority survives.

## Prior HIGH disposition

The prior v0.1 HIGH is closed:
- formal design Gate now exactly matches live canonical Gate `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`;
- the positive requested verdict is explicitly `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC`;
- implementation-only / no-retry boundaries are explicit.

## Blocking finding — HIGH Design/Authority

`ReplayBinding.parser_replacements` is frozen as `tuple[tuple[str, str], ...]`, and the prose requires both replacement tables to have no duplicate key while every parser replacement must match an argv value exactly once; missing, extra, duplicate, or non-unique matches fail as `replay_drift`.

That contract cannot replay the exact frozen v1.6 base. In the formal parent launcher `RAW[2]`, the same clean-root value

`/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8`

appears as the complete value of both:
- `--cwd`
- `--bootstrap-project-root`

Both positions must become `/proc/self/fd/8` in the canonical v1.6 parser. Therefore:
- one value-only `(old,new)` entry has two matches and violates the required unique-match rule;
- two entries with the same `old` violate the frozen no-duplicate-key rule.

The canonical case therefore self-fails under the proposed API before implementation. This recreates the exact class of replay non-reproducibility that the launcher-freeze Gate is meant to remove.

## Exact acceptance

Replace value-only parser replacement authority with an unambiguous flag/position-aware contract, for example:

`parser_replacements: tuple[tuple[str, str, str], ...]` interpreted as `(flag, expected_old_value, new_value)`.

Equivalent index-aware authority is acceptable if equally frozen and testable. The contract must require:
1. each flag occurs exactly once in parsed `RAW[2]`;
2. its immediately following value equals the frozen expected old value;
3. replacement touches only that adjacent value;
4. duplicate flags/targets, missing flags, wrong old values, reordered pairs, extra matches, or ambiguous positions fail-close as `BLOCKED_AUTHORITY_NOT_CLOSED:<category>`;
5. the canonical case independently replaces both `--cwd` and `--bootstrap-project-root` even though their old values are byte-identical;
6. direct CPU/static tests include this duplicate-old-value canonical witness plus wrong-flag/wrong-adjacent-value/reordered-target negatives.

Keep the already-good boundaries unchanged:
- pure stdlib replay helper, no Git/path/FD/exec I/O;
- formal Git-blob caller responsibility and base length/SHA verification;
- zero pre-existing owner-FD then one adjacent insertion;
- exact parser/outer bytes+SHA checks;
- v1.6 authority consumed, no retry;
- no v1.7 request construction before implementation closure and a new independent request review.

## Blocker summary

- Design/Authority: 1 HIGH
- Production implementation: 0
- Evidence-only: 0
- child/runtime: 0

No implementation or Stage-1 retry is authorized by this review.
