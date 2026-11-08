# Issue24 Stage3A — Real H100 C-B1 1×1 Actor source-witness mismatch: REQUEST_CHANGES

**Formal verdict: REQUEST_CHANGES_H4_REAL_C1S1_ACTOR_SOURCE_WITNESSES.**

2026-11-08. Independent execution and review: GPT. Narrow remediation owner: Codex.

Frozen implementation pair: Root 599e7ce9d0e9ee5bb1cf96fe687bb28e35b6f77e; Child/Root Gitlink 11e1855d58cb9f017243a08d610fb33a4443b773. Root PR25 and Child PR7 remain Draft and unmerged. Docs-only commit successors are not a replacement for either implementation SHA.

## Actual bounded hardware run

Exactly one Policy Server GPU6 plus one genuine Wan BF16 B1/wait0 Worker GPU4 and one genuine RoboCasa CloseFridge Sim GPU4 were launched under an isolated EvalV2 fresh namespace. The Local-TTT L checkpoint was iter_000015000. The original configuration retained Python float terminate_grace_s=15.0 as an explicit H2 real-world proof. NVIDIA-only EGL and render group access had previously passed. Strict vendor and approved asset-manifest preflight, checkpoint and source fingerprint checks all passed.

Real Policy DCP loaded on GPU6; independent real Wan Worker loaded on GPU4 and passed its private bootstrap, actual CUDA UUID plus full NVML GPU index/PCI identity READY gate. These events show that the previous H2/H3 startup incompatibilities are now actually surpassed, in addition to their earlier CPU Code Gate approvals. The Worker later exited with return code 0 and no active owned group. The actual Actor exited with return code 1; Policy Server was then safely terminated. GPU4–7 ended at 0 MiB, without residual processes. Earlier real-model fixed-input Visual96, FastState, Prefix, Action exact0 PASS remains valid and independent from this gate.

## H4 HIGH: incompatible Root / Child sets

Root scripts/robocasa_eval_v2/runtime.py lines 524–600 builds an eight-source base set for the Actor, then adds 10 explicit frozen Child source files for C sim_shared_vae mode.

Child cosmos_framework/simulation/robocasa/eval_v2_worker.py lines 40–59 still constructs only the previous base set (plus phase_b transactions) and rejects any input whose source_files key set does not exactly equal the local expected modules. Thus the actual Actor rejected the Root-signed source set *before* calling render_devices.configure, env.reset, or env.step.

Child Actor old 8 labels:
worker, native, adapter, slot, rendering, media, generated_video, transactions.

Additional 10 Root C labels:
shared_client, local_client, transaction_client, feature_trace, feature_evidence, session_transactions, batch_transactions, vae_protocol, vae_worker, vae_client.

Actual Actor Config contained all 18 labels, no missing old labels, and all 18 files were present in the exact frozen Child Git checkout; all path and SHA256 checks individually passed. The sole mismatch is the unextended Child Actor expected-set contract. Actual traceback: ValueError: incomplete native source witnesses.

The original run report says status=partial, expected=1, invalid=1, valid=0, results_qualified=false; it is an invalid STARTUP attempt rather than a failed robot task or SR=0. No actual env.step, Action Chunk, Owner poststep receipt, Worker history IPC, Local-TTT transaction commit, Policy response ACK or Session End could be verified at this gate.

## Exact evidence

Authorized data host:
 /mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue24_h2_h3_599e7ce9_11e1855d_C1S1_real_20261108/

Machine-validated independent_H4_actor_source_witness_evidence.json SHA256:
 f8298ac777b4edad7f6187c061ac5c0e6f83aeaef56abeb95755fca33b4727ad

Raw fresh/dry-run logs, unchanged signed Actor Config, worker/server/actor stdout, process closure records and run summary are retained on server. No private Actor credentials or model files uploaded. Root/Child worktrees clean; GPU4–7 all0MiB post-exit.

## Required narrow Codex remedy

1. Prefer extending ONLY the Child Actor source-witness allowlist for the explicitly opted-in phase_b + sim_shared_vae profile, with the above exact 10 extra symbols and their actual imported module origin and source SHA256; use a fixed source-defined map, NEVER derive the allowlist from the untrusted cfg source_files.
2. Preserve exact set equality of source labels and exact per-label absolute path / SHA256, including old base8 and transactions. Any omission, extra label, wrong content hash, wrong import origin, source/checkout mismatch, wrong profile, or inconsistent mode must remain fail closed.
3. Legacy A/off and B/server_vae retain their existing strict eight-source expectation and behavior. Do not remove extra Root source witnesses, bypass Actor verification, rewrite Actor config after sealing, silently fall back to server_vae, or allow arbitrary source-key supersets.
4. Add focused CPU integration regression that builds the exact Root-supplied eighteen-label C Actor config and proves Actor membership and actual imported-source checks. Add negative missing/extra/wrong SHA/path/label/profile and pre-env.reset failure tests, plus A/B exact legacy protection. Include original RED/GREEN proof, Ruff, raw JUnit and a new exact Formal Root+Child Gitlink pair; request an independent GPT Code Gate before another real H100 attempt.
5. Avoid introducing an alternate runtime, broad refactor, model changes, new Bvae8 Action admission, 900EP runs or V3 merge.

**Final verdict: REQUEST_CHANGES_H4_REAL_C1S1_ACTOR_SOURCE_WITNESSES.** The previous H2/H3 narrow CPU and genuine Wan B1 numerical gates remain PASS; the first complete C-B1 real single-Server/single-Sim closed-loop gate is still BLOCKED before env.reset. Codex owns the smallest H4 source-witness contract patch; independent review must approve the new Pair before rerunning the same one-episode C-B1 smoke.
