# DS_PRO owner-relayed iter1300 static DCP + Gate B design evidence receipt

Date: 2026-10-13; DS_PRO reports purely read-only extraction, no torchrun/GPU/DCP load/training and no edit to old production.
Evidence category: text report owner-pasted to GPT (the full original report remains in conversation). GPT has no direct training-server DCP bytes or original command stdout.

Static iter1300 report:
- Old formal job: formal_verified_index_30k, original Index8 checkpoint path ends checkpoints/iter_000001300; latest_checkpoint.txt points iter_000001300. Owner explicitly ruled iter1400 save failed and disallowed its use.
- 4 DCP component .metadata files parsed by SafeUnpickler as Metadata(version=1.0.0). Model=569 entries; optim=2826; scheduler=10; trainer=49. All model/optim/scheduler/trainer 8 rank .distcp fragments present; zip CRC test passed for 32 shards. Model/optim rank0 EOCD counts match metadata entry counts.
- trainer iteration=1300, scheduler rank0 last_epoch=1300/_step_count=1301, 8 rank dataloader iteration=1300; profile/cache/source digests cross-rank reported consistent; episode identities 2188 unique, 64 assigned rank-local slot keys, each rank 18 tasks.
- Current old Index8 config_digest reported exactly 70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37, matching Formal30k preflight owner log.
- Files only statically validated. No DCP native restore/deserialization into model, optimizer, scheduler, local slow/fast state, RNG or FSDP collective tested. No exact raw per-rank profile tuple copied into report.

Gate B draft supplied by DS_PRO:
- Compared Index8 child 5ac9a904c46da658e1b3e0816d3a7d95ce99c945 to Packed128 child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686 but incorrectly called formal Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 the same Root for both.
- Proposed loading iter1300 with --phase resume for both layouts, locking random seed/sigma/noise/dropout and testing loss/grad/optimizer/Local. Draft thresholds loss rel <=1e-6; per-FQN max-abs gradient<=1e-6; optimizer param diff <=1e-6, Fast State elementwise same.
- Migration draft requires new Packed128 config_digest to equal old 70e9867f...df37 while also forbidding digest rewriting and strict Resume bypass. Current exact Packed128 implementation includes native_batch_layout in config_digest and Local restore checks top-level and Sidecar provenance digest against current.
- Draft profile claims all eight profile tuples identical and shows 16-element rank-free tail (8,0,8,2,96,15,256,64,256,32,4,16,0.1,64,16,17), while source _profile(window) returns 17 elements prefixed rank.

Independent GitHub source checks at review:
- wxwy/psm_wma formal old running Source Root b159f45906f7261d028aecc226ab7f2bb9807eb9 pins Child 937066ffd90f2bf783ad4fbb4909e9c0b8922982.
- intermediate old Index8 comparison root e730e3063ee3638f0bafd79473f52a76f851c935 pins Child 5ac9a904c46da658e1b3e0816d3a7d95ce99c945.
- new Packed128 formal Root c4731bca1a590663db88bd6cd74dbcf9fd513a85 pins Child c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686.
- Old formal to old comparison child differ in 4 telemetry/monitor only files; they are not one exact source pair.
- exact Packed phase5.py digest authority includes native_batch_layout, and local_memory_grouped_resume.py 120-125 and 172-180 reject wrong top-level or provenance config_digest; phase5.py _resume_checkpoint uses latest pointer and same job namespace.
- _profile() in local_memory_grouped_resume.py includes rank, world_size, seed, B, GA, plus 12 fixed geometry fields: total length 17, with rank first.

Evidence classification: static file completeness/provenance accepted within read-only scope; draft Gate B and migration plan require source-aware remediation. No production, child, checkpoint, pointer or GPU action taken by GPT.
Review: docs/collab/chatgpt/reviews/2026-10-13_V3_iter1300_static_checkpoint_GateB_and_migration_plan_fresh_evidence_review.md
DS reply request: docs/collab/chatgpt/requests/2026-10-13_DS_PRO_revise_GateB_index8_packed128_checkpoint_migration_plan.md