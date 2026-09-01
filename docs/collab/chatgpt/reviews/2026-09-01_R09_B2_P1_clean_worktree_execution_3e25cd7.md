# R09-B2 P1 production-manifest clean-worktree execution adjustment review

- Request: `3e25cd7f3cddd8c74511d7478149c7e00a638235`
- Approved implementation/source: `4177e83088e6c2e0a2b620bfdf8593e325fc375b`
- Reviewed Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **APPROVE_P1_PRODUCTION_MANIFEST_CLEAN_WORKTREE**

## Decision

Using an independent clean checkout/worktree is acceptable and preferable to mutating or deleting user-owned untracked training/evaluation outputs in the main worktree. The P1 builder/verifier derive provenance and source hashes from the supplied `--root`, so a detached clean checkout pinned to the approved root revision and exact Gitlink preserves the intended source identity while isolating runtime artifacts from the user's active worktree.

## Mandatory execution conditions

1. Before the single build attempt, the alternate checkout must have root `HEAD == 4177e83088e6c2e0a2b620bfdf8593e325fc375b`, submodule `HEAD == 21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`, root Gitlink equal to that submodule revision, and no tracked/untracked source changes.
2. `artifacts/g0/r09/b2/p1_production_manifest_100x16x128/` in that checkout must not exist and must not be Git-tracked before launch.
3. Keep the previously approved frozen inputs and parameters unchanged: CPU-only, `CUDA_VISIBLE_DEVICES=`/no visible GPU use, optimizer_updates=100, grad_accum=16, max_samples_per_batch=128, shuffle_seed=42, existing LIBERO metadata and verified latent cache only.
4. Only the manifest builder followed by the existing P1 verifier is authorized. No MP4/VAE/model/weight I/O, no `torchrun`, training, evaluation or inference.
5. The build authorization is one-shot. If the build or verifier terminates with an error or leaves a partial target directory, do not overwrite/retry that path; preserve evidence and request a fresh path/review.
6. After the build, generated artifact files may make the alternate worktree non-clean; that is expected. No source file may change. The header/source provenance must still identify the pinned root/Gitlink, and the P1 verifier must PASS before the artifact can be used by P4.
7. Copying/committing the successful artifact back into the main repository is a separate evidence-publication step. Its hashes/content must remain bit-identical; this approval does not close P1 production-manifest evidence or P4 by itself.

## Scope

This approval is limited to the single CPU-only production-manifest build and its P1 verifier in the clean alternate checkout. It does not authorize P4 closure, P5, B2-T, GPU execution, `torchrun`, training, evaluation, inference, or broader changes.
