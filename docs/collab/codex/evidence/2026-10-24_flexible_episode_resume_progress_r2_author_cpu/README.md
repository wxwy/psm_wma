# Production HIGH-01 r2 — author CPU evidence

Formal Root6151e0712f28ace5d92258a8feb31fa8f1ee81c1 / unchanged Child813a550dab5d6b5b5e3be90d38bb97527956b4dc.

Final five-group combination:164 top-level passed +72 subtests,0 failure/error/skip. JUnit declares tests=236 but contains164 testcase elements; successful subtests are counted without individual XML elements. This is author evidence, not GPT or DS independent CPU acceptance.

Red uses the old CLI from6e10c8d4 and nine new finalization cases:8 failures/1pass. Green uses corrected CLI plus opening-limit guard:10pass. Red/green and final console logs/XML are byte-preserving gzip archives. Final junit.xml remains directly readable. No historical pass counts are added to this result.

commands.txt and frozen_source_sha256.json identify the run and15 files. Static checks verify syntax, unchanged protected paths/Child and exact tested source hashes. Source hashes also match formal commit blobs. source.patch is baseline6e10c8d4->formalRoot with zero context (--unidiff-zero required for application). artifact_sha256.json covers every other evidence file.

DS should lock the exact new Root/Child in a clean detached worktree and use the same five-file CPU combination, external logs/cache and Ruff0.12.7; adapt only environment paths. Any failure returns original evidence without production edits. No GPU/real model/Kitchen/DCP/training is authorized. New sources, original Job errors and cleanup are tested with the existing CPU fake harness; physical behavior is not established here.
