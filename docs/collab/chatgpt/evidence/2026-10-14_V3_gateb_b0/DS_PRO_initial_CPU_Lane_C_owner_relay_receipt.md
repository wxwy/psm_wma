# DS_PRO Gate B0 initial CPU batch evidence — accepted source-audit receipt, NOT Gate close

**Report provided in Owner conversation** on 2026-10-13, reviewed 2026-10-14. DS_PRO (validation only) declared `BLOCKED_CANDIDATE` because ZIP wasn't on DS host and diagnostic branch then only had numerics at `853cf9a850d62e01596cd175683e89b5cbab97ff`. No Lane B/D was run. This receipt records **DS-reported evidence**, not GPT firsthand DS machine stdout/files.

**Frozen formal source:** root `b159f45906f7261d028aecc226ab7f2bb9807eb9`, Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`. **Frozen Packed target:** root `c4731bca1a590663db88bd6cd74dbcf9fd513a85`, Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`. Actual source checkpoint `iter_000001300` only.

## Reported Lane A/C results (do not automatically re-run)

- Lane A (source/worktree/env): pair/Gitlink clean, no GPU; original candidate artifact missing only.
- Four metadata components: model569, optim2826, scheduler10, trainer49 entries; each of four had .metadata, overall 32 distcp shards, 8 rank sidecar pickle; all static read-only.
- 8 rank dataloader sidecars: format `psm_v3_corrected_grouped_local_v2`, iteration1300; profile `(rank, 8, 0, 8, 2, 96, 15, 256, 64, 256, 32, 4, 16, 0.1, 64, 16, 17)`; config_digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`; nested provenance and 4 finite CPU fp32 fast tensors matched; manifest/corpus/binding verified. Raw source catalog: 9126 episodes / 18 underlying task classes.
- CPU pure Planner created two consecutive windows for all8 ranks with the **actual** counts below. Index8 per rank per window has **16 calls GA0 + 16 calls GA1** (safe equal collective call count at the planner level); this is not proof of real FSDP execution safety beyond call counts.
- Checkpoint before/after: DS report 484-path normalized manifest `size+sha256+mtime_ns` had **0 content differences**. Of these, all 44 actual iter1300 DCP/sidecar files unchanged. DS raw manifests live on its host at `/tmp/ds_pro_v3_gateb_b0_20261013/ckpt_before_manifest.json` and `ckpt_after_manifest.json` (GPT did not read them directly).

| rank | plan0 GA0,GA1 | plan1 GA0,GA1 | plan0 terminal GA0,GA1 | plan1 terminal GA0,GA1 |
|---:|---|---|---|---|
|0|128,128|122,128|0,0|1,0|
|1|128,123|115,128|0,1|1,0|
|2|111,128|128,128|2,0|0,0|
|3|113,128|128,128|1,0|0,1|
|4|123,122|116,128|1,1|1,0|
|5|113,128|128,128|2,0|0,0|
|6|101,128|125,128|4,0|1,0|
|7|128,128|128,128|0,0|0,0|

**Important implication:** True frozen iter1300 successor already covers Terminal Partial on several ranks while Index8 maintains 16/16 call rhythm for both windows. The future B1 design must still cover Full×P0/P1 and Terminal×P0/P1 per Owner's explicit four decisions. Planner-level symmetry does NOT prove gradient parity, Local-TTT semantics or actual collective synchronization.

## Candidate delivery remediation

GPT verified original 5-file ZIP SHA256 `911946134effd478071ef61180ff0eaadaee4721f4b7dc70080a6b5e348c6852` and **committed byte-identical source content** to isolated branch `v3-gateb-comparator-b0`, new exact HEAD `528c100fd120c3fad52739f2ec09a8cd8cab50e6`. Files: tools/gates/v3_packed128_gateb_compare.py, v3_gateb_numerics.py, test_v3_packed128_gateb_compare.py, docs/DS_PRO_V3_GATEB_B0_CPU_VALIDATION_2026-10-13.md, tools/gates/GATE_B0_README.md. Root Formal V3 implementation and Gitlink unchanged. GPT local CPU run on exact ZIP code: `21 passed` and `py_compile exit0`; GPU `paired-run` intentional reject exit2; Ruff not available locally. This is **not** DS Lane B/D evidence or B0 Gate close.

**Next only:** DS_PRO completes skipped Lane B (Ruff/compile/pytest/negative) and Lane D (both pinned producer CPU legs + report comparator) using precise branch source; one consolidated report; GPT one independent review. No GPU/torchrun/Nsight/real DCP FSDP8 load, DCP mutation, checkpoint migration or formal resume authorized.
