# V3 Packed128 implementation receipt — 2026-10-13

Formal Root Implementation: c4731bca1a590663db88bd6cd74dbcf9fd513a85
Formal Child/Gitlink: c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686
Previous Child: 5ac9a904c46da658e1b3e0816d3a7d95ce99c945
GitHub compare: https://github.com/wxwy/cosmos-framework/compare/5ac9a904c46da658e1b3e0816d3a7d95ce99c945...c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686
Evidence category: source and exact Git diff only. GPT has not executed project-complete CPU tests, real H100 parity or formal training.

Owner contract: B_stream8, TBPTT16, active_GA2, world_size8, one Native Forward+Backward per GA member, full128 consumers/GA, 2 native model calls/optimizer/rank. No intermediate Batch16/32/64 trials.

Exact Child diff: nine files:
1. cosmos_framework/model/generator/mot/local_memory_grouped_window.py: slot-major pack_member with exact slot/episode/step/S0/prefix validation; one F/B per GA, n_member/N weighting, Candidate Local commit after successful backward.
2. cosmos_framework/model/generator/mot/local_memory_grouped_window_test.py: B8/T16/GA2, terminal128+8, S0, terminal-rebind, T32/GA3, rollback and synthetic FP32 packed-vs-index Local gradient oracle.
3. cosmos_framework/trainer/local_memory_grouped.py: model receives merged native payload/prefix batch once per GA; original FSDP/optimizer/GradScaler/Local ownership untouched.
4. cosmos_framework/trainer/local_memory_grouped_test.py: 128-sample native collate, one callback F/B per member, optimizer/GA/resume/async contracts.
5. examples/psm_wma_robocasa_corrected_telemetry.py: expected native call count equals GA member count and metric weights use actual consumer counts.
6. examples/psm_wma_robocasa_corrected_telemetry_test.py: 2-call packed and metric checks, audit-hash preservation and loss weighting.
7. cosmos_framework/utils/training_audit.py: model inputs slot-major; convert trace-only rows to original index-major identity SHA, rejecting duplicate/malformed coordinates.
8. examples/psm_wma_robocasa_corrected_phase5.py: native-layout version added to strict config_digest so old per-index checkpoint cannot silently resume in new mode.
9. examples/psm_wma_robocasa_corrected_phase5_test.py: digest-layout separation and observer GA member count.

Frozen production semantics: rank-local GA has 128+128 valid consumers/full window (256/rank, 2048/8ranks), partial terminal GA uses actual counts e.g. 128/136 and 8/136. Model loss weighting preserves current V3 whole-native scalar (not an unreviewed change to V2 auxiliary loss handling). Local TTT create_graph=True remains, graph not detached; candidate state published only after optimizer success.

Known limitations: V2 historical fixed-input real-model parity (~2.39% gradient-L2, 5% former threshold) does not certify new V3 packed path. Changed MoT batch packing, sigma/noise random stream, BF16/FSDP kernels and sample-normalization demand new parity. Current running Formal30k checkout and DCP were not touched.
Review: docs/collab/chatgpt/reviews/2026-10-13_V3_packed128_native_implementation_incremental_review_c4731bca_c8dabbb3.md
DS CPU handoff: docs/collab/chatgpt/requests/2026-10-13_DS_PRO_V3_packed128_native_CPU_Gate_and_GPU_parity_handoff.md