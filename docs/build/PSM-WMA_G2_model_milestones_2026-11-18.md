# G2 model integration M00–M09 milestones (carried from PR #60)

These task-status notes were carried forward from the model integration branch without overwriting the newer V3 root task ledger.

- **G2-M00 / G2-M01 / G2-B-C0** — REVIEW (author ABI delivered, not independent approval)；Codex B；固定Root739d39cf/Child ec9356fafd1fd18cc0bd552b7eb23428f59df7f6。公共合同+归属表，11 CPU PASS/0skip、static PASS；A/C/D均ACK并依赖唯一C0。不以C0代替后继集成证据。

- **G2-M02 (A)** — REVIEW 作者CPU/已普通集成；Child4209b151/Root35a2580e交接和证据均保留，Reader/spatial生产blob未改；不是独立最终批准。

- **G2-M03 / G2-M04 (B core)** — REVIEW 作者CPU，Child固定7e888f217dfcddc35ed73782f65c6e0890c72c3a；UND共享helper、joint G/L、模型/FSDP/public generation接线；scoped198 PASS，旧C0 none/Local-only输出/grad/RNG逐位相同。尚未A/C/D组合或真实GPU/FSDP，不宣称M07完成。

- **G2-M05 (C)** — REVIEW 作者CPU/已普通集成；最终Child26243dae9be7a2ab7ef5d544f8759b398ce917f9、Root343421d6c2fb78d577739e118dbd600021c991d2；v2静态初始文本/native span/data adapter、严格G1 warm-start、optimizer/TRAIN_A-B/GA/Local边界、checkpoint及Phase5 overlay/runbook均保留。实际DATA_B/C、GPU/FSDP仍未验。

- **G2-M06 (D)** — REVIEW 作者CPU/已普通集成；固定Child6991142cb94256f497347db40f58ad0ee3f482aa及最终Root0be8fd36b28fca81ce7343c7bd7ab1c673d94783全部原始交接/证据/server runbook保留；actual mask SHA/key完整，world_size>1 Session cache拒绝。真实provider/weight-config versions factory尚未冻结。

- **G2-M07** — REVIEW 最终源码/CPU集成候选 Child9370c3858532b4d61630138431145c8360e86eb0，Root唯一绑定；A4209/C262/D699普通合入且36归属blob无损，30文件636 PASS/1原真实资产preflight SKIP/0fail/error。13项B组合含实际native action头、双Session缓存、严格G1 warm-start/A-B/model-optimizer-stage-RNG恢复；旧partial pair b7ea01d7/6d72及442证据保留。待独立审核，非GPU/FSDP批准。

- **G2-M08 / G2-M09** — TODO；真实 GPU/FSDP/恢复/cache-on-off/Local inner及DATA_B/C 由执行侧fixed pair验证，GA=1；正式batch/GA/预算/recipe/loader/provider待实测，不以CPU替代。
