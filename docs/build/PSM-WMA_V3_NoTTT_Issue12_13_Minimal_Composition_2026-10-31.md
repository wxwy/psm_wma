# No-TTT Issue12 + Issue13 minimal composition candidate

Start from latest canonical V3 `b260290ef09ef25a8a41259aef153df5efff3369`.
Isolated Root branch `v3-nottt-integrated-20261031`; no canonical merge, real GPU,
model/data/DCP access or training Resume. Owner authorized a new combined Pair
and minimal synthetic composition check, not historical full-suite reruns.

## Reuse exact approved code

- Issue13 `24dbb677f7a60eeab6934c44352c7e00fa6d9b36`: exact three Root
  production blobs (two No-TTT launchers plus no_ttt_console.py) and three
  accompanying tests. No wrapper/argv/default change during composition.
- Issue12 `c66ade95b044d3664cd782d43d7917a604425db3`:
  exact Child/Gitlink `baf1b5bf46853e9849a91518803b9738fc216235` and Root
  receiver test. No Child file or new Child commit required. Its13 selected
  donor files and1,255 preserved canonical objects remain the approved set.
- Detailed exact-pair GPT APPROVE_CODE reviews are inherited from canonical
  docs/collab/chatgpt/reviews. Earlier candidates and their immutable evidence
  remain on published branches; reference them rather than relabeling old runs.
- New implementation adds only a focused composition test plus this runbook and
  bookkeeping. Existing EvalV2/current canonical sources and records preserved.

## Minimum CPU composition

Six new cases: real4/8-GPU shell entrypoints in synthetic Fresh/Resume, positive
workers8 for the approved world4/GA4 path, world4 workers0 synchronous control,
and a post-binding injected failure. The fake torchrun executable invokes real
CPU profile parsing, actual MatchedNoTTTTrainer.bind_grouped_stream and actual
AsyncLoader construction, replacing only Producer inputs/recipe metadata.
No model/optimizer, actual torchrun, distributed rank or Worker pool starts.
Real spawn/next-window overlap/Resume semantics remain covered by accepted
Issue12 evidence; no second performance experiment is necessary.

Assert Rank0 progress only, complete stdout/stderr raw log, exact failure code
and explicit error, no Trainer job directory, no RAW fallback at positive workers,
runtime-only profile, no RNG mutation at bind, original world/GA/T/B/phase/budget
argv. Existing8GPU launcher remains synchronous; positive-worker world8 support
is outside both approved candidates. No new CLI option or training default.

Bind exact Git objects before executing:3 Root production files match Issue13;
whole Child equals approved baf; all other Root production subtrees equal
canonical baseline. Scoped Ruff0.12.7/check/format/AST, bash -n, ShellCheck0.10.0,
clean exactPair/source-before-after, raw6-case JUnit and command/log/environment
records. No rerun of49/43/58/301 or GPU A/B. Stop on failure; preserve diagnostics.
Final author PASS is not GPT/DS independent Code Gate or runtime authorization.

## Handoff

Commit a new Root implementation with the existing approved Child/Gitlink,
publish only the isolated Root branch, retain exact source/artifact evidence and
append canonical-path Inbox within the candidate without rewriting canonical
history. Request fresh incremental **composition** Code Gate, then STOP. Later
formal Resume must be separately Owner-authorized from original complete C12200;
no A/B-generated checkpoint, original Job/config/identity/history operation here.
